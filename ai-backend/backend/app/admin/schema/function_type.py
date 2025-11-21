# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.common.schema import SchemaBase


class FunctionTypeBase(SchemaBase):
    """功能类型基础Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="功能类型名称")


class CreateFunctionTypeParams(FunctionTypeBase):
    """创建功能类型Schema"""

    pass


class UpdateFunctionTypeParams(SchemaBase):
    """更新功能类型Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="功能类型名称")


class FunctionTypeInDB(FunctionTypeBase):
    """数据库中的功能类型Schema"""

    id: str = Field(..., description="功能类型ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class FunctionType(FunctionTypeInDB):
    """功能类型响应Schema"""

    pass


class FunctionTypeParams(BaseModel):
    """功能类型查询参数"""

    name: Optional[str] = Field(None, description="功能类型名称（模糊搜索）")
    page: int = Field(1, ge=1, description="页码，默认1")
    size: int = Field(10, ge=1, le=200, description="每页数量，默认10")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., min_items=1, description="功能类型ID数组")


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除数量")
