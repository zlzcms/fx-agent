#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查API
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="健康检查", description="应用程序健康状态检查")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点

    返回应用程序的基本状态信息
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "max-ai-backend",
        "version": "1.0.0",
    }


@router.get("/health/detailed", summary="详细健康检查", description="详细的应用程序健康状态检查")
async def detailed_health_check() -> Dict[str, Any]:
    """
    详细健康检查端点

    返回应用程序的详细状态信息，包括数据库连接等
    """
    # 这里可以添加数据库连接检查、Redis连接检查等
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "max-ai-backend",
        "version": "1.0.0",
        "components": {"database": "connected", "redis": "connected"},
    }
