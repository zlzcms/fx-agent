# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:59:19
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 10:59:31
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.risk_level import (
    CreateRiskLevelParams,
    DeleteParams,
    DeleteResponse,
    UpdateRiskLevelParams,
)
from backend.app.admin.service.risk_level_service import risk_level_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("", summary="获取风控等级列表", dependencies=[DependsJwtAuth])
async def get_risk_levels(
    name: Optional[str] = Query(None, description="风控等级名称（模糊搜索）"),
    min_score: Optional[int] = Query(None, ge=0, le=1000, description="最小分数筛选"),
    max_score: Optional[int] = Query(None, ge=0, le=1000, description="最大分数筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取风控等级列表"""
    data = await risk_level_service.get_paginated_list(
        db, name=name, min_score=min_score, max_score=max_score, page=page, size=size
    )
    return response_base.success(data=data)


@router.get("/all", summary="获取所有风控等级（不分页）", dependencies=[DependsJwtAuth])
async def get_all_risk_levels(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[dict]]:
    """获取所有风控等级（不分页）"""
    data = await risk_level_service.get_all(db)
    return response_base.success(data=data)


@router.get("/{level_id}", summary="获取风控等级详情", dependencies=[DependsJwtAuth])
async def get_risk_level_detail(
    level_id: str = Path(..., description="风控等级ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取风控等级详情"""
    data = await risk_level_service.get_detail(db, level_id=level_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="风控等级不存在"), data={})
    return response_base.success(data=data)


@router.post("", summary="创建风控等级", dependencies=[DependsJwtAuth])
async def create_risk_level(
    request: CreateRiskLevelParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """创建风控等级"""
    try:
        data = await risk_level_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put("/{level_id}", summary="更新风控等级", dependencies=[DependsJwtAuth])
async def update_risk_level(
    level_id: str = Path(..., description="风控等级ID"),
    request: UpdateRiskLevelParams = ...,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """更新风控等级"""
    try:
        data = await risk_level_service.update(db, level_id=level_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控等级不存在"), data={})
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.delete("", summary="删除风控等级", dependencies=[DependsJwtAuth])
async def delete_risk_levels(
    request: DeleteParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """批量删除风控等级"""
    try:
        data = await risk_level_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=DeleteResponse(deleted_count=0))
