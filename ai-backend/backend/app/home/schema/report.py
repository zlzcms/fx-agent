#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pydantic import Field

from backend.common.pagination import PageData
from backend.common.schema import SchemaBase


class ReportItem(SchemaBase):
    id: int = Field(description="报告ID")
    assistant_id: str = Field(description="AI助手ID")
    model_id: str = Field(description="AI模型ID")
    subscription_id: Optional[int] = Field(default=None, description="订阅ID")
    subscription_name: Optional[str] = Field(default=None, description="订阅名称")
    report_score: float = Field(description="报告评分")
    report_result: Optional[str] = Field(default=None, description="报告结果")
    created_time: datetime = Field(description="创建时间")
    is_read: bool = Field(description="是否已读")


class ReportListResponse(PageData[ReportItem]):
    pass
