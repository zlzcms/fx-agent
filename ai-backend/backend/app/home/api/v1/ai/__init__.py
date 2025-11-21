#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from . import assistant, models, reports, subscriptions

router = APIRouter()

router.include_router(models.router, prefix="/models", tags=["AI模型"])
router.include_router(reports.router, prefix="/reports", tags=["我的报告"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["我的订阅"])
router.include_router(assistant.router, prefix="/assistants", tags=["AI助理"])

# 定义路由器并导出
__all__ = ["router"]
