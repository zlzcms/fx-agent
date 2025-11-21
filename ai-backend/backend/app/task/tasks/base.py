#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import asyncio

from datetime import datetime
from typing import Any

from celery import Task
from sqlalchemy.exc import SQLAlchemyError

from backend.common.socketio.actions import task_notification
from backend.core.conf import settings
from backend.database.db import async_db_session


class TaskBase(Task):
    """Celery 任务基类"""

    autoretry_for = (SQLAlchemyError,)
    max_retries = settings.CELERY_TASK_MAX_RETRIES

    async def before_start(self, task_id: str, args, kwargs) -> None:
        """
        任务开始前执行钩子

        :param task_id: 任务 ID
        :return:
        """
        await task_notification(msg=f"任务 {task_id} 开始执行")

        await self._before_start_async(task_id)

    async def on_success(self, retval: Any, task_id: str, args, kwargs) -> None:
        """
        任务成功后执行钩子

        :param retval: 任务返回值
        :param task_id: 任务 ID
        :return:
        """
        await task_notification(msg=f"任务 {task_id} 执行成功")

        await self._after_return_async(task_id)

    # def on_failure(self, exc: Exception, task_id: str, args, kwargs, einfo) -> None:
    #     """
    #     任务失败后执行钩子

    #     :param exc: 异常对象
    #     :param task_id: 任务 ID
    #     :param einfo: 异常信息
    #     :return:
    #     """
    #     asyncio.create_task(task_notification(msg=f'任务 {task_id} 执行失败'))

    async def on_failure(self, exc: Exception, task_id: str, args, kwargs, einfo) -> None:
        """
        任务失败后执行钩子

        :param exc: 异常对象
        :param task_id: 任务 ID
        :param einfo: 异常信息
        :return:
        """
        await task_notification(msg=f"任务 {task_id} 执行失败")

        await self._after_return_async(task_id)

    async def _update_execution_record(self, task_id: str, updates: dict):
        from backend.app.task.crud.crud_execution import task_scheduler_execution_dao

        async with async_db_session() as db:
            await task_scheduler_execution_dao.update_by_celery_task_id(db=db, celery_task_id=task_id, obj_in=updates)
            await db.commit()

    async def _before_start_async(self, task_id: str) -> None:
        await self._update_execution_record(
            task_id,
            {
                "start_time": datetime.now(),
            },
        )

    async def _after_return_async(self, task_id: str) -> None:
        await self._update_execution_record(
            task_id,
            {
                "end_time": datetime.now(),
            },
        )
