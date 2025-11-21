# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.home.api.v1.ai import router as ai_router
from backend.app.home.api.v1.auth import router as auth_router
from backend.app.home.api.v1.chat import router as chat_router
from backend.app.home.api.v1.static import router as static_router

router = APIRouter()


# 添加home根路由
@router.get("/")
async def home_root():
    return JSONResponse(content={"message": "Home API is running!", "status": "healthy"})


# 直接包含子路由，因为子路由已经设置了前缀
router.include_router(auth_router, tags=["auth"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(ai_router, prefix="/ai", tags=["ai"])
router.include_router(static_router, prefix="/static", tags=["静态文件"])
