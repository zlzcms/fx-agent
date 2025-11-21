# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 20:44:28
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base


class AIAssistant(Base):
    """AI助手模型"""

    __tablename__ = "ai_assistants"

    # 主键和必填字段（没有默认值）
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="助手ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="助手名称")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="助手类型")
    ai_model_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="AI模型ID")
    assistant_type_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="助手类型ID")

    # 可选字段（有默认值）
    avatar: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="助手头像URL")
    description: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="助手描述")
    model_definition: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="模型定义")

    # 执行配置字段
    execution_frequency: Mapped[str] = mapped_column(
        Enum("minutes", "hours", "daily", "weekly", "monthly", name="execution_frequency_enum"),
        default="daily",
        comment="执行频率",
    )
    execution_time: Mapped[Optional[str]] = mapped_column(String(10), default="09:00", comment="执行时间")
    execution_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=None, comment="分钟间隔")
    execution_hours: Mapped[Optional[int]] = mapped_column(Integer, default=None, comment="小时间隔")
    execution_weekday: Mapped[Optional[str]] = mapped_column(String(10), default=None, comment="执行星期")
    execution_weekly_time: Mapped[Optional[str]] = mapped_column(String(10), default=None, comment="每周执行时间")
    execution_day: Mapped[Optional[str]] = mapped_column(String(10), default=None, comment="执行日期")
    execution_monthly_time: Mapped[Optional[str]] = mapped_column(String(10), default=None, comment="每月执行时间")

    # 模板配置
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为模板")
    is_view_myself: Mapped[bool] = mapped_column(Boolean, default=False, comment="本人查看")

    # 数据源配置
    data_limit: Mapped[int] = mapped_column(Integer, default=100, comment="数据限制条数")

    # 新增数据权限和时间范围配置字段
    data_permission: Mapped[Optional[str]] = mapped_column(String(50), default=None, comment="数据权限")
    data_permission_values: Mapped[Optional[list]] = mapped_column(JSON, default=None, comment="数据权限具体值")
    data_time_range_type: Mapped[str] = mapped_column(
        Enum("day", "month", "quarter", "year", name="data_time_range_enum"),
        default="month",
        comment="数据时间范围类型",
    )
    data_time_value: Mapped[int] = mapped_column(Integer, default=1, comment="数据时间范围值")

    # 输出配置字段
    output_format: Mapped[str] = mapped_column(
        Enum("table", "document", "both", name="output_format_enum"), default="table", comment="输出格式"
    )
    output_data: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
        comment="输出数据：table格式时存储JSON字符串，document格式时存储Markdown文本，both格式时存储混合内容",
    )
    include_charts: Mapped[bool] = mapped_column(Boolean, default=False, comment="包含图表")
    auto_export: Mapped[bool] = mapped_column(Boolean, default=False, comment="自动导出")
    export_formats: Mapped[Optional[list]] = mapped_column(JSON, default=None, comment="导出格式")

    # 文档格式相关字段
    document_template: Mapped[Optional[str]] = mapped_column(String(50), default=None, comment="文档模板")
    custom_template: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="自定义模板")

    # 其他设置
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=None, comment="其他设置")

    ai_analysis_count: Mapped[int] = mapped_column(Integer, default=0, comment="AI分析次数")
    last_analysis_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=None, comment="最后一次分析时间"
    )

    # 状态和时间字段
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
    created_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    personnel_relations = relationship(
        "AIAssistantPersonnel", init=False, back_populates="assistant", cascade="all, delete-orphan"
    )
    notification_relations = relationship(
        "AIAssistantNotification", init=False, back_populates="assistant", cascade="all, delete-orphan"
    )
    permission_relations = relationship(
        "AIAssistantPermission", init=False, back_populates="assistant", cascade="all, delete-orphan"
    )

    # 模板关联关系
    template_relation = relationship(
        "AIAssistantTemplate", init=False, back_populates="assistant", cascade="all, delete-orphan", uselist=False
    )

    reports = relationship("AiAssistantReportLog", back_populates="assistants")

    # 便捷访问属性（基于关联表）
    @property
    def responsible_persons(self) -> List[str]:
        """获取指定人员ID列表"""
        return [rel.personnel_id for rel in self.personnel_relations]

    @property
    def notification_methods(self) -> List[str]:
        """获取通知方式ID列表"""
        return [rel.notification_id for rel in self.notification_relations]

    @property
    def permission_ids(self) -> List[str]:
        """获取数据权限ID列表"""
        return [rel.permission_id for rel in self.permission_relations]

    @property
    def data_sources(self) -> List[Dict[str, Any]]:
        """获取数据源配置"""
        # 从settings字段获取数据源配置
        if self.settings and "data_sources" in self.settings:
            return self.settings["data_sources"]
        return []

    def get_next_execution_time(self, from_time=None) -> datetime:
        """
        根据执行频率配置计算下次执行时间

        Args:
            from_time: 计算的起始时间，默认为当前时间

        Returns:
            下次执行的时间点
        """
        from datetime import datetime, timedelta

        # 如果未提供起始时间，则使用当前时间
        if from_time is None:
            from_time = datetime.now()

        # 根据不同的执行频率计算下次执行时间
        if self.execution_frequency == "minutes":
            # 每隔X分钟执行一次
            minutes = self.execution_minutes or 30  # 默认30分钟
            if minutes < 5:
                minutes = 5  # 最小5分钟间隔
            elif minutes > 1440:
                minutes = 1440  # 最大1440分钟（24小时）

            # 计算下一个整分钟时间点
            next_time = from_time + timedelta(minutes=minutes)

            return next_time

        elif self.execution_frequency == "hours":
            # 每隔X小时执行一次
            hours = self.execution_hours or 2  # 默认2小时
            if hours < 1:
                hours = 1  # 最小1小时间隔
            elif hours > 24:
                hours = 24  # 最大24小时

            # 计算下一个整点时间
            next_time = from_time + timedelta(hours=hours)

            return next_time

        elif self.execution_frequency == "daily":
            # 每天在指定时间执行
            exec_time = self.execution_time or "09:00"  # 默认上午9点
            hour, minute = map(int, exec_time.split(":"))

            # 创建今天的执行时间点
            next_time = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 如果时间已过，则安排在明天的同一时间
            if next_time <= from_time:
                next_time = next_time + timedelta(days=1)

            return next_time

        elif self.execution_frequency == "weekly":
            # 每周在指定的星期几和时间执行
            weekday = int(self.execution_weekday or 1)  # 默认周一，周日为0，周一到周六为1-6
            exec_time = self.execution_weekly_time or "19:00"  # 默认晚上7点
            hour, minute = map(int, exec_time.split(":"))

            # 计算本周的指定星期几
            current_weekday = from_time.weekday()  # 周一为0，周日为6
            if current_weekday == 6:
                current_weekday = 0  # 调整周日的索引为0，与前端保持一致
            else:
                current_weekday += 1  # 调整其他天的索引，使周一为1，周日为0

            days_ahead = weekday - current_weekday
            if days_ahead < 0:  # 如果已经过了本周的指定星期几，则计算下周
                days_ahead += 7

            # 如果是当天但时间已过，则需要再推迟一周
            if days_ahead == 0 and from_time.hour > hour or (from_time.hour == hour and from_time.minute >= minute):
                days_ahead = 7

            next_time = from_time + timedelta(days=days_ahead)
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return next_time

        elif self.execution_frequency == "monthly":
            # 每月在指定的日期和时间执行
            day = int(self.execution_day or 1)  # 默认每月1日
            exec_time = self.execution_monthly_time or "19:00"  # 默认晚上7点
            hour, minute = map(int, exec_time.split(":"))

            # 创建本月的执行时间点
            next_time = from_time.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)  # 先设为本月1日

            # 处理月末日期可能超出范围的问题
            import calendar

            _, last_day = calendar.monthrange(next_time.year, next_time.month)
            if day > last_day:
                day = last_day

            # 设置为指定的日期
            next_time = next_time.replace(day=day)

            # 如果时间已过，则计算下个月的相同日期
            if next_time <= from_time:
                # 转到下个月
                if next_time.month == 12:
                    next_time = next_time.replace(year=next_time.year + 1, month=1)
                else:
                    next_time = next_time.replace(month=next_time.month + 1)

                # 处理下个月日期可能超出范围的问题
                _, next_last_day = calendar.monthrange(next_time.year, next_time.month)
                if day > next_last_day:
                    next_time = next_time.replace(day=next_last_day)
                else:
                    next_time = next_time.replace(day=day)

            return next_time

        else:
            # 默认为当前时间加一天
            return from_time + timedelta(days=1)


