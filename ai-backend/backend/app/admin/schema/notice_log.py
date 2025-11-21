#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class NoticeLogSchemaBase(SchemaBase):
    """通知日志基础模型"""

    description: str = Field(..., description="通知描述，例如：订阅报告通知，报告id:56")
    notification_type: str = Field(..., description="通知方式：email/lark_webhook")
    content: str = Field(..., description="通知发送时的主体内容")
    address: str = Field(..., description="通知地址：邮箱地址/webhook地址")
    is_success: bool = Field(default=False, description="通知是否成功：True=成功，False=失败")
    failure_reason: Optional[str] = Field(default=None, description="通知失败原因描述")


class CreateNoticeLogParam(NoticeLogSchemaBase):
    """创建通知日志参数"""


class UpdateNoticeLogParam(NoticeLogSchemaBase):
    """更新通知日志参数"""


class GetNoticeLogDetail(NoticeLogSchemaBase):
    """通知日志详情"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="通知日志ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class NoticeLogQueryParam(SchemaBase):
    """通知日志查询参数"""

    description: Optional[str] = Field(None, description="通知描述关键字")
    notification_type: Optional[str] = Field(None, description="通知方式筛选")
    is_success: Optional[bool] = Field(None, description="成功状态筛选")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
