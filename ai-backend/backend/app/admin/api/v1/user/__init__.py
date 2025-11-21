# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:25:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-07 19:52:30
from fastapi import APIRouter

from backend.app.admin.api.v1.user.warehouse import router as warehouse_router

# 创建用户模块路由器
warehouse_user_router = APIRouter()

# 注册数据仓用户相关路由
warehouse_user_router.include_router(warehouse_router, prefix="/members", tags=["数据仓用户管理"])

# 导出用户模块路由器
__all__ = ["warehouse_user_router"]
