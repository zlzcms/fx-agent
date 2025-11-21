# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 12:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 12:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_datasource_collection import crud_datasource_collection
from backend.app.admin.schema.datasource_collection import (
    DataSourceCollectionCreate,
    DataSourceCollectionListItem,
)


class DataSourceCollectionService:
    """数据源集合服务"""

    async def get_list(
        self, db: AsyncSession, *, status: Optional[bool] = None, query_name: Optional[str] = None
    ) -> List[DataSourceCollectionListItem]:
        """获取集合列表"""
        records = await crud_datasource_collection.get_list(db, status=status, query_name=query_name)

        return [
            DataSourceCollectionListItem(
                id=record.id,
                name=record.name,
                description=record.description,
                query_name=record.query_name,
                status=record.status,
                created_time=record.created_time,
                updated_time=record.updated_time,
                datasource_count=len(record.datasources) if record.datasources else 0,
            )
            for record in records
        ]

    async def create_or_get(
        self, db: AsyncSession, *, name: str, query_name: str, description: Optional[str] = None, status: bool = True
    ) -> str:
        """创建或获取集合，返回集合ID"""
        collection_create = DataSourceCollectionCreate(
            name=name, description=description, status=status, query_name=query_name
        )

        collection = await crud_datasource_collection.create_or_get(db, obj_in=collection_create)
        return collection.id


datasource_collection_service = DataSourceCollectionService()
