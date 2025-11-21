#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

from passlib.context import CryptContext
from pydantic import ValidationError

from backend.core.conf import get_settings

settings = get_settings()

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT算法
ALGORITHM = settings.TOKEN_ALGORITHM


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    参数:
        subject: 令牌主体，通常是用户ID
        expires_delta: 过期时间增量，如果为None则使用默认值

    返回:
        JWT访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.TOKEN_EXPIRE_SECONDS)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建刷新令牌

    参数:
        subject: 令牌主体，通常是用户ID
        expires_delta: 过期时间增量，如果为None则使用默认值

    返回:
        JWT刷新令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.TOKEN_REFRESH_EXPIRE_SECONDS)

    to_encode = {"exp": expire, "sub": str(subject), "refresh": True}
    encoded_jwt = jwt.encode(to_encode, settings.TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证令牌

    参数:
        token: JWT令牌

    返回:
        解码后的令牌数据，如果无效则返回None
    """
    try:
        payload = jwt.decode(token, settings.TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, ValidationError):
        return None


def get_password_hash(password: str) -> str:
    """
    获取密码哈希

    参数:
        password: 原始密码

    返回:
        密码哈希
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    参数:
        plain_password: 原始密码
        hashed_password: 哈希密码

    返回:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)
