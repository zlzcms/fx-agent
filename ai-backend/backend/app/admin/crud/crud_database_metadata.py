# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:49:50
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-16 15:37:04
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.database_metadata import DatabaseMetadata
from backend.app.admin.schema.database_metadata import DatabaseTreeNodeCreate


class CRUDDatabaseMetadata(CRUDPlus[DatabaseMetadata]):
    """数据库元数据CRUD操作"""

    async def get_by_metadata_id(self, db: AsyncSession, *, metadata_id: str) -> Optional[DatabaseMetadata]:
        """根据元数据ID获取记录"""
        result = await db.execute(select(self.model).where(self.model.metadata_id == metadata_id))
        return result.scalars().first()

    async def get_by_type(self, db: AsyncSession, *, type_name: str) -> Sequence[DatabaseMetadata]:
        """根据类型获取记录列表"""
        result = await db.execute(select(self.model).where(self.model.type == type_name))
        return result.scalars().all()

    async def get_by_parent_id(self, db: AsyncSession, *, parent_id: Optional[str]) -> Sequence[DatabaseMetadata]:
        """根据父ID获取子节点列表"""
        if parent_id is None:
            result = await db.execute(select(self.model).where(self.model.parent_id.is_(None)))
        else:
            result = await db.execute(select(self.model).where(self.model.parent_id == parent_id))
        return result.scalars().all()

    async def get_tree_structure(
        self,
        db: AsyncSession,
        *,
        database_name: Optional[str] = None,
        include_tables: bool = True,
        include_fields: bool = True,
    ) -> Sequence[DatabaseMetadata]:
        """获取树形结构数据"""
        query = select(self.model)

        # 构建查询条件
        conditions = []

        if database_name:
            # 如果指定了数据库名，只获取该数据库及其子节点
            conditions.append(and_(self.model.type == "database", self.model.name == database_name))
            if include_tables:
                conditions.append(and_(self.model.type == "table", self.model.parent_id == f"db_{database_name}"))
            if include_fields and include_tables:
                # 获取该数据库下所有表的字段
                subquery = select(DatabaseMetadata.metadata_id).where(
                    and_(DatabaseMetadata.type == "table", DatabaseMetadata.parent_id == f"db_{database_name}")
                )
                conditions.append(and_(self.model.type == "field", self.model.parent_id.in_(subquery)))
        else:
            # 获取所有数据
            conditions.append(self.model.type == "database")
            if include_tables:
                conditions.append(self.model.type == "table")
            if include_fields:
                conditions.append(self.model.type == "field")

        if conditions:
            from sqlalchemy import or_

            query = query.where(or_(*conditions))

        query = query.order_by(self.model.type, self.model.name)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_databases(self, db: AsyncSession) -> Sequence[DatabaseMetadata]:
        """获取所有数据库列表"""
        result = await db.execute(select(self.model).where(self.model.type == "database").order_by(self.model.name))
        return result.scalars().all()

    async def get_tables_with_fields(self, db: AsyncSession, *, database_name: str) -> Sequence[DatabaseMetadata]:
        """获取指定数据库的表和字段信息"""
        db_id = f"db_{database_name}"

        # 获取表信息
        tables_query = select(self.model).where(and_(self.model.type == "table", self.model.parent_id == db_id))

        # 获取字段信息
        fields_query = select(self.model).where(
            and_(self.model.type == "field", self.model.parent_id.like(f"table_{database_name}_%"))
        )

        # 合并查询结果
        from sqlalchemy import union_all

        combined_query = union_all(tables_query, fields_query).order_by("type", "name")

        result = await db.execute(combined_query)
        return result.scalars().all()

    async def get_table_fields(
        self, db: AsyncSession, *, database_name: str, table_name: str
    ) -> Sequence[DatabaseMetadata]:
        """获取指定表的字段信息"""
        table_id = f"table_{database_name}_{table_name}"

        result = await db.execute(
            select(self.model)
            .where(and_(self.model.type == "field", self.model.parent_id == table_id))
            .order_by(self.model.name)
        )
        return result.scalars().all()

    async def batch_update_descriptions(self, db: AsyncSession, *, updates: List[dict]) -> int:
        """批量更新描述信息"""
        updated_count = 0

        for update_data in updates:
            metadata_id = update_data["id"]
            description = update_data["description"]

            # 更新记录
            result = await db.execute(select(self.model).where(self.model.metadata_id == metadata_id))
            record = result.scalars().first()

            if record:
                record.description = description
                updated_count += 1

        await db.commit()
        return updated_count

    async def delete_by_database_name(self, db: AsyncSession, *, database_name: str) -> int:
        """删除指定数据库的所有元数据"""
        from sqlalchemy import delete

        # 删除字段
        fields_result = await db.execute(
            delete(self.model).where(self.model.parent_id.like(f"table_{database_name}_%"))
        )

        # 删除表
        tables_result = await db.execute(
            delete(self.model).where(and_(self.model.type == "table", self.model.parent_id == f"db_{database_name}"))
        )

        # 删除数据库
        db_result = await db.execute(
            delete(self.model).where(
                and_(self.model.type == "database", self.model.metadata_id == f"db_{database_name}")
            )
        )

        await db.commit()
        return fields_result.rowcount + tables_result.rowcount + db_result.rowcount

    async def create_or_update(self, db: AsyncSession, *, obj_in: DatabaseTreeNodeCreate) -> DatabaseMetadata:
        """创建或更新元数据记录"""
        # 先尝试获取现有记录
        existing = await self.get_by_metadata_id(db, metadata_id=obj_in.id)

        if existing:
            # 更新现有记录，但保留description字段
            update_data = obj_in.model_dump(exclude_unset=True, exclude={"description"})
            for field, value in update_data.items():
                if hasattr(existing, field) and field != "id":  # 不更新id字段
                    setattr(existing, field, value)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # 创建新记录，使用传入的所有数据包括description
            db_obj = self.model(
                metadata_id=obj_in.id,
                name=obj_in.name,
                type=obj_in.type,
                description=obj_in.description,
                parent_id=obj_in.parent_id,
                field_type=obj_in.field_type,
                is_nullable=obj_in.is_nullable,
                default_value=obj_in.default_value,
                table_rows=obj_in.table_rows,
                table_size=obj_in.table_size,
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj


crud_database_metadata = CRUDDatabaseMetadata(DatabaseMetadata)
