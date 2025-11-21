#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.admin.api.router import v1 as admin_v1
from backend.app.home.api.router import v1 as home_v1
from backend.app.task.api.router import v1 as task_v1

router = APIRouter()


# 添加API根路由
@router.get("/")
async def api_root():
    return JSONResponse(content={"message": "FastAPI Backend is running!", "status": "healthy"})


router.include_router(admin_v1)
router.include_router(home_v1)
router.include_router(task_v1)
