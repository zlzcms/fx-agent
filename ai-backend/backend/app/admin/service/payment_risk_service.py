#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出金风控分析服务
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_assistant import crud_risk_assistant
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.app.admin.service.report_log_service import report_log_service
from backend.common.enums import AnalysisType, RiskType, TrainingLogType
from backend.common.log import logger

# 配置日志
data_analysis_service = DataAnalysisService()


class PaymentRiskService:
    """出金风控分析服务"""

    def _extract_recommendations(self, analysis_data: dict) -> str:
        """
        从分析数据中提取推荐建议
        尝试从多个可能的位置获取recommendations数据
        """
        recommendations = analysis_data.get("recommendations", [])

        # 格式化为字符串
        if recommendations:
            return "\n".join([f"• {rec}" for rec in recommendations])

        return ""

    async def analyze_payment_risk_async(
        self, member_id: int, db: AsyncSession, task_id: str, progress_callback=None
    ) -> Dict[str, Any]:
        """异步分析用户出金风险（用于Celery任务）"""
        try:
            logger.info(f"开始异步分析用户 {member_id} 的出金风险，任务ID: {task_id}")

            # 更新进度
            if progress_callback:
                await progress_callback(10, "获取风控助手配置...")

            # 1. 获取风控助手配置
            assistant = await crud_risk_assistant.get_by_risk_type(db, risk_type=RiskType.PAYMENT)
            if not assistant:
                logger.error("未找到出金风控助手配置")
                return {
                    "status": False,
                    "message": "未找到出金风控助手配置",
                    "data": {},
                }

            # 更新进度
            if progress_callback:
                await progress_callback(20, "获取用户信息...")

            # 2. 获取用户信息
            user_info = await self._get_user_info(db, member_id)
            if not user_info:
                logger.warning(f"未找到用户 {member_id} 的信息")
                return {
                    "status": False,
                    "message": "未找到用户信息",
                    "data": {},
                }

            # 更新进度
            if progress_callback:
                await progress_callback(40, "准备分析参数...")

            # 3. 准备分析参数
            basic_info = await self._prepare_basic_info(db, assistant, user_info)

            # 更新进度
            if progress_callback:
                await progress_callback(60, "开始数据分析...")

            # 4. 执行数据分析
            query_types = [
                "user_mt5_positions",
                "user_mt5_user",
                "user_mt5_trades",
                "user_mt4_user",
                "user_mt4_trades",
                "user_mtlogin",
                "user_forword_log",
                "user_login_log",
                "user_amount_log",
                "user_data",
            ]
            data_permission_values = [member_id]
            condition = {"data_time_range_type": "quarter", "data_time_value": 1}

            try:
                # 直接获取用户数据
                user_result = await data_analysis_service.get_user_data(
                    db=db,
                    query_types=query_types,
                    data_permission_values=data_permission_values,
                    condition=condition,
                    basicInfo=basic_info,
                    crm_user_id=member_id,  # member_id就是crm_user_id
                )

                # 直接分析数据
                users_info = {"data": user_result.get("data")}
                analysis_result = await data_analysis_service.analyze_data(
                    db, users_info, basic_info, basic_info.get("model", {})
                )

            except Exception as e:
                logger.error(f"数据分析服务调用失败: {str(e)}")
                return {
                    "status": False,
                    "message": f"数据分析服务调用失败: {str(e)}",
                    "data": {},
                }

            # 更新进度
            if progress_callback:
                await progress_callback(80, "保存分析结果...")

            # 5. 保存分析结果
            report_log = await self._save_analysis_result(
                db=db,
                assistant=assistant,
                member_id=member_id,
                user_info=user_info,
                basic_info=basic_info,
                analysis_result=analysis_result,
                input_prompt="",
            )

            # 更新进度
            if progress_callback:
                await progress_callback(100, "分析完成")

            return {
                "status": True,
                "message": "出金风控分析完成",
                "data": analysis_result,
                "report_id": report_log.get("id") if report_log else None,
            }

        except Exception as e:
            logger.exception(f"异步出金风控分析失败: {str(e)}")
            return {
                "status": False,
                "message": f"异步出金风控分析失败: {str(e)}",
                "data": {},
            }

    async def _get_user_info(self, db: AsyncSession, member_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            from backend.app.admin.crud.crud_user import user_dao

            user = await user_dao.get(db, member_id)
            if not user:
                return None

            return {
                "id": user.id,
                "nickname": user.nickname or user.username,
                "email": user.email,
                "phone": user.phone,
                "username": user.username,
                "created_time": user.created_time.isoformat() if user.created_time else None,
            }
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    async def _prepare_basic_info(self, db: AsyncSession, assistant: Any, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """准备基础信息"""
        try:
            # 获取输出格式配置
            output_format_table = assistant.variable_config or {}
            output_format_document = assistant.report_config or ""

            # 构建基础信息
            basic_info = await data_analysis_service.build_basic_info(
                db=db,
                assistant_id=assistant.id,
                ai_model_id=assistant.ai_model_id,
                name=assistant.name,
                description=assistant.role,
                background=assistant.background,
                model_definition=assistant.task_prompt,
                output_format_table=output_format_table,
                output_format_document=output_format_document,
                analysis_type=AnalysisType.risk,
                risk_type=RiskType.PAYMENT,
                training_type=TrainingLogType.risk_control_assistant,
            )

            # 添加用户信息
            basic_info.update(
                {
                    "user_info": user_info,
                    **assistant.to_dict(),
                }
            )
            return basic_info
        except Exception as e:
            logger.error(f"准备基础信息失败: {e}")
            return {}

    async def _save_analysis_result(
        self,
        db: AsyncSession,
        assistant: Any,
        member_id: int,
        user_info: Dict[str, Any],
        basic_info: Dict[str, Any],
        analysis_result: Dict[str, Any],
        input_prompt: str,
    ) -> Optional[Any]:
        """保存分析结果到risk_report_log"""
        try:
            # 构建风控报告日志
            risk_report_log = {
                "assistant_id": assistant.id,
                "member_id": member_id,
                "user_info": user_info,
                "basic_info": basic_info,
                "analysis_result": analysis_result,
                "input_prompt": input_prompt,
                "created_time": datetime.now(),
            }

            # 保存到数据库
            report_log = await report_log_service.add_ai_assistant_report_log(db=db, log_data=risk_report_log)

            logger.info(f"风控分析结果已保存，报告ID: {report_log.id if report_log else 'None'}")
            return report_log

        except Exception as e:
            logger.exception(f"保存分析结果失败: {e}")
            return None


# 创建服务实例
payment_risk_service = PaymentRiskService()
