#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT工具类 - 统一JWT相关操作
"""

import json

from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.common.dataclasses import TokenPayload
from backend.common.exception import errors
from backend.common.security.jwt import base64_decode_token, jwt_decode
from backend.core.conf import get_settings
from backend.database.redis import redis_client
from backend.utils.serializers import select_as_dict

settings = get_settings()


class JWTUtils:
    """JWT工具类 - 统一JWT相关操作"""

    @staticmethod
    def decode_token_with_fallback(token: str) -> str:
        """解码Token，支持Base64解码和向后兼容"""
        try:
            return base64_decode_token(token)
        except errors.TokenError:
            return token

    @staticmethod
    def is_user_active(user: Optional[User]) -> bool:
        """检查用户是否处于活跃状态"""
        return user is not None and user.status == 1

    @staticmethod
    def validate_user_status(user: Optional[User]) -> None:
        """验证用户状态，如果无效则抛出异常"""
        if not JWTUtils.is_user_active(user):
            AuthErrorHandler.raise_auth_error("用户已被禁用")

    @staticmethod
    async def verify_token_in_redis(token_payload: TokenPayload, decoded_token: str, redis_prefix: str = None) -> None:
        """验证token是否存在于Redis中"""
        import logging

        if redis_prefix is None:
            redis_prefix = settings.TOKEN_REDIS_PREFIX

        try:
            redis_key = f"{redis_prefix}:{token_payload.id}:{token_payload.session_uuid}"
            logging.debug(f"验证Redis token: key={redis_key}")

            redis_token = await redis_client.get(redis_key)

            if not redis_token:
                logging.warning(f"Token已过期: user_id={token_payload.id}, session_uuid={token_payload.session_uuid}")
                raise errors.TokenError(msg="Token 已过期")

            if decoded_token != redis_token:
                logging.warning(f"Token已失效: user_id={token_payload.id}, session_uuid={token_payload.session_uuid}")
                raise errors.TokenError(msg="Token 已失效")

            logging.debug(f"Token验证成功: user_id={token_payload.id}")

        except errors.TokenError:
            raise
        except Exception as e:
            logging.error(f"Redis token验证失败: user_id={token_payload.id}, error={str(e)}", exc_info=True)
            raise errors.TokenError(msg=f"缓存服务暂时不可用: {str(e)}")

    @staticmethod
    async def get_user_from_db(db: AsyncSession, user_id: int) -> Optional[User]:
        """从数据库获取用户"""
        import logging

        from backend.app.admin.crud.crud_user import user_dao

        try:
            logging.debug(f"查询数据库用户: ID={user_id}")
            user = await user_dao.get(db, user_id=user_id)
            if user:
                logging.debug(f"数据库用户查询成功: {user.username} (ID: {user_id})")
            else:
                logging.warning(f"数据库用户不存在: ID={user_id}")
            return user
        except Exception as e:
            logging.error(f"数据库用户查询失败: ID={user_id}, error={str(e)}", exc_info=True)
            raise errors.TokenError(msg=f"数据库服务暂时不可用: {str(e)}")

    @staticmethod
    async def get_user_with_cache(
        db: AsyncSession, user_id: int, cache_prefix: str = None, expire: int = None
    ) -> Optional[User]:
        """带缓存的用户获取 - 始终返回 SQLAlchemy User 对象"""
        import logging

        if cache_prefix is None:
            cache_prefix = settings.JWT_USER_REDIS_PREFIX
        if expire is None:
            # 使用专用的用户缓存TTL，默认7天，避免因1天TTL导致频繁落库
            expire = settings.JWT_USER_REDIS_EXPIRE_SECONDS

        try:
            cached_user = await redis_client.get(f"{cache_prefix}:{user_id}")
            if cached_user:
                try:
                    user_data = json.loads(cached_user)
                    logging.debug(f"从缓存获取用户: ID={user_id}")
                    # 从缓存数据重新构建 SQLAlchemy User 对象
                    return await JWTUtils._reconstruct_user_from_cache_data(user_data, db)
                except Exception as e:
                    logging.warning(f"缓存数据反序列化失败: ID={user_id}, error={str(e)}")
                    pass

            logging.debug(f"从数据库获取用户: ID={user_id}")
            user = await JWTUtils.get_user_from_db(db, user_id)
            if not user:
                logging.warning(f"用户不存在: ID={user_id}")
                return None

            try:
                # 缓存用户数据（作为字典）
                user_dict = select_as_dict(user)
                await redis_client.setex(f"{cache_prefix}:{user_id}", expire, json.dumps(user_dict, default=str))
                logging.debug(f"用户数据已缓存: ID={user_id}")
                return user
            except Exception as e:
                logging.warning(f"用户数据缓存失败: ID={user_id}, error={str(e)}")
                return user

        except Exception as e:
            logging.error(f"获取用户失败: ID={user_id}, error={str(e)}", exc_info=True)
            raise errors.TokenError(msg=f"用户服务暂时不可用: {str(e)}")

    @staticmethod
    async def _reconstruct_user_from_cache_data(user_data: dict, db: AsyncSession) -> User:
        """从缓存数据重新构建 SQLAlchemy User 对象 - 通过重新查询数据库确保正确的 instrumentation"""
        # 从缓存数据中获取用户ID，然后重新从数据库查询
        user_id = user_data.get("id")
        if not user_id:
            raise errors.TokenError(msg="缓存数据缺少用户ID")

        # 重新从数据库获取用户，确保有正确的 instrumentation
        return await JWTUtils.get_user_from_db(db, user_id)

    @staticmethod
    async def authenticate_user(token: str, db: AsyncSession, redis_prefix: str = None) -> User:
        """统一的用户认证流程 - 支持普通JWT和CRM Token"""
        import logging

        try:
            decoded_token = JWTUtils.decode_token_with_fallback(token)

            try:
                crm_payload = JWTUtils.decode_crm_token(decoded_token)
                if JWTUtils.is_crm_token(crm_payload):
                    logging.info("检测到CRM token，使用CRM认证流程")
                    return await JWTUtils.authenticate_crm_user(token, db)
            except errors.TokenError as e:
                logging.debug(f"非CRM token，继续普通JWT流程: {str(e)}")
                pass

            logging.info("使用普通JWT认证流程")
            token_payload = jwt_decode(decoded_token)
            await JWTUtils.verify_token_in_redis(token_payload, decoded_token, redis_prefix)

            user = await JWTUtils.get_user_with_cache(db, token_payload.id)
            if not user:
                logging.warning(f"用户不存在: ID={token_payload.id}")
                AuthErrorHandler.raise_auth_error("用户不存在")

            JWTUtils.validate_user_status(user)
            logging.info(f"用户认证成功: {user.username} (ID: {user.id})")
            return user

        except errors.TokenError as e:
            logging.warning(f"Token认证失败: {str(e)}")
            AuthErrorHandler.raise_auth_error(str(e))
        except errors.ConflictError as e:
            logging.error(f"数据冲突: {str(e)}")
            AuthErrorHandler.raise_auth_error(f"数据冲突: {str(e)}")
        except errors.NotFoundError as e:
            logging.warning(f"资源不存在: {str(e)}")
            AuthErrorHandler.raise_auth_error(f"资源不存在: {str(e)}")
        except Exception as e:
            logging.error(f"认证流程异常: {str(e)}", exc_info=True)
            AuthErrorHandler.raise_auth_error(f"认证失败: {str(e)}")

    @staticmethod
    def decode_crm_token(token: str) -> dict:
        """解码CRM token，返回原始payload（跳过签名验证）"""
        from jose import jwt

        try:
            payload = jwt.decode(
                token, key="", options={"verify_signature": False, "verify_exp": False, "verify_aud": False}
            )
            return payload
        except Exception as e:
            raise errors.TokenError(msg=f"CRM token解码失败: {str(e)}")

    @staticmethod
    def is_crm_token(payload: dict) -> bool:
        """判断是否为CRM系统token"""
        return payload.get("aud") == "AI"

    @staticmethod
    async def get_crm_user_info(member_id: str, email: str) -> dict:
        """调用CRM系统接口获取用户信息"""
        import logging

        import httpx

        from backend.core.conf import settings

        url = f"{settings.CRM_API_BASE_URL}/api/ai_ext/getUserInfo"
        headers = {"Token": settings.CRM_API_TOKEN, "Content-Type": "application/json"}
        data = {"member_id": member_id, "email": email}

        logging.info(f"调用CRM API获取用户信息: member_id={member_id}, email={email}")
        logging.debug(f"CRM API URL: {url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=settings.CRM_API_TIMEOUT)
                response.raise_for_status()

                result = response.json()
                logging.debug(f"CRM API响应: {result}")

                if result.get("code") == 200:
                    user_data = result.get("data", {})
                    logging.info(f"CRM API调用成功: 获取到用户数据 - {user_data.get('username', 'N/A')}")
                    return user_data
                else:
                    error_msg = result.get("message", "Unknown error")
                    logging.error(f"CRM API返回错误: code={result.get('code')}, message={error_msg}")
                    raise errors.TokenError(msg=f"CRM接口返回错误: {error_msg}")

        except httpx.TimeoutException:
            logging.error(f"CRM API调用超时: timeout={settings.CRM_API_TIMEOUT}s")
            raise errors.TokenError(msg="CRM服务暂时不可用，请稍后重试")
        except httpx.HTTPStatusError as e:
            logging.error(f"CRM API HTTP错误: status={e.response.status_code}, text={e.response.text}")
            raise errors.TokenError(msg=f"CRM服务错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logging.error(f"CRM API请求错误: {str(e)}")
            raise errors.TokenError(msg="CRM服务连接失败")
        except Exception as e:
            logging.error(f"CRM API调用异常: {str(e)}", exc_info=True)
            raise errors.TokenError(msg=f"CRM服务调用失败: {str(e)}")

    @staticmethod
    async def authenticate_crm_user(token: str, db: AsyncSession) -> User:
        """CRM系统用户认证流程 - 优化版（跳过已存在用户的CRM接口调用）"""
        import logging

        try:
            decoded_token = JWTUtils.decode_token_with_fallback(token)
            token_payload = JWTUtils.decode_crm_token(decoded_token)

            if not JWTUtils.is_crm_token(token_payload):
                logging.warning("非CRM系统token")
                raise errors.TokenError(msg="非CRM系统token")

            jti = token_payload.get("jti")
            email = token_payload.get("email")

            if not jti:
                logging.warning("CRM token缺少jti字段")
                raise errors.TokenError(msg="CRM token缺少jti字段")

            logging.info(f"开始CRM用户认证: jti={jti}, email={email}")
            user = await JWTUtils.get_user_by_crm_id(db, jti)

            if user:
                logging.info(f"CRM用户已存在，直接返回: {user.username} (CRM ID: {jti})")
                return user
            else:
                logging.info(f"CRM用户不存在，调用接口创建新用户: {jti}")
                crm_user_info = await JWTUtils.get_crm_user_info(jti, email)
                logging.debug(f"CRM接口返回用户信息: {crm_user_info}")

                user = await JWTUtils.create_crm_user_from_api(db, jti, crm_user_info)
                return user

        except errors.TokenError as e:
            logging.warning(f"CRM认证失败 - Token错误: {str(e)}")
            AuthErrorHandler.raise_auth_error(str(e))
        except errors.ConflictError as e:
            logging.error(f"CRM认证失败 - 数据冲突: {str(e)}")
            AuthErrorHandler.raise_auth_error(f"数据冲突: {str(e)}")
        except errors.NotFoundError as e:
            logging.warning(f"CRM认证失败 - 资源不存在: {str(e)}")
            AuthErrorHandler.raise_auth_error(f"资源不存在: {str(e)}")
        except Exception as e:
            logging.error(f"CRM认证失败 - 未知错误: {str(e)}", exc_info=True)
            AuthErrorHandler.raise_auth_error(f"CRM认证失败: {str(e)}")

    @staticmethod
    async def get_user_by_crm_id(db: AsyncSession, crm_user_id: str) -> Optional[User]:
        """通过CRM用户ID获取用户"""
        from backend.app.admin.crud.crud_user import user_dao

        return await user_dao.get_by_crm_user_id(db, crm_user_id)

    @staticmethod
    async def create_crm_user_from_api(db: AsyncSession, crm_user_id: str, crm_user_info: dict) -> User:
        """根据CRM接口返回的信息创建用户"""
        import logging
        import secrets
        import string

        import bcrypt

        from backend.app.admin.crud.crud_role import role_dao
        from backend.app.admin.crud.crud_user import user_dao
        from backend.common.security.jwt import get_hash_password

        try:
            logging.info(f"开始创建CRM用户: crm_user_id={crm_user_id}")

            email = crm_user_info.get("email", "")
            if email and await user_dao.get_by_email(db, email):
                logging.error(f"邮箱已被使用: {email}")
                raise errors.ConflictError(msg="邮箱已被使用")

            base_username = crm_user_info.get("username", crm_user_info.get("nickname", f"crm_{crm_user_id}"))
            username = base_username
            counter = 1
            while await user_dao.get_by_username(db, username):
                username = f"{base_username}_{counter}"
                counter += 1

            def generate_random_password(length=12):
                characters = string.ascii_letters + string.digits + "!@#$%^&*"
                return "".join(secrets.choice(characters) for _ in range(length))

            password = generate_random_password()
            salt = bcrypt.gensalt()
            hashed_password = get_hash_password(password, salt)

            role = await role_dao.get(db, 3)
            if not role:
                logging.error("客户端用户角色不存在: role_id=3")
                raise errors.NotFoundError(msg="客户端用户角色不存在")

            # 数据清理和验证
            phone = crm_user_info.get("phone", "")
            avatar = crm_user_info.get("avatar", "")

            # 验证头像URL，如果为空或无效则设为None
            if avatar and avatar.strip():
                # 简单验证URL格式
                if not (avatar.startswith("http://") or avatar.startswith("https://")):
                    logging.warning(f"头像URL格式不正确，设为None: {avatar}")
                    avatar = None
            else:
                avatar = None

            user_data = {
                "username": username,
                "nickname": crm_user_info.get("nickname", username),
                "password": hashed_password,
                "salt": salt,
                "email": email,
                "phone": phone,
                "avatar": avatar,
                "crm_user_id": crm_user_id,
                "dept_id": None,
                "status": 1,
                "is_superuser": False,
                "is_staff": False,
                "is_multi_login": True,
            }

            new_user = User(**user_data)
            new_user.roles = [role]

            db.add(new_user)
            await db.flush()
            await db.refresh(new_user)
            await db.commit()  # 提交事务，确保数据持久化

            logging.info(f"创建CRM用户成功: {username} (ID: {new_user.id}, CRM ID: {crm_user_id})")

            return new_user

        except errors.ConflictError:
            raise
        except errors.NotFoundError:
            raise
        except Exception as e:
            logging.error(f"创建CRM用户失败: crm_user_id={crm_user_id}, error={str(e)}", exc_info=True)
            raise errors.TokenError(msg=f"用户创建失败: {str(e)}")

    @staticmethod
    def get_token_from_request(request: Request) -> Optional[str]:
        """从请求中获取token"""
        from backend.common.security.jwt import get_token

        try:
            return get_token(request)
        except Exception:
            return None


class AuthErrorHandler:
    """认证错误处理类"""

    @staticmethod
    def raise_auth_error(detail: str) -> None:
        """抛出统一的认证错误"""
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
        )

    @staticmethod
    def raise_token_error(msg: str) -> None:
        """抛出token错误"""
        AuthErrorHandler.raise_auth_error(f"Token错误: {msg}")
