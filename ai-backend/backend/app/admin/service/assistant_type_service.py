# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:42:19
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:39:55

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_assistant_type import crud_assistant_type
from backend.app.admin.schema.assistant_type import (
    CreateAssistantTypeParams,
    DeleteResponse,
    UpdateAssistantTypeParams,
)
from backend.common.pagination import PageData


class AssistantTypeService:
    """助手类型服务"""

    def _type_to_dict(self, assistant_type: any) -> dict:
        """将助手类型转换为字典"""
        return {
            "id": assistant_type.id,
            "name": assistant_type.name,
            "created_time": assistant_type.created_time,
            "updated_time": assistant_type.updated_time,
        }

    async def get_paginated_list(
        self, db: AsyncSession, *, name: Optional[str] = None, page: int = 1, size: int = 10
    ) -> PageData[dict]:
        """获取分页助手类型列表"""
        assistant_types, total = await crud_assistant_type.get_list(db, name=name, page=page, size=size)

        # 转换为字典
        items = [self._type_to_dict(assistant_type) for assistant_type in assistant_types]

        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links={
                "first": f"?page=1&size={size}",
                "last": f"?page={total_pages}&size={size}",
                "self": f"?page={page}&size={size}",
                "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
                "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
            },
        )

    async def get_all(self, db: AsyncSession) -> List[dict]:
        """获取所有助手类型"""
        assistant_types = await crud_assistant_type.get_all(db)
        return [self._type_to_dict(assistant_type) for assistant_type in assistant_types]

    async def get_detail(self, db: AsyncSession, *, type_id: str) -> Optional[dict]:
        """获取助手类型详情"""
        assistant_type = await crud_assistant_type.get(db, id=type_id)
        if not assistant_type:
            return None
        return self._type_to_dict(assistant_type)

    async def create(self, db: AsyncSession, *, request: CreateAssistantTypeParams) -> dict:
        """创建助手类型"""
        # 检查助手类型名称是否已存在
        if await crud_assistant_type.check_name_exists(db, name=request.name):
            raise ValueError(f"助手类型名称 '{request.name}' 已存在")

        # 创建助手类型
        assistant_type = await crud_assistant_type.create(db, obj_in=request)
        return self._type_to_dict(assistant_type)

    async def update(self, db: AsyncSession, *, type_id: str, request: UpdateAssistantTypeParams) -> Optional[dict]:
        """更新助手类型"""
        # 检查助手类型是否存在
        assistant_type = await crud_assistant_type.get(db, id=type_id)
        if not assistant_type:
            return None

        # 如果更新名称，检查是否重复
        if request.name and request.name != assistant_type.name:
            if await crud_assistant_type.check_name_exists(db, name=request.name, exclude_id=type_id):
                raise ValueError(f"助手类型名称 '{request.name}' 已存在")

        # 更新助手类型
        updated_type = await crud_assistant_type.update(db, db_obj=assistant_type, obj_in=request)
        return self._type_to_dict(updated_type)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量删除助手类型"""
        # 检查助手类型是否存在
        for type_id in ids:
            assistant_type = await crud_assistant_type.get(db, id=type_id)
            if not assistant_type:
                raise ValueError(f"助手类型 ID '{type_id}' 不存在")

        # 批量删除
        deleted_count = await crud_assistant_type.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)


assistant_type_service = AssistantTypeService()
