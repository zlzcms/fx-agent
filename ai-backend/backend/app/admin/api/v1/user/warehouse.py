# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:30:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-07 20:25:30
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.warehouse_user import (
    AgentQueryParams,
    AgentResponse,
    CrmUserQueryParams,
    CrmUserResponse,
    UserDetailResponse,
    WarehouseUserQueryParams,
    WarehouseUserResponse,
)
from backend.app.admin.service.warehouse_user_service import UserType, warehouse_user_service
from backend.common.pagination import PageData
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get(
    "",
    summary="获取数据仓用户列表",
    description="从t_member表获取用户列表，支持分页和条件筛选",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_users(
    *,
    db: AsyncSession = Depends(get_db),
    nickname: Optional[str] = Query(None, description="用户昵称"),
    email: Optional[str] = Query(None, description="用户邮箱"),
    sex: Optional[int] = Query(None, description="性别：0-保密 1-男 2-女"),
    username: Optional[str] = Query(None, description="姓名"),
    status: Optional[bool] = Query(None, description="状态：true-激活 false-未激活"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[WarehouseUserResponse]]:
    """
    获取数据仓用户列表

    查询参数说明：
    - **nickname**: 用户昵称（模糊搜索）
    - **email**: 用户邮箱（模糊搜索）
    - **sex**: 性别：0-保密 1-男 2-女
    - **username**: 姓名（模糊搜索）
    - **status**: 状态：true-激活 false-未激活
    - **keyword**: 关键词搜索（可搜索昵称、邮箱、姓名等）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    """
    params = WarehouseUserQueryParams(
        nickname=nickname,
        email=email,
        sex=sex,
        username=username,
        status=status,
        keyword=keyword,
    )

    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.WAREHOUSE,
        params=params,
        page=page,
        size=page_size,
    )
    return response_base.success(data=data)


@router.get(
    "/users/{user_id}",
    summary="获取数据仓用户详情",
    description="根据用户ID获取用户详细信息",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_user_detail(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int = Path(..., description="用户ID", ge=1),
) -> ResponseSchemaModel[UserDetailResponse]:
    """
    获取数据仓用户详情

    - **user_id**: 用户ID
    """
    user = await warehouse_user_service.get_user_detail(db, user_id, UserType.WAREHOUSE)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return response_base.success(data=user)


@router.get(
    "/crm-users",
    summary="获取数据仓CRM用户列表",
    description="从t_member表获取CRM用户列表，筛选条件为userType='staff'，支持分页和条件筛选",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_crm_users(
    *,
    db: AsyncSession = Depends(get_db),
    nickname: Optional[str] = Query(None, description="用户昵称"),
    email: Optional[str] = Query(None, description="用户邮箱"),
    username: Optional[str] = Query(None, description="姓名"),
    status: Optional[bool] = Query(None, description="状态：true-激活 false-未激活"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[CrmUserResponse]]:
    """
    获取数据仓CRM用户列表

    CRM用户定义：满足以下条件的用户
    - userType = 'staff'

    查询参数说明：
    - **nickname**: 用户昵称（模糊搜索）
    - **email**: 用户邮箱（模糊搜索）
    - **username**: 姓名（模糊搜索）
    - **status**: 状态：true-激活 false-未激活
    - **keyword**: 关键词搜索（可搜索昵称、邮箱、姓名等）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    """
    params = CrmUserQueryParams(
        nickname=nickname,
        email=email,
        username=username,
        status=status,
        keyword=keyword,
    )

    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.CRM,
        params=params,
        page=page,
        size=page_size,
    )
    return response_base.success(data=data)


@router.get(
    "/crm-users-all",
    summary="获取所有数据仓CRM用户（不分页）",
    description="从t_member表获取所有CRM用户，筛选条件为userType='staff'，不分页返回所有结果",
    dependencies=[DependsJwtAuth],
)
async def get_all_warehouse_crm_users(
    *,
    db: AsyncSession = Depends(get_db),
    status: Optional[bool] = Query(None, description="状态：true-激活 false-未激活"),
) -> ResponseSchemaModel[List[WarehouseUserResponse]]:
    """
    获取所有数据仓CRM用户（不分页）

    CRM用户定义：满足以下条件的用户
    - userType = 'staff'

    查询参数说明：
    - **status**: 状态：true-激活 false-未激活
    """
    params = CrmUserQueryParams(status=status)
    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.CRM,
        params=params,
    )
    return response_base.success(data=data)


@router.get(
    "/crm-users/{user_id}",
    summary="获取数据仓CRM用户详情",
    description="根据用户ID获取CRM用户详细信息，筛选条件为userType='staff'",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_crm_user_detail(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int = Path(..., description="用户ID", ge=1),
) -> ResponseSchemaModel[UserDetailResponse]:
    """
    获取数据仓CRM用户详情

    CRM用户定义：满足以下条件的用户
    - userType = 'staff'

    - **user_id**: 用户ID
    """
    user = await warehouse_user_service.get_user_detail(db, user_id, UserType.CRM)
    if user is None:
        raise HTTPException(status_code=404, detail="CRM用户不存在")
    return response_base.success(data=user)


@router.get(
    "/agents",
    summary="获取数据仓代理商列表",
    description="从t_member表获取代理商列表，筛选条件为userType='agent'，支持分页和条件筛选",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_agents(
    *,
    db: AsyncSession = Depends(get_db),
    nickname: Optional[str] = Query(None, description="用户昵称"),
    username: Optional[str] = Query(None, description="姓名"),
    status: Optional[bool] = Query(None, description="状态：true-激活 false-未激活"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[AgentResponse]]:
    """
    获取数据仓代理商列表

    - **nickname**: 用户昵称
    - **username**: 姓名
    - **status**: 状态：true-激活 false-未激活
    - **keyword**: 关键词搜索
    - **page**: 页码
    - **page_size**: 每页数量
    """
    params = AgentQueryParams(
        nickname=nickname,
        username=username,
        status=status,
        keyword=keyword,
    )
    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.AGENT,
        params=params,
        page=page,
        size=page_size,
    )
    return response_base.success(data=data)


@router.get(
    "/agents/{user_id}",
    summary="获取数据仓代理商详情",
    description="根据用户ID获取代理商详细信息，筛选条件为userType='agent'",
    dependencies=[DependsJwtAuth],
)
async def get_warehouse_agent_detail(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int = Path(..., description="用户ID", ge=1),
) -> ResponseSchemaModel[UserDetailResponse]:
    """
    获取数据仓代理商详情

    - **user_id**: 用户ID
    """
    user = await warehouse_user_service.get_user_detail(db, user_id, UserType.AGENT)
    if user is None:
        raise HTTPException(status_code=404, detail="代理商不存在")
    return response_base.success(data=user)


@router.get(
    "/users-all",
    summary="获取所有数据仓用户（不分页）",
    description="获取所有激活状态的数据仓用户，不分页",
    dependencies=[DependsJwtAuth],
)
async def get_all_warehouse_users(
    *,
    db: AsyncSession = Depends(get_db),
    status: Optional[bool] = Query(True, description="状态：true-激活 false-未激活"),
) -> ResponseSchemaModel[list[WarehouseUserResponse]]:
    """
    获取所有数据仓用户（不分页）

    - **status**: 状态：true-激活 false-未激活，默认为true
    """
    params = WarehouseUserQueryParams(status=status)

    # 使用不分页方法获取所有数据
    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.WAREHOUSE,
        params=params,
    )
    return response_base.success(data=data)


@router.get(
    "/agents-all",
    summary="获取所有数据仓代理商（不分页）",
    description="获取所有激活状态的数据仓代理商，不分页",
    dependencies=[DependsJwtAuth],
)
async def get_all_warehouse_agents(
    *,
    db: AsyncSession = Depends(get_db),
    status: Optional[bool] = Query(True, description="状态：true-激活 false-未激活"),
) -> ResponseSchemaModel[list[AgentResponse]]:
    """
    获取所有数据仓代理商（不分页）

    - **status**: 状态：true-激活 false-未激活，默认为true
    """
    params = AgentQueryParams(status=status)

    # 使用不分页方法获取所有数据
    data = await warehouse_user_service.get_users(
        db,
        user_type=UserType.AGENT,
        params=params,
    )
    return response_base.success(data=data)
