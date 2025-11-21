# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class FunctionType(Base):
    """功能类型表"""

    __tablename__ = "function_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="功能类型ID，使用UUID")
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="功能类型名称")
