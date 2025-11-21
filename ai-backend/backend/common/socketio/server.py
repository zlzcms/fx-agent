#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

import socketio

from backend.common.log import log
from backend.common.security.jwt import jwt_authentication
from backend.core.conf import settings
from backend.database.redis import redis_client


def validate_origin_with_patterns(origin: str, patterns: list) -> bool:
    """
    使用正则表达式模式验证来源域名

    Args:
        origin: 请求的来源域名
        patterns: 正则表达式模式列表

    Returns:
        bool: 是否匹配任一模式
    """
    if not origin or not patterns:
        return False

    for pattern in patterns:
        try:
            if re.match(pattern, origin):
                return True
        except re.error as e:
            log.warning(f"Invalid regex pattern '{pattern}': {e}")
            continue

    return False


def validate_origin_with_exact_match(origin: str, allowed_origins: list) -> bool:
    """
    使用精确匹配验证来源域名

    Args:
        origin: 请求的来源域名
        allowed_origins: 允许的精确域名列表

    Returns:
        bool: 是否在允许的域名列表中
    """
    if not origin or not allowed_origins:
        return False

    return origin in allowed_origins


def validate_origin(origin: str) -> bool:
    """
    综合验证来源域名，同时支持精确匹配和正则表达式模式匹配

    Args:
        origin: 请求的来源域名

    Returns:
        bool: 是否通过验证
    """
    if not origin:
        return False

    # 1. 首先尝试精确匹配
    if validate_origin_with_exact_match(origin, settings.CORS_ALLOWED_ORIGINS):
        log.info(f"CORS 精确匹配验证通过：来源 '{origin}'")
        return True

    # 2. 然后尝试正则表达式模式匹配
    if validate_origin_with_patterns(origin, settings.CORS_ALLOWED_ORIGIN_PATTERNS):
        log.info(f"CORS 正则模式匹配验证通过：来源 '{origin}'")
        return True

    return False


# 创建 Socket.IO 服务器实例
# 使用 cors_allowed_origins="*" 并在 connect 事件中进行自定义 CORS 验证
sio = socketio.AsyncServer(
    logger=False,
    engineio_logger=False,
    always_connect=True,
    async_mode="asgi",
    cors_allowed_origins="*",  # 允许所有来源，在 connect 事件中进行自定义验证
    cors_credentials=True,
    ping_timeout=60,  # 客户端ping超时时间（秒）
    ping_interval=25,  # 服务器ping间隔（秒）
    max_http_buffer_size=1000000,  # 最大HTTP缓冲区大小
)


@sio.event
async def connect(sid, environ, auth):
    """Socket 连接事件 - 包含自定义 CORS 验证"""
    # 1. 首先进行 CORS 验证
    origin = environ.get("HTTP_ORIGIN")
    if origin:
        # 使用综合验证函数，同时支持精确匹配和正则表达式模式匹配
        if not validate_origin(origin):
            log.warning(f"WebSocket 连接被拒绝：来源 '{origin}' 不在允许的 CORS 列表中")
            return False
    else:
        log.warning("WebSocket 连接缺少 Origin 头")

    # 2. 进行原有的授权验证
    if not auth:
        log.error("WebSocket 连接失败：无授权")
        return False

    session_uuid = auth.get("session_uuid")
    token = auth.get("token")
    if not token or not session_uuid:
        log.error("WebSocket 连接失败：授权失败，请检查")
        return False

    # 免授权直连
    if token == settings.WS_NO_AUTH_MARKER:
        await redis_client.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
        log.info(f"WebSocket 免授权连接成功：{sid}")
        return True

    try:
        await jwt_authentication(token)
    except Exception as e:
        log.info(f"WebSocket 连接失败：{str(e)}")
        return False

    await redis_client.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
    log.info(f"WebSocket 连接成功：{sid}")
    return True


@sio.event
async def disconnect(sid) -> None:
    """Socket 断开连接事件"""
    try:
        await redis_client.spop(settings.TOKEN_ONLINE_REDIS_PREFIX)
        log.info(f"WebSocket 断开连接：{sid}")
    except Exception as e:
        log.error(f"WebSocket 断开连接处理失败 {sid}: {str(e)}")
