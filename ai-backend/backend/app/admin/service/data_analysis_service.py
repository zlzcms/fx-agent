#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agents.data_analyze_agent import DataAnalyzeAgent
from backend.agents.agents.get_users_agent import GetUsersAgent
from backend.agents.tools.data_to_markdown import users_to_markdown
from backend.app.admin.model.ai_model import AIModel
from backend.app.admin.model.ai_training_log import AITrainingLog
from backend.app.admin.service.report_log_service import report_log_service
from backend.app.admin.service.risk_tag_service import risk_tag_service
from backend.app.admin.types import (
    AnalysisPrompt,
    AnalysisResult,
    BasicInfo,
    DataSourceConfig,
    ModelConfig,
    ProcessAnalysisResult,
    QueryCondition,
    RiskTagTemplate,
    TimeRange,
    TrainingLogResult,
    UserDataResult,
    UsersInfo,
)
from backend.common.enums import AnalysisType, RiskType, TrainingLogType
from backend.common.log import logger
from backend.database.db import get_db
from backend.utils.time_utils import generate_time_range


class DataAnalysisService:
    """数据分析服务类，协调各种智能体进行数据分析"""

    def __init__(self) -> None:
        self.basicInfo: BasicInfo = {}
        self.data_sources: Dict[str, DataSourceConfig] = {}

    async def get_user_data(
        self,
        db: AsyncSession,
        query_types: List[str],
        data_permission_values: List[str],
        condition: Optional[QueryCondition] = None,
        basicInfo: Optional[BasicInfo] = None,
        crm_user_id: Optional[int] = None,
        **kwargs: Any,
    ) -> UserDataResult:
        if basicInfo is None:
            basicInfo = {}
        if condition is None:
            condition = {}

        self.basicInfo = basicInfo
        config = await self._get_model(db, basicInfo.get("ai_model_id"))
        self.basicInfo["model"] = config
        condition_result = await self._query_mcp_data_by_condition(condition)
        self.data_sources = {}

        for query_type in query_types:
            self.data_sources[query_type] = DataSourceConfig(
                user_id=data_permission_values,
                range_time=TimeRange(
                    data_start_date=condition_result.get("start_date"),
                    data_end_date=condition_result.get("end_date"),
                ),
            )

        get_users_agent = GetUsersAgent()
        logger.info(f"DataAnalysisService.get_user_data 传递crm_user_id: {crm_user_id}")
        result = await get_users_agent.get_users(data_sources=self.data_sources, crm_user_id=crm_user_id)

        if result.get("success"):
            return UserDataResult(
                success=True,
                message=result.get("message", "用户数据获取成功"),
                data=result.get("data"),
            )
        else:
            raise Exception(result.get("message", "用户数据获取失败"))

    async def analyze_data(
        self,
        db: AsyncSession,
        users_info: UsersInfo,
        basicInfo: Optional[BasicInfo],
        llm_config: Optional[ModelConfig] = None,
    ) -> AnalysisResult:
        if llm_config is None:
            llm_config = {}

        analysis_prompt = await self._get_analysis_prompt(db, basicInfo)

        result: AnalysisResult = {
            "status": "rejected",
            "message": "无数据可分析",
            "data": None,
        }

        if users_info and users_info.get("data"):
            users_markdown_data = users_to_markdown(users_info)
            # 将模型配置包装在llm字段下，以符合Base类的期望格式
            agent_config = {"llm": llm_config} if llm_config else {}
            data_analyze_agent = DataAnalyzeAgent(config=agent_config)
            success, data, data_markdown = await data_analyze_agent.report_analyze_data(
                user_query="",
                conversation_history=None,
                analyze_data=users_markdown_data,
                analysis_prompt=analysis_prompt,
                data_request=self.data_sources,
                is_property_analysis=True,
            )
            agent_result = data_analyze_agent.result
            if agent_result:
                result = AnalysisResult(
                    status="accepted",
                    message="分析完成",
                    data=agent_result,
                    confidence=agent_result.get("confidence"),
                    analytical_report=agent_result.get("analytical_report"),
                    property_analysis=agent_result.get("property_analysis"),
                )

        return result

    async def analyze_user_data(
        self,
        db: AsyncSession,
        query_types: List[str],
        data_permission_values: List[str],
        condition: Optional[QueryCondition] = None,
        basicInfo: Optional[BasicInfo] = None,
        crm_user_id: Optional[int] = None,
        **kwargs: Any,
    ) -> AnalysisResult:
        try:
            user_result = await self.get_user_data(
                db, query_types, data_permission_values, condition, basicInfo, crm_user_id=crm_user_id, **kwargs
            )
            users_info = {"data": user_result.get("data")}
            result = await self.analyze_data(db, users_info, basicInfo, llm_config=basicInfo.get("model", {}))
            return result
        except Exception as e:
            return AnalysisResult(
                status="rejected",
                message=str(e),
                data=None,
            )

    async def _query_mcp_data_by_condition(self, condition: Optional[QueryCondition] = None) -> Dict[str, Any]:
        if condition is None:
            condition = {}

        results: Dict[str, Any] = {}
        data_time_range_type = condition.get("data_time_range_type")
        data_time_value = condition.get("data_time_value")
        fixed_end_time = condition.get("fixed_end_time")

        if data_time_range_type and data_time_value:
            start_time, end_time = generate_time_range(data_time_range_type, data_time_value, fixed_end_time)
            results = {"start_date": start_time, "end_date": end_time}
        if condition.get("start_date"):
            results["start_date"] = condition.get("start_date")
        if condition.get("end_date"):
            results["end_date"] = condition.get("end_date")
        return results

    async def _get_risk_tag_template(self, db: AsyncSession, risk_type: Optional[RiskType]) -> List[RiskTagTemplate]:
        if not risk_type:
            return []

        risk_tags = await risk_tag_service.get_by_risk_type(db, risk_type=risk_type)
        if not risk_tags:
            return []

        return [
            RiskTagTemplate(
                id=tag["id"],
                name=tag["name"],
                description=tag["description"],
            )
            for tag in risk_tags
        ]

    async def _get_analysis_prompt(self, db: AsyncSession, basicInfo: Optional[BasicInfo] = None) -> AnalysisPrompt:
        if basicInfo is None:
            basicInfo = {}

        prompt: AnalysisPrompt = {
            "role_prompt_template": "",
            "property_analysis_format": "",
            "analytical_report_format": "",
        }

        try:
            # 安全获取基础信息，避免 None 值
            model_definition = basicInfo.get("model_definition") or "请根据数据分析用户需求，生成分析报告。"
            prompt["role_prompt_template"] = model_definition

            # 安全获取表格模板
            try:
                property_analysis_format = basicInfo.get("output_format_table", {})
            except Exception as e:
                logger.warning(f"获取表格模板失败: {str(e)}")
                property_analysis_format = {}

            analytical_report_format = basicInfo.get("output_format_document") or ""
            prompt["property_analysis_format"] = property_analysis_format
            prompt["analytical_report_format"] = analytical_report_format

            # 获取风险标签模板
            risk_type = basicInfo.get("risk_type")
            if risk_type:
                risk_tags = await self._get_risk_tag_template(db, risk_type)
                if risk_tags:
                    # 将风险标签格式化为字符串，供AI提示词使用
                    risk_tags_str = "\n".join(
                        [
                            f"{{'id': '{tag['id']}', 'name': '{tag['name']}', 'description': '{tag['description']}'}}"
                            for tag in risk_tags
                        ]
                    )
                    prompt["risk_tags_template"] = risk_tags_str

            return prompt

        except Exception as e:
            logger.exception(f"构建分析提示配置失败: {str(e)}")
            # 返回最基本的安全配置
            return AnalysisPrompt(
                role_prompt_template=f"你是一个专业的{basicInfo.get('name', '数据分析')}助手",
                property_analysis_format="",
                analytical_report_format=basicInfo.get("model_definition", "请分析提供的数据"),
            )

    async def _get_model(self, db: AsyncSession, model_id: Optional[str] = None) -> ModelConfig:
        # 查询AI模型配置
        model_result: ModelConfig = {}

        # 如果model_id为空，尝试获取系统默认模型
        if not model_id:
            try:
                from backend.plugin.config.crud.crud_config import config_dao

                config = await config_dao.get_by_key(db, "ai_default_model_id")
                if config and config.value:
                    model_id = config.value
            except Exception as e:
                logger.debug(f"获取系统默认模型失败: {str(e)}")

        # 如果还是没有model_id，返回空配置
        if not model_id:
            return model_result

        stmt = select(AIModel).where(AIModel.id == model_id)
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return model_result

        if not model.status:
            return model_result

        # 准备LangGraph代理的配置
        model_result = ModelConfig(
            id=model.id,
            name=model.name,
            api_key=model.api_key,
            base_url=model.base_url,
            model_name=model.model,
            temperature=model.temperature,
        )
        return model_result

    def _serialize_datetime_objects(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    async def _add_training_log(self, result: Dict[str, Any], success: bool = True) -> TrainingLogResult:
        try:
            model = self.basicInfo.get("model")
            if not model:
                return TrainingLogResult(success=False, message="模型信息不存在")

            clean_basic_info = self._serialize_datetime_objects(self.basicInfo)
            if not result:
                result = {}
            data = result.get("data", {})
            training_log = AITrainingLog(
                model_id=model.get("id"),
                model_name=model.get("name"),
                prompt_template=result.get("prompt"),
                success=success,
                data=result,
                assistant_id=clean_basic_info.get("assistant_id", ""),
                log_type=clean_basic_info.get("training_type", TrainingLogType.ai_assistant.value),
                score=data.get("confidence", 0),
                content=data.get("analytical_report", ""),
                ai_response=result,
                base_info=clean_basic_info,
            )

            db_gen = get_db()
            db = await anext(db_gen)
            try:
                db.add(training_log)
                await db.commit()
            finally:
                await db.close()

            return TrainingLogResult(success=True, message="训练日志添加成功")

        except Exception as e:
            logger.exception(f"训练日志添加失败: {str(e)}")
            return TrainingLogResult(success=False, message=f"训练日志添加失败: {str(e)}")

    async def process_analysis_result(
        self,
        db: AsyncSession,
        task_status: Dict[str, Any],
        assistant_id: str,
        member_ids: List[Any],
        basic_info: Dict[str, Any],
        data: Any,
    ) -> ProcessAnalysisResult:
        try:
            analysis_data = task_status.get("result", {})

            # 构建分析报告日志
            report_log = {
                "assistant_id": assistant_id,
                "model_id": basic_info.get("ai_model_id"),
                "member_ids": member_ids,
                "sql_data": task_status.get("file"),
                "prompt_data": "",
                "input_prompt": task_status.get("prompt", {}),
                "report_status": True,
                "report_score": analysis_data.get("confidence", 0),
                "report_result": json.dumps(analysis_data),
                "report_table": json.dumps(analysis_data.get("property_analysis", {})),
                "report_document": analysis_data.get("analytical_report", ""),
                "ai_response": data,
                "id": None,
            }

            # 保存分析报告日志
            await report_log_service.add_ai_assistant_report_log(db=db, log_data=report_log)

            return report_log

        except Exception as e:
            logger.exception(f"处理分析结果失败: {str(e)}")
            raise

    async def save_training_log(
        self,
        db: AsyncSession,
        assistant_id: str,
        model_id: str,
        model_name: str,
        log_type: TrainingLogType,
        data: Dict[str, Any],
        ai_response: Optional[Dict[str, Any]] = None,
        success: bool = True,
        prompt: str = "",
        basic_info: Optional[Dict[str, Any]] = None,
    ) -> TrainingLogResult:
        try:
            clean_basic_info = self._serialize_datetime_objects(basic_info or {})
            clean_data = self._serialize_datetime_objects(data or {})
            clean_ai_response = self._serialize_datetime_objects(ai_response or {})

            training_log = AITrainingLog(
                model_id=model_id,
                model_name=model_name,
                prompt_template=prompt,
                success=success,
                data=clean_data,
                assistant_id=assistant_id,
                log_type=log_type,
                score=clean_data.get("confidence", 0) if clean_data else 0,
                content=clean_data.get("analytical_report", "") if clean_data else "",
                ai_response=clean_ai_response,
                base_info=clean_basic_info,
            )

            db.add(training_log)
            await db.commit()

            return TrainingLogResult(success=True, message="训练日志添加成功")

        except Exception as e:
            logger.exception(f"训练日志添加失败: {str(e)}")
            return TrainingLogResult(success=False, message=f"训练日志添加失败: {str(e)}")

    async def build_basic_info(
        self,
        db: AsyncSession,
        assistant_id: str,
        ai_model_id: str,
        name: str,
        description: Optional[str] = None,
        background: Optional[str] = None,
        model_definition: Optional[str] = None,
        output_format_table: Optional[Dict[str, Any]] = None,
        output_format_document: Optional[str] = None,
        analysis_type: AnalysisType = AnalysisType.general,
        risk_type: Optional[RiskType] = None,
        training_type: Optional[TrainingLogType] = None,
        **kwargs: Any,
    ) -> BasicInfo:
        # 如果ai_model_id为空，尝试获取系统默认模型
        actual_model_id = ai_model_id
        if not actual_model_id:
            try:
                from backend.plugin.config.crud.crud_config import config_dao

                config = await config_dao.get_by_key(db, "ai_default_model_id")
                if config and config.value:
                    actual_model_id = config.value
            except Exception as e:
                logger.debug(f"获取系统默认模型失败: {str(e)}")

        model_info = await self._get_model(db, actual_model_id)
        basic_info: BasicInfo = {
            "assistant_id": assistant_id,
            "ai_model_id": actual_model_id,  # 使用实际使用的模型ID（可能是默认模型）
            "model_definition": model_definition or "",
            "name": name,
            "description": description or "",
            "background": background or "",
            "output_format": "both",
            "output_format_table": output_format_table or {},
            "output_format_document": output_format_document or "",
            "analysis_type": analysis_type,
            "model": model_info,
            "training_type": training_type,
        }

        if risk_type:
            basic_info["risk_type"] = risk_type

        basic_info.update(kwargs)

        return basic_info


# 创建服务实例
data_analysis_service = DataAnalysisService()
