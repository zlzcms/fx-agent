#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from core.config import settings
from core.log import logger, set_custom_logfile, setup_logging
from db.warehouse import warehouse_db

# 初始化日志系统
setup_logging()
set_custom_logfile()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 管理数据库连接池的启动和关闭"""
    # 启动时初始化数据库连接池
    logger.info("正在初始化数据库连接池...")
    try:
        await warehouse_db.initialize()
        logger.info("数据库连接池初始化成功")
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}")
        raise

    yield

    # 关闭时清理数据库连接池
    logger.info("正在关闭数据库连接池...")
    try:
        await warehouse_db.close()
        logger.info("数据库连接池已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接池时出错: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="MCP服务 - 数据仓库分析与查询API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 设置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(CorrelationIdMiddleware, validator=False)

# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点，包含数据库连接状态"""
    try:
        # 检查数据库连接池状态
        if warehouse_db.pool is None or warehouse_db.pool.closed:
            return {
                "status": "unhealthy",
                "service": "mcp_service",
                "database": "disconnected",
            }

        # 执行简单查询验证连接
        await warehouse_db.execute_query("SELECT 1")
        return {
            "status": "healthy",
            "service": "mcp_service",
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "mcp_service",
            "database": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
