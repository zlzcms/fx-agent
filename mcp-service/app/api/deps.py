#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from core.config import settings

# API密钥认证 - 支持两种方式: Authorization头和X-API-Key头
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
x_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    request: Request,
    api_key_header: Optional[str] = Security(api_key_header),
    x_api_key: Optional[str] = Security(x_api_key_header),
) -> str:
    """验证API密钥

    参数:
        request: 请求对象
        api_key_header: 请求头中的Authorization字段
        x_api_key: 请求头中的X-API-Key字段

    返回:
        验证通过的API密钥

    异常:
        HTTPException: 认证失败时抛出
    """
    api_key = None

    # 检查URL查询参数中是否有API密钥
    api_key_query = request.query_params.get("api_key")

    # 优先使用X-API-Key头
    if x_api_key:
        api_key = x_api_key
    # 其次使用Authorization头
    elif api_key_header:
        # 检查格式是否为 "Bearer {token}"
        if api_key_header.startswith("Bearer "):
            api_key = api_key_header.replace("Bearer ", "")
        else:
            api_key = api_key_header  # 也接受直接提供的密钥
    # 最后检查URL查询参数
    elif api_key_query:
        api_key = api_key_query

    # 如果所有方式都没有提供API密钥
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API密钥缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 启用调试模式时允许使用"test-api-key"
    if settings.DEBUG and api_key == "test-api-key":
        return api_key

    # 验证API密钥
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key
