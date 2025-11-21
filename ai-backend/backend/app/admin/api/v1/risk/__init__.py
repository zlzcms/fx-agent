# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:59:30
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 10:59:52

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from . import payment_risk, risk_assistants, risk_levels, risk_tags

router = APIRouter()

router.include_router(risk_levels.router, prefix="/risk-levels", tags=["风控等级管理"])
router.include_router(risk_tags.router, prefix="/risk-tags", tags=["风控标签管理"])
router.include_router(risk_assistants.router, prefix="/risk-assistants", tags=["风控助手管理"])
router.include_router(payment_risk.router, prefix="/payment", tags=["出金风控"])

# 定义路由器并导出
__all__ = ["router"]
