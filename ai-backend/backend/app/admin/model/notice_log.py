#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key
from backend.utils.timezone import timezone


class NoticeLog(Base):
    """通知日志记录表"""

    __tablename__ = "sys_notice_log"

    id: Mapped[id_key] = mapped_column(init=False)
    description: Mapped[str] = mapped_column(String(500), comment="通知描述，例如：订阅报告通知，报告id:56")
    notification_type: Mapped[str] = mapped_column(String(50), comment="通知方式：email/lark_webhook")
    content: Mapped[str] = mapped_column(Text, comment="通知发送时的主体内容")
    address: Mapped[str] = mapped_column(String(500), comment="通知地址：邮箱地址/webhook地址")
    is_success: Mapped[bool] = mapped_column(Boolean, default=False, comment="通知是否成功：True=成功，False=失败")
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="通知失败原因描述")

    # 时间字段
    created_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, onupdate=timezone.now, comment="更新时间"
    )
