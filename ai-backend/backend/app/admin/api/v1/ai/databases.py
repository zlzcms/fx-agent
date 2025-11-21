# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:51:12
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 10:35:41
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.database_metadata import (
    BatchUpdateDescriptionsRequest,
    BatchUpdateDescriptionsResponse,
    DatabaseListItem,
    DatabaseTreeNode,
    MCPDataRequest,
    RefreshDatabaseRequest,
    RefreshDatabaseResponse,
)
from backend.app.admin.service.database_metadata_service import database_metadata_service
from backend.app.home.clients.mcp_client import mcp_client
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db
from backend.utils.time_utils import generate_time_range

router = APIRouter()


@router.get("/tree", summary="获取数据库树形结构", dependencies=[DependsJwtAuth])
async def get_database_tree(
    database_name: Optional[str] = Query(None, description="指定数据库名称"),
    include_tables: bool = Query(True, description="是否包含表信息"),
    include_fields: bool = Query(True, description="是否包含字段信息"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[DatabaseTreeNode]]:
    """
    获取数据库树形结构

    Args:
        database_name: 指定数据库名称，不指定则返回所有数据库
        include_tables: 是否包含表信息
        include_fields: 是否包含字段信息
        db: 数据库会话

    Returns:
        数据库树形结构列表
    """
    data = await database_metadata_service.get_database_tree(
        db, database_name=database_name, include_tables=include_tables, include_fields=include_fields
    )
    return response_base.success(data=data)


@router.get(
    "/{database_name}/tables-with-fields", summary="获取指定数据库的表和字段信息", dependencies=[DependsJwtAuth]
)
async def get_tables_with_fields(
    database_name: str, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[DatabaseTreeNode]]:
    """
    获取指定数据库的表和字段信息

    Args:
        database_name: 数据库名称
        db: 数据库会话

    Returns:
        表和字段信息列表
    """
    data = await database_metadata_service.get_database_tree(
        db, database_name=database_name, include_tables=True, include_fields=True
    )
    return response_base.success(data=data)


@router.get(
    "/{database_name}/tables/{table_name}/fields", summary="获取指定表的字段信息", dependencies=[DependsJwtAuth]
)
async def get_table_fields(
    database_name: str, table_name: str, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[DatabaseTreeNode]]:
    """
    获取指定表的字段信息

    Args:
        database_name: 数据库名称
        table_name: 表名称
        db: 数据库会话

    Returns:
        字段信息列表
    """
    data = await database_metadata_service.get_table_fields(db, database_name=database_name, table_name=table_name)
    return response_base.success(data=data)


@router.put("/descriptions", summary="批量更新描述信息", dependencies=[DependsJwtAuth])
async def batch_update_descriptions(
    request: BatchUpdateDescriptionsRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[BatchUpdateDescriptionsResponse]:
    """
    批量更新数据库、表、字段的描述信息

    Args:
        request: 批量更新请求
        db: 数据库会话

    Returns:
        更新结果
    """
    result = await database_metadata_service.batch_update_descriptions(db, request=request)
    return response_base.success(data=result)


@router.post("/refresh", summary="刷新数据库结构", dependencies=[DependsJwtAuth])
async def refresh_database_structure(
    request: RefreshDatabaseRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[RefreshDatabaseResponse]:
    """
    刷新数据库结构信息

    Args:
        request: 刷新请求
        db: 数据库会话

    Returns:
        刷新结果
    """
    result = await database_metadata_service.refresh_database_structure(db, request=request)
    return response_base.success(data=result)


# 获取mcp获取数据
@router.post("/mcp/query-data", summary="查询MCP数据", dependencies=[DependsJwtAuth])
async def query_mcp_data(request: MCPDataRequest, db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[Dict]:
    """
    查询MCP数据

    Args:
        request: MCP数据查询请求
        db: 数据库会话

    Returns:
        MCP数据查询响应
    """
    query_types = request.query_types
    data_permission_values = request.data_permission_values
    start_time, end_time = generate_time_range(request.data_time_range_type, request.data_time_value)
    results = {}
    for data_permission_value in data_permission_values:
        parameters = {"user_id": data_permission_value, "start_time": start_time, "end_time": end_time}
        result = await mcp_client.get_data(query_types, parameters)
        # print(f"result type: {type(result)}")
        if result.get("success"):
            results[data_permission_value] = result.get("data")
        else:
            results[data_permission_value] = result.get("message")

    # 调用MCP客户端查询数据
    # result = 44

    return response_base.success(data=results)


@router.get("", summary="获取数据库列表", dependencies=[DependsJwtAuth])
async def get_databases(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[DatabaseListItem]]:
    """获取所有数据库列表（含描述）"""
    data = await database_metadata_service.get_databases(db)
    return response_base.success(data=data)
