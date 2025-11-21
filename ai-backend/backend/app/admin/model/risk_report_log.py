#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风控报告记录模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.enums import RiskAnalysisType
from backend.common.model import Base


class RiskReportLog(Base):
    """风控报告记录表"""

    __tablename__ = "risk_report_log"

    # 必填字段（无默认值）
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True, comment="报告ID")
    assistant_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_assistant.id"), comment="风控助手ID")
    model_id: Mapped[str] = mapped_column(String(36), index=True, comment="AI模型ID")
    risk_type: Mapped[str] = mapped_column(String(50), index=True, comment="风险类型")
    member_id: Mapped[str] = mapped_column(String(36), index=True, comment="用户ID")
    report_score: Mapped[float] = mapped_column(Float(53), comment="报告评分")
    sql_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="SQL查询数据，JSON格式")
    prompt_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="提示词数据，JSON格式")
    input_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="输入提示词")
    score: Mapped[Optional[float]] = mapped_column(Float(53), nullable=True, comment="风险评分")
    report_tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True, comment="报告标签，JSONB数组")
    report_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="报告结果")
    report_table: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="报告表格数据，JSON格式"
    )
    report_document: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="报告文档")
    report_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="报告PDF文件URL")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="风险描述，支持外部系统展示")
    # 处理建议，处理结果，处理人，处理时间
    handle_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="处理建议")
    handle_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, init=False, comment="处理结果")
    handle_user: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, init=False, comment="处理人")
    handle_user_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, init=False, comment="处理人名称")
    handle_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, init=False, comment="处理时间")
    member_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="用户名称")

    # 有默认值的字段
    report_status: Mapped[bool] = mapped_column(Boolean, default=True, comment="报告状态")
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要处理")
    ai_response: Mapped[Optional[str]] = mapped_column(JSON, default=None, comment="AI响应")

    # 增量分析相关字段
    analysis_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default=RiskAnalysisType.STOCK,
        comment="分析类型：STOCK=存量，INCREMENTAL=增量，TRIGGERED=触发",
    )
    trigger_sources: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None, comment="触发原因：new_register,new_login,new_transfer等，多个用逗号分隔"
    )
    detection_window_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None, comment="检测窗口信息：时间范围、窗口大小等"
    )

    assistant = relationship("RiskAssistant", back_populates="reports")
