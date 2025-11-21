#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Sequence

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.task.model import TaskSchedulerExecution


class CRUDTaskSchedulerExecution:
    """任务调度执行记录CRUD类"""

    @staticmethod
    async def get(db: AsyncSession, pk: int) -> TaskSchedulerExecution | None:
        """
        获取任务调度执行记录

        :param db: 数据库会话
        :param pk: 主键
        :return: TaskSchedulerExecution | None
        """
        return await db.get(TaskSchedulerExecution, pk)

    @staticmethod
    async def get_by_celery_task_id(db: AsyncSession, celery_task_id: str) -> TaskSchedulerExecution | None:
        """
        根据Celery任务ID获取执行记录

        :param db: 数据库会话
        :param celery_task_id: Celery任务ID
        :return: TaskSchedulerExecution | None
        """
        stmt = select(TaskSchedulerExecution).where(TaskSchedulerExecution.celery_task_id == celery_task_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_subscription_id(
        db: AsyncSession, subscription_id: int, limit: int = 50
    ) -> Sequence[TaskSchedulerExecution]:
        """
        根据订阅ID获取执行记录

        :param db: 数据库会话
        :param subscription_id: 订阅ID
        :param limit: 限制返回数量
        :return: Sequence[TaskSchedulerExecution]
        """
        stmt = (
            select(TaskSchedulerExecution)
            .where(TaskSchedulerExecution.subscription_id == subscription_id)
            .order_by(desc(TaskSchedulerExecution.execution_time))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_all(db: AsyncSession) -> Sequence[TaskSchedulerExecution]:
        """
        获取所有任务调度执行记录

        :param db: 数据库会话
        :return: Sequence[TaskSchedulerExecution]
        """
        stmt = select(TaskSchedulerExecution).order_by(desc(TaskSchedulerExecution.execution_time))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def get_list(
        scheduler_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        """
        获取任务调度执行记录列表查询条件

        :param scheduler_id: 任务调度ID
        :param user_id: 用户ID
        :param status: 执行状态
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: Select
        """
        conditions = []

        if scheduler_id is not None:
            conditions.append(TaskSchedulerExecution.scheduler_id == scheduler_id)
        if user_id is not None:
            conditions.append(TaskSchedulerExecution.user_id == user_id)
        if status:
            conditions.append(TaskSchedulerExecution.status == status)
        if start_time:
            conditions.append(TaskSchedulerExecution.execution_time >= start_time)
        if end_time:
            conditions.append(TaskSchedulerExecution.execution_time <= end_time)

        return (
            select(TaskSchedulerExecution)
            .where(and_(*conditions))
            .order_by(desc(TaskSchedulerExecution.execution_time))
        )

    @staticmethod
    async def create(db: AsyncSession, obj_in: dict) -> TaskSchedulerExecution:
        """
        创建任务调度执行记录

        :param db: 数据库会话
        :param obj_in: 创建参数字典
        :return: TaskSchedulerExecution
        """
        db_obj = TaskSchedulerExecution(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, pk: int, obj_in: dict) -> int:
        """
        更新任务调度执行记录

        :param db: 数据库会话
        :param pk: 主键
        :param obj_in: 更新参数字典
        :return: 更新行数
        """
        stmt = TaskSchedulerExecution.__table__.update().where(TaskSchedulerExecution.id == pk).values(**obj_in)
        result = await db.execute(stmt)
        return result.rowcount

    @staticmethod
    async def update_by_celery_task_id(db: AsyncSession, celery_task_id: str, obj_in: dict) -> int:
        """
        根据Celery任务ID更新执行记录

        :param db: 数据库会话
        :param celery_task_id: Celery任务ID
        :param obj_in: 更新参数字典
        :return: 更新行数
        """
        stmt = (
            TaskSchedulerExecution.__table__.update()
            .where(TaskSchedulerExecution.celery_task_id == celery_task_id)
            .values(**obj_in)
        )
        result = await db.execute(stmt)
        return result.rowcount

    @staticmethod
    async def delete(db: AsyncSession, pk: int) -> int:
        """
        删除任务调度执行记录

        :param db: 数据库会话
        :param pk: 主键
        :return: 删除行数
        """
        stmt = TaskSchedulerExecution.__table__.delete().where(TaskSchedulerExecution.id == pk)
        result = await db.execute(stmt)
        return result.rowcount

    @staticmethod
    async def delete_batch(db: AsyncSession, pks: list[int]) -> int:
        """
        批量删除任务调度执行记录

        :param db: 数据库会话
        :param pks: 主键列表
        :return: 删除行数
        """
        stmt = TaskSchedulerExecution.__table__.delete().where(TaskSchedulerExecution.id.in_(pks))
        result = await db.execute(stmt)
        return result.rowcount


task_scheduler_execution_dao: CRUDTaskSchedulerExecution = CRUDTaskSchedulerExecution()
