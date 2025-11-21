#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Celery任务管理相关的数据模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CeleryTaskInfo(BaseModel):
    """Celery任务信息"""

    task_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    state: str = Field(..., description="任务状态")
    received: Optional[datetime] = Field(None, description="接收时间")
    started: Optional[datetime] = Field(None, description="开始时间")
    succeeded: Optional[datetime] = Field(None, description="成功时间")
    failed: Optional[datetime] = Field(None, description="失败时间")
    retried: Optional[datetime] = Field(None, description="重试时间")
    revoked: Optional[datetime] = Field(None, description="撤销时间")
    args: Optional[List[Any]] = Field(None, description="位置参数")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="关键字参数")
    result: Optional[Any] = Field(None, description="任务结果")
    traceback: Optional[str] = Field(None, description="错误堆栈")
    runtime: Optional[float] = Field(None, description="运行时间(秒)")
    worker: Optional[str] = Field(None, description="执行的worker")
    queue: Optional[str] = Field(None, description="队列名称")
    routing_key: Optional[str] = Field(None, description="路由键")
    eta: Optional[datetime] = Field(None, description="预计执行时间")
    expires: Optional[datetime] = Field(None, description="过期时间")
    retries: Optional[int] = Field(None, description="重试次数")


class CeleryWorkerInfo(BaseModel):
    """Celery Worker信息"""

    name: str = Field(..., description="Worker名称")
    status: str = Field(..., description="Worker状态")
    active_tasks: int = Field(0, description="活跃任务数")
    processed_tasks: int = Field(0, description="已处理任务数")
    load_avg: Optional[List[float]] = Field(None, description="负载平均值")
    pool: Optional[str] = Field(None, description="进程池类型")
    concurrency: Optional[int] = Field(None, description="并发数")
    broker: Optional[str] = Field(None, description="消息代理")
    heartbeat: Optional[datetime] = Field(None, description="心跳时间")


class CeleryQueueInfo(BaseModel):
    """Celery队列信息"""

    name: str = Field(..., description="队列名称")
    messages: int = Field(0, description="消息数量")
    consumers: int = Field(0, description="消费者数量")
    memory: Optional[int] = Field(None, description="内存使用")


class CeleryStatsInfo(BaseModel):
    """Celery统计信息"""

    total_tasks: int = Field(0, description="总任务数")
    active_tasks: int = Field(0, description="活跃任务数")
    pending_tasks: int = Field(0, description="等待任务数")
    success_tasks: int = Field(0, description="成功任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    retried_tasks: int = Field(0, description="重试任务数")
    revoked_tasks: int = Field(0, description="撤销任务数")
    workers_online: int = Field(0, description="在线Worker数")
    workers_offline: int = Field(0, description="离线Worker数")


class TaskQueryParams(BaseModel):
    """任务查询参数"""

    task_name: Optional[str] = Field(None, description="任务名称筛选")
    state: Optional[str] = Field(None, description="任务状态筛选")
    worker: Optional[str] = Field(None, description="Worker筛选")
    queue: Optional[str] = Field(None, description="队列筛选")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页数量")


class TaskActionRequest(BaseModel):
    """任务操作请求"""

    task_ids: List[str] = Field(..., description="任务ID列表")
    action: str = Field(..., description="操作类型: revoke, retry, terminate")
    signal: Optional[str] = Field("SIGTERM", description="终止信号")


class ScheduledTaskInfo(BaseModel):
    """定时任务信息"""

    name: str = Field(..., description="任务名称")
    task: str = Field(..., description="任务函数")
    schedule: str = Field(..., description="调度表达式")
    args: Optional[List[Any]] = Field(None, description="位置参数")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="关键字参数")
    enabled: bool = Field(True, description="是否启用")
    last_run: Optional[datetime] = Field(None, description="上次运行时间")
    next_run: Optional[datetime] = Field(None, description="下次运行时间")
    total_runs: int = Field(0, description="总运行次数")
    success_runs: int = Field(0, description="成功运行次数")
    failed_runs: int = Field(0, description="失败运行次数")
