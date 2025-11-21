#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIChatFileBase(BaseModel):
    """AI Chat File 基础模型"""

    chat_message_id: str = Field(..., description="关联的聊天消息ID")
    filename: Optional[str] = Field(None, description="文件名")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_paths: Optional[Dict[str, str]] = Field(None, description="多文件路径")
    export_directory: Optional[str] = Field(None, description="导出目录")
    task_id: Optional[str] = Field(None, description="任务ID")
    data_source: Optional[str] = Field(None, description="数据源")
    export_time: Optional[str] = Field(None, description="导出时间")
    url: Optional[str] = Field(None, description="文件URL")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_type: Optional[str] = Field(None, description="文件类型")
    status: bool = Field(True, description="文件状态")


class AIChatFileCreate(AIChatFileBase):
    """AI Chat File 创建模型"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="文件ID")


class AIChatFileUpdate(BaseModel):
    """AI Chat File 更新模型"""

    filename: Optional[str] = Field(None, description="文件名")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_paths: Optional[Dict[str, str]] = Field(None, description="多文件路径")
    export_directory: Optional[str] = Field(None, description="导出目录")
    task_id: Optional[str] = Field(None, description="任务ID")
    data_source: Optional[str] = Field(None, description="数据源")
    export_time: Optional[str] = Field(None, description="导出时间")
    url: Optional[str] = Field(None, description="文件URL")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_type: Optional[str] = Field(None, description="文件类型")
    status: Optional[bool] = Field(None, description="文件状态")


class AIChatFileResponse(AIChatFileBase):
    """AI Chat File 响应模型"""

    id: str = Field(..., description="文件ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class AIChatFileListResponse(BaseModel):
    """AI Chat File 列表响应模型"""

    files: list[AIChatFileResponse] = Field(..., description="文件列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class ExportResultCreate(BaseModel):
    """从ExportResult创建文件的模型"""

    chat_message_id: str = Field(..., description="关联的聊天消息ID")
    success: bool = Field(..., description="是否成功")
    filename: Optional[str] = Field(None, description="文件名")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_paths: Optional[Dict[str, str]] = Field(None, description="多文件路径")
    export_directory: Optional[str] = Field(None, description="导出目录")
    task_id: Optional[str] = Field(None, description="任务ID")
    data_source: Optional[str] = Field(None, description="数据源")
    export_time: Optional[str] = Field(None, description="导出时间")
    url: Optional[str] = Field(None, description="文件URL")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_type: Optional[str] = Field(None, description="文件类型")
