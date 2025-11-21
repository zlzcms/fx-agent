#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from math import ceil
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_api_key import crud_api_key
from backend.app.admin.model.api_key import ApiKey
from backend.app.admin.schema.api_key import CreateApiKeyParams, DeleteApiKeyResponse, UpdateApiKeyParams
from backend.common.pagination import PageData


class ApiKeyService:
    """API Key服务"""

    def _key_to_dict(self, key: ApiKey, include_full_key: bool = False) -> dict:
        """将API Key转换为字典"""
        data = {
            "id": key.id,
            "key_name": key.key_name,
            "description": key.description,
            "status": key.status,
            "expires_at": key.expires_at,
            "last_used_at": key.last_used_at,
            "last_used_ip": key.last_used_ip,
            "usage_count": key.usage_count,
            "user_id": key.user_id,
            "created_time": key.created_time,
            "updated_time": key.updated_time,
        }
        if include_full_key:
            data["api_key"] = key.api_key
            data["ip_whitelist"] = key.ip_whitelist
            data["permissions"] = key.permissions
        else:
            # 只返回前8个和后8个字符，中间用*代替
            api_key = key.api_key
            if len(api_key) <= 16:
                # 如果长度小于等于16，全部显示
                data["api_key_prefix"] = api_key
            else:
                # 前8个字符 + 中间用*代替 + 后8个字符
                prefix = api_key[:8]
                suffix = api_key[-8:]
                middle_stars = "*" * (len(api_key) - 16)
                data["api_key_prefix"] = f"{prefix}{middle_stars}{suffix}"
        return data

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        key_name: Optional[str] = None,
        status: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        size: int = 10,
        include_full_key: bool = False,
    ) -> PageData[dict]:
        """获取分页API Key列表"""
        keys, total = await crud_api_key.get_list(
            db, key_name=key_name, status=status, user_id=user_id, page=page, size=size
        )

        items = [self._key_to_dict(key, include_full_key=include_full_key) for key in keys]
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

    async def get_detail(self, db: AsyncSession, *, api_key_id: int, include_full_key: bool = False) -> Optional[dict]:
        """获取API Key详情"""
        key = await crud_api_key.get(db, id=api_key_id)
        if not key:
            return None
        return self._key_to_dict(key, include_full_key=include_full_key)

    async def create(self, db: AsyncSession, *, request: CreateApiKeyParams, user_id: int) -> dict:
        """创建API Key"""
        if await crud_api_key.check_key_name_exists(db, key_name=request.key_name):
            raise ValueError(f"API Key名称 '{request.key_name}' 已存在")

        key = await crud_api_key.create(db, obj_in=request, user_id=user_id)
        return self._key_to_dict(key, include_full_key=True)

    async def update(self, db: AsyncSession, *, api_key_id: int, request: UpdateApiKeyParams) -> Optional[dict]:
        """更新API Key"""
        key = await crud_api_key.get(db, id=api_key_id)
        if not key:
            return None

        if request.key_name and request.key_name != key.key_name:
            if await crud_api_key.check_key_name_exists(db, key_name=request.key_name, exclude_id=api_key_id):
                raise ValueError(f"API Key名称 '{request.key_name}' 已存在")

        updated_key = await crud_api_key.update(db, db_obj=key, obj_in=request)
        return self._key_to_dict(updated_key)

    async def delete(self, db: AsyncSession, *, api_key_id: int) -> bool:
        """删除API Key（软删除）"""
        return await crud_api_key.delete(db, id=api_key_id)

    async def delete_batch(self, db: AsyncSession, *, ids: List[int]) -> DeleteApiKeyResponse:
        """批量删除API Key（软删除）"""
        deleted_count = await crud_api_key.delete_batch(db, ids=ids)
        return DeleteApiKeyResponse(deleted_count=deleted_count)


api_key_service = ApiKeyService()
