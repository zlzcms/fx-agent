#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风控报告记录模型
"""

from typing import Any, Dict, Optional

from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base

# TYPE_CHECKING imports removed as relationships are no longer needed


class AiAssistantReportLog(Base):
    """AI助手报告记录表"""

    __tablename__ = "ai_assistant_report_log"

    # 必填字段（无默认值，包括nullable但无default的字段）
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True, comment="报告ID")
    assistant_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_assistants.id"), comment="AI助手ID")
    model_id: Mapped[str] = mapped_column(String(36), index=True, comment="AI模型ID")
    member_ids: Mapped[str] = mapped_column(String(1500), index=True, comment="用户ID列表")
    subscription_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True, comment="订阅ID")
    sql_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="SQL查询数据，JSON格式")
    prompt_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="提示词数据，JSON格式")
    input_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="输入提示词")
    report_score: Mapped[float] = mapped_column(Float, comment="报告评分")
    report_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="报告结果")
    report_table: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="报告表格数据，JSON格式"
    )
    report_document: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="报告文档")
    ai_response: Mapped[Optional[str]] = mapped_column(JSON, default=None, comment="AI响应")

    # 有默认值的字段
    report_status: Mapped[bool] = mapped_column(Boolean, default=True, comment="报告状态")

    # 关联关系
    assistants = relationship("AIAssistant", init=False, back_populates="reports")
