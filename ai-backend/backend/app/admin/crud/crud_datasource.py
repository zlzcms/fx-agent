# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-13 10:43:48
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 19:50:12
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.datasource import DataSource
from backend.app.admin.schema.datasource import DataSourceCreate, DataSourceUpdate


class CRUDDataSource(CRUDPlus[DataSource]):
    """数据源CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[DataSource]:
        """根据ID获取数据源"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.collection))
            .where(and_(self.model.id == id, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_by_database_and_table(
        self, db: AsyncSession, *, database_name: str, table_name: str
    ) -> Optional[DataSource]:
        """根据数据库名和表名获取数据源"""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.database_name == database_name,
                    self.model.table_name == table_name,
                    self.model.deleted_at.is_(None),
                )
            )
        )
        return result.scalars().first()

    async def get_list(
        self, db: AsyncSession, *, database_name: Optional[str] = None, collection_id: Optional[str] = None
    ) -> Sequence[DataSource]:
        """获取数据源列表"""
        query = select(self.model).options(selectinload(self.model.collection)).where(self.model.deleted_at.is_(None))

        conditions = []
        if database_name:
            conditions.append(self.model.database_name == database_name)
        if collection_id:
            conditions.append(self.model.collection_id == collection_id)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(self.model.created_time.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: DataSourceCreate) -> DataSource:
        """创建数据源"""
        # 生成更短的唯一数据源ID
        import uuid

        unique_id = uuid.uuid4().hex[:12]  # 使用12位随机字符串
        db_obj = self.model(
            id=f"ds_{unique_id}",
            collection_id=obj_in.collection_id,
            database_name=obj_in.database_name,
            table_name=obj_in.table_name,
            description=obj_in.description,
            data_count=obj_in.data_count,
            relation_field=obj_in.relation_field,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: DataSource, obj_in: DataSourceUpdate) -> DataSource:
        """更新数据源"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "status":  # status 字段不属于数据源模型
                setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除数据源"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def batch_create(self, db: AsyncSession, *, objs_in: List[DataSourceCreate]) -> List[DataSource]:
        """批量创建数据源"""
        import uuid

        db_objs = []
        for obj_in in objs_in:
            unique_id = uuid.uuid4().hex[:12]  # 使用12位随机字符串
            db_obj = self.model(
                id=f"ds_{unique_id}",
                collection_id=obj_in.collection_id,
                database_name=obj_in.database_name,
                table_name=obj_in.table_name,
                description=obj_in.description,
                data_count=obj_in.data_count,
                relation_field=obj_in.relation_field,
            )
            db_objs.append(db_obj)

        db.add_all(db_objs)
        await db.commit()

        for db_obj in db_objs:
            await db.refresh(db_obj)

        return db_objs


crud_datasource = CRUDDataSource(DataSource)
