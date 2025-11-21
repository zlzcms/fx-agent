# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 12:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 12:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class DataSourceCollection(Base):
    """数据源集合模型"""

    __tablename__ = "ai_datasource_collection"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True, comment="集合ID")
    name: Mapped[str] = mapped_column(String(100), unique=True, comment="集合名称")
    query_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None, comment="查询名称")
    description: Mapped[Optional[str]] = mapped_column(String(500), default=None, comment="集合描述")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="启用状态")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )

    # # 关联关系 - 不使用Mapped类型注解避免dataclass问题
    # datasources = relationship(
    #     "DataSource",
    #     back_populates="collection",
    #     cascade="all, delete-orphan"
    # )
