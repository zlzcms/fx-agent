# -*- coding: utf-8 -*-
# @Author: AI Assistant
# @Date:   2023-11-25 15:25:30
# @Last Modified by:   AI Assistant
# @Last Modified time: 2023-11-25 15:35:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class AIDataAnalysis(Base):
    """AI助手分析数据记录表"""

    __tablename__ = "ai_assistant_data_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="记录ID，使用UUID")
    assistant_id: Mapped[str] = mapped_column(String(36), index=True, comment="AI助手ID")
    database_name: Mapped[str] = mapped_column(String(100), index=True, comment="数据库名")
    table_name: Mapped[str] = mapped_column(String(100), index=True, comment="表名")
    field_id: Mapped[str] = mapped_column(String(100), index=True, comment="字段ID")
    result_summary: Mapped[Optional[str]] = mapped_column(Text, comment="分析结果摘要")
    analysis_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="分析时间")
