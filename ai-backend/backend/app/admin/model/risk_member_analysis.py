# -*- coding: utf-8 -*-
# @Author: AI Assistant
# @Date:   2023-11-25 14:13:45
# @Last Modified by:   AI Assistant
# @Last Modified time: 2023-11-25 14:36:07
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class RiskMemberAnalysis(Base):
    """风控员工分析记录表"""

    __tablename__ = "risk_member_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="记录ID，使用UUID")
    member_id: Mapped[str] = mapped_column(String(36), index=True, comment="员工ID")
    risk_type: Mapped[str] = mapped_column(String(50), index=True, comment="风险类型")
    analysis_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="分析时间")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="", comment="备注")
