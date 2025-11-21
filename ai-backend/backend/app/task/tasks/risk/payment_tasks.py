from datetime import datetime
from typing import Any, Dict

from backend.app.admin.crud.crud_risk_tasks import crud_risk_tasks
from backend.app.admin.model.risk_tasks import TaskStatus as DBTaskStatus
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.app.task.celery import celery_app
from backend.common.enums import RiskType
from backend.common.log import logger
from backend.database.db import async_db_session

# 导入定时风控任务的辅助函数
from .helpers import (
    _build_analysis_basic_info,
    _build_query_condition,
    _create_error_response,
    _get_data_sources,
    _merge_analysis_config,
    _perform_user_analysis,
    _save_analysis_result,
    _validate_analysis_config,
    _validate_user_and_assistant,
)

data_analysis_service = DataAnalysisService()


@celery_app.task(
    name="payment_risk_analysis",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_kwargs={"max_retries": 2, "countdown": 30},
    rate_limit="10/m",
    concurrency=4,
    time_limit=300,  # 硬超时：5分钟
    soft_time_limit=240,  # 软超时：4分钟
)
async def payment_risk_analysis(
    self, member_id: int, db_task_id: str = None, setting: Dict[str, Any] = {}, **kwargs
) -> dict:
    """出金风控分析任务 - 参照定时风控任务架构"""

    async with async_db_session() as db:
        try:
            # 初始化任务状态
            if db_task_id:
                await crud_risk_tasks.update_task_status(
                    db, task_id=db_task_id, status=DBTaskStatus.PROCESSING, progress=10, message="开始执行风控分析"
                )

            # 验证用户和助手 - 使用定时风控任务的验证逻辑
            is_valid, assistant, user_detail, user_nickname, error_msg = await _validate_user_and_assistant(
                db, RiskType.PAYMENT.value, str(member_id)
            )
            if not is_valid:
                logger.error(error_msg)
                if db_task_id:
                    await crud_risk_tasks.update_task_status(
                        db, task_id=db_task_id, status=DBTaskStatus.FAILED, progress=100, message=error_msg
                    )
                return _create_error_response(str(member_id), message=error_msg, task_id=self.request.id)

            # 更新进度
            if db_task_id:
                await crud_risk_tasks.update_task_status(
                    db, task_id=db_task_id, status=DBTaskStatus.PROCESSING, progress=25, message="准备数据分析..."
                )

            # 配置验证和准备 - 使用定时风控任务的配置逻辑
            analysis_config = _merge_analysis_config(assistant.setting or {}, setting)
            is_valid, error_msg = _validate_analysis_config(analysis_config)
            if not is_valid:
                error_msg = f"配置验证失败: {error_msg}"
                logger.error(error_msg)
                if db_task_id:
                    await crud_risk_tasks.update_task_status(
                        db, task_id=db_task_id, status=DBTaskStatus.FAILED, progress=100, message=error_msg
                    )
                return _create_error_response(str(member_id), error_msg, self.request.id, user_nickname)

            # 构建分析基础信息
            basic_info = await _build_analysis_basic_info(db, assistant, analysis_config)
            data_sources = _get_data_sources(analysis_config)
            query_condition = _build_query_condition(analysis_config)

            if not data_sources:
                error_msg = "未配置数据源，无法进行数据分析"
                logger.error(error_msg)
                if db_task_id:
                    await crud_risk_tasks.update_task_status(
                        db, task_id=db_task_id, status=DBTaskStatus.FAILED, progress=100, message=error_msg
                    )
                return _create_error_response(str(member_id), error_msg, self.request.id, user_nickname)

            # 获取任务创建者ID - 从任务参数中获取
            task_creator_id = kwargs.get("task_creator_id")

            # 如果仍然没有获取到task_creator_id，使用系统默认用户
            if not task_creator_id:
                try:
                    from backend.core.conf import settings

                    task_creator_id = settings.SYSTEM_DEFAULT_USER_ID
                    logger.warning(f"使用系统默认用户ID: {task_creator_id}")
                except Exception as e:
                    logger.error(f"获取系统默认用户ID失败: {e}")

            # 更新进度
            if db_task_id:
                await crud_risk_tasks.update_task_status(
                    db, task_id=db_task_id, status=DBTaskStatus.PROCESSING, progress=50, message="执行数据分析..."
                )

            # 执行分析 - 使用定时风控任务的分析逻辑
            success, analysis_result, error_msg = await _perform_user_analysis(
                db=db,
                assistant=assistant,
                user_id=str(member_id),
                user_nickname=user_nickname,
                analysis_config=analysis_config,
                basic_info=basic_info,
                data_sources=data_sources,
                query_condition=query_condition,
                task_creator_id=task_creator_id,
            )

            if not success:
                logger.error(error_msg)
                if db_task_id:
                    await crud_risk_tasks.update_task_status(
                        db, task_id=db_task_id, status=DBTaskStatus.FAILED, progress=100, message=error_msg
                    )
                return _create_error_response(str(member_id), error_msg, self.request.id, user_nickname)

            # 更新进度
            if db_task_id:
                await crud_risk_tasks.update_task_status(
                    db, task_id=db_task_id, status=DBTaskStatus.PROCESSING, progress=80, message="保存分析结果..."
                )

            # 保存分析结果 - 使用定时风控任务的保存逻辑
            report_log = await _save_analysis_result(
                db=db,
                assistant=assistant,
                user_id=str(member_id),
                user_nickname=user_nickname,
                basic_info=basic_info,
                analysis_result=analysis_result,
                data_sources=data_sources,
                query_condition=query_condition,
                analysis_type="payment_risk",
                trigger_sources="api",
                detection_window_info=None,
            )

            # 任务完成 - 更新任务状态并保存分析结果
            if db_task_id:
                task = await crud_risk_tasks.get_by_task_id(db, task_id=db_task_id)
                if task:
                    task.status = DBTaskStatus.COMPLETED
                    task.progress = 100
                    task.message = "分析完成"
                    task.completed_at = datetime.now()
                    task.updated_at = datetime.now()

                    # 保存分析结果和报告ID
                    task.analysis_result = analysis_result.get("data") if isinstance(analysis_result, dict) else None
                    task.report_id = (
                        report_log.get("id") if isinstance(report_log, dict) and report_log.get("success") else None
                    )

                    # 如果有风险评分和等级，也保存
                    if task.analysis_result and isinstance(task.analysis_result, dict):
                        task.risk_score = task.analysis_result.get("risk_score")
                        task.risk_level = task.analysis_result.get("risk_level")

                    await db.commit()
                    await db.refresh(task)

            return {
                "status": True,
                "message": "分析完成",
                "data": analysis_result,
                "report_id": report_log.get("id")
                if isinstance(report_log, dict) and report_log.get("success")
                else None,
            }

        except Exception as e:
            error_msg = f"出金风控分析任务出现异常: {str(e)}"
            logger.exception(error_msg)

            if db_task_id:
                try:
                    await crud_risk_tasks.update_task_status(
                        db,
                        task_id=db_task_id,
                        status=DBTaskStatus.FAILED,
                        progress=0,
                        message="任务执行异常",
                        error_message=str(e),
                    )
                except Exception:
                    pass

            # 任务失败，记录错误
            return _create_error_response(str(member_id), error_msg, self.request.id, user_nickname or "")
