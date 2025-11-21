# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 10:43:11
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 18:45:25
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class DataSource(Base):
    """数据源模型"""

    __tablename__ = "ai_datasource"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, comment="数据源ID")
    collection_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("ai_datasource_collection.id", ondelete="CASCADE"), comment="所属集合ID"
    )
    database_name: Mapped[str] = mapped_column(String(100), comment="数据库名称")
    table_name: Mapped[str] = mapped_column(String(100), comment="表名")
    description: Mapped[Optional[str]] = mapped_column(String(500), default=None, comment="数据源描述")
    data_count: Mapped[Optional[int]] = mapped_column(Integer, default=None, comment="数据量")
    relation_field: Mapped[Optional[str]] = mapped_column(String(100), default=None, comment="关联字段名")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )

    # # 关联关系 - 不使用Mapped类型注解避免dataclass问题
    # collection = relationship(
    #     "DataSourceCollection",
    #     back_populates="datasources"
    # )
