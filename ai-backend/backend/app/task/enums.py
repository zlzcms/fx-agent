#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.common.enums import IntEnum, StrEnum


class TaskSchedulerType(IntEnum):
    """任务调度类型"""

    INTERVAL = 0
    CRONTAB = 1


class PeriodType(StrEnum):
    """周期类型"""

    DAYS = "days"
    HOURS = "hours"
    MINUTES = "minutes"
    SECONDS = "seconds"
    MICROSECONDS = "microseconds"


class TaskExecutionStatus(StrEnum):
    """任务执行状态枚举"""

    PENDING = "PENDING"  # 等待执行
    STARTED = "STARTED"  # 已开始
    SUCCESS = "SUCCESS"  # 成功
    FAILURE = "FAILURE"  # 失败
    RETRY = "RETRY"  # 重试
    REVOKED = "REVOKED"  # 已撤销
