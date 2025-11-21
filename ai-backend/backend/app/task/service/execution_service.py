#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, Sequence

from celery.result import AsyncResult
from sqlalchemy import Select

from backend.app.task.crud.crud_execution import task_scheduler_execution_dao
from backend.app.task.model import TaskSchedulerExecution
from backend.common.exception import errors
from backend.database.db import async_db_session


class TaskSchedulerExecutionService:
    """任务调度执行记录服务类"""

    @staticmethod
    async def get(*, pk: int) -> TaskSchedulerExecution | None:
        """
        获取任务调度执行记录详情

        :param pk: 执行记录 ID
        :return:
        """
        async with async_db_session() as db:
            execution = await task_scheduler_execution_dao.get(db, pk)
            if not execution:
                raise errors.NotFoundError(msg="执行记录不存在")
            return execution

    @staticmethod
    async def get_by_celery_task_id(*, celery_task_id: str) -> TaskSchedulerExecution | None:
        """
        根据Celery任务ID获取执行记录

        :param celery_task_id: Celery任务ID
        :return:
        """
        async with async_db_session() as db:
            execution = await task_scheduler_execution_dao.get_by_celery_task_id(db, celery_task_id)
            if not execution:
                raise errors.NotFoundError(msg="执行记录不存在")
            return execution

    @staticmethod
    async def get_all() -> Sequence[TaskSchedulerExecution]:
        """获取所有任务调度执行记录"""
        async with async_db_session() as db:
            executions = await task_scheduler_execution_dao.get_all(db)
            return executions

    @staticmethod
    def get_select(
        *,
        scheduler_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> Select:
        """
        获取任务调度执行记录列表查询条件

        :param scheduler_id: 任务调度ID
        :param user_id: 用户ID
        :param status: 执行状态
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return:
        """
        return task_scheduler_execution_dao.get_list(
            scheduler_id=scheduler_id,
            user_id=user_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    async def update_status(
        *,
        celery_task_id: str,
        status: str,
        result: dict | None = None,
        error_message: str | None = None,
        worker_name: str | None = None,
        retries: int | None = None,
        execution_time: datetime | None = None,
    ) -> int:
        """
        更新执行记录状态

        :param celery_task_id: Celery任务ID
        :param status: 执行状态
        :param result: 执行结果
        :param error_message: 错误信息

        :param worker_name: Worker名称
        :param retries: 重试次数
        :param execution_time: 执行时间
        :return:
        """
        async with async_db_session.begin() as db:
            update_data = {"status": status}

            if result is not None:
                update_data["result"] = result
            if error_message is not None:
                update_data["error_message"] = error_message
            if worker_name is not None:
                update_data["worker_name"] = worker_name
            if retries is not None:
                update_data["retries"] = retries
            if execution_time is not None:
                update_data["execution_time"] = execution_time

            count = await task_scheduler_execution_dao.update_by_celery_task_id(db, celery_task_id, update_data)
            return count

    @staticmethod
    async def delete(*, pk: int) -> int:
        """
        删除执行记录

        :param pk: 执行记录 ID
        :return:
        """
        async with async_db_session.begin() as db:
            execution = await task_scheduler_execution_dao.get(db, pk)
            if not execution:
                raise errors.NotFoundError(msg="执行记录不存在")
            count = await task_scheduler_execution_dao.delete(db, pk)
            return count

    @staticmethod
    async def delete_batch(*, pks: list[int]) -> int:
        """
        批量删除执行记录

        :param pks: 执行记录 ID 列表
        :return:
        """
        async with async_db_session.begin() as db:
            count = await task_scheduler_execution_dao.delete_batch(db, pks)
            return count

    @staticmethod
    async def get_with_real_time_status(*, pk: int) -> Dict[str, Any]:
        """
        获取执行记录并包含实时状态信息

        :param pk: 执行记录 ID
        :return: 包含实时状态的执行记录信息
        """
        async with async_db_session() as db:
            execution = await task_scheduler_execution_dao.get(db, pk)
            if not execution:
                raise errors.NotFoundError(msg="执行记录不存在")

            # 获取Celery任务的实时状态
            real_time_info = await TaskSchedulerExecutionService._get_celery_task_info(execution.celery_task_id)

            # 构建返回数据
            result = {
                "id": execution.id,
                "scheduler_id": execution.scheduler_id,
                "celery_task_id": execution.celery_task_id,
                "user_id": execution.user_id,
                "subscription_id": execution.subscription_id,
                "created_time": execution.created_time,
                "execution_time": execution.execution_time,
                "updated_time": execution.updated_time,
                "worker_name": execution.worker_name,
                "queue_name": execution.queue_name,
                "retries": execution.retries,
                "result": execution.result,
                "error_message": execution.error_message,
                # 数据库中的状态
                "db_status": execution.status,
                # Celery的实时状态
                "real_time_status": real_time_info["status"],
                "real_time_result": real_time_info["result"],
                "real_time_traceback": real_time_info["traceback"],
                # 状态是否一致
                "status_consistent": execution.status == real_time_info["status"],
                # 最终显示的状态（优先使用实时状态）
                "status": real_time_info["status"] if real_time_info["status"] != "PENDING" else execution.status,
            }

            return result

    @staticmethod
    async def get_all_with_real_time_status() -> list[Dict[str, Any]]:
        """
        获取所有执行记录并包含实时状态信息

        :return: 包含实时状态的执行记录列表
        """
        async with async_db_session() as db:
            executions = await task_scheduler_execution_dao.get_all(db)

            results = []
            for execution in executions:
                # 获取Celery任务的实时状态
                real_time_info = await TaskSchedulerExecutionService._get_celery_task_info(execution.celery_task_id)

                result = {
                    "id": execution.id,
                    "scheduler_id": execution.scheduler_id,
                    "celery_task_id": execution.celery_task_id,
                    "user_id": execution.user_id,
                    "subscription_id": execution.subscription_id,
                    "created_time": execution.created_time,
                    "execution_time": execution.execution_time,
                    "updated_time": execution.updated_time,
                    "worker_name": execution.worker_name,
                    "queue_name": execution.queue_name,
                    "retries": execution.retries,
                    "result": execution.result,
                    "error_message": execution.error_message,
                    # 数据库中的状态
                    "db_status": execution.status,
                    # Celery的实时状态
                    "real_time_status": real_time_info["status"],
                    "real_time_result": real_time_info["result"],
                    "real_time_traceback": real_time_info["traceback"],
                    # 状态是否一致
                    "status_consistent": execution.status == real_time_info["status"],
                    # 最终显示的状态（优先使用实时状态）
                    "status": real_time_info["status"] if real_time_info["status"] != "PENDING" else execution.status,
                }

                results.append(result)

            return results

    @staticmethod
    async def _get_celery_task_info(celery_task_id: str) -> Dict[str, Any]:
        """
        获取Celery任务的实时信息

        :param celery_task_id: Celery任务ID
        :return: 任务信息字典
        """
        try:
            # 导入celery_app（避免循环导入）
            from backend.app.task.celery import celery_app

            result = AsyncResult(celery_task_id, app=celery_app)

            return {
                "status": result.status,
                "result": result.result,
                "traceback": result.traceback,
                "successful": result.successful(),
                "failed": result.failed(),
                "ready": result.ready(),
            }
        except Exception as e:
            # 如果获取Celery状态失败，返回默认值
            return {
                "status": "UNKNOWN",
                "result": None,
                "traceback": str(e),
                "successful": False,
                "failed": False,
                "ready": False,
            }

    @staticmethod
    async def sync_status_with_celery(*, celery_task_id: str) -> bool:
        """
        同步数据库状态与Celery状态

        :param celery_task_id: Celery任务ID
        :return: 是否同步成功
        """
        try:
            # 获取Celery任务的实时状态
            real_time_info = await TaskSchedulerExecutionService._get_celery_task_info(celery_task_id)

            if real_time_info["status"] != "UNKNOWN":
                # 更新数据库状态
                await TaskSchedulerExecutionService.update_status(
                    celery_task_id=celery_task_id,
                    status=real_time_info["status"],
                    result=real_time_info["result"] if real_time_info["result"] else None,
                )
                return True

            return False
        except Exception:
            return False


task_scheduler_execution_service: TaskSchedulerExecutionService = TaskSchedulerExecutionService()
