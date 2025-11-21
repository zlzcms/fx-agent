# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 20:44:28
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base, id_key


class AISubscription(Base):
    """AI订阅模型"""

    __tablename__ = "ai_subscription"

    # 主键和必填字段
    id: Mapped[id_key] = mapped_column(init=False, comment="订阅ID")
    assistant_id: Mapped[str] = mapped_column(ForeignKey("ai_assistants.id"), nullable=False, comment="助手ID")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="创建用户ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="订阅名称")
    subscription_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="订阅类型")

    # 执行配置字段（有默认值）
    execution_frequency: Mapped[str] = mapped_column(
        String(20),
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
    is_view_myself: Mapped[bool] = mapped_column(Boolean, default=False, comment="本人查看")

    # 其他设置（有默认值）
    setting: Mapped[Optional[dict]] = mapped_column(JSON, default=None, comment="其他设置（包含数据范围限制配置）")
    responsible_persons: Mapped[Optional[list]] = mapped_column(JSON, default=None, comment="通知对象列表")

    ai_analysis_count: Mapped[int] = mapped_column(Integer, default=0, comment="分析次数")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, comment="删除时间，NULL表示未删除"
    )
    last_analysis_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, comment="最后一次分析时间"
    )

    # 状态和关联字段
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="订阅状态")

    # 关联关系
    notification_relations = relationship(
        "AISubscriptionNotification", init=False, back_populates="subscription", cascade="all, delete-orphan"
    )

    # 便捷访问属性（基于关联表）

    @property
    def notification_methods(self) -> List[str]:
        """获取通知方式ID列表"""
        return [rel.notification_id for rel in self.notification_relations]

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


class AISubscriptionNotificationMethod(Base):
    """AI订阅通知方式表"""

    __tablename__ = "ai_subscription_notification_methods"

    # 主键和必填字段（没有默认值）
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False, comment="通知方式ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="通知方式名称")
    type: Mapped[str] = mapped_column(
        String(20),
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
    subscription_relations = relationship(
        "AISubscriptionNotification", init=False, back_populates="notification_method"
    )


class AISubscriptionNotification(Base):
    """助手-通知方式关联表"""

    __tablename__ = "ai_subscription_notifications"

    # 主键和必填字段
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, init=False, comment="关联ID")
    subscription_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ai_subscription.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        init=False,
        comment="订阅ID",
    )
    notification_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ai_subscription_notification_methods.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
        comment="通知方式ID",
    )

    # 通知发送相关字段
    report_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, init=False, comment="关联报告ID")
    send_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        init=False,
        comment="发送状态: pending-待发送, sending-发送中, sent-已发送, failed-发送失败",
    )
    send_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, init=False, comment="发送时间")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, init=False, comment="重试次数")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, init=False, comment="错误信息")

    # 可选字段（有默认值）
    created_time: Mapped[datetime] = mapped_column(DateTime, init=False, default=datetime.now, comment="创建时间")
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, init=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关联关系
    subscription = relationship("AISubscription", init=False, back_populates="notification_relations")
    notification_method = relationship(
        "AISubscriptionNotificationMethod",
        init=False,
        back_populates="subscription_relations",
        foreign_keys=[notification_id],
    )

    # 移除唯一约束，允许一个订阅有多个相同的通知方式
    # __table_args__ = (UniqueConstraint("subscription_id", "notification_id", name="uk_subscription_notification"),)
