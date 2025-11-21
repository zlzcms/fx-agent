#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class RecommendedQuestion(Base):
    """推荐问法表"""

    __tablename__ = "sys_recommended_questions"

    id: Mapped[id_key] = mapped_column(init=False)
    title: Mapped[str] = mapped_column(String(100), comment="问法标题")
    content: Mapped[str] = mapped_column(Text, comment="问法内容")
    role_ids: Mapped[list[int] | None] = mapped_column(JSON, comment="关联角色ID列表")
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序")
    status: Mapped[int] = mapped_column(default=1, comment="状态(0停用 1正常)")
    is_default: Mapped[bool] = mapped_column(default=False, comment="是否默认问法")
    created_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=datetime.now, comment="创建时间"
    )
    updated_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), init=False, onupdate=datetime.now, comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