class AIPersonnel(Base):
    """AI人员表"""

    __tablename__ = "ai_personnel"

    # 主键和必填字段（没有默认值）
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="人员ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")

    # 可选字段（有默认值）
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, default=None, comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None, comment="电话")
    department: Mapped[Optional[str]] = mapped_column(String(100), default=None, comment="部门")
    position: Mapped[Optional[str]] = mapped_column(String(100), default=None, comment="职位")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态")
    created_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    # assistant_relations = relationship("AIAssistantPersonnel", init=False, back_populates="personnel")


class AINotificationMethod(Base):
    """AI通知方式表"""

    __tablename__ = "ai_notification_methods"

    # 主键和必填字段（没有默认值）
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="通知方式ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="通知方式名称")
    type: Mapped[str] = mapped_column(
        Enum("email", "sms", "dingtalk", "wechat_work", "feishu", name="notification_type_enum"),
        nullable=False,
        comment="通知类型",
    )

    # 可选字段（有默认值）
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=None, comment="配置信息")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态")
    created_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    assistant_relations = relationship("AIAssistantNotification", init=False, back_populates="notification_method")


class AIDataPermission(Base):
    """AI数据权限表"""

    __tablename__ = "ai_data_permissions"

    # 主键和必填字段（没有默认值）
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="权限ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    permission_type: Mapped[str] = mapped_column(
        Enum(
            "time_range", "user_scope", "ip_range", "data_scope", "field_level", "custom", name="permission_type_enum"
        ),
        nullable=False,
        comment="权限类型",
    )
    permission_config: Mapped[dict] = mapped_column(JSON, nullable=False, comment="权限配置")

    # 可选字段（有默认值）
    description: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="权限描述")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态")
    created_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    assistant_relations = relationship("AIAssistantPermission", init=False, back_populates="permission")


