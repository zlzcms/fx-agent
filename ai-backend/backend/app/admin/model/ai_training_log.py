# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-07-03 17:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-03 17:53:52

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.enums import TrainingLogType
from backend.common.model import DataClassBase, id_key
from backend.utils.timezone import timezone


class AITrainingLog(DataClassBase):
    """AI模型训练操作记录表"""

    __tablename__ = "ai_training_logs"

    id: Mapped[id_key] = mapped_column(init=False)
    model_id: Mapped[str] = mapped_column(String(36), index=True, comment="关联的AI模型ID")
    model_name: Mapped[str] = mapped_column(String(100), comment="模型名称")
    log_type: Mapped[TrainingLogType] = mapped_column(
        String(50), default=TrainingLogType.ai_assistant, comment="日志类型（如：ai_assistant，risk_control_assistant）"
    )
    prompt_template: Mapped[Optional[str]] = mapped_column(JSON, default=None, comment="使用的提示词模板")
    base_info: Mapped[Optional[list]] = mapped_column(JSON, default=None, comment="基础信息")
    data: Mapped[Optional[JSON]] = mapped_column(JSON, default=None, comment="数据")
    assistant_id: Mapped[Optional[str]] = mapped_column(String(36), default=None, comment="AI助手ID")
    # 训练结果
    success: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否成功")
    score: Mapped[Optional[float]] = mapped_column(Float, default=0, comment="评分/准确率")

    content: Mapped[Optional[str]] = mapped_column(Text, default=None, comment="内容")
    ai_response: Mapped[Optional[list]] = mapped_column(JSON, default=None, comment="AI响应")
    created_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, comment="记录创建时间"
    )
    updated_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, default_factory=timezone.now, onupdate=timezone.now, comment="记录更新时间"
    )
