# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-14 13:40:57
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-14 14:20:12

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.ai_model import (
    CreateAIModelParams,
    DeleteParams,
    DeleteResponse,
    ModelTypeEnum,
    StatusParams,
    TestResponse,
    UpdateAIModelParams,
)
from backend.app.admin.service.ai_model_service import ai_model_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("", summary="获取AI模型列表", dependencies=[DependsJwtAuth])
async def get_ai_models(
    name: Optional[str] = Query(None, description="模型名称（模糊搜索）"),
    model_type: Optional[ModelTypeEnum] = Query(None, description="模型类型"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """
    获取AI模型列表

    Args:
        name: 模型名称筛选（模糊搜索）
        model_type: 模型类型筛选
        status: 状态筛选
        page: 页码
        size: 每页数量
        db: 数据库会话

    Returns:
        分页AI模型列表
    """
    data = await ai_model_service.get_paginated_list(
        db, name=name, model_type=model_type, status=status, page=page, size=size
    )
    return response_base.success(data=data)


@router.get("/all", summary="获取所有AI模型（不分页）", dependencies=[DependsJwtAuth])
async def get_all_ai_models(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[dict]]:
    """
    获取所有启用的AI模型（不分页）

    Args:
        db: 数据库会话

    Returns:
        所有启用的AI模型列表
    """
    data = await ai_model_service.get_all_enabled(db)
    return response_base.success(data=data)


@router.get("/default", summary="获取系统默认AI模型", dependencies=[DependsJwtAuth])
async def get_default_ai_model(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """
    获取系统默认AI模型

    返回当前系统配置的默认AI模型信息。

    Args:
        db: 数据库会话

    Returns:
        默认AI模型信息，如果未设置则返回空字典
    """
    default_model_id = await ai_model_service.get_default_model_id(db)

    if not default_model_id:
        return response_base.success(data={})

    model_detail = await ai_model_service.get_detail(db, model_id=default_model_id)

    if not model_detail:
        return response_base.success(data={})

    return response_base.success(data=model_detail)


@router.get("/{model_id}", summary="获取AI模型详情", dependencies=[DependsJwtAuth])
async def get_ai_model_detail(
    model_id: str = Path(..., description="模型ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    获取AI模型详情

    Args:
        model_id: 模型ID
        db: 数据库会话

    Returns:
        AI模型详情
    """
    data = await ai_model_service.get_detail(db, model_id=model_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="AI模型不存在"))
    return response_base.success(data=data)


@router.post("", summary="创建AI模型", dependencies=[DependsJwtAuth])
async def create_ai_model(
    request: CreateAIModelParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    创建AI模型

    Args:
        request: 创建请求
        db: 数据库会话

    Returns:
        创建的AI模型信息
    """
    try:
        data = await ai_model_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.put("/default/{model_id}", summary="设置系统默认AI模型", dependencies=[DependsJwtAuth])
async def set_default_ai_model(
    model_id: str = Path(..., description="模型ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    设置系统默认AI模型

    此接口用于后台管理系统配置系统全局默认使用的AI模型。
    设置后，所有未指定模型的聊天会话将使用此默认模型。

    Args:
        model_id: 要设置为默认的模型ID
        db: 数据库会话

    Returns:
        设置结果
    """
    try:
        data = await ai_model_service.set_default_model(db, model_id=model_id)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put("/{model_id}/status", summary="切换AI模型状态", dependencies=[DependsJwtAuth])
async def toggle_ai_model_status(
    model_id: str = Path(..., description="模型ID"), request: StatusParams = ..., db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    切换AI模型状态

    Args:
        model_id: 模型ID
        request: 状态请求，包含status字段
        db: 数据库会话

    Returns:
        更新后的AI模型信息
    """
    try:
        data = await ai_model_service.toggle_status(db, model_id=model_id, status=request.status)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="AI模型不存在"))
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.put("/{model_id}", summary="更新AI模型", dependencies=[DependsJwtAuth])
async def update_ai_model(
    model_id: str = Path(..., description="模型ID"),
    request: UpdateAIModelParams = ...,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """
    更新AI模型

    Args:
        model_id: 模型ID
        request: 更新请求
        db: 数据库会话

    Returns:
        更新后的AI模型信息
    """
    try:
        data = await ai_model_service.update(db, model_id=model_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="AI模型不存在"))
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.delete("", summary="删除AI模型", dependencies=[DependsJwtAuth])
async def delete_ai_models(
    request: DeleteParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """
    批量删除AI模型

    Args:
        request: 删除请求，包含ids字段
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        data = await ai_model_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.post("/{model_id}/test", summary="测试AI模型连接", dependencies=[DependsJwtAuth])
async def test_ai_model_connection(
    model_id: str = Path(..., description="模型ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[TestResponse]:
    """
    测试AI模型连接

    Args:
        model_id: 模型ID
        db: 数据库会话

    Returns:
        测试结果
    """
    data = await ai_model_service.test_connection(db, model_id=model_id)
    return response_base.success(data=data)
