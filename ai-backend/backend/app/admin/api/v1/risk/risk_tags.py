# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 14:15:58
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-05 15:30:18
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.risk_tag import (
    CreateRiskTagParams,
    DeleteParams,
    DeleteResponse,
    UpdateRiskTagParams,
)
from backend.app.admin.service.risk_tag_service import risk_tag_service
from backend.common.enums import RiskType
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("/risk-types/all", summary="获取所有风控类型", dependencies=[DependsJwtAuth])
async def get_all_risk_types() -> ResponseSchemaModel[List[dict]]:
    """获取所有风控类型"""
    risk_types = RiskType.get_all_types()
    return response_base.success(data=risk_types)


@router.get("", summary="获取风控标签列表", dependencies=[DependsJwtAuth])
async def get_risk_tags(
    name: Optional[str] = Query(None, description="标签名称（模糊搜索）"),
    risk_type: Optional[RiskType] = Query(None, description="风控类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取风控标签列表"""
    try:
        data = await risk_tag_service.get_paginated_list(db, name=name, risk_type=risk_type, page=page, size=size)
        return response_base.success(data=data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return response_base.fail(res=CustomResponse(code=500, msg=f"内部错误: {str(e)}"), data={})


@router.get("/all", summary="获取所有风控标签（不分页）", dependencies=[DependsJwtAuth])
async def get_all_risk_tags(
    risk_type: Optional[RiskType] = Query(None, description="风控类型"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[dict]]:
    """获取所有风控标签（不分页）"""
    data = await risk_tag_service.get_all(db, risk_type=risk_type)
    return response_base.success(data=data)


@router.get("/risk-type/{risk_type}", summary="根据风控类型获取风控标签", dependencies=[DependsJwtAuth])
async def get_tags_by_risk_type(
    risk_type: RiskType = Path(..., description="风控类型"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[dict]]:
    """根据风控类型获取所有风控标签"""
    data = await risk_tag_service.get_by_risk_type(db, risk_type=risk_type)
    return response_base.success(data=data)


@router.get("/{tag_id}", summary="获取风控标签详情", dependencies=[DependsJwtAuth])
async def get_risk_tag_detail(
    tag_id: int = Path(..., description="标签ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取风控标签详情"""
    data = await risk_tag_service.get_detail(db, tag_id=tag_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="风控标签不存在"), data={})
    return response_base.success(data=data)


@router.post("", summary="创建风控标签", dependencies=[DependsJwtAuth])
async def create_risk_tag(
    request: CreateRiskTagParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """创建风控标签"""
    try:
        data = await risk_tag_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put("/{tag_id}", summary="更新风控标签", dependencies=[DependsJwtAuth])
async def update_risk_tag(
    tag_id: int = Path(..., description="标签ID"),
    request: UpdateRiskTagParams = ...,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """更新风控标签"""
    try:
        data = await risk_tag_service.update(db, tag_id=tag_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控标签不存在"), data={})
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.delete("", summary="删除风控标签", dependencies=[DependsJwtAuth])
async def delete_risk_tags(
    request: DeleteParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """批量删除风控标签"""
    try:
        data = await risk_tag_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=DeleteResponse(deleted_count=0))
