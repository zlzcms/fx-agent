#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from backend.app.admin.model import User
from backend.common.exception.errors import AuthorizationError, TokenError
from backend.common.log import log
from backend.common.security.api_key_auth import authenticate_api_key
from backend.common.security.jwt import jwt_authentication
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.utils.serializers import MsgSpecJSONResponse


class _AuthenticationError(AuthenticationError):
    """重写内部认证错误类"""

    def __init__(
        self, *, code: int | None = None, msg: str | None = None, headers: dict[str, Any] | None = None
    ) -> None:
        """
        初始化认证错误

        :param code: 错误码
        :param msg: 错误信息
        :param headers: 响应头
        :return:
        """
        self.code = code
        self.msg = msg
        self.headers = headers


class JwtAuthMiddleware(AuthenticationBackend):
    """JWT 认证中间件"""

    @staticmethod
    def auth_exception_handler(conn: HTTPConnection, exc: _AuthenticationError) -> Response:
        """
        覆盖内部认证错误处理

        :param conn: HTTP 连接对象
        :param exc: 认证错误对象
        :return:
        """
        return MsgSpecJSONResponse(content={"code": exc.code, "msg": exc.msg, "data": None}, status_code=exc.code)

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, User] | None:
        """
        认证请求

        :param request: FastAPI 请求对象
        :return:
        """
        # 如果禁用认证功能，返回一个默认的系统用户
        if settings.DISABLE_AUTH:
            # 创建一个默认的系统用户对象
            # 注意：User 模型中 id, uuid, join_time, last_login_time 字段设置了 init=False，不能在构造函数中传入
            default_user = User(
                username="system",
                nickname="系统用户",
                password=None,  # 系统用户不需要密码
                salt=None,  # 系统用户不需要盐
                email=None,
                phone=None,
                avatar=None,
                status=1,
                is_superuser=True,
                is_staff=True,
                is_multi_login=False,
                dept_id=None,
                crm_user_id="system",
            )
            # 手动设置 init=False 的字段
            default_user.id = 1
            default_user.uuid = "system"
            default_user.join_time = datetime.now()
            default_user.last_login_time = None
            return AuthCredentials(["authenticated"]), default_user

        token = request.headers.get("Authorization")
        if not token:
            return None

        path = request.url.path
        if path in settings.TOKEN_REQUEST_PATH_EXCLUDE:
            return None
        for pattern in settings.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN:
            if pattern.match(path):
                return None

        scheme, token = get_authorization_scheme_param(token)
        if scheme.lower() != "bearer":
            return None

        try:
            # 检查是否是API Key格式（以ak_开头）
            if token.startswith("ak_"):
                # API Key认证
                async with async_db_session() as db:
                    user, _ = await authenticate_api_key(token, request, db)
            else:
                # JWT认证
                user = await jwt_authentication(token)
        except (TokenError, AuthorizationError) as exc:
            raise _AuthenticationError(code=exc.code, msg=exc.detail, headers=exc.headers)
        except HTTPException as exc:
            # 正确映射 FastAPI 的 HTTPException 到认证错误，避免误返回 500
            raise _AuthenticationError(code=exc.status_code, msg=exc.detail, headers=exc.headers)
        except Exception as e:
            log.exception(f"认证异常：{e}")
            # 兜底异常分支，尽量从异常中提取标准字段
            raise _AuthenticationError(
                code=getattr(e, "status_code", getattr(e, "code", 500)),
                msg=getattr(e, "detail", getattr(e, "msg", "Internal Server Error")),
            )

        # 请注意，此返回使用非标准模式，所以在认证通过时，将丢失某些标准特性
        # 标准返回模式请查看：https://www.starlette.io/authentication/
        return AuthCredentials(["authenticated"]), user
