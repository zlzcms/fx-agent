from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model.risk_assistant import RiskAssistant
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.app.admin.service.incremental_risk_user_service import incremental_risk_user_service
from backend.app.task.celery import celery_app
from backend.common.enums import RiskAnalysisType, RiskType
from backend.common.log import logger
from backend.database.db import async_db_session

# 导入辅助函数
from .helpers import (
    _build_analysis_basic_info,
    _build_query_condition,
    _create_detection_window_info,
    _create_error_response,
    _create_success_response,
    _create_task_info,
    _get_data_sources,
    _get_db_session,
    _get_target_users,
    _merge_analysis_config,
    _perform_user_analysis,
    _save_analysis_result,
    _validate_analysis_config,
    _validate_and_get_assistant,
    _validate_user_and_assistant,
)

# 常量定义
DEFAULT_USER_LIMIT = 100
data_analysis_service = DataAnalysisService()


@celery_app.task(
    name="scheduled_risk_analysis",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_kwargs={"max_retries": 2, "countdown": 30},
)
async def scheduled_risk_analysis(
    self, risk_type: RiskType, setting: Optional[Dict[str, Any]] = None, concurrent_count: int = 1, **kwargs
) -> dict:
    """定时风控分析任务"""
    setting = setting or {}

    async with _get_db_session() as db:
        is_valid, assistant, error_msg = await _validate_and_get_assistant(db, risk_type)
        if not is_valid or assistant is None:
            return {"status": False, "message": error_msg}

        # 获取任务创建者ID
        task_creator_id = kwargs.get("task_creator_id")
        result = await _process_parallel_risk_analysis(db, assistant, setting, concurrent_count, task_creator_id)
        result["risk_assistant"] = assistant.to_dict()
        return result


