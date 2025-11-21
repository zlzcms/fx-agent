# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks

from backend.app.admin.model import User
from backend.app.home.api.deps import get_current_home_user
from backend.app.home.service.auth_service import auth_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.core.conf import get_settings
from backend.database.db import get_db

settings = get_settings()

router = APIRouter()


@router.post(
    "/login",
    name="home_login",
    summary="用户登录",
    description="支持JSON格式登录，用户名密码认证",
    dependencies=[Depends(RateLimiter(times=5, minutes=1))],
)
async def home_login(
    request: Request, response: Response, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    用户登录API

    支持JSON格式，需要提供用户名和密码
    """
    try:
        # 检查Content-Type
        content_type = request.headers.get("content-type", "")
        if not content_type or "application/json" not in content_type:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="请求必须使用application/json格式"
            )

        # 获取JSON数据
        try:
            login_data = await request.json()
        except Exception as json_error:
            # 处理JSON解析错误
            if "Expecting value" in str(json_error):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求体为空或不是有效的JSON格式")
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"JSON解析失败: {str(json_error)}")

        # 验证请求数据结构
        if not isinstance(login_data, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求体必须是JSON对象")

        # 提取登录参数
        username = login_data.get("username")
        password = login_data.get("password")

        # 验证必须参数
        if not username or not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码为必填项")

        # 认证用户
        user = await auth_service.authenticate_user(db, username=username, password=password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 记录登录时间等信息
        await auth_service.update_login_info(db, user=user, request=request)

        # 创建令牌
        tokens = await auth_service.create_tokens(user.id)

        # 设置刷新令牌到Cookie
        response.set_cookie(
            key="home_refresh_token",
            value=tokens["refresh_token"],
            max_age=settings.TOKEN_REFRESH_EXPIRE_SECONDS,
            httponly=True,
        )

        return response_base.success(
            data={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "access_token_expire_time": tokens["access_token_expire_time"],
                "refresh_token_expire_time": tokens["refresh_token_expire_time"],
                "session_uuid": tokens["session_uuid"],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nickname": user.nickname,
                    "phone": user.phone,
                    "avatar": user.avatar,
                    "status": user.status,
                    "is_superuser": user.is_superuser,
                    "is_staff": user.is_staff,
                    "is_multi_login": user.is_multi_login,
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # 记录详细错误信息用于调试
        import logging

        logging.error(f"登录异常: {str(e)}", exc_info=True)

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"登录失败: {str(e)}")


@router.post("/refresh-token", summary="刷新访问令牌", description="使用请求体中的刷新令牌获取新的访问令牌")
async def refresh_access_token(request: Request) -> Any:
    """
    刷新访问令牌API

    支持从请求体或Cookie中获取刷新令牌
    """
    # 优先从请求体中获取刷新令牌
    refresh_token = None
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
    except Exception:
        pass

    # 如果请求体中没有，尝试从Cookie中获取
    if not refresh_token:
        refresh_token = request.cookies.get("home_refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 验证刷新令牌
        new_token = await auth_service.refresh_access_token(refresh_token)
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return response_base.success(data=new_token)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"刷新令牌失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", name="home_logout", summary="用户登出")
async def home_logout(
    request: Request, response: Response, current_user: User = Depends(get_current_home_user)
) -> ResponseSchemaModel:
    """
    用户登出API

    使当前令牌失效并清除Cookie
    """
    await auth_service.logout(request=request, user_id=current_user.id)

    # 清除Cookie（设置过期时间确保删除）
    response.delete_cookie("home_refresh_token", path="/", httponly=True, samesite="lax")

    return response_base.success(data={"message": "登出成功"})
