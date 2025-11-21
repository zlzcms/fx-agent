# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:40:58
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:18:34

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AssistantType(Base):
    """助手类型表"""

    __tablename__ = "ai_assistant_type"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="助手类型ID，使用UUID")
    name: Mapped[str] = mapped_column(String(100), index=True, unique=True, comment="助手类型名称")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
