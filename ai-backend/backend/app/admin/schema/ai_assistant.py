# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-25 17:28:05
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


class AIAssistantBase(SchemaBase):
    """AI助手基础Schema"""

    name: str = Field(..., description="助手名称", min_length=1, max_length=100)
    type: str = Field(..., description="助手类型", max_length=50)
    assistant_type_id: str = Field(..., description="助手类型ID", max_length=50)
    ai_model_id: str = Field(..., description="AI模型ID", max_length=50)
    avatar: Optional[str] = Field(None, description="助手头像URL")
    description: Optional[str] = Field(None, description="助手描述")
    model_definition: Optional[str] = Field(None, description="模型定义")
    execution_frequency: str = Field("daily", description="执行频率", pattern="^(minutes|hours|daily|weekly|monthly)$")
    execution_time: Optional[str] = Field("09:00", description="执行时间")
    execution_minutes: Optional[int] = Field(None, description="分钟间隔", ge=5, le=1440)
    execution_hours: Optional[int] = Field(None, description="小时间隔", ge=1, le=24)
    execution_weekday: Optional[str] = Field(None, description="执行星期")
    execution_weekly_time: Optional[str] = Field(None, description="每周执行时间")
    execution_day: Optional[str] = Field(None, description="执行日期")
    execution_monthly_time: Optional[str] = Field(None, description="每月执行时间")
    status: bool = Field(True, description="状态")
    is_template: bool = Field(False, description="是否为模板")
    is_view_myself: bool = Field(False, description="本人查看")

    # 数据源相关配置
    data_limit: int = Field(100, description="数据限制条数", ge=1, le=10000)

    # 数据权限和时间范围配置字段
    data_permission: Optional[str] = Field(None, description="数据权限")
    data_permission_values: Optional[List[str | int]] = Field(None, description="数据权限具体值")
    data_time_range_type: str = Field("month", description="数据时间范围类型", pattern="^(day|month|quarter|year)$")
    data_time_value: int = Field(1, description="数据时间范围值", ge=1, le=100)

    # 输出相关配置
    output_format: str = Field("table", description="输出格式", pattern="^(table|document|both)$")
    output_data: Optional[str | Dict[str, Any]] = Field(None, description="输出数据")
    include_charts: bool = Field(False, description="包含图表")
    auto_export: bool = Field(False, description="自动导出")

    # 复杂配置字段 - 修改responsible_persons字段类型
    responsible_persons: Optional[List[PersonnelData]] = Field(None, description="指定人员")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    data_sources: Optional[List[Dict[str, Any]]] = Field(None, description="分析数据源")
    data_permissions: Optional[List[str]] = Field(None, description="数据权限范围")
    settings: Optional[Dict[str, Any]] = Field(None, description="其他设置")


class AIAssistantCreate(AIAssistantBase):
    """创建AI助手Schema"""

    pass


class AIAssistantUpdate(SchemaBase):
    """更新AI助手Schema"""

    name: Optional[str] = Field(None, description="助手名称", min_length=1, max_length=100)
    type: Optional[str] = Field(None, description="助手类型", max_length=50)
    assistant_type_id: Optional[str] = Field(None, description="助手类型ID", max_length=50)
    ai_model_id: Optional[str] = Field(None, description="AI模型ID", max_length=50)
    avatar: Optional[str] = Field(None, description="助手头像URL")
    description: Optional[str] = Field(None, description="助手描述")
    model_definition: Optional[str] = Field(None, description="模型定义")
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
    status: Optional[bool] = Field(None, description="状态")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_view_myself: Optional[bool] = Field(None, description="本人查看")

    # 数据源相关配置
    data_limit: Optional[int] = Field(None, description="数据限制条数", ge=1, le=10000)

    # 数据权限和时间范围配置字段
    data_permission: Optional[str] = Field(None, description="数据权限")
    data_permission_values: Optional[List[str | int]] = Field(None, description="数据权限具体值")
    data_time_range_type: Optional[str] = Field(
        None, description="数据时间范围类型", pattern="^(day|month|quarter|year)$"
    )
    data_time_value: Optional[int] = Field(None, description="数据时间范围值", ge=1, le=100)

    # 输出相关配置
    output_format: Optional[str] = Field(None, description="输出格式", pattern="^(table|document|both)$")
    output_data: Optional[str | Dict[str, Any]] = Field(None, description="输出数据")
    include_charts: Optional[bool] = Field(None, description="包含图表")
    auto_export: Optional[bool] = Field(None, description="自动导出")

    # 复杂配置字段 - 修改responsible_persons字段类型
    responsible_persons: Optional[List[PersonnelData]] = Field(None, description="指定人员")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    data_sources: Optional[List[Dict[str, Any]]] = Field(None, description="分析数据源")
    data_permissions: Optional[List[str]] = Field(None, description="数据权限范围")
    settings: Optional[Dict[str, Any]] = Field(None, description="其他设置")
    ai_analysis_count: Optional[int] = Field(None, description="AI分析次数")
    last_analysis_time: Optional[datetime] = Field(None, description="最后一次分析时间")


