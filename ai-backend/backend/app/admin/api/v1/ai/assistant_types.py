# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:42:59
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 18:03:20

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.assistant_type import (
    CreateAssistantTypeParams,
    DeleteParams,
    DeleteResponse,
    UpdateAssistantTypeParams,
)
from backend.app.admin.service.assistant_type_service import assistant_type_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("", summary="获取助手类型列表", dependencies=[DependsJwtAuth])
async def get_assistant_types(
    name: Optional[str] = Query(None, description="助手类型名称（模糊搜索）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取助手类型列表"""
    data = await assistant_type_service.get_paginated_list(db, name=name, page=page, size=size)
    return response_base.success(data=data)


@router.get("/all", summary="获取所有助手类型（不分页）", dependencies=[DependsJwtAuth])
async def get_all_assistant_types(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[dict]]:
    """获取所有助手类型（不分页）"""
    data = await assistant_type_service.get_all(db)
    return response_base.success(data=data)


@router.get("/{type_id}", summary="获取助手类型详情", dependencies=[DependsJwtAuth])
async def get_assistant_type_detail(
    type_id: str = Path(..., description="助手类型ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取助手类型详情"""
    data = await assistant_type_service.get_detail(db, type_id=type_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="助手类型不存在"), data={})
    return response_base.success(data=data)


@router.post("", summary="创建助手类型", dependencies=[DependsJwtAuth])
async def create_assistant_type(
    request: CreateAssistantTypeParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """创建助手类型"""
    try:
        data = await assistant_type_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put("/{type_id}", summary="更新助手类型", dependencies=[DependsJwtAuth])
async def update_assistant_type(
    type_id: str = Path(..., description="助手类型ID"),
    request: UpdateAssistantTypeParams = ...,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """更新助手类型"""
    try:
        data = await assistant_type_service.update(db, type_id=type_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="助手类型不存在"), data={})
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.delete("", summary="删除助手类型", dependencies=[DependsJwtAuth])
async def delete_assistant_types(
    request: DeleteParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """批量删除助手类型"""
    try:
        data = await assistant_type_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=DeleteResponse(deleted_count=0))
