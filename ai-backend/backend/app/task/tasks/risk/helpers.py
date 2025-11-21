#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
风险分析任务辅助函数
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_assistant import crud_risk_assistant
from backend.app.admin.model.risk_assistant import RiskAssistant
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.app.admin.service.warehouse_user_service import UserType, warehouse_user_service
from backend.app.admin.types import QueryCondition
from backend.common.enums import RiskType
from backend.common.log import logger
from backend.database.db import get_db

data_analysis_service = DataAnalysisService()


# ==================== 工具函数 ====================


def _extract_recommendations_from_list(recommendations: List[str]) -> str:
    """从推荐列表提取处理建议"""
    if not isinstance(recommendations, list) or not recommendations:
        return ""

    return "\n".join(f"• {rec}" for rec in recommendations if rec)


@asynccontextmanager
async def _get_db_session():
    """获取数据库会话的上下文管理器"""
    db_gen = get_db()
    db = await db_gen.__anext__()
    try:
        yield db
    finally:
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass


def _create_detection_window_info(time_window_hours: int, trigger_source: str) -> Dict[str, Any]:
    """创建检测窗口信息"""
    return {
        "time_window_hours": time_window_hours,
        "analysis_time": datetime.now().isoformat(),
        "trigger_source": trigger_source,
    }


def _create_task_info(user_id: str, task_id: str, **extra_fields) -> Dict[str, Any]:
    """创建任务信息"""
    task_info = {
        "user_id": user_id,
        "task_id": task_id,
        "status": "submitted",
    }
    task_info.update(extra_fields)
    return task_info


# ==================== 响应处理函数 ====================


def _create_error_response(
    user_id: str, message: str, task_id: Optional[str] = None, user_nickname: Optional[str] = None
) -> Dict[str, Any]:
    """创建错误响应"""
    response = {
        "user_id": user_id,
        "user_nickname": user_nickname or "",
        "status": False,
        "message": message,
    }
    if task_id:
        response["task_id"] = task_id
    return response


