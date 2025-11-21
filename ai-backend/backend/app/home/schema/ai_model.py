#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.common.enums import ModelTypeEnum

# 导出ModelTypeEnum供其他模块使用
__all__ = ["AIModelResponse", "ModelTypeEnum"]


class AIModelResponse(BaseModel):
    """AI模型响应Schema"""

    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    model_type: str = Field(..., description="模型类型")
    model: str = Field(..., description="模型名称/标识符，如gpt-4-turbo")
    temperature: float = Field(..., description="温度参数，值范围0-1")
    status: bool = Field(..., description="状态：true=启用，false=禁用")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)
