# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from backend.app.home.api.v1.auth.login import router as login_router
from backend.app.home.api.v1.auth.user import router as user_router

router = APIRouter(prefix="/auth")
router.include_router(login_router)
router.include_router(user_router)
