#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class RecommendedQuestionSchemaBase(SchemaBase):
    """推荐问法基础模型"""

    title: str = Field(description="问法标题")
    content: str = Field(description="问法内容")
    role_ids: list[int] | None = Field(None, description="关联角色ID列表")
    sort_order: int = Field(0, description="排序")
    status: StatusType = Field(description="状态")
    is_default: bool = Field(False, description="是否默认问法")


class CreateRecommendedQuestionParam(RecommendedQuestionSchemaBase):
    """创建推荐问法参数"""


class UpdateRecommendedQuestionParam(RecommendedQuestionSchemaBase):
    """更新推荐问法参数"""


class DeleteRecommendedQuestionParam(SchemaBase):
    """删除推荐问法参数"""

    pks: list[int] = Field(description="推荐问法 ID 列表")


class GetRecommendedQuestionDetail(RecommendedQuestionSchemaBase):
    """推荐问法详情"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="推荐问法 ID")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")


class GetRecommendedQuestionsByRoleParam(SchemaBase):
    """根据角色获取推荐问法参数"""

    role_ids: list[int] = Field(description="角色ID列表")
    limit: int = Field(3, description="返回数量限制")


class GetRecommendedQuestionsByRoleResult(RecommendedQuestionSchemaBase):
    """根据角色获取推荐问法结果"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="推荐问法 ID")
