#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base, id_key

if TYPE_CHECKING:
    from backend.app.admin.model import User


class ApiKey(Base):
    """API Key表"""

    __tablename__ = "sys_api_key"

    id: Mapped[id_key] = mapped_column(init=False)
    key_name: Mapped[str] = mapped_column(String(100), comment="API Key名称", index=True)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment="API Key值")
    api_secret: Mapped[str] = mapped_column(String(255), comment="API Secret（加密存储）")
    description: Mapped[str | None] = mapped_column(Text, default=None, comment="描述")
    status: Mapped[int] = mapped_column(default=1, index=True, comment="状态(0停用 1启用)")
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, comment="过期时间，NULL表示永不过期"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, comment="最后使用时间")
    last_used_ip: Mapped[str | None] = mapped_column(String(50), default=None, comment="最后使用IP")
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    ip_whitelist: Mapped[str | None] = mapped_column(Text, default=None, comment="IP白名单，多个IP用逗号分隔")
    permissions: Mapped[str | None] = mapped_column(Text, default=None, comment="权限列表，JSON格式存储")

    # 关联用户
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), default=None, comment="创建者用户ID"
    )
    user: Mapped[User | None] = relationship(init=False, back_populates="api_keys")

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
