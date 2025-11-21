# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:57:17
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 10:59:20

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from backend.common.schema import SchemaBase


class RiskLevelBase(SchemaBase):
    """风控等级基础Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="风控等级名称")
    start_score: int = Field(..., ge=0, le=1000, description="评分范围开始分")
    end_score: int = Field(..., ge=0, le=1000, description="评分范围结束分")
    description: Optional[str] = Field(None, max_length=500, description="风控等级描述")

    @validator("end_score")
    def validate_score_range(cls, v, values):
        if "start_score" in values and v <= values["start_score"]:
            raise ValueError("结束分必须大于开始分")
        return v


class CreateRiskLevelParams(RiskLevelBase):
    """创建风控等级Schema"""

    pass


class UpdateRiskLevelParams(SchemaBase):
    """更新风控等级Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="风控等级名称")
    start_score: Optional[int] = Field(None, ge=0, le=1000, description="评分范围开始分")
    end_score: Optional[int] = Field(None, ge=0, le=1000, description="评分范围结束分")
    description: Optional[str] = Field(None, max_length=500, description="风控等级描述")

    @validator("end_score")
    def validate_score_range(cls, v, values):
        if v is not None and "start_score" in values and values["start_score"] is not None:
            if v <= values["start_score"]:
                raise ValueError("结束分必须大于开始分")
        return v


class RiskLevelInDB(RiskLevelBase):
    """数据库中的风控等级Schema"""

    id: str = Field(..., description="风控等级ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class RiskLevel(RiskLevelInDB):
    """风控等级响应Schema"""

    pass


class RiskLevelParams(BaseModel):
    """风控等级查询参数"""

    name: Optional[str] = Field(None, description="风控等级名称（模糊搜索）")
    min_score: Optional[int] = Field(None, ge=0, le=1000, description="最小分数筛选")
    max_score: Optional[int] = Field(None, ge=0, le=1000, description="最大分数筛选")
    page: int = Field(1, ge=1, description="页码，默认1")
    size: int = Field(10, ge=1, le=200, description="每页数量，默认10")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., min_items=1, description="风控等级ID数组")


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除数量")
