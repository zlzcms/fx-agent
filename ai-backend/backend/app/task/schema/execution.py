#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from backend.app.task.enums import TaskExecutionStatus
from backend.app.task.schema.scheduler import GetTaskSchedulerDetail
from backend.common.schema import SchemaBase


class TaskSchedulerExecutionSchemaBase(SchemaBase):
    """任务调度执行记录基础模型"""

    scheduler_id: int = Field(description="任务调度ID")
    celery_task_id: str = Field(description="Celery任务ID")
    user_id: int | None = Field(default=None, description="执行用户ID")
    subscription_id: int | None = Field(default=None, description="订阅ID")
    execution_time: datetime | None = Field(default=None, description="执行时间")
    start_time: datetime | None = Field(default=None, description="任务开始执行时间")
    end_time: datetime | None = Field(default=None, description="任务结束执行时间")


class GetTaskSchedulerExecutionDetail(TaskSchedulerExecutionSchemaBase):
    """获取任务调度执行详情响应"""

    id: int
    scheduler: GetTaskSchedulerDetail | None = None


class CreateTaskSchedulerExecutionParam(TaskSchedulerExecutionSchemaBase):
    """创建任务调度执行记录参数"""

    pass


class UpdateTaskSchedulerExecutionParam(SchemaBase):
    """更新任务调度执行记录参数"""

    status: TaskExecutionStatus = Field(description="执行状态")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """验证状态值"""
        if isinstance(v, str):
            try:
                return TaskExecutionStatus(v)
            except ValueError:
                raise ValueError(f"无效的状态值: {v}")
        return v

    result: Any | None = Field(default=None, description="执行结果")
    error_message: str | None = Field(default=None, description="错误信息")

    start_time: datetime | None = Field(default=None, description="任务开始执行时间")
    end_time: datetime | None = Field(default=None, description="任务结束执行时间")
    worker_name: str | None = Field(default=None, description="执行Worker名称")
    retries: int | None = Field(default=None, description="重试次数")


class DeleteTaskSchedulerExecutionParam(SchemaBase):
    """删除任务调度执行记录参数"""

    pks: list[int] = Field(description="执行记录ID列表")