# 关联表模型
class AIAssistantPersonnel(Base):
    """助手-人员关联表"""

    __tablename__ = "ai_assistant_personnel"

    # 主键和必填字段
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="关联ID")
    assistant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("ai_assistants.id", ondelete="CASCADE"), nullable=False, init=False, comment="助手ID"
    )
    personnel_id: Mapped[str] = mapped_column(String(50), nullable=False, init=False, comment="人员ID")
    username: Mapped[str] = mapped_column(String(50), init=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(100), init=False, comment="邮箱")

    # 可选字段（有默认值）
    created_time: Mapped[datetime] = mapped_column(DateTime, init=False, default=datetime.now, comment="创建时间")

    # 关联关系
    assistant = relationship("AIAssistant", init=False, back_populates="personnel_relations")
    # personnel = relationship("AIPersonnel", init=False, back_populates="assistant_relations")

    # 唯一约束
    __table_args__ = (UniqueConstraint("assistant_id", "personnel_id", name="uk_assistant_personnel"),)


class AIAssistantNotification(Base):
    """助手-通知方式关联表"""

    __tablename__ = "ai_assistant_notifications"

    # 主键和必填字段
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="关联ID")
    assistant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("ai_assistants.id", ondelete="CASCADE"), nullable=False, init=False, comment="助手ID"
    )
    notification_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ai_notification_methods.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
        comment="通知方式ID",
    )

    # 可选字段（有默认值）
    created_time: Mapped[datetime] = mapped_column(DateTime, init=False, default=datetime.now, comment="创建时间")

    # 关联关系
    assistant = relationship("AIAssistant", init=False, back_populates="notification_relations")
    notification_method = relationship("AINotificationMethod", init=False, back_populates="assistant_relations")

    # 唯一约束
    __table_args__ = (UniqueConstraint("assistant_id", "notification_id", name="uk_assistant_notification"),)


class AIAssistantPermission(Base):
    """助手-数据权限关联表"""

    __tablename__ = "ai_assistant_permissions"

    # 主键和必填字段
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="关联ID")
    assistant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("ai_assistants.id", ondelete="CASCADE"), nullable=False, init=False, comment="助手ID"
    )
    permission_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ai_data_permissions.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
        comment="数据权限ID",
    )

    # 可选字段（有默认值）
    created_time: Mapped[datetime] = mapped_column(DateTime, init=False, default=datetime.now, comment="创建时间")

    # 关联关系
    assistant = relationship("AIAssistant", init=False, back_populates="permission_relations")
    permission = relationship("AIDataPermission", init=False, back_populates="assistant_relations")

    # 唯一约束
    __table_args__ = (UniqueConstraint("assistant_id", "permission_id", name="uk_assistant_permission"),)


class AIAssistantTemplate(Base):
    """AI助手模板表"""

    __tablename__ = "ai_assistant_templates"

    # 主键和必填字段
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="模板ID")
    assistant_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ai_assistants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        init=False,
        comment="助手ID",
    )

    # 可选字段（有默认值）
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否开启")
    created_time: Mapped[datetime] = mapped_column(DateTime, init=False, default=datetime.now, comment="创建时间")
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    assistant = relationship("AIAssistant", init=False, back_populates="template_relation")

    # 唯一约束
    __table_args__ = (UniqueConstraint("assistant_id", name="uk_assistant_template"),)
