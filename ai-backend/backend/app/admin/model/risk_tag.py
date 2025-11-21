# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 14:13:45
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 14:36:07
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class RiskTag(Base):
    """风控标签表"""

    __tablename__ = "risk_tag"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, comment="标签ID，自增主键"
    )
    risk_type: Mapped[str] = mapped_column(String(50), index=True, comment="风控类型")
    name: Mapped[str] = mapped_column(String(100), index=True, comment="标签名称")
    description: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="标签描述")

    # 软删除字段
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
