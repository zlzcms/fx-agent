# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 22:15:00
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.ai_subscription import (
    AISubscriptionCreate,
    AISubscriptionQueryParams,
    AISubscriptionUpdate,
    BatchDeleteRequest,
    CloneRequest,
)
from backend.app.admin.service.ai_subscription_service import AISubscriptionService
from backend.common.pagination import PageData
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get(
    "", summary="获取AI订阅列表", description="获取AI订阅列表，支持分页和条件筛选", dependencies=[DependsJwtAuth]
)
async def get_ai_subscriptions(
    *,
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Query(None, description="订阅名称"),
    assistant_name: Optional[str] = Query(None, description="助手名称"),
    responsible_person: Optional[str] = Query(None, description="负责人员"),
    status: Optional[bool] = Query(None, description="订阅状态"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[Dict[str, Any]]]:
    """
    获取AI订阅列表

    查询参数说明：
    - **name**: 订阅名称（模糊搜索）
    - **assistant_name**: 助手名称（模糊搜索）
    - **responsible_person**: 负责人员（模糊搜索）
    - **status**: 订阅状态（true/false）
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100
    """
    params = AISubscriptionQueryParams(
        name=name,
        assistant_name=assistant_name,
        responsible_person=responsible_person,
        status=status,
    )

    data = await AISubscriptionService.get_ai_subscription_list(
        db,
        params=params,
        page=page,
        size=size,
    )
    return response_base.success(data=data)


@router.get(
    "/all",
    summary="获取所有AI订阅",
    description="获取所有AI订阅（不分页），用于下拉选择等场景",
    dependencies=[DependsJwtAuth],
)
async def get_all_ai_subscriptions(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[Dict[str, Any]]]:
    """
    获取所有AI订阅（不分页）
    """
    result = await AISubscriptionService.get_all_ai_subscriptions(db)
    return response_base.success(data=result)


@router.get(
    "/options/types",
    summary="获取AI订阅类型选项",
    description="获取可用的AI订阅类型列表",
    dependencies=[DependsJwtAuth],
)
async def get_subscription_types(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[Dict[str, str]]]:
    """
    获取AI订阅类型选项

    返回可用的订阅类型列表，用于下拉选择
    """
    result = await AISubscriptionService.get_subscription_types(db)
    return response_base.success(data=result)


@router.get(
    "/notification-methods",
    name="subscriptions_get_notification_methods",
    summary="获取通知方式",
    description="获取所有可用的通知方式",
    dependencies=[DependsJwtAuth],
)
async def subscriptions_get_notification_methods(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[Dict[str, Any]]]:
    """
    获取通知方式列表

    返回所有可用的通知方式配置，用于订阅配置中的通知方式选择
    """
    result = await AISubscriptionService.get_notification_methods(db)
    return response_base.success(data=result)


@router.get("/{id}", summary="获取AI订阅详情", description="根据ID获取AI订阅详情信息", dependencies=[DependsJwtAuth])
async def get_ai_subscription(
    id: int = Path(..., description="AI订阅ID"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    获取AI订阅详情

    - **id**: AI订阅ID
    """
    result = await AISubscriptionService.get_ai_subscription(db, id=id)
    return response_base.success(data=result)


@router.post("", summary="创建AI订阅", description="创建新的AI订阅", dependencies=[DependsJwtAuth])
async def create_ai_subscription(
    *, request: Request, db: AsyncSession = Depends(get_db), obj_in: AISubscriptionCreate
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    创建AI订阅
    """
    # 从JWT token中获取当前用户ID
    current_user_id = request.user.id
    result = await AISubscriptionService.create_ai_subscription(db, obj_in=obj_in, user_id=current_user_id)
    return response_base.success(data=result)


@router.put("/{id}", summary="更新AI订阅", description="更新AI订阅信息", dependencies=[DependsJwtAuth])
async def update_ai_subscription(
    *, id: int = Path(..., description="AI订阅ID"), db: AsyncSession = Depends(get_db), obj_in: AISubscriptionUpdate
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    更新AI订阅

    - **id**: AI订阅ID
    """
    result = await AISubscriptionService.update_ai_subscription(db, id=id, obj_in=obj_in)
    return response_base.success(data=result)


@router.delete("", summary="批量删除AI订阅", description="批量删除AI订阅", dependencies=[DependsJwtAuth])
async def delete_ai_subscriptions(
    *, db: AsyncSession = Depends(get_db), request: BatchDeleteRequest
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    批量删除AI订阅
    """
    result = await AISubscriptionService.delete_ai_subscription(db, ids=request.ids)
    return response_base.success(data=result)


@router.post(
    "/{id}/clone", summary="克隆AI订阅", description="克隆现有AI订阅创建新的订阅", dependencies=[DependsJwtAuth]
)
async def clone_ai_subscription(
    *, id: int = Path(..., description="要克隆的AI订阅ID"), db: AsyncSession = Depends(get_db), request: CloneRequest
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    克隆AI订阅

    - **id**: 要克隆的AI订阅ID
    - **name**: 新订阅名称
    """
    result = await AISubscriptionService.clone_ai_subscription(db, id=id, new_name=request.name)
    return response_base.success(data=result)


@router.post(
    "/{id}/toggle",
    summary="启用/禁用订阅",
    description="切换AI订阅的启用/禁用状态",
    dependencies=[DependsJwtAuth],
)
async def toggle_subscription(
    *, id: int = Path(..., description="AI订阅ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    启用/禁用AI订阅

    - **id**: AI订阅ID
    """
    result = await AISubscriptionService.toggle_subscription_status(db, id=id)
    return response_base.success(data=result)


@router.post(
    "/{id}/execute",
    summary="立即执行订阅",
    description="立即执行指定的AI订阅，生成报告",
    dependencies=[DependsJwtAuth],
)
async def execute_subscription(
    *,
    request: Request,
    id: int = Path(..., description="AI订阅ID"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    立即执行AI订阅

    - **id**: AI订阅ID
    """
    # 从JWT token中获取当前用户ID
    current_user_id = request.user.id
    result = await AISubscriptionService.execute_subscription_now(db, id=id, user_id=current_user_id)
    return response_base.success(data=result)


@router.get(
    "/{id}/execution-history",
    summary="获取执行历史",
    description="获取AI订阅的执行历史记录",
    dependencies=[DependsJwtAuth],
)
async def get_subscription_history(
    *,
    id: int = Path(..., description="AI订阅ID"),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="返回记录数量"),
) -> ResponseSchemaModel[List[Dict[str, Any]]]:
    """
    获取AI订阅执行历史

    - **id**: AI订阅ID
    - **limit**: 返回记录数量，最大200
    """
    result = await AISubscriptionService.get_subscription_execution_history(db, id=id, limit=limit)
    return response_base.success(data=result)
