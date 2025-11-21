# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 10:43:11
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-16 14:33:35
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.datasource import (
    DataSourceListItem,
)
from backend.app.admin.service.datasource_service import datasource_service
from backend.app.admin.service.warehouse_user_service import warehouse_user_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("/all", summary="获取所有数据源集合（不分页）", dependencies=[DependsJwtAuth])
async def get_all_datasources(
    collection_name: Optional[str] = Query(None, description="集合名称"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[DataSourceListItem]]:
    """
    获取所有数据源集合（不分页）

    Args:
        collection_name: 集合名称筛选
        status: 状态筛选
        db: 数据库会话

    Returns:
        所有数据源集合列表
    """
    data = await datasource_service.get_list(db, collection_name=collection_name, status=status)
    return response_base.success(data=data)


@router.get("/countries", summary="获取所有国家列表", dependencies=None)
async def get_all_countries() -> ResponseSchemaModel[dict]:
    """
    获取所有国家列表

    Returns:
        所有国家列表
    """
    try:
        countries = await warehouse_user_service.get_all_countries()
        # print(f"查询结果: {countries}")

        # 确保返回正确的数据格式
        if countries is None:
            countries = []

        # 返回字典格式的数据
        result_data = {"countries": countries, "total": len(countries) if countries else 0}

        return response_base.success(data=result_data)
    except Exception as e:
        # print(f"获取国家列表异常: {str(e)}")
        # 确保异常情况下也返回正确格式，添加data参数
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"获取国家列表失败: {str(e)}"),
            data={"countries": [], "total": 0},  # 确保返回正确的数据结构
        )


@router.get("/{datasource_id}", summary="获取数据源集合详情", dependencies=[DependsJwtAuth])
async def get_datasource_detail(
    datasource_id: str = Path(..., description="集合ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    获取数据源集合详情

    Args:
        datasource_id: 集合ID
        db: 数据库会话

    Returns:
        数据源集合详情
    """
    data = await datasource_service.get_detail(db, datasource_id=datasource_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="数据源集合不存在"))
    return response_base.success(data=data)


@router.put("/{datasource_id}", summary="更新数据源集合", dependencies=[DependsJwtAuth])
async def update_datasource(
    datasource_id: str = Path(..., description="集合ID"), request: dict = ..., db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    更新数据源集合

    Args:
        datasource_id: 集合ID
        request: 更新请求
        db: 数据库会话

    Returns:
        更新后的数据源集合详情
    """
    try:
        data = await datasource_service.update(db, datasource_id=datasource_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="数据源集合不存在"))
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.put("/{datasource_id}/status", summary="切换数据源集合状态", dependencies=[DependsJwtAuth])
async def toggle_datasource_status(
    datasource_id: str = Path(..., description="集合ID"), db: AsyncSession = Depends(get_db), request: dict = ...
) -> ResponseSchemaModel[dict]:
    """
    切换数据源集合状态

    Args:
        datasource_id: 集合ID
        db: 数据库会话
        request: 状态请求，包含status字段

    Returns:
        更新后的数据源集合详情
    """
    try:
        status = request.get("status")
        if status is None:
            return response_base.fail(res=CustomResponse(code=400, msg="请提供status参数"))

        data = await datasource_service.toggle_status(db, datasource_id=datasource_id, status=status)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="数据源集合不存在"))

        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.delete("", summary="删除数据源集合", dependencies=[DependsJwtAuth])
async def delete_datasources(request: dict, db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[dict]:
    """
    批量删除数据源集合

    Args:
        request: 删除请求，包含ids字段
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        ids = request.get("ids", [])
        if not ids:
            return response_base.fail(res=CustomResponse(code=400, msg="请选择要删除的数据源集合"))

        deleted_count = await datasource_service.delete_batch(db, ids=ids)
        return response_base.success(data={"deleted_count": deleted_count})
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.post("/batch", summary="创建数据源集合", dependencies=[DependsJwtAuth])
async def batch_create_datasources(request: dict, db: AsyncSession = Depends(get_db)):
    """
    创建数据源集合

    Args:
        request: 创建请求
        db: 数据库会话

    Returns:
        创建结果
    """
    try:
        # 验证必要字段
        if not request.get("collection_name"):
            return response_base.fail(res=CustomResponse(code=400, msg="请提供集合名称"))
        if not request.get("query_name"):
            return response_base.fail(res=CustomResponse(code=400, msg="请提供查询名称"))

        data = await datasource_service.batch_create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.get("", summary="获取数据源集合列表", dependencies=[DependsJwtAuth])
async def get_datasources(
    collection_name: Optional[str] = Query(None, description="集合名称"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[DataSourceListItem]]:
    """
    获取数据源集合列表

    Args:
        collection_name: 集合名称筛选
        status: 状态筛选
        page: 页码
        size: 每页数量
        db: 数据库会话

    Returns:
        分页数据源集合列表
    """
    data = await datasource_service.get_paginated_list(
        db,
        collection_name=collection_name,
        status=status,
        page=page,
        size=size,
    )
    return response_base.success(data=data)
