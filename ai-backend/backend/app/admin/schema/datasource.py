# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 12:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 12:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pydantic import Field

from backend.common.schema import SchemaBase


class DataSourceListItem(SchemaBase):
    """数据源集合列表项Schema"""

    # 集合信息
    id: str = Field(..., description="集合ID")
    collection_name: str = Field(..., description="集合名称")
    collection_description: Optional[str] = Field(None, description="集合描述")
    query_name: Optional[str] = Field(None, description="查询名称")
    status: bool = Field(..., description="集合状态")
    data_sources_count: int = Field(0, description="数据源总数")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
