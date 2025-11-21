#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AIChat(Base):
    """AI Chat model for storing chat sessions"""

    __tablename__ = "ai_chat"

    # 使用新的mapped_column语法，与数据库表结构保持一致
    id: Mapped[str] = mapped_column(String(36), primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=False, index=True, init=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_models.id"), nullable=False, init=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, comment="删除时间，NULL表示未删除"
    )
    # 历史对话总结字段 - 用于节省token
    history_summary: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, default=None, comment="历史对话压缩摘要，用于减少token消耗"
    )
    summary_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, comment="摘要生成时间", index=True
    )
    channel: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None, comment="渠道标识，用于追踪来源"
    )
    # 数据库表中有这些字段，但Base类也提供了created_time和updated_time
    # 为了避免冲突，我们使用Base类的字段

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "model_id": self.model_id,
            "status": self.status,
            "channel": self.channel,
            "history_summary": self.history_summary,
            "summary_time": self.summary_time.isoformat() if self.summary_time else None,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
        }
