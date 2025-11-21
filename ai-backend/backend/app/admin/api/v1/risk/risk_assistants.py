#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.risk_assistant import (
    CreateRiskAssistantParams,
    DeleteParams,
    DeleteResponse,
    UpdateRiskAssistantParams,
    UpdateStatusParams,
)
from backend.app.admin.service.risk_assistant_service import risk_assistant_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("", summary="获取风控助手列表", dependencies=[DependsJwtAuth])
async def get_risk_assistants(
    name: Optional[str] = Query(None, description="风控助手名称（模糊搜索）"),
    ai_model_id: Optional[str] = Query(None, description="AI模型ID筛选"),
    risk_type: Optional[str] = Query(None, description="风险类型筛选"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取风控助手列表"""
    data = await risk_assistant_service.get_paginated_list(
        db, name=name, ai_model_id=ai_model_id, status=status, page=page, size=size
    )
    return response_base.success(data=data)


@router.get("/all", summary="获取所有风控助手（不分页）", dependencies=[DependsJwtAuth])
async def get_all_risk_assistants(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[dict]]:
    """获取所有风控助手（不分页）"""
    data = await risk_assistant_service.get_all(db)
    return response_base.success(data=data)


@router.get("/{assistant_id}", summary="获取风控助手详情", dependencies=[DependsJwtAuth])
async def get_risk_assistant_detail(assistant_id: str, db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[dict]:
    """获取风控助手详情"""
    data = await risk_assistant_service.get_detail(db, assistant_id=assistant_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="风控助手不存在"), data={})
    return response_base.success(data=data)


@router.post("", summary="创建风控助手", dependencies=[DependsJwtAuth])
async def create_risk_assistant(
    request: CreateRiskAssistantParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """创建风控助手"""
    try:
        data = await risk_assistant_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put("/{assistant_id}", summary="更新风控助手", dependencies=[DependsJwtAuth])
async def update_risk_assistant(
    assistant_id: str, request: UpdateRiskAssistantParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """更新风控助手"""
    try:
        data = await risk_assistant_service.update(db, assistant_id=assistant_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控助手不存在"), data={})
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.delete("", summary="删除风控助手", dependencies=[DependsJwtAuth])
async def delete_risk_assistants(
    request: DeleteParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """批量删除风控助手"""
    try:
        data = await risk_assistant_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=DeleteResponse(deleted_count=0))


@router.put("/{assistant_id}/status", summary="更新风控助手状态", dependencies=[DependsJwtAuth])
async def update_risk_assistant_status(
    assistant_id: str, request: UpdateStatusParams, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """更新风控助手状态"""
    data = await risk_assistant_service.update_status(db, assistant_id=assistant_id, status=request.status)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="风控助手不存在"), data={})
    return response_base.success(data=data)


@router.get("/by-model/{ai_model_id}", summary="根据AI模型获取风控助手", dependencies=[DependsJwtAuth])
async def get_risk_assistants_by_model(
    ai_model_id: str, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[dict]]:
    """根据AI模型ID获取风控助手列表"""
    data = await risk_assistant_service.get_by_ai_model(db, ai_model_id=ai_model_id)
    return response_base.success(data=data)
