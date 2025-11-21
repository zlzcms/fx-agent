# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:31:27
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from backend.app.admin.api.health import router as health_router
from backend.app.admin.api.v1.ai import router as ai_router
from backend.app.admin.api.v1.auth import router as auth_router
from backend.app.admin.api.v1.dashboard import router as dashboard_router
from backend.app.admin.api.v1.log import router as log_router
from backend.app.admin.api.v1.monitor import router as monitor_router
from backend.app.admin.api.v1.risk import router as risk_router
from backend.app.admin.api.v1.static import router as static_router
from backend.app.admin.api.v1.sys import router as sys_router
from backend.app.admin.api.v1.user import warehouse_user_router
from backend.core.conf import settings

v1 = APIRouter(prefix=settings.FASTAPI_API_V1_PATH)

v1.include_router(health_router)
v1.include_router(auth_router)
v1.include_router(sys_router)
v1.include_router(log_router)
v1.include_router(monitor_router)
v1.include_router(dashboard_router, prefix="/dashboard")
v1.include_router(ai_router, prefix="/ai")
v1.include_router(risk_router, prefix="/risk")
v1.include_router(warehouse_user_router, prefix="/warehouse")
v1.include_router(static_router, prefix="/static")
