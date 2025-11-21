# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:58:48
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 13:37:20

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_level import crud_risk_level
from backend.app.admin.schema.risk_level import CreateRiskLevelParams, DeleteResponse, UpdateRiskLevelParams
from backend.common.pagination import PageData


class RiskLevelService:
    """风控等级服务"""

    def _level_to_dict(self, risk_level: any) -> dict:
        """将风控等级转换为字典"""
        return {
            "id": risk_level.id,
            "name": risk_level.name,
            "start_score": risk_level.start_score,
            "end_score": risk_level.end_score,
            "description": risk_level.description,
            "created_time": risk_level.created_time,
            "updated_time": risk_level.updated_time,
        }

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页风控等级列表"""
        risk_levels, total = await crud_risk_level.get_list(
            db, name=name, min_score=min_score, max_score=max_score, page=page, size=size
        )

        # 转换为字典
        items = [self._level_to_dict(risk_level) for risk_level in risk_levels]

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
        """获取所有风控等级"""
        risk_levels = await crud_risk_level.get_all(db)
        return [self._level_to_dict(risk_level) for risk_level in risk_levels]

    async def get_by_score(self, db: AsyncSession, *, score: float) -> Optional[dict]:
        """根据分数获取对应的风险等级"""
        risk_level = await crud_risk_level.get_by_score(db, score=score)
        if not risk_level:
            return None
        return self._level_to_dict(risk_level)

    async def get_detail(self, db: AsyncSession, *, level_id: str) -> Optional[dict]:
        """获取风控等级详情"""
        risk_level = await crud_risk_level.get(db, id=level_id)
        if not risk_level:
            return None
        return self._level_to_dict(risk_level)

    async def create(self, db: AsyncSession, *, request: CreateRiskLevelParams) -> dict:
        """创建风控等级"""
        # 检查风控等级名称是否已存在
        if await crud_risk_level.check_name_exists(db, name=request.name):
            raise ValueError(f"风控等级名称 '{request.name}' 已存在")

        # 检查分数范围是否重叠
        if await crud_risk_level.check_score_range_overlap(
            db, start_score=request.start_score, end_score=request.end_score
        ):
            raise ValueError(f"分数范围 {request.start_score}-{request.end_score} 与现有风控等级重叠")

        # 创建风控等级
        risk_level = await crud_risk_level.create(db, obj_in=request)
        return self._level_to_dict(risk_level)

    async def update(self, db: AsyncSession, *, level_id: str, request: UpdateRiskLevelParams) -> Optional[dict]:
        """更新风控等级"""
        # 检查风控等级是否存在
        risk_level = await crud_risk_level.get(db, id=level_id)
        if not risk_level:
            return None

        # 如果更新名称，检查是否重复
        if request.name and request.name != risk_level.name:
            if await crud_risk_level.check_name_exists(db, name=request.name, exclude_id=level_id):
                raise ValueError(f"风控等级名称 '{request.name}' 已存在")

        # 如果更新分数范围，检查是否重叠
        start_score = request.start_score if request.start_score is not None else risk_level.start_score
        end_score = request.end_score if request.end_score is not None else risk_level.end_score

        if request.start_score is not None or request.end_score is not None:
            if await crud_risk_level.check_score_range_overlap(
                db, start_score=start_score, end_score=end_score, exclude_id=level_id
            ):
                raise ValueError(f"分数范围 {start_score}-{end_score} 与现有风控等级重叠")

        # 更新风控等级
        updated_level = await crud_risk_level.update(db, db_obj=risk_level, obj_in=request)
        return self._level_to_dict(updated_level)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量删除风控等级"""
        # 检查风控等级是否存在
        for level_id in ids:
            risk_level = await crud_risk_level.get(db, id=level_id)
            if not risk_level:
                raise ValueError(f"风控等级 ID '{level_id}' 不存在")

        # 批量删除
        deleted_count = await crud_risk_level.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)


risk_level_service = RiskLevelService()
