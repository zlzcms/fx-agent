# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:51:23
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-29 10:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from . import (
    agent,
    assistant_types,
    assistants,
    data_analysis,
    databases,
    datasources,
    models,
    report_logs,
    sql_generator,
    subscriptions,
)

router = APIRouter()

router.include_router(assistants.router, prefix="/assistants", tags=["AI助手管理"])
router.include_router(databases.router, prefix="/databases", tags=["数据库管理"])
router.include_router(datasources.router, prefix="/datasources", tags=["数据源管理"])
router.include_router(models.router, prefix="/models", tags=["AI模型管理"])
router.include_router(assistant_types.router, prefix="/assistant-types", tags=["助手类型管理"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["AI订阅管理"])
router.include_router(sql_generator.router, prefix="/sql-generator", tags=["SQL生成器"])
router.include_router(agent.router, prefix="/agent", tags=["代理服务"])
router.include_router(report_logs.router, prefix="/reports", tags=["报告日志"])
router.include_router(data_analysis.router, prefix="/data-analysis", tags=["数据分析服务"])

# 定义路由器并导出
__all__ = ["router"]
