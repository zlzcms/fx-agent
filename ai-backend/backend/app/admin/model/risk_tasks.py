#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险任务表模型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DECIMAL, JSON, Column, DateTime, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from backend.common.model import Base


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    """任务类型枚举"""

    PAYMENT_RISK = "payment_risk"


class RiskLevel(str, Enum):
    """风险等级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskTasks(Base):
    """风险任务表"""

    __tablename__ = "risk_tasks"

    # 主键和标识
    task_id = Column(String(64), primary_key=True, comment="任务唯一标识，UUID格式")

    # 任务基本信息
    task_type = Column(SQLEnum(TaskType), default=TaskType.PAYMENT_RISK, comment="任务类型")
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    member_id = Column(Integer, nullable=False, comment="用户ID")
    progress = Column(Integer, default=0, comment="进度百分比(0-100)")
    message = Column(Text, nullable=True, comment="状态描述信息")
    report_id = Column(Integer, nullable=True, comment="报告日志ID")

    # 请求数据
    request_data = Column(JSON, nullable=True, comment="原始请求参数（payment_info等）")

    # 结果数据
    risk_score = Column(DECIMAL(5, 2), nullable=True, comment="风险评分 0.00-100.00")
    risk_level = Column(SQLEnum(RiskLevel), nullable=True, comment="风险等级")
    analysis_result = Column(JSON, nullable=True, comment="详细分析结果")

    # 错误处理
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="任务创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="任务更新时间")
    completed_at = Column(DateTime, nullable=True, comment="任务完成时间")


# 索引
Index("idx_risk_tasks_member_id", RiskTasks.member_id)
Index("idx_risk_tasks_status", RiskTasks.status)
Index("idx_risk_tasks_created_at", RiskTasks.created_at)
Index("idx_risk_tasks_task_type_status", RiskTasks.task_type, RiskTasks.status)
