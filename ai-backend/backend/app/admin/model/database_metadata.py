# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:48:42
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-25 17:53:13
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key
from backend.utils.timezone import timezone


class DatabaseMetadata(Base):
    """数据库元数据表"""

    __tablename__ = "ai_database_metadata"

    id: Mapped[id_key] = mapped_column(init=False)
    metadata_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="元数据唯一标识")
    name: Mapped[str] = mapped_column(String(100), index=True, comment="名称（数据库名、表名、字段名）")
    type: Mapped[str] = mapped_column(String(20), index=True, comment="类型：database/table/field")
    description: Mapped[str | None] = mapped_column(Text, default=None, comment="描述信息")
    parent_id: Mapped[str | None] = mapped_column(String(100), default=None, index=True, comment="父节点ID")

    # 字段特有属性
    field_type: Mapped[str | None] = mapped_column(String(100), default=None, comment="字段类型")
    is_nullable: Mapped[bool | None] = mapped_column(
        Boolean().with_variant(INTEGER, "postgresql"), default=None, comment="是否可为空"
    )
    default_value: Mapped[str | None] = mapped_column(Text, default=None, comment="默认值")

    # 表特有属性
    table_rows: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="表数据行数")
    table_size: Mapped[str | None] = mapped_column(String(20), default=None, comment="表大小")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, onupdate=timezone.now, comment="更新时间"
    )
