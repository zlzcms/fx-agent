# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:30:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-07 20:20:25
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WarehouseUserQueryParams(BaseModel):
    """普通用户查询参数"""

    nickname: Optional[str] = None
    email: Optional[str] = None
    sex: Optional[int] = None  # 0-保密 1-男 2-女
    username: Optional[str] = None
    status: Optional[bool] = None
    keyword: Optional[str] = None


class CrmUserQueryParams(BaseModel):
    """CRM用户查询参数"""

    nickname: Optional[str] = None
    email: Optional[str] = None
    sex: Optional[int] = None  # 0-保密 1-男 2-女
    username: Optional[str] = None
    status: Optional[bool] = None
    keyword: Optional[str] = None


class AgentQueryParams(BaseModel):
    """代理商查询参数"""

    nickname: Optional[str] = None
    username: Optional[str] = None
    sex: Optional[int] = None  # 0-保密 1-男 2-女
    status: Optional[bool] = None
    email: Optional[str] = None
    keyword: Optional[str] = None


class WarehouseUserResponse(BaseModel):
    """普通用户响应模型"""

    id: int
    nickname: str
    email: Optional[str] = None
    username: Optional[str] = None
    sex: Optional[int] = None  # 0-保密 1-男 2-女
    status: Optional[bool] = None
    create_time: Optional[datetime] = None
    last_login_time: Optional[datetime] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    level: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CrmUserResponse(BaseModel):
    """CRM用户响应模型"""

    id: int
    nickname: str
    email: Optional[str] = None
    username: Optional[str] = None
    company: Optional[str] = None
    status: Optional[bool] = None
    create_time: Optional[datetime] = None
    last_login_time: Optional[datetime] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AgentResponse(BaseModel):
    """代理商响应模型"""

    id: int
    nickname: str
    username: Optional[str] = None
    email: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[bool] = None
    create_time: Optional[datetime] = None
    last_login_time: Optional[datetime] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserDetailResponse(BaseModel):
    """用户详情响应模型"""

    id: int
    nickname: str
    email: Optional[str] = None
    username: Optional[str] = None
    sex: Optional[int] = None
    status: Optional[bool] = None
    create_time: Optional[datetime] = None
    last_login_time: Optional[datetime] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    level: Optional[int] = None
    domain: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None

    # 可能的CRM用户或代理商特定字段
    is_crm_user: Optional[bool] = None
    is_agent: Optional[bool] = None
    scope: Optional[int] = None
    admin: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
