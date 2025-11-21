#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Key认证模块
"""

from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_api_key import crud_api_key
from backend.app.admin.model import User
from backend.common.exception.errors import AuthorizationError


async def authenticate_api_key(api_key: str, request: Request, db: AsyncSession) -> tuple[User, Optional[int]]:
    """
    验证API Key并返回用户信息

    :param api_key: API Key值
    :param request: 请求对象
    :param db: 数据库会话
    :return: (用户对象, API Key ID)
    """
    # 从数据库获取API Key
    api_key_obj = await crud_api_key.get_by_api_key(db, api_key=api_key)
    if not api_key_obj:
        raise AuthorizationError(msg="API Key无效或已停用")

    # 检查是否过期
    if await crud_api_key.check_expired(api_key_obj=api_key_obj):
        raise AuthorizationError(msg="API Key已过期")

    # 检查IP白名单
    client_ip = getattr(request.state, "ip", None)
    if client_ip and not await crud_api_key.check_ip_allowed(api_key_obj=api_key_obj, ip=client_ip):
        raise AuthorizationError(msg=f"IP地址 {client_ip} 不在白名单中")

    # 更新使用信息
    await crud_api_key.update_usage(db, api_key_obj=api_key_obj, ip=client_ip)

    # 创建API Key系统用户对象（不关联真实用户，简化设计）
    # user_id字段仅用于记录创建者（审计目的），认证时不需要查询用户
    api_key_user = User(
        username=f"api_key_{api_key_obj.id}",
        nickname=f"API Key: {api_key_obj.key_name}",
        password=None,
        salt=None,
        status=1,
        is_staff=True,
        crm_user_id=f"api_key_{api_key_obj.id}",
    )
    api_key_user.id = 0  # 使用特殊ID标识这是API Key用户
    api_key_user.uuid = f"api_key_{api_key_obj.id}"

    return api_key_user, api_key_obj.id
