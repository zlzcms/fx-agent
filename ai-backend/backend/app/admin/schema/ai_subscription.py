# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 21:30:05
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.common.schema import SchemaBase


# 人员数据Schema
class PersonnelData(BaseModel):
    """人员数据Schema"""

    personnel_id: str = Field(..., description="人员ID", max_length=50)
    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    email: str = Field(..., description="邮箱", max_length=100)


class AISubscriptionBase(SchemaBase):
    """AI订阅基础Schema"""

    assistant_id: str = Field(..., description="助手ID", max_length=50)
    name: str = Field(..., description="订阅名称", min_length=1, max_length=100)
    subscription_type: str = Field(..., description="订阅类型", max_length=50)
    execution_frequency: str = Field("daily", description="执行频率", pattern="^(minutes|hours|daily|weekly|monthly)$")
    execution_time: Optional[str] = Field("09:00", description="执行时间")
    execution_minutes: Optional[int] = Field(None, description="分钟间隔", ge=5, le=1440)
    execution_hours: Optional[int] = Field(None, description="小时间隔", ge=1, le=24)
    execution_weekday: Optional[str] = Field(None, description="执行星期")
    execution_weekly_time: Optional[str] = Field(None, description="每周执行时间")
    execution_day: Optional[str] = Field(None, description="执行日期")
    execution_monthly_time: Optional[str] = Field(None, description="每月执行时间")
    is_view_myself: bool = Field(False, description="本人查看")

    # 复杂配置字段
    responsible_persons: Optional[List[PersonnelData]] = Field(None, description="指定人员")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    setting: Optional[Dict[str, Any]] = Field(None, description="其他设置（包含数据范围限制配置）")
    status: bool = Field(True, description="订阅状态")


class AISubscriptionCreate(AISubscriptionBase):
    """创建AI订阅Schema"""

    pass


class AISubscriptionUpdate(SchemaBase):
    """更新AI订阅Schema"""

    assistant_id: Optional[str] = Field(None, description="助手ID", max_length=50)
    name: Optional[str] = Field(None, description="订阅名称", min_length=1, max_length=100)
    subscription_type: Optional[str] = Field(None, description="订阅类型", max_length=50)
    execution_frequency: Optional[str] = Field(
        None, description="执行频率", pattern="^(minutes|hours|daily|weekly|monthly)$"
    )
    execution_time: Optional[str] = Field(None, description="执行时间")
    execution_minutes: Optional[int] = Field(None, description="分钟间隔", ge=5, le=1440)
    execution_hours: Optional[int] = Field(None, description="小时间隔", ge=1, le=24)
    execution_weekday: Optional[str] = Field(None, description="执行星期")
    execution_weekly_time: Optional[str] = Field(None, description="每周执行时间")
    execution_day: Optional[str] = Field(None, description="执行日期")
    execution_monthly_time: Optional[str] = Field(None, description="每月执行时间")
    is_view_myself: Optional[bool] = Field(None, description="本人查看")

    # 复杂配置字段
    responsible_persons: Optional[List[PersonnelData]] = Field(None, description="指定人员")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    setting: Optional[Dict[str, Any]] = Field(None, description="其他设置（包含数据范围限制配置）")
    status: Optional[bool] = Field(None, description="订阅状态")
    ai_analysis_count: Optional[int] = Field(None, description="AI分析次数")
    last_analysis_time: Optional[datetime] = Field(None, description="最后一次分析时间")


class AISubscriptionInDB(AISubscriptionBase):
    """数据库中的AI订阅Schema"""

    id: int = Field(..., description="订阅ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
    ai_analysis_count: int = Field(0, description="AI分析次数")
    last_analysis_time: Optional[datetime] = Field(None, description="最后一次分析时间")


class AISubscriptionItem(AISubscriptionInDB):
    """AI订阅列表项Schema"""

    pass


class AISubscriptionDetail(AISubscriptionInDB):
    """AI订阅详情Schema"""

    pass


class AISubscriptionQueryParams(SchemaBase):
    """AI订阅查询参数Schema"""

    name: Optional[str] = Field(None, description="订阅名称")
    assistant_name: Optional[str] = Field(None, description="助手名称")
    responsible_person: Optional[str] = Field(None, description="负责人员")
    status: Optional[bool] = Field(None, description="订阅状态")


# 批量操作相关Schema
class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    ids: List[int] = Field(..., description="要删除的ID列表", min_items=1)


class BatchToggleStatusRequest(BaseModel):
    """批量切换状态请求"""

    ids: List[int] = Field(..., description="要切换状态的ID列表", min_items=1)
    status: bool = Field(..., description="目标状态")


class CloneRequest(BaseModel):
    """克隆请求"""

    name: str = Field(..., description="新订阅名称", min_length=1, max_length=100)
