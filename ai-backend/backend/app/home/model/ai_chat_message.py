#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AIChatMessage(Base):
    """AI Chat Message model for storing individual messages in a chat session"""

    __tablename__ = "ai_chat_message"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    response_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )  # For storing query results
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, default=None, comment="删除时间，NULL表示未删除"
    )
    is_interrupted: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)  # 标记消息是否被中断

    def to_dict(self):
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "response_data": self.response_data,
            "is_interrupted": self.is_interrupted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
        }
