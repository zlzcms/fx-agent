# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from backend.app.home.api.v1.static.static import router as static_router

router = APIRouter()
router.include_router(static_router)
