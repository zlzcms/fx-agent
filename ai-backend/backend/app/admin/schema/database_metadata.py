# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:49:05
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 10:35:11
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from backend.common.schema import SchemaBase


class DatabaseTreeNodeBase(SchemaBase):
    """数据库树节点基础Schema"""

    id: str = Field(..., description="唯一标识")
    name: str = Field(..., description="名称（数据库名、表名、字段名）")
    type: Literal["database", "table", "field"] = Field(..., description="类型")
    description: Optional[str] = Field(None, description="描述信息")
    parent_id: Optional[str] = Field(None, description="父节点ID")

    # 字段特有属性
    field_type: Optional[str] = Field(None, description="字段类型（VARCHAR, INT等）")
    is_nullable: Optional[bool] = Field(None, description="是否可为空")
    default_value: Optional[str] = Field(None, description="默认值")

    # 表特有属性
    table_rows: Optional[int] = Field(None, description="表数据行数")
    table_size: Optional[str] = Field(None, description='表大小（如："1.2MB"）')


class DatabaseTreeNode(DatabaseTreeNodeBase):
    """数据库树节点响应Schema"""

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DatabaseTreeNodeCreate(DatabaseTreeNodeBase):
    """创建数据库树节点Schema"""

    pass


class DatabaseTreeNodeUpdate(SchemaBase):
    """更新数据库树节点Schema"""

    description: Optional[str] = Field(None, description="描述信息")


class DatabaseDescriptionUpdate(BaseModel):
    """单个描述更新项"""

    id: str = Field(..., description="节点ID")
    type: Literal["database", "table", "field"] = Field(..., description="节点类型")
    description: str = Field(..., description="新的描述信息")


class BatchUpdateDescriptionsRequest(BaseModel):
    """批量更新描述请求"""

    updates: List[DatabaseDescriptionUpdate] = Field(..., description="更新列表")


class BatchUpdateDescriptionsResponse(BaseModel):
    """批量更新描述响应"""

    success: bool = Field(..., description="是否成功")
    updated_count: int = Field(..., description="更新数量")
    message: str = Field(..., description="响应消息")


class RefreshDatabaseRequest(BaseModel):
    """刷新数据库结构请求"""

    database_name: Optional[str] = Field(None, description="数据库名称，不指定则刷新所有")


class RefreshDatabaseResponse(BaseModel):
    """刷新数据库结构响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    scanned_databases: List[str] = Field(..., description="扫描的数据库列表")
    scanned_tables: int = Field(..., description="扫描的表数量")
    scanned_fields: int = Field(..., description="扫描的字段数量")


class DatabaseTreeQueryParams(BaseModel):
    """数据库树查询参数"""

    database_name: Optional[str] = Field(None, description="指定数据库名称")
    include_tables: bool = Field(True, description="是否包含表信息")
    include_fields: bool = Field(True, description="是否包含字段信息")


class DatabaseListItem(BaseModel):
    id: str = Field(..., description="数据库ID")
    name: str = Field(..., description="数据库名称")
    description: Optional[str] = Field(None, description="数据库描述")


class FieldMetadata(BaseModel):
    """字段元数据信息"""

    field_name: str = Field(..., description="字段名称")
    exists: bool = Field(..., description="字段是否存在于元数据中")
    description: Optional[str] = Field(None, description="字段描述")
    field_type: Optional[str] = Field(None, description="字段类型")


class TableMetadata(BaseModel):
    """表元数据信息"""

    table_name: str = Field(..., description="表名称")
    exists: bool = Field(..., description="表是否存在于元数据中")
    field_count: int = Field(..., description="字段数量")
    fields: List[FieldMetadata] = Field(..., description="字段信息列表")


class SqlAnalysisResponse(BaseModel):
    """SQL分析响应"""

    valid: bool = Field(..., description="SQL是否有效")
    database_name: Optional[str] = Field(None, description="数据库名称")
    tables: List[TableMetadata] = Field(..., description="表信息列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class SqlValidationRequest(BaseModel):
    """SQL验证请求"""

    sql: str = Field(..., description="要验证的SQL语句")


class SqlExecuteRequest(BaseModel):
    """SQL执行请求"""

    sql: str = Field(..., description="要执行的SQL语句")
    limit: int = Field(10, description="最大返回行数")


class MCPDataRequest(BaseModel):
    """MCP数据查询请求"""

    query_types: List[str] = Field(..., description="查询类型列表")
    data_permission: Optional[str] = Field(None, description="数据权限范围")
    data_permission_values: Optional[List[Any]] = Field(None, description="数据权限值列表")
    data_time_range_type: Optional[str] = Field(None, description="数据时间范围类型")
    data_time_value: Optional[int] = Field(None, description="数据时间范围值")


class MCPDataResponse(BaseModel):
    """MCP数据查询响应"""

    data: Dict[str, Any] = Field(..., description="查询结果数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="查询结果元数据")
    success: bool = Field(..., description="查询是否成功")
    message: str = Field(..., description="状态消息")
