#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_tag import crud_risk_tag
from backend.app.admin.schema.risk_tag import CreateRiskTagParams, DeleteResponse, UpdateRiskTagParams
from backend.common.enums import RiskType
from backend.common.pagination import PageData


class RiskTagService:
    """风控标签服务"""

    def _tag_to_dict(self, tag: any) -> dict:
        """将风控标签转换为字典"""
        return {
            "id": tag.id,
            "risk_type": tag.risk_type,
            "risk_type_name": RiskType.get_display_name(tag.risk_type),
            "name": tag.name,
            "description": tag.description,
            "created_time": tag.created_time,
            "updated_time": tag.updated_time,
        }

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        risk_type: Optional[RiskType] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页风控标签列表"""
        tags, total = await crud_risk_tag.get_list(db, name=name, risk_type=risk_type, page=page, size=size)

        # 转换为字典
        items = [self._tag_to_dict(tag) for tag in tags]

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

    async def get_all(self, db: AsyncSession, *, risk_type: Optional[RiskType] = None) -> List[dict]:
        """获取所有风控标签"""
        tags = await crud_risk_tag.get_all(db, risk_type=risk_type)
        return [self._tag_to_dict(tag) for tag in tags]

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[dict]:
        """根据名称获取风控标签"""
        tag = await crud_risk_tag.get_by_name(db, name=name)
        if not tag:
            return None
        return self._tag_to_dict(tag)

    async def get_by_risk_type(self, db: AsyncSession, *, risk_type: RiskType) -> List[dict]:
        """根据风控类型获取所有风控标签"""
        tags = await crud_risk_tag.get_by_risk_type(db, risk_type=risk_type)
        return [self._tag_to_dict(tag) for tag in tags]

    async def get_detail(self, db: AsyncSession, *, tag_id: int) -> Optional[dict]:
        """获取风控标签详情"""
        tag = await crud_risk_tag.get(db, id=tag_id)
        if not tag:
            return None
        return self._tag_to_dict(tag)

    async def create(self, db: AsyncSession, *, request: CreateRiskTagParams) -> dict:
        """创建风控标签"""
        # 检查风控类型是否有效
        if request.risk_type not in RiskType.get_member_values():
            raise ValueError(f"风控类型 '{request.risk_type}' 无效")

        # 检查风控标签名称在该风控类型下是否已存在
        if await crud_risk_tag.check_name_exists(db, name=request.name, risk_type=request.risk_type):
            raise ValueError(f"标签名称 '{request.name}' 在该风控类型下已存在")

        # 创建风控标签
        tag = await crud_risk_tag.create(db, obj_in=request)
        return self._tag_to_dict(tag)

    async def update(self, db: AsyncSession, *, tag_id: int, request: UpdateRiskTagParams) -> Optional[dict]:
        """更新风控标签"""
        # 检查风控标签是否存在
        tag = await crud_risk_tag.get(db, id=tag_id)
        if not tag:
            return None

        # 如果更新风控类型，检查风控类型是否有效
        if request.risk_type and request.risk_type != tag.risk_type:
            if request.risk_type not in RiskType.get_member_values():
                raise ValueError(f"风控类型 '{request.risk_type}' 无效")

        # 如果更新名称或风控类型，检查名称是否重复
        check_risk_type = request.risk_type if request.risk_type else tag.risk_type
        if request.name and (request.name != tag.name or request.risk_type != tag.risk_type):
            if await crud_risk_tag.check_name_exists(
                db, name=request.name, risk_type=check_risk_type, exclude_id=tag_id
            ):
                raise ValueError(f"标签名称 '{request.name}' 在该风控类型下已存在")

        # 更新风控标签
        updated_tag = await crud_risk_tag.update(db, db_obj=tag, obj_in=request)
        return self._tag_to_dict(updated_tag)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量软删除风控标签"""
        # 检查风控标签是否存在（仅检查未删除的）
        for tag_id in ids:
            tag = await crud_risk_tag.get(db, id=tag_id)
            if not tag:
                raise ValueError(f"风控标签 ID '{tag_id}' 不存在或已被删除")

        # 批量软删除
        deleted_count = await crud_risk_tag.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)

    async def get_by_ids_include_deleted(self, db: AsyncSession, *, ids: List[str]) -> List[dict]:
        """根据ID列表获取风控标签（包含已删除的标签，用于历史记录显示）"""
        tags = await crud_risk_tag.get_by_ids_include_deleted(db, ids=ids)
        return [self._tag_to_dict(tag) for tag in tags]


risk_tag_service = RiskTagService()
