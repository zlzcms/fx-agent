# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:31:27
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from backend.app.home.api.v1 import router as v1_router
from backend.core.conf import settings

v1 = APIRouter(prefix=settings.FASTAPI_API_V1_PATH)
v1.include_router(v1_router, prefix="/home")
