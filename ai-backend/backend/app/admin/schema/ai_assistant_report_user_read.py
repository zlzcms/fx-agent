#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告用户阅读关系Schema（Admin）
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from backend.common.schema import SchemaBase


class AiAssistantReportUserReadSchemaBase(SchemaBase):
    """AI助手报告用户阅读关系基础模型"""

    report_id: int = Field(description="报告ID")
    user_id: int = Field(description="用户ID")
    is_read: bool = Field(default=False, description="是否已读(0: 未读, 1: 已读)")
    read_time: Optional[datetime] = Field(None, description="阅读时间")


class CreateAiAssistantReportUserReadParam(AiAssistantReportUserReadSchemaBase):
    """创建AI助手报告用户阅读关系参数"""

    pass


class UpdateAiAssistantReportUserReadParam(SchemaBase):
    """更新AI助手报告用户阅读关系参数"""

    is_read: Optional[bool] = Field(None, description="是否已读(0: 未读, 1: 已读)")
    read_time: Optional[datetime] = Field(None, description="阅读时间")


class GetAiAssistantReportUserReadDetail(AiAssistantReportUserReadSchemaBase):
    """AI助手报告用户阅读关系详情"""

    id: int = Field(description="关系ID")
    created_time: datetime = Field(description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class MarkReportAsReadParam(SchemaBase):
    """标记报告为已读参数"""

    report_id: int = Field(description="报告ID")
    user_id: int = Field(description="用户ID")


class GetUserUnreadReportsParam(SchemaBase):
    """获取用户未读报告参数"""

    user_id: int = Field(description="用户ID")
    limit: int = Field(default=50, description="限制数量")


class GetReportReadUsersParam(SchemaBase):
    """获取报告已读用户参数"""

    report_id: int = Field(description="报告ID")
