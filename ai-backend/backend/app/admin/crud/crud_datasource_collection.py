# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 12:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-13 12:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.datasource_collection import DataSourceCollection
from backend.app.admin.schema.datasource_collection import (
    DataSourceCollectionCreate,
    DataSourceCollectionUpdate,
)


class CRUDDataSourceCollection(CRUDPlus[DataSourceCollection]):
    """数据源集合CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[DataSourceCollection]:
        """根据ID获取集合记录"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[DataSourceCollection]:
        """根据集合名称获取记录"""
        result = await db.execute(
            select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_by_query_name(self, db: AsyncSession, *, query_name: str) -> Optional[DataSourceCollection]:
        """根据查询名称获取记录"""
        result = await db.execute(
            select(self.model).where(and_(self.model.query_name == query_name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_list(
        self, db: AsyncSession, *, status: Optional[bool] = None, query_name: Optional[str] = None
    ) -> Sequence[DataSourceCollection]:
        """获取集合列表"""
        query = select(self.model).where(self.model.deleted_at.is_(None))

        if status is not None:
            query = query.where(self.model.status == status)

        if query_name is not None:
            query = query.where(self.model.query_name.ilike(f"%{query_name}%"))

        query = query.order_by(self.model.created_time.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: DataSourceCollectionCreate) -> DataSourceCollection:
        """创建集合"""
        collection_id = f"dc_{uuid.uuid4().hex[:8]}"
        db_obj = self.model(
            id=collection_id,
            name=obj_in.name,
            description=obj_in.description,
            status=obj_in.status,
            query_name=obj_in.query_name,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: DataSourceCollection, obj_in: DataSourceCollectionUpdate
    ) -> DataSourceCollection:
        """更新集合"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除集合"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def create_or_get(self, db: AsyncSession, *, obj_in: DataSourceCollectionCreate) -> DataSourceCollection:
        """创建或获取集合（如果名称已存在则返回现有集合）"""
        # 先尝试获取现有集合
        existing = await self.get_by_name(db, name=obj_in.name)
        if existing:
            return existing

        # 创建新集合
        return await self.create(db, obj_in=obj_in)


crud_datasource_collection = CRUDDataSourceCollection(DataSourceCollection)
