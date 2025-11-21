#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ApiKeyBase(BaseModel):
    """API Key基础Schema"""

    key_name: str = Field(..., description="API Key名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=1000)
    expires_at: Optional[datetime] = Field(None, description="过期时间，NULL表示永不过期")
    ip_whitelist: Optional[str] = Field(None, description="IP白名单，多个IP用逗号分隔")
    permissions: Optional[str] = Field(None, description="权限列表，JSON格式存储")


class CreateApiKeyParams(ApiKeyBase):
    """创建API Key参数"""

    pass


class UpdateApiKeyParams(BaseModel):
    """更新API Key参数"""

    key_name: Optional[str] = Field(None, description="API Key名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=1000)
    status: Optional[int] = Field(None, description="状态(0停用 1启用)", ge=0, le=1)
    expires_at: Optional[datetime] = Field(None, description="过期时间，NULL表示永不过期")
    ip_whitelist: Optional[str] = Field(None, description="IP白名单，多个IP用逗号分隔")
    permissions: Optional[str] = Field(None, description="权限列表，JSON格式存储")


class DeleteApiKeyParams(BaseModel):
    """删除API Key参数"""

    ids: List[int] = Field(..., description="要删除的ID列表", min_length=1)


class DeleteApiKeyResponse(BaseModel):
    """删除API Key响应"""

    deleted_count: int = Field(..., description="删除数量")
