#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base, id_key

if TYPE_CHECKING:
    from backend.app.task.model.scheduler import TaskScheduler


class TaskSchedulerExecution(Base):
    """任务调度执行记录"""

    __tablename__ = "task_scheduler_execution"
    __table_args__ = (
        Index("idx_user_scheduler", "user_id", "scheduler_id"),
        Index("idx_subscription_scheduler", "subscription_id", "scheduler_id"),
        Index("idx_user_execution_time", "user_id", "execution_time"),
        Index("idx_start_end_time", "start_time", "end_time"),
    )

    id: Mapped[id_key] = mapped_column(init=False)
    scheduler_id: Mapped[int] = mapped_column(ForeignKey("task_scheduler.id", ondelete="CASCADE"), comment="任务调度ID")
    celery_task_id: Mapped[str] = mapped_column(String(155), unique=True, index=True, comment="Celery任务ID")
    report_id: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None, comment="生成的报告ID")
    execution_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, comment="执行时间")
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, comment="任务开始执行时间"
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, comment="任务结束执行时间")
    # 有默认值的字段
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sys_user.id", ondelete="SET NULL"), default=None, comment="执行用户ID"
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_subscription.id", ondelete="SET NULL"), default=None, comment="订阅ID"
    )
    status: Mapped[str | None] = mapped_column(
        String(20), default="running", comment="执行状态：running, completed, failed"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="错误信息")

    # 关联关系
    scheduler: Mapped[TaskScheduler] = relationship("TaskScheduler", back_populates="executions", init=False)
