# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 15:32:47
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 15:38:19
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import Base


class RiskAssistant(Base):
    """风控助手表"""

    __tablename__ = "risk_assistant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="风控助手ID，使用UUID")
    risk_type: Mapped[str] = mapped_column(String(100), nullable=True, comment="风险类型")
    name: Mapped[str] = mapped_column(String(100), index=True, unique=True, comment="风控助手名称")
    ai_model_id: Mapped[str] = mapped_column(String(36), comment="使用的AI模型ID，关联ai_model表")
    role: Mapped[str] = mapped_column(String(200), comment="角色定义")
    background: Mapped[Optional[str]] = mapped_column(Text, comment="背景描述")
    task_prompt: Mapped[str] = mapped_column(Text, comment="任务提示词")
    variable_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="变量配置，JSON格式存储"
    )
    report_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="报告配置，JSON格式存储"
    )
    setting: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="设置，JSON格式存储")
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态：True-启用，False-禁用")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, comment="删除时间")
    ai_analysis_count: Mapped[int] = mapped_column(Integer, default=0, comment="AI分析次数")
    last_analysis_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=None, comment="最后一次分析时间"
    )

    # 关联风控报告
    reports = relationship("RiskReportLog", back_populates="assistant")

    def __repr__(self):
        return f"<RiskAssistant(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        import json

        # 处理可能是字符串格式的JSON字段
        def parse_json_field(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except json.JSONDecodeError:
                    return field_value
            return field_value

        return {
            "id": self.id,
            "risk_type": self.risk_type,
            "name": self.name,
            "ai_model_id": self.ai_model_id,
            "role": self.role,
            "background": self.background,
            "task_prompt": self.task_prompt,
            "variable_config": parse_json_field(self.variable_config),
            "report_config": parse_json_field(self.report_config),
            "setting": self.setting,
            "status": self.status,
            "ai_analysis_count": self.ai_analysis_count,
            "last_analysis_time": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "created_time": self.created_time.isoformat()
            if hasattr(self, "created_time") and self.created_time
            else None,
            "updated_time": self.updated_time.isoformat()
            if hasattr(self, "updated_time") and self.updated_time
            else None,
        }
