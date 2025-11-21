# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-14 13:38:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-01 16:14:42

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AIModel(Base):
    """AI模型配置表"""

    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="模型ID，使用UUID")
    name: Mapped[str] = mapped_column(String(100), index=True, comment="模型名称")
    api_key: Mapped[str] = mapped_column(Text, comment="API密钥，加密存储")
    model_type: Mapped[str] = mapped_column(String(50), index=True, comment="模型类型")
    model: Mapped[str] = mapped_column(String(100), comment="模型名称/标识符，如gpt-4-turbo")
    temperature: Mapped[float] = mapped_column(Float, default=0.75, comment="温度参数，值范围0-1")
    base_url: Mapped[Optional[str]] = mapped_column(String(500), default=None, comment="API基础URL")
    status: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="状态：1=启用，0=禁用")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True, comment="软删除时间，NULL表示未删除"
    )
