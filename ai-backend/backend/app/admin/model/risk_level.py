# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:56:57
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 11:49:24
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class RiskLevel(Base):
    """风控等级表"""

    __tablename__ = "risk_level"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="风控等级ID，使用UUID")
    name: Mapped[str] = mapped_column(String(100), index=True, unique=True, comment="风控等级名称")
    start_score: Mapped[int] = mapped_column(Integer, comment="评分范围开始分")
    end_score: Mapped[int] = mapped_column(Integer, comment="评分范围结束分")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="风控等级描述")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
