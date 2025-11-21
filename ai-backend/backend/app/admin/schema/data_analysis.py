#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.common.enums import DataTimeRangeType


class MultiUserDataAnalysisRequest(BaseModel):
    """多用户数据分析请求模型"""

    query_types: List[Any] = Field(..., description="查询类型列表")
    data_permission_values: List[Any] = Field(..., description="数据权限值列表")
    data_time_range_type: Optional[DataTimeRangeType] = Field(..., description="数据时间范围类型")
    data_time_value: Optional[int] = Field(None, description="数据时间值")
    basicInfo: Dict[str, Any] = Field(None, description="基本信息")
    condition: Optional[Dict[str, Any]] = Field(None, description="查询条件")


class DataAnalysisResponse(BaseModel):
    """数据分析响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    success: bool = Field(True, description="请求是否成功")  # 添加这个字段


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""

    task_id: Optional[str] = Field(None, description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    progress: Optional[int] = Field(None, description="进度百分比", ge=0, le=100)
    description: Optional[str] = Field(None, description="任务描述")
    result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    file: Optional[Dict[str, Any]] = Field(None, description="生成的文件信息")


class TaskLogEntry(BaseModel):
    """任务日志条目模型"""

    timestamp: str = Field(..., description="时间戳")
    source: str = Field(..., description="日志来源")
    event_type: str = Field(..., description="事件类型")
    data: Dict[str, Any] = Field(..., description="事件数据")


class TaskLogsResponse(BaseModel):
    """任务日志响应模型"""

    task_id: str = Field(..., description="任务ID")
    log_count: int = Field(..., description="日志条目数量")
    logs: List[TaskLogEntry] = Field(..., description="日志条目列表")


class TaskQueryParams(BaseModel):
    """任务查询参数"""

    source: Optional[str] = Field(None, description="按来源筛选日志")
    event_type: Optional[str] = Field(None, description="按事件类型筛选日志")
