#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出金风控相关Schema
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class PaymentRiskAnalysisRequest(BaseModel):
    """出金风控分析请求模型"""

    member_id: int = Field(..., description="用户ID", ge=1)


class PaymentRiskTaskResponse(BaseModel):
    """出金风控任务创建响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    member_id: int = Field(..., description="用户ID")


class PaymentRiskTaskStatusResponse(BaseModel):
    """出金风控任务状态查询响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[int] = Field(None, description="进度百分比(0-100)", ge=0, le=100)
    message: str = Field(..., description="状态描述")
    member_id: int = Field(..., description="用户ID")
    created_at: Optional[str] = Field(None, description="任务创建时间")
    updated_at: Optional[str] = Field(None, description="任务更新时间")


class PaymentRiskAnalysisResponse(BaseModel):
    """出金风控分析结果响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    member_id: int = Field(..., description="用户ID")
    data: Dict[str, Any] = Field(..., description="完整分析报告数据")
    report_id: Optional[int] = Field(None, description="报告日志ID")
    report_pdf_url: Optional[str] = Field(None, description="报告PDF文件静态路径")
    created_at: Optional[str] = Field(None, description="任务创建时间")
    completed_at: Optional[str] = Field(None, description="任务完成时间")


# 保持向后兼容的旧响应模型
class PaymentRiskAnalysisLegacyResponse(BaseModel):
    """出金风控分析响应模型（向后兼容）"""

    status: bool = Field(..., description="分析状态")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="完整分析报告数据")
    report_id: Optional[int] = Field(None, description="报告日志ID")
