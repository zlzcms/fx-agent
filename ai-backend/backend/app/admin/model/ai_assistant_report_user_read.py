#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告用户阅读关系表模型
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AiAssistantReportUserRead(Base):
    """AI助手报告用户阅读关系表"""

    __tablename__ = "ai_assistant_report_user_read"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, init=False, comment="关系ID", index=True
    )
    report_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="报告ID")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID", index=True
    )
    read_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, comment="阅读时间"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已读(0: 未读, 1: 已读)")

    __table_args__ = (UniqueConstraint("report_id", "user_id", name="uk_report_user_read"),)
