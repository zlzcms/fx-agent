# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-14 13:38:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 19:34:55

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from backend.common.enums import ModelTypeEnum
from backend.common.schema import SchemaBase


class AIModelBase(SchemaBase):
    """AI模型基础Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    api_key: str = Field(..., min_length=8, description="API密钥")
    base_url: Optional[str] = Field(None, max_length=500, description="API基础URL")
    model_type: ModelTypeEnum = Field(..., description="模型类型")
    model: str = Field(..., min_length=1, max_length=100, description="模型名称/标识符，如gpt-4-turbo")
    temperature: float = Field(0.75, ge=0, le=1, description="温度参数，值范围0-1")
    status: bool = Field(True, description="状态：true=启用，false=禁用")

    @field_validator("base_url")
    def validate_base_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("base_url必须是有效的URL格式")
        return v


class CreateAIModelParams(AIModelBase):
    """创建AI模型Schema"""

    pass


class UpdateAIModelParams(SchemaBase):
    """更新AI模型Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    api_key: Optional[str] = Field(None, min_length=8, description="API密钥")
    base_url: Optional[str] = Field(None, max_length=500, description="API基础URL")
    model_type: Optional[ModelTypeEnum] = Field(None, description="模型类型")
    model: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称/标识符，如gpt-4-turbo")
    temperature: Optional[float] = Field(None, ge=0, le=1, description="温度参数，值范围0-1")
    status: Optional[bool] = Field(None, description="状态：true=启用，false=禁用")

    @field_validator("base_url")
    def validate_base_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("base_url必须是有效的URL格式")
        return v


class AIModelInDB(AIModelBase):
    """数据库中的AI模型Schema"""

    id: str = Field(..., description="模型ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    def mask_api_key(self) -> str:
        """脱敏处理API Key"""
        if len(self.api_key) <= 12:
            return self.api_key[:4] + "*" * 4 + self.api_key[-4:]
        return self.api_key[:8] + "*" * 8 + self.api_key[-4:]


class AIModel(AIModelInDB):
    """AI模型响应Schema"""

    @property
    def api_key_masked(self) -> str:
        """返回脱敏的API Key"""
        return self.mask_api_key()


class AIModelParams(BaseModel):
    """AI模型查询参数"""

    name: Optional[str] = Field(None, description="模型名称（模糊搜索）")
    model_type: Optional[ModelTypeEnum] = Field(None, description="模型类型")
    status: Optional[bool] = Field(None, description="状态筛选")
    page: int = Field(1, ge=1, description="页码，默认1")
    size: int = Field(10, ge=1, le=200, description="每页数量，默认10")


class StatusParams(BaseModel):
    """状态切换参数"""

    status: bool = Field(..., description="目标状态")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., min_items=1, description="模型ID数组")


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除数量")


class TestResponse(BaseModel):
    """测试连接响应"""

    success: bool = Field(..., description="测试结果")
    message: Optional[str] = Field(None, description="错误信息或成功信息")