def _create_success_response(
    user_id: str,
    user_nickname: str,
    success: bool = True,
    message: str = "分析完成",
    data: Any = None,
    task_id: Optional[str] = None,
) -> Dict[str, Any]:
    """创建成功响应"""
    response = {
        "user_id": user_id,
        "user_nickname": user_nickname,
        "status": success,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    if task_id:
        response["task_id"] = task_id
    return response


# ==================== 配置处理函数 ====================


def _merge_analysis_config(assistant_config: dict, override_config: dict) -> dict:
    """智能合并配置，避免空值覆盖有效配置"""
    merged = assistant_config.copy()

    for key, value in override_config.items():
        if value is None:
            continue

        if isinstance(value, (list, dict)):
            if value:
                merged[key] = value
        else:
            merged[key] = value

    return merged


def _get_data_sources(config: dict) -> List[str]:
    """获取数据源配置"""
    return config.get("data_sources") or config.get("query_types", [])


def _build_query_condition(config: dict) -> QueryCondition:
    """构建查询条件"""
    return {
        "data_time_range_type": config.get("data_time_range_type", "year"),
        "data_time_value": config.get("data_time_value", 2),
    }


def _validate_analysis_config(config: dict) -> Tuple[bool, str]:
    """验证分析配置"""
    data_sources = _get_data_sources(config)
    if not data_sources:
        return False, "未配置数据源，请在助手设置中添加 data_sources 或 query_types"

    valid_time_ranges = {"day", "week", "month", "quarter", "year"}
    time_range_type = config.get("data_time_range_type")
    if time_range_type and time_range_type not in valid_time_ranges:
        return False, f"无效的时间范围类型: {time_range_type}"

    time_value = config.get("data_time_value", 1)
    if not isinstance(time_value, int) or time_value <= 0:
        return False, f"无效的时间值: {time_value}"

    return True, ""


# ==================== 用户处理函数 ====================


async def _get_target_users(
    db: AsyncSession, assistant: RiskAssistant, setting: Dict[str, Any], limit: Optional[int] = None
) -> List[Any]:
    """获取目标用户列表"""
    target_user_id = setting.get("target_user_id")
    if target_user_id:
        if isinstance(target_user_id, list):
            users = []
            for user_id in target_user_id:
                user_detail = await warehouse_user_service.get_user_detail(db, int(user_id), UserType.WAREHOUSE)
                if user_detail:
                    users.append(user_detail)
            return users
        else:
            user_detail = await warehouse_user_service.get_user_detail(db, int(target_user_id), UserType.WAREHOUSE)
            return [user_detail] if user_detail else []

    return await warehouse_user_service.get_unanalyzed_users_by_risk_type(
        db, risk_type=assistant.risk_type, limit=limit or 100
    )


async def _validate_and_get_assistant(
    db: AsyncSession, risk_type: RiskType
) -> Tuple[bool, Optional[RiskAssistant], str]:
    """验证并获取风控助手"""
    if not risk_type:
        return False, None, "未找到风险类型"

    assistant = await crud_risk_assistant.get_by_risk_type(db, risk_type=risk_type)
    if not assistant:
        return False, None, f"未找到风险类型为 {risk_type} 的风控助手"

    return True, assistant, ""


async def _validate_user_and_assistant(
    db: AsyncSession, risk_type: str, user_id: Optional[str]
) -> Tuple[bool, Optional[RiskAssistant], Optional[Any], str, str]:
    """验证用户和助手，返回 (is_valid, assistant, user_detail, user_nickname, error_msg)"""
    # 验证助手
    assistant = await crud_risk_assistant.get_by_risk_type(db, risk_type=RiskType(risk_type))
    if not assistant:
        return False, None, None, "", f"未找到风险类型 {risk_type} 对应的风控助手"

    # 验证用户ID
    if not user_id:
        return False, assistant, None, "", "未提供用户ID"

    # 获取用户详情
    user_detail = await warehouse_user_service.get_user_detail(db, int(user_id), UserType.WAREHOUSE)
    if not user_detail:
        return False, assistant, None, "", f"未找到用户ID {user_id} 的信息"

    user_nickname = user_detail.nickname or ""
    return True, assistant, user_detail, user_nickname, ""


# ==================== 分析处理函数 ====================


async def _build_analysis_basic_info(
    db: AsyncSession, assistant: RiskAssistant, setting: Dict[str, Any]
) -> Dict[str, Any]:
    """构建分析基础信息"""
    import json

    from backend.common.enums import AnalysisType, TrainingLogType

    if isinstance(assistant.variable_config, dict):
        output_format_table = assistant.variable_config
    elif isinstance(assistant.variable_config, str):
        try:
            output_format_table = json.loads(assistant.variable_config)
        except json.JSONDecodeError:
            output_format_table = {}
    else:
        output_format_table = {}

    if isinstance(assistant.report_config, dict):
        output_format_document = assistant.report_config
    elif isinstance(assistant.report_config, str):
        try:
            output_format_document = json.loads(assistant.report_config)
        except json.JSONDecodeError:
            output_format_document = {}
    else:
        output_format_document = {}

    return await data_analysis_service.build_basic_info(
        db=db,
        assistant_id=assistant.id,
        ai_model_id=assistant.ai_model_id,
        name=assistant.name,
        description=assistant.role,
        background=assistant.background or "",
        model_definition=assistant.task_prompt,
        output_format_table=output_format_table,
        output_format_document=output_format_document.get("content", "")
        if isinstance(output_format_document, dict)
        else str(output_format_document or ""),
        analysis_type=AnalysisType.risk,
        risk_type=assistant.risk_type,
        training_type=TrainingLogType.risk_control_assistant,
    )


async def _perform_user_analysis(
    db: AsyncSession,
    assistant: RiskAssistant,
    user_id: str,
    user_nickname: str,
    analysis_config: Dict[str, Any],
    basic_info: Dict[str, Any],
    data_sources: list,
    query_condition: Dict[str, Any],
    task_creator_id: Optional[int] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """执行用户数据分析"""
    try:
        # 获取crm_user_id - task_creator_id本身就是MCP需要的crm_user_id
        if task_creator_id:
            crm_user_id = int(task_creator_id)
        else:
            error_msg = "未提供task_creator_id，MCP服务需要此参数进行权限验证"
            logger.error(error_msg)
            return False, None, error_msg

        # 获取用户数据
        user_result = await data_analysis_service.get_user_data(
            db=db,
            query_types=data_sources,
            condition=query_condition,
            basicInfo=basic_info,
            data_permission_values=[user_id],
            crm_user_id=crm_user_id,
        )

        user_data = user_result.get("data")
        if not user_data:
            error_msg = (
                f"用户 {user_nickname} (ID: {user_id}) 在时间范围 "
                f"{query_condition.get('data_time_range_type', 'quarter')} 内没有找到任何数据记录。"
                "建议：1) 扩大查询时间范围 2) 检查用户是否有实际业务数据 3) 确认数据源配置正确"
            )
            logger.warning(error_msg)
            return False, None, error_msg

        # 执行分析
        users_info = {"data": user_data}
        analysis_result = await data_analysis_service.analyze_data(
            db, users_info, basic_info, basic_info.get("model", {})
        )

        return True, analysis_result, ""

    except Exception as e:
        error_msg = f"数据分析服务调用失败: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


async def _save_analysis_result(
    db: AsyncSession,
    assistant: RiskAssistant,
    user_id: str,
    user_nickname: str,
    basic_info: Dict[str, Any],
    analysis_result: Dict[str, Any],
    data_sources: list,
    query_condition: Dict[str, Any],
    analysis_type: str,
    trigger_sources: Optional[str],
    detection_window_info: Optional[Dict[str, Any]],
) -> dict:
    """保存分析结果到数据库"""
    try:
        import json

        from backend.app.admin.service.report_log_service import report_log_service
        from backend.app.admin.types import RiskReportLogData, SqlData

        # 防御性检查：确保 analysis_result 是字典
        if not isinstance(analysis_result, dict):
            logger.error(f"analysis_result 应该是字典，但收到了 {type(analysis_result).__name__}: {analysis_result}")
            return {"success": False, "error": f"analysis_result type error: {type(analysis_result).__name__}"}

        analysis_data = analysis_result.get("data", {})

        # 构建 SQL 数据
        sql_data: SqlData = {}
        if data_sources:
            sql_data["data_sources"] = data_sources
        if query_condition:
            sql_data["query_condition"] = query_condition

        # 构建提示数据
        prompt_data = {
            key: basic_info.get(key)
            for key in ["model_definition", "output_format_table", "output_format_document"]
            if basic_info.get(key)
        }

        # 构建数据库日志数据
        db_log_data: RiskReportLogData = {
            "assistant_id": assistant.id,
            "model_id": basic_info.get("ai_model_id"),
            "risk_type": basic_info.get("risk_type"),
            "input_prompt": analysis_data.get("prompt", ""),
            "member_name": user_nickname,
            "member_id": int(user_id),
            "report_score": analysis_data.get("data", {}).get("confidence", 0.0),
            "score": analysis_data.get("data", {}).get("risk_score", 0),
            "report_tags": analysis_data.get("data", {}).get("risk_tags", []),
            "report_document": analysis_data.get("data", {}).get("analytical_report", ""),
            "report_table": analysis_data.get("data", {}).get("property_analysis", []),
            "handle_suggestion": _extract_recommendations_from_list(
                analysis_data.get("data", {}).get("recommendations", [])
            ),
            "description": analysis_data.get("data", {}).get("description", ""),
            "report_result": json.dumps(analysis_data),
            "analysis_type": analysis_type,
            "trigger_sources": trigger_sources,
            "ai_response": analysis_result.get("data", {}).get("response", {}),
            "detection_window_info": detection_window_info,
            "sql_data": sql_data,
            "prompt_data": prompt_data,
        }

        # 保存到数据库
        report_log = await report_log_service.add_risk_report_log(db=db, log_data=db_log_data)

        # 如果保存成功且有报告文档，生成PDF文件
        if report_log and report_log.report_document:
            try:
                from backend.agents.tools.data_export_tool import DataExportTool

                # 使用 DataExportTool 生成 PDF（统一管理）
                export_tool = DataExportTool(data_source="risk", base_path="admin")

                # 使用 report_id 作为 task_id 和文件名
                result = export_tool.export_markdown_to_pdf(
                    markdown_content=report_log.report_document,
                    task_id=str(report_log.id),
                    filename=f"risk_report_{report_log.id}",
                )

                if result.get("success"):
                    # 更新 report_pdf_url 字段
                    report_log.report_pdf_url = result.get("url")
                    db.add(report_log)
                    await db.commit()
                    await db.refresh(report_log)
                    logger.info(
                        f"PDF生成成功并更新到数据库: {result.get('url')} (大小: {result.get('file_size')} bytes)"
                    )
                else:
                    logger.warning(f"PDF生成失败，report_id: {report_log.id}, 错误: {result.get('error_message')}")
            except Exception as e:
                logger.exception(f"生成PDF时发生异常: {str(e)}")
                # PDF 生成失败不影响主流程，继续返回成功

        return {"id": report_log.id, "success": True} if report_log else {"success": False}

    except Exception as e:
        # 记录异常堆栈，便于排查问题
        logger.exception(f"保存分析结果到数据库失败: {str(e)}")
        return {"success": False, "error": str(e)}
