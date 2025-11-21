#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from celery.schedules import schedule

from backend.app.task.utils.tzcrontab import TzAwareCrontab

# 参考：https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
LOCAL_BEAT_SCHEDULE = {
    "测试同步任务": {
        "task": "task_demo",
        "schedule": schedule(30),
    },
    "测试异步任务": {
        "task": "task_demo_async",
        "schedule": TzAwareCrontab("1"),
    },
    "测试传参任务": {
        "task": "task_demo_params",
        "schedule": TzAwareCrontab("1"),
        "args": ["你好，"],
        "kwargs": {"world": "世界"},
    },
    "清理操作日志": {
        "task": "backend.app.task.tasks.db_log.tasks.delete_db_opera_log",
        "schedule": TzAwareCrontab("0", "0", day_of_week="6"),
    },
    "清理登录日志": {
        "task": "backend.app.task.tasks.db_log.tasks.delete_db_login_log",
        "schedule": TzAwareCrontab("0", "0", day_of_month="15"),
    },
    # "增量客户风控分析": {
    #     "task": "scheduled_incremental_risk_analysis",
    #     "schedule": TzAwareCrontab("0", "*/6", "*", "*", "*"),
    #     "kwargs": {"risk_type": "all_employee", "time_window_hours": 6},
    # },
    # "增量员工风控分析": {
    #     "task": "scheduled_incremental_risk_analysis",
    #     "schedule": TzAwareCrontab("15", "*/6", "*", "*", "*"),
    #     "kwargs": {"risk_type": "crm_user", "time_window_hours": 6},
    # },
    # "增量代理商风控分析": {
    #     "task": "scheduled_incremental_risk_analysis",
    #     "schedule": TzAwareCrontab("30", "*/6", "*", "*", "*"),
    #     "kwargs": {"risk_type": "agent_user", "time_window_hours": 6},
    # },
    # "增量出金风控分析": {
    #     "task": "scheduled_incremental_risk_analysis",
    #     "schedule": TzAwareCrontab("45", "*/12", "*", "*", "*"),
    #     "kwargs": {"risk_type": "payment", "time_window_hours": 12},
    # },
}
