#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.api.deps import get_current_home_user
from backend.app.home.service.subscription_service import HomeSubscriptionService
from backend.common.pagination import PageData
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.database.db import get_db

router = APIRouter()


@router.get(
    "",
    summary="获取我的订阅通知",
    description="获取当前用户作为通知对象的AI订阅列表（仅显示启用的订阅）",
)
async def get_my_subscriptions(
    *,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_home_user),
    name: Optional[str] = Query(None, description="订阅名称"),
    subscription_type: Optional[str] = Query(None, description="订阅类型"),
    assistant_name: Optional[str] = Query(None, description="助手名称"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[Dict]]:
    """
    获取我的订阅通知列表

    返回当前登录用户作为通知对象的启用状态AI订阅信息。
    根据responsible_persons字段中的personnel_id与当前用户ID匹配进行过滤。

    查询参数说明：
    - **name**: 订阅名称（模糊搜索）
    - **subscription_type**: 订阅类型
    - **assistant_name**: 助手名称（模糊搜索）
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100

    注意：只返回启用状态（status=true）的订阅
    """
    data = await HomeSubscriptionService.get_user_subscriptions(
        db,
        user_id=str(current_user.id),
        name=name,
        subscription_type=subscription_type,
        assistant_name=assistant_name,
        status=True,  # 固定为True，只获取启用的订阅
        page=page,
        size=size,
    )
    return response_base.success(data=data)


@router.get(
    "/{subscription_id}",
    summary="获取订阅详情",
    description="获取指定订阅的详细信息（仅限当前用户有权限的订阅）",
)
async def get_my_subscription_detail(
    *,
    request: Request,
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_home_user),
) -> ResponseSchemaModel[Dict]:
    """
    获取我的订阅详情

    返回指定订阅的详细信息，仅当当前用户是该订阅的通知对象时才能访问。
    """
    data = await HomeSubscriptionService.get_user_subscription_detail(
        db,
        subscription_id=subscription_id,
        user_id=str(current_user.id),
    )
    return response_base.success(data=data)
