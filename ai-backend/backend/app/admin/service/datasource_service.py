# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 10:44:21
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-16 14:34:20
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_datasource_collection import crud_datasource_collection
from backend.app.admin.schema.datasource import (
    DataSourceListItem,
)
from backend.app.admin.schema.datasource_collection import (
    DataSourceCollectionUpdate,
)
from backend.common.pagination import PageData


class DataSourceService:
    """数据源服务"""

    async def get_list(
        self, db: AsyncSession, *, collection_name: Optional[str] = None, status: Optional[bool] = None
    ) -> List[DataSourceListItem]:
        """获取数据源集合列表"""
        collections = await crud_datasource_collection.get_list(db, status=status)

        result = []
        for collection in collections:
            # 如果指定了 collection_name，进行模糊匹配
            if collection_name and collection_name.lower() not in collection.name.lower():
                continue

            result.append(
                DataSourceListItem(
                    id=collection.id,
                    collection_name=collection.name,
                    collection_description=collection.description,
                    query_name=collection.query_name,
                    status=collection.status,
                    data_sources_count=0,  # 不再计算数据源数量
                    created_time=collection.created_time,
                    updated_time=collection.updated_time,
                )
            )

        return result

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        collection_name: Optional[str] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[DataSourceListItem]:
        """获取分页数据源列表 - 以集合为维度返回"""
        # 获取所有集合记录
        collections = await crud_datasource_collection.get_list(db, status=status)

        result = []
        for collection in collections:
            # 如果指定了 collection_name，进行模糊匹配
            if collection_name and collection_name.lower() not in collection.name.lower():
                continue

            result.append(
                DataSourceListItem(
                    id=collection.id,
                    collection_name=collection.name,
                    collection_description=collection.description,
                    query_name=collection.query_name,
                    status=collection.status,
                    data_sources_count=0,  # 不再计算数据源数量
                    created_time=collection.created_time,
                    updated_time=collection.updated_time,
                )
            )

        # 手动实现分页
        total = len(result)
        start_index = (page - 1) * size
        end_index = start_index + size
        items = result[start_index:end_index]

        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links={
                "first": f"?page=1&size={size}",
                "last": f"?page={total_pages}&size={size}",
                "self": f"?page={page}&size={size}",
                "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
                "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
            },
        )

    async def get_detail(self, db: AsyncSession, *, datasource_id: str) -> Optional[dict]:
        """获取数据源集合详情"""
        # 查询集合
        collection = await crud_datasource_collection.get(db, id=datasource_id)
        if not collection:
            return None

        return {
            "id": collection.id,
            "collection_id": collection.id,
            "collection_name": collection.name,
            "query_name": collection.query_name,
            "collection_description": collection.description,
            "status": collection.status,
            "data_sources_count": 0,  # 不再计算数据源数量
            "created_time": collection.created_time,
            "updated_time": collection.updated_time,
            "datasources": [],  # 空列表，不再查询数据源
            "collection": {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "query_name": collection.query_name,
                "status": collection.status,
                "created_time": collection.created_time,
                "updated_time": collection.updated_time,
            },
        }

    async def update(self, db: AsyncSession, *, datasource_id: str, request: dict) -> Optional[dict]:
        """更新数据源集合"""
        # 查询集合
        collection = await crud_datasource_collection.get(db, id=datasource_id)
        if not collection:
            return None

        # 更新集合信息
        collection_update_data = {}

        if request.get("collection_name") is not None:
            collection_update_data["name"] = request["collection_name"]
        if request.get("collection_description") is not None:
            collection_update_data["description"] = request["collection_description"]
        if request.get("query_name") is not None:
            collection_update_data["query_name"] = request["query_name"]
        if request.get("status") is not None:
            collection_update_data["status"] = request["status"]

        if collection_update_data:
            collection_update = DataSourceCollectionUpdate(**collection_update_data)
            updated_collection = await crud_datasource_collection.update(
                db, db_obj=collection, obj_in=collection_update
            )

            # 返回更新后的集合详情
            return await self.get_detail(db, datasource_id=updated_collection.id)

        # 如果没有更新，返回原始数据
        return await self.get_detail(db, datasource_id=datasource_id)

    async def toggle_status(self, db: AsyncSession, *, datasource_id: str, status: bool) -> Optional[dict]:
        """切换数据源集合状态"""
        # 查询集合
        collection = await crud_datasource_collection.get(db, id=datasource_id)
        if not collection:
            return None

        # 更新状态
        collection_update = DataSourceCollectionUpdate(status=status)
        updated_collection = await crud_datasource_collection.update(db, db_obj=collection, obj_in=collection_update)

        # 返回更新后的集合详情
        return await self.get_detail(db, datasource_id=updated_collection.id)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量删除数据源集合"""
        deleted_count = 0

        for datasource_id in ids:
            # 删除集合
            if await crud_datasource_collection.delete(db, id=datasource_id):
                deleted_count += 1

        return deleted_count

    async def batch_create(self, db: AsyncSession, *, request: dict) -> dict:
        """批量创建数据源集合"""
        from backend.app.admin.schema.datasource_collection import DataSourceCollectionCreate

        # 1. 创建集合
        collection_create = DataSourceCollectionCreate(
            name=request["collection_name"],
            description=request.get("collection_description"),
            status=request.get("status", True),
            query_name=request["query_name"],
        )

        collection = await crud_datasource_collection.create(db, obj_in=collection_create)

        # 返回结果
        return {
            "collection_id": collection.id,
            "collection_name": collection.name,
            "created_count": 0,  # 不再创建数据源
            "datasources": [],  # 空列表，不再有数据源
        }


datasource_service = DataSourceService()
