#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User

# 使用后端通用的JWT认证模块和User模型
from backend.database.db import get_db


async def get_current_home_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    获取当前Home用户（用于依赖注入）

    参数:
        request: FastAPI请求对象
        db: 数据库会话

    返回:
        当前用户对象

    异常:
        HTTPException: 认证失败时抛出
    """
    from backend.common.security.jwt_utils import AuthErrorHandler, JWTUtils

    try:
        # 获取令牌
        token = JWTUtils.get_token_from_request(request)
        if not token:
            AuthErrorHandler.raise_auth_error("未提供认证令牌")

        # 使用统一的认证流程
        return await JWTUtils.authenticate_user(token, db)

    except HTTPException:
        raise
    except Exception as e:
        AuthErrorHandler.raise_auth_error(f"认证失败: {str(e)}")


async def get_optional_home_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """
    获取当前Home用户，但不强制认证（用于依赖注入）

    参数:
        request: FastAPI请求对象
        db: 数据库会话

    返回:
        当前用户对象，如果未认证则返回None
    """
    from backend.common.security.jwt_utils import JWTUtils

    try:
        # 获取令牌，但不抛出异常
        token = JWTUtils.get_token_from_request(request)
        if not token:
            return None

        # 使用统一的认证流程
        return await JWTUtils.authenticate_user(token, db)

    except Exception:
        return None
