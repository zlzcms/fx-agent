# -*- coding: utf-8 -*-
# @Author: claude-4-sonnet
# @Date:   2025-06-27 10:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SelectedTableField(BaseModel):
    """表中选定的字段"""

    field_id: str = Field(..., description="字段ID")
    field_name: str = Field(..., description="字段名称")


class TableDataSource(BaseModel):
    """表数据源"""

    database_name: Optional[str] = Field(None, description="数据库名称")
    table_name: str = Field(..., description="表名")
    table_description: Optional[str] = Field(None, description="表描述")
    data_limit: Optional[int] = Field(200, description="数据限制")
    relation_field: Optional[str] = Field(None, description="关联字段名，用于多表关联")
    selected_fields: Optional[List[str]] = Field(None, description="选定的字段ID列表")
    selected_field_names: List[str] = Field(..., description="选定的字段名称列表")


class DataSourceLinkField(BaseModel):
    """数据源链接字段"""

    fromField: str = Field(..., description="来源字段")
    fromTable: str = Field(..., description="来源表")


class ConditionField(BaseModel):
    """条件字段"""

    fromField: str = Field(..., description="条件字段名")
    fromTable: str = Field(..., description="条件表名")
    value: Any = Field(..., description="条件值")
    operator: str = Field("=", description="条件操作符，默认为等于")


class SqlGenerateRequest(BaseModel):
    """SQL生成请求"""

    database_name: str = Field(..., description="数据库名称")
    tables: List[TableDataSource] = Field(..., description="要查询的表列表")
    condition: Optional[str | ConditionField] = Field(None, description="查询条件，可以是字符串或条件字段对象")
    order_by: Optional[str] = Field(None, description="排序字段")
    order_direction: Optional[str] = Field("DESC", description="排序方向")
    dataSourcesLinkField: Optional[DataSourceLinkField] = Field(None, description="数据源链接字段")
    data_permission: Optional[str] = Field(None, description="数据权限")
    data_permission_values: Optional[List[Any]] = Field(None, description="数据权限值")
    data_time_range_type: Optional[str] = Field(None, description="数据时间范围类型")
    data_time_value: Optional[int] = Field(None, description="数据时间范围值")


class SqlGenerateResponse(BaseModel):
    """SQL生成响应"""

    sql: str = Field(..., description="生成的SQL语句")
    description: str = Field(..., description="SQL描述")


class SqlExecutionResult(BaseModel):
    """SQL执行结果"""

    dataSourceId: str = Field(..., description="数据源ID")
    dataSourceName: str = Field(..., description="数据源名称")
    rows: List[Dict[str, Any]] = Field(..., description="查询结果行")


class DataSourceLinkRequest(BaseModel):
    """数据源链接请求"""

    dataSourcesLinkField: DataSourceLinkField = Field(..., description="数据源链接字段")
    sqlExecutionResult: SqlExecutionResult = Field(..., description="SQL执行结果")
    selectedTables: List[TableDataSource] = Field(..., description="选定的表列表")


class DataSourceLinkResponse(BaseModel):
    """数据源链接响应"""

    link_field: str
    dataSourceId: str
    fields_info: List[dict]
    data_rows: List[dict]


class LinkedDataQueryColumn(BaseModel):
    """链接数据查询列信息"""

    column_name: str
    column_description: Optional[str] = None
    children_columns: Optional[List["LinkedDataQueryColumn"]] = None


class LinkedDataQueryRequest(BaseModel):
    """链接数据查询请求"""

    primaryDataSourceResult: dict = Field(..., description="主数据源查询结果")
    noPrimaryDataSource: List[dict] = Field(..., description="非主数据源列表")


class LinkedDataQueryResponse(BaseModel):
    """链接数据查询响应"""

    rows: List[dict] = Field(default_factory=list, description="合并后的数据行")
    columns: List[LinkedDataQueryColumn] = Field(default_factory=list, description="合并后的列信息")
    compress_data: dict = Field(default_factory=dict, description="压缩格式的数据")
    message: str = Field(default="查询成功", description="处理消息")


LinkedDataQueryColumn.update_forward_refs()
