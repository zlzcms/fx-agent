#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.common.enums import RiskType


class RiskTagBase(BaseModel):
    """风控标签基础Schema"""

    risk_type: RiskType = Field(..., description="风控类型")
    name: str = Field(..., description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="标签描述", max_length=500)


class CreateRiskTagParams(RiskTagBase):
    """创建风控标签参数"""

    pass


class UpdateRiskTagParams(BaseModel):
    """更新风控标签参数"""

    risk_type: Optional[RiskType] = Field(None, description="风控类型")
    name: Optional[str] = Field(None, description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="标签描述", max_length=500)


class RiskTag(RiskTagBase):
    """风控标签响应Schema"""

    id: int = Field(..., description="标签ID")
    risk_type_name: Optional[str] = Field(None, description="风控类型名称")
    created_time: str = Field(..., description="创建时间")
    updated_time: str = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class RiskTagParams(BaseModel):
    """风控标签查询参数"""

    name: Optional[str] = Field(None, description="标签名称（模糊搜索）")
    risk_type: Optional[RiskType] = Field(None, description="风控类型")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, gt=0, le=200, description="每页数量")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., description="要删除的ID列表", min_length=1)


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除数量")