@celery_app.task(
    name="scheduled_incremental_risk_analysis",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_kwargs={"max_retries": 2, "countdown": 30},
)
async def scheduled_incremental_risk_analysis(
    self,
    risk_type: RiskType,
    time_window_hours: int = 6,
    setting: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> dict:
    """增量风控分析任务"""
    setting = setting or {}

    async with _get_db_session() as db:
        is_valid, assistant, error_msg = await _validate_and_get_assistant(db, risk_type)
        if not is_valid or assistant is None:
            return {"status": False, "message": error_msg}

        # 获取任务创建者ID
        task_creator_id = kwargs.get("task_creator_id")
        result = await _process_parallel_incremental_risk_analysis(
            db, assistant, time_window_hours, setting, task_creator_id
        )
        result["risk_assistant"] = assistant.to_dict()
        return result


async def _process_parallel_incremental_risk_analysis(
    db: AsyncSession,
    assistant: RiskAssistant,
    time_window_hours: int = 6,
    setting: Optional[Dict[str, Any]] = None,
    task_creator_id: Optional[int] = None,
) -> dict:
    setting = setting or {}

    try:
        incremental_users_data = await incremental_risk_user_service.get_incremental_users_by_risk_type(
            db, risk_type=RiskType(assistant.risk_type), hours=time_window_hours, limit=None
        )

        if not incremental_users_data:
            return {
                "status": False,
                "message": "未找到增量用户",
                "total_users": 0,
                "total_submitted": 0,
                "submitted_tasks": [],
                "time_window_hours": time_window_hours,
            }

        total_users = len(incremental_users_data)
        all_task_results = []

        for user_data in incremental_users_data:
            user_id = user_data["user_id"]
            trigger_source = user_data["trigger_reasons"]

            task_kwargs = {
                "risk_type": assistant.risk_type,
                "user_id": str(user_id),
                "analysis_type": RiskAnalysisType.INCREMENTAL,
                "trigger_sources": trigger_source,
                "detection_window_info": _create_detection_window_info(time_window_hours, trigger_source),
            }
            if setting:
                task_kwargs["setting"] = setting
            if task_creator_id:
                task_kwargs["task_creator_id"] = task_creator_id

            task = process_single_user_risk_analysis.delay(**task_kwargs)  # type: ignore[attr-defined]

            all_task_results.append(_create_task_info(str(user_id), task.id, trigger_source=trigger_source))

        return {
            "status": True,
            "message": f"已提交 {len(all_task_results)} 个增量用户的风控分析任务",
            "submitted_tasks": all_task_results,
            "total_users": total_users,
            "total_submitted": len(all_task_results),
            "time_window_hours": time_window_hours,
        }

    except Exception as e:
        logger.exception(f"提交增量并行任务失败: {str(e)}")
        return {"status": False, "message": str(e)}


async def _process_parallel_risk_analysis(
    db: AsyncSession,
    assistant: RiskAssistant,
    setting: Optional[Dict[str, Any]] = None,
    concurrent_count: int = 2,
    task_creator_id: Optional[int] = None,
) -> dict:
    setting = setting or {}

    try:
        unanalyzed_users = await _get_target_users(db, assistant, setting, concurrent_count)

        if not unanalyzed_users:
            return {"status": False, "message": "未找到未分析的用户", "total_submitted": 0, "submitted_tasks": []}

        task_results = []
        for user in unanalyzed_users:
            task_kwargs = {
                "risk_type": assistant.risk_type,
                "user_id": str(user.id),
                "user_nickname": user.nickname,
            }
            if setting:
                task_kwargs["setting"] = setting
            if task_creator_id:
                task_kwargs["task_creator_id"] = task_creator_id

            task = process_single_user_risk_analysis.delay(**task_kwargs)  # type: ignore[attr-defined]
            task_results.append(_create_task_info(str(user.id), task.id, user_nickname=user.nickname))

        return {
            "status": True,
            "message": f"已提交 {len(task_results)} 个用户的风控分析任务",
            "submitted_tasks": task_results,
            "total_submitted": len(task_results),
        }

    except Exception as e:
        logger.exception(f"提交并行任务失败: {str(e)}")
        return {"status": False, "message": str(e)}


@celery_app.task(
    name="process_single_user_risk_analysis",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_kwargs={"max_retries": 2, "countdown": 30},
    rate_limit="10/m",
    concurrency=4,
    time_limit=300,  # 硬超时：5分钟
    soft_time_limit=240,  # 软超时：4分钟
)
async def process_single_user_risk_analysis(
    self,
    risk_type: str,
    setting: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    user_nickname: Optional[str] = None,
    analysis_type: str = RiskAnalysisType.STOCK,
    trigger_sources: Optional[str] = None,
    detection_window_info: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> dict:
    """单用户风控分析任务"""
    setting = setting or {}

    async with async_db_session() as db:
        try:
            # 验证用户和助手
            is_valid, assistant, user_detail, user_nickname, error_msg = await _validate_user_and_assistant(
                db, risk_type, user_id
            )
            if not is_valid:
                logger.error(error_msg)
                return _create_error_response(user_id or "unknown", message=error_msg, task_id=self.request.id)

            # 配置验证和准备
            analysis_config = _merge_analysis_config(assistant.setting or {}, setting)
            is_valid, error_msg = _validate_analysis_config(analysis_config)
            if not is_valid:
                error_msg = f"配置验证失败: {error_msg}"
                logger.error(error_msg)
                return _create_error_response(user_id, error_msg, self.request.id, user_nickname)

            basic_info = await _build_analysis_basic_info(db, assistant, analysis_config)
            data_sources = _get_data_sources(analysis_config)
            query_condition = _build_query_condition(analysis_config)

            if not data_sources:
                error_msg = "未配置数据源，无法进行数据分析"
                logger.error(error_msg)
                return _create_error_response(user_id, error_msg, self.request.id, user_nickname)

            # 获取任务创建者ID - 从任务参数中获取
            task_creator_id = kwargs.get("task_creator_id")

            # 如果仍然没有获取到task_creator_id（比如通过Flower调用），使用系统默认用户
            if not task_creator_id:
                try:
                    from backend.core.conf import settings

                    task_creator_id = settings.SYSTEM_DEFAULT_USER_ID
                    logger.warning(f"使用系统默认用户ID: {task_creator_id}")
                except Exception as e:
                    logger.error(f"获取系统默认用户ID失败: {e}")

            # 执行分析
            success, analysis_result, error_msg = await _perform_user_analysis(
                db,
                assistant,
                user_id,
                user_nickname,
                analysis_config,
                basic_info,
                data_sources,
                query_condition,
                task_creator_id,
            )
            if not success:
                return _create_error_response(user_id, error_msg, self.request.id, user_nickname)

            # 保存结果
            await _save_analysis_result(
                db,
                assistant,
                user_id,
                user_nickname,
                basic_info,
                analysis_result,
                data_sources,
                query_condition,
                analysis_type,
                trigger_sources,
                detection_window_info,
            )

            return _create_success_response(
                user_id, user_nickname, True, "分析完成", analysis_result.get("data"), self.request.id
            )

        except Exception as e:
            # 检查是否是软超时
            if hasattr(self, "request") and hasattr(self.request, "expires"):
                logger.warning(f"单用户 {user_id} 风控分析任务软超时: {str(e)}")
                return _create_error_response(
                    user_id or "unknown",
                    message=f"任务执行超时，请检查用户数据量或调整查询条件: {str(e)}",
                    task_id=self.request.id,
                )
            else:
                logger.exception(f"单用户 {user_id} 风控分析任务失败: {str(e)}")
                return _create_error_response(user_id or "unknown", message=str(e), task_id=self.request.id)
