# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.app.admin.schema.user import UpdateUserParam
from backend.app.home.api.deps import get_current_home_user
from backend.common.response.response_schema import ResponseModel, response_base
from backend.core.conf import get_settings
from backend.database.db import get_db

settings = get_settings()

router = APIRouter()


@router.get("/me", response_model=dict, summary="获取当前登录用户信息")
async def get_my_info(current_user: User = Depends(get_current_home_user)) -> Any:
    """
    获取当前登录用户信息
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "nickname": current_user.nickname,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "status": current_user.status,
        "is_superuser": current_user.is_superuser,
        "is_staff": current_user.is_staff,
        "is_multi_login": current_user.is_multi_login,
        "join_time": current_user.join_time.isoformat() if current_user.join_time else None,
        "last_login_time": current_user.last_login_time.isoformat() if current_user.last_login_time else None,
    }


@router.put("/me", response_model=dict, summary="更新当前登录用户信息")
async def update_my_info(
    user_in: UpdateUserParam,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user),
) -> Any:
    """
    更新当前登录用户信息
    """
    from backend.app.admin.crud.crud_user import user_dao

    # 更新用户信息
    await user_dao.update(db, input_user=current_user, obj=user_in)

    # 获取更新后的用户信息
    updated_user = await user_dao.get(db, user_id=current_user.id)

    return {
        "id": updated_user.id,
        "username": updated_user.username,
        "email": updated_user.email,
        "nickname": updated_user.nickname,
        "phone": updated_user.phone,
        "avatar": updated_user.avatar,
        "status": updated_user.status,
        "is_superuser": updated_user.is_superuser,
        "is_staff": updated_user.is_staff,
        "is_multi_login": updated_user.is_multi_login,
        "join_time": updated_user.join_time.isoformat() if updated_user.join_time else None,
        "last_login_time": updated_user.last_login_time.isoformat() if updated_user.last_login_time else None,
    }


@router.get("/check-username/{username}", response_model=ResponseModel, summary="检查用户名是否可用")
async def check_username(username: str, db: AsyncSession = Depends(get_db)) -> ResponseModel:
    """
    检查用户名是否可用
    """
    from backend.app.admin.crud.crud_user import user_dao

    existing_user = await user_dao.get_by_username(db, username=username)
    if existing_user:
        return response_base.fail(data={"message": "用户名已被使用"})
    return response_base.success(data={"message": "用户名可用"})