class AIAssistantInDB(AIAssistantBase):
    """数据库中的AI助手Schema"""

    id: str = Field(..., description="助手ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    # 重写复杂字段，因为数据库中存储的是JSON格式
    responsible_persons: Optional[List[str]] = Field(None, description="指定人员")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    data_sources: Optional[List[Dict[str, Any]]] = Field(None, description="分析数据源")
    data_permissions: Optional[List[str]] = Field(None, description="数据权限范围")


class AIAssistantItem(AIAssistantInDB):
    """AI助手列表项Schema"""

    pass


class AIAssistantDetail(AIAssistantInDB):
    """AI助手详情Schema"""

    pass


class AIAssistantQueryParams(SchemaBase):
    """AI助手查询参数Schema"""

    name: Optional[str] = Field(None, description="助手名称")
    assistant_type_id: Optional[str] = Field(None, description="助手类型ID")
    ai_model_id: Optional[str] = Field(None, description="AI模型ID")
    responsible_person: Optional[str] = Field(None, description="负责人员")
    status: Optional[bool] = Field(None, description="状态")
    is_template: Optional[bool] = Field(None, description="是否为模板")


# AIPersonnel 相关 schema 已删除，改为使用 sys_user 表


# 通知方式相关Schema
class AINotificationMethodBase(SchemaBase):
    """AI通知方式基础Schema"""

    name: str = Field(..., description="通知方式名称", min_length=1, max_length=50)
    type: str = Field(..., description="通知类型", pattern="^(email|sms|dingtalk|wechat_work|feishu)$")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    status: bool = Field(True, description="状态")


class AINotificationMethodCreate(AINotificationMethodBase):
    """创建AI通知方式Schema"""

    pass


class AINotificationMethodUpdate(SchemaBase):
    """更新AI通知方式Schema"""

    name: Optional[str] = Field(None, description="通知方式名称", min_length=1, max_length=50)
    type: Optional[str] = Field(None, description="通知类型", pattern="^(email|sms|dingtalk|wechat_work|feishu)$")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    status: Optional[bool] = Field(None, description="状态")


class AINotificationMethodInDB(AINotificationMethodBase):
    """数据库中的AI通知方式Schema"""

    id: int = Field(..., description="通知方式ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


# 数据权限相关Schema
class AIDataPermissionBase(SchemaBase):
    """AI数据权限基础Schema"""

    name: str = Field(..., description="权限名称", min_length=1, max_length=100)
    permission_type: str = Field(
        ..., description="权限类型", pattern="^(time_range|user_scope|ip_range|data_scope|field_level|custom)$"
    )
    permission_config: Dict[str, Any] = Field(..., description="权限配置")
    description: Optional[str] = Field(None, description="权限描述")
    status: bool = Field(True, description="状态")


class AIDataPermissionCreate(AIDataPermissionBase):
    """创建AI数据权限Schema"""

    pass


class AIDataPermissionUpdate(SchemaBase):
    """更新AI数据权限Schema"""

    name: Optional[str] = Field(None, description="权限名称", min_length=1, max_length=100)
    permission_type: Optional[str] = Field(
        None, description="权限类型", pattern="^(time_range|user_scope|ip_range|data_scope|field_level|custom)$"
    )
    permission_config: Optional[Dict[str, Any]] = Field(None, description="权限配置")
    description: Optional[str] = Field(None, description="权限描述")
    status: Optional[bool] = Field(None, description="状态")


class AIDataPermissionInDB(AIDataPermissionBase):
    """数据库中的AI数据权限Schema"""

    id: str = Field(..., description="权限ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


# 批量操作相关Schema
class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    ids: List[str] = Field(..., description="要删除的ID列表", min_items=1)


class BatchToggleStatusRequest(BaseModel):
    """批量切换状态请求"""

    ids: List[str] = Field(..., description="要切换状态的ID列表", min_items=1)
    status: bool = Field(..., description="目标状态")


class ToggleTemplateStatusRequest(BaseModel):
    """切换模板状态请求"""

    is_open: bool = Field(..., description="模板开启状态")


class CloneRequest(BaseModel):
    """克隆请求"""

    name: str = Field(..., description="新助手名称", min_length=1, max_length=100)
