# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:41:14
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:37:32

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.common.schema import SchemaBase


class AssistantTypeBase(SchemaBase):
    """助手类型基础Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="助手类型名称")


class CreateAssistantTypeParams(AssistantTypeBase):
    """创建助手类型Schema"""

    pass


class UpdateAssistantTypeParams(SchemaBase):
    """更新助手类型Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="助手类型名称")


class AssistantTypeInDB(AssistantTypeBase):
    """数据库中的助手类型Schema"""

    id: str = Field(..., description="助手类型ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class AssistantType(AssistantTypeInDB):
    """助手类型响应Schema"""

    pass


class AssistantTypeParams(BaseModel):
    """助手类型查询参数"""

    name: Optional[str] = Field(None, description="助手类型名称（模糊搜索）")
    page: int = Field(1, ge=1, description="页码，默认1")
    size: int = Field(10, ge=1, le=200, description="每页数量，默认10")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., min_items=1, description="助手类型ID数组")


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除数量")
