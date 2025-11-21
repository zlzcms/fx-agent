#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, field_serializer

from backend.app.task import celery_app
from backend.common.schema import SchemaBase


class TaskResultSchemaBase(SchemaBase):
    """任务结果基础模型"""

    task_id: str = Field(description="任务 ID")
    status: str = Field(description="执行状态")
    result: Any | None = Field(description="执行结果")
    date_done: datetime | None = Field(description="结束时间")
    traceback: str | None = Field(description="错误回溯")
    name: str | None = Field(description="任务名称")
    args: bytes | None = Field(description="任务位置参数")
    kwargs: bytes | None = Field(description="任务关键字参数")
    worker: str | None = Field(description="运行 Worker")
    retries: int | None = Field(description="重试次数")
    queue: str | None = Field(description="运行队列")


class DeleteTaskResultParam(SchemaBase):
    """删除任务结果参数"""

    pks: list[int] = Field(description="任务结果 ID 列表")


class GetTaskResultDetail(TaskResultSchemaBase):
    """任务结果详情"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="任务结果 ID")

    @field_serializer("args", "kwargs", when_used="unless-none")
    def serialize_params(self, value: bytes | None, _info) -> Any:
        return celery_app.backend.decode(value)

    @field_serializer("result", when_used="unless-none")
    def serialize_result(self, value: Any, _info) -> Any:
        if value is None:
            return None

        # 如果是bytes类型，尝试解码
        if isinstance(value, bytes):
            try:
                decoded_result = celery_app.backend.decode(value)
                return self._sanitize_result(decoded_result)
            except Exception:
                return str(value)

        # 对于其他类型，直接进行清理
        return self._sanitize_result(value)

    def _sanitize_result(self, obj: Any) -> Any:
        """递归清理结果中的SQLAlchemy对象"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            sanitized = {}
            for k, v in obj.items():
                # 跳过SQLAlchemy内部属性
                if k.startswith("_"):
                    continue
                # 检查值是否为SQLAlchemy对象
                if hasattr(v, "__table__"):
                    # 如果是SQLAlchemy对象，只保留基本信息
                    if hasattr(v, "id"):
                        sanitized[k] = {"id": getattr(v, "id", None)}
                    continue
                sanitized[k] = self._sanitize_result(v)
            return sanitized
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_result(item) for item in obj]
        elif hasattr(obj, "__table__"):
            # 如果是SQLAlchemy对象，只返回基本信息
            if hasattr(obj, "id"):
                return {"id": getattr(obj, "id", None)}
            return None
        else:
            # 对于其他类型，尝试转换为字符串
            try:
                return str(obj)
            except Exception:
                return None
