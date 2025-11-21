#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险任务CRUD操作
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.risk_tasks import RiskTasks, TaskStatus


class CRUDRiskTasks(CRUDPlus[RiskTasks]):
    """风险任务CRUD操作"""

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str) -> Optional[RiskTasks]:
        """根据task_id获取任务"""
        result = await db.execute(select(self.model).where(self.model.task_id == task_id))
        return result.scalars().first()

    async def create_task(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        member_id: int,
        task_type: str = "payment_risk",
        request_data: dict = None,
        message: str = "任务已创建",
    ) -> RiskTasks:
        """创建新任务"""
        task = RiskTasks()
        task.task_id = task_id
        task.task_type = task_type
        task.status = TaskStatus.PENDING
        task.member_id = member_id
        task.progress = 0
        task.message = message
        task.request_data = request_data
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def update_task_status(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[RiskTasks]:
        """更新任务状态"""
        task = await self.get_by_task_id(db, task_id=task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.now()

        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if error_message is not None:
            task.error_message = error_message
        if completed_at is not None:
            task.completed_at = completed_at

        await db.commit()
        await db.refresh(task)
        return task

    async def update_task_result(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        analysis_result: dict,
        risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        report_id: Optional[int] = None,
    ) -> Optional[RiskTasks]:
        """更新任务结果"""
        task = await self.get_by_task_id(db, task_id=task_id)
        if not task:
            return None

        task.analysis_result = analysis_result
        task.updated_at = datetime.now()

        if risk_score is not None:
            task.risk_score = risk_score
        if risk_level is not None:
            task.risk_level = risk_level
        if report_id is not None:
            task.report_id = report_id

        await db.commit()
        await db.refresh(task)
        return task

    async def get_tasks_by_member_id(
        self, db: AsyncSession, *, member_id: int, status: Optional[TaskStatus] = None, limit: int = 10
    ) -> List[RiskTasks]:
        """根据用户ID获取任务列表"""
        query = select(self.model).where(self.model.member_id == member_id)

        if status is not None:
            query = query.where(self.model.status == status)

        query = query.order_by(desc(self.model.created_at)).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_pending_tasks(self, db: AsyncSession, limit: int = 100) -> List[RiskTasks]:
        """获取待处理任务"""
        query = (
            select(self.model)
            .where(self.model.status == TaskStatus.PENDING)
            .order_by(self.model.created_at)
            .limit(limit)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def increment_retry_count(self, db: AsyncSession, *, task_id: str) -> Optional[RiskTasks]:
        """增加重试次数"""
        task = await self.get_by_task_id(db, task_id=task_id)
        if not task:
            return None

        task.retry_count += 1
        task.updated_at = datetime.now()

        await db.commit()
        await db.refresh(task)
        return task


# 创建实例
crud_risk_tasks = CRUDRiskTasks(RiskTasks)
