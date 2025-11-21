#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import User

# 使用后端通用的JWT实现和User模型
from backend.common.exception import errors
from backend.common.security.jwt import (
    create_access_token,
    create_new_token,
    create_refresh_token,
    get_token,
    jwt_decode,
)
from backend.core.conf import get_settings

settings = get_settings()

# OAuth2密码流认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.FASTAPI_API_V1_PATH}/home/auth/login")


class AuthService:
    """客户端认证服务"""

    def __init__(self):
        self.oauth2_scheme = oauth2_scheme

    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        认证用户

        参数:
            db: 数据库会话
            username: 用户名
            password: 密码

        返回:
            认证通过的用户，如果认证失败则返回None
        """
        user = await user_dao.get_by_username(db, username=username)
        if not user:
            return None

        # 检查用户状态
        if user.status != 1:  # 1表示正常状态
            return None

        # 检查密码
        if not user.password:
            return None

        # 使用后端统一的密码验证
        from backend.common.security.jwt import password_verify

        if not password_verify(password, user.password):
            return None

        return user

    async def create_tokens(self, user_id: int) -> Dict[str, Any]:
        """
        创建访问令牌和刷新令牌

        参数:
            user_id: 用户ID

        返回:
            包含令牌和过期时间的字典
        """
        print(f"为用户 {user_id} 创建令牌")

        # 获取用户信息用于令牌创建
        from backend.database.db import async_db_session

        async with async_db_session() as db:
            user = await user_dao.get(db, user_id=user_id)
            username = user.username if user else str(user_id)
            nickname = user.nickname if user else username

        # 使用后端通用的JWT实现创建访问令牌
        access_token_data = await create_access_token(
            user_id,
            multi_login=True,
            # 添加额外信息
            username=username,
            nickname=nickname,
            type="home_user",
        )
        print(f"创建的访问令牌: {access_token_data.access_token[:20]}...")

        # 创建刷新令牌
        refresh_token_data = await create_refresh_token(access_token_data.session_uuid, user_id, multi_login=True)
        print(f"创建的刷新令牌: {refresh_token_data.refresh_token[:20]}...")

        # 组合令牌数据
        return {
            "access_token": access_token_data.access_token,
            "refresh_token": refresh_token_data.refresh_token,
            "token_type": "bearer",
            "access_token_expire_time": access_token_data.access_token_expire_time,
            "refresh_token_expire_time": refresh_token_data.refresh_token_expire_time,
            "session_uuid": access_token_data.session_uuid,
        }

    async def get_current_user(self, db: AsyncSession, token: str) -> Optional[User]:
        """
        获取当前用户

        参数:
            db: 数据库会话
            token: 访问令牌

        返回:
            当前用户，如果令牌无效则返回None
        """
        from backend.common.security.jwt_utils import JWTUtils

        try:
            # 使用统一的认证流程
            return await JWTUtils.authenticate_user(token, db)
        except Exception:
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        刷新访问令牌

        参数:
            refresh_token: 刷新令牌

        返回:
            新的令牌信息，如果刷新失败则返回None
        """
        try:
            # Refresh Token是JWT格式，直接解码（不需要Base64解码）
            # 从刷新令牌中解析用户ID和session_uuid
            token_payload = jwt_decode(refresh_token)
            user_id = token_payload.id

            # 获取用户信息
            from backend.database.db import async_db_session

            async with async_db_session() as db:
                user = await user_dao.get(db, user_id=user_id)
                if not user:
                    raise errors.TokenError(msg="用户不存在")
                if user.status != 1:
                    raise errors.TokenError(msg="用户已被禁用")
                username = user.username
                nickname = user.nickname or username

            # 使用后端通用的JWT实现刷新令牌
            # 注意：create_new_token期望接收原始的refresh_token字符串（用于Redis验证）
            new_token_data = await create_new_token(
                refresh_token,  # 使用原始token，不是解码后的
                token_payload.session_uuid,
                user_id,
                True,
                # 添加额外信息
                username=username,
                nickname=nickname,
                type="home_user",
            )

            if not new_token_data:
                return None

            return {
                "access_token": new_token_data.new_access_token,
                "access_token_expire_time": new_token_data.new_access_token_expire_time,
                "refresh_token": new_token_data.new_refresh_token,
                "refresh_token_expire_time": new_token_data.new_refresh_token_expire_time,
                "session_uuid": new_token_data.session_uuid,
            }
        except Exception:
            return None

    async def update_login_info(self, db: AsyncSession, user: User, request: Request) -> None:
        """
        更新用户登录信息

        参数:
            db: 数据库会话
            user: 用户对象
            request: 请求对象
        """
        # 更新最后登录时间
        await user_dao.update_login_time(db, username=user.username)

    async def logout(self, request: Request, user_id: int) -> None:
        """
        用户登出

        参数:
            request: 请求对象
            user_id: 用户ID
        """
        try:
            token = get_token(request)
            if not token:
                return

            token_payload = jwt_decode(token)
            session_uuid = token_payload.session_uuid
            refresh_token = request.cookies.get("home_refresh_token")

            # 清理所有相关的Redis键，与admin模块保持一致
            from backend.core.conf import get_settings
            from backend.database.redis import redis_client

            settings = get_settings()
            await redis_client.delete(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{session_uuid}")
            await redis_client.delete(f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{user_id}:{session_uuid}")
            if refresh_token:
                # 刷新令牌的Redis键以session_uuid为后缀进行存储，按当前会话删除
                await redis_client.delete(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{session_uuid}")

        except Exception:
            pass


auth_service = AuthService()
