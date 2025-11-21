# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 12:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 12:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from backend.common.schema import SchemaBase

if TYPE_CHECKING:
    from backend.app.admin.schema.datasource import DataSourceListItem


class DataSourceCollectionBase(SchemaBase):
    """数据源集合基础Schema"""

    name: str = Field(..., description="集合名称")
    description: Optional[str] = Field(None, description="集合描述")
    status: bool = Field(True, description="启用状态")
    query_name: str = Field(..., description="查询名称")


class DataSourceCollectionCreate(DataSourceCollectionBase):
    """创建数据源集合Schema"""

    pass


class DataSourceCollectionUpdate(SchemaBase):
    """更新数据源集合Schema"""

    name: Optional[str] = Field(None, description="集合名称")
    description: Optional[str] = Field(None, description="集合描述")
    status: Optional[bool] = Field(None, description="启用状态")
    query_name: Optional[str] = Field(None, description="查询名称")


class DataSourceCollectionInDB(DataSourceCollectionBase):
    """数据库中的数据源集合Schema"""

    id: str = Field(..., description="集合ID")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")


class DataSourceCollectionListItem(DataSourceCollectionInDB):
    """数据源集合列表项Schema"""

    datasource_count: Optional[int] = Field(None, description="包含的数据源数量")


class DataSourceCollectionDetail(DataSourceCollectionInDB):
    """数据源集合详情Schema"""

    datasources: List["DataSourceListItem"] = Field(default_factory=list, description="包含的数据源列表")
