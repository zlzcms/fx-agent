# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:41:41
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-21 17:22:24

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.assistant_type import AssistantType
from backend.app.admin.schema.assistant_type import CreateAssistantTypeParams, UpdateAssistantTypeParams


class CRUDAssistantType(CRUDPlus[AssistantType]):
    """助手类型CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[AssistantType]:
        """根据ID获取助手类型"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AssistantType]:
        """根据名称获取助手类型"""
        result = await db.execute(
            select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_list(
        self, db: AsyncSession, *, name: Optional[str] = None, page: int = 1, size: int = 10
    ) -> tuple[Sequence[AssistantType], int]:
        """获取助手类型分页列表"""
        query = select(self.model).where(self.model.deleted_at.is_(None))
        count_query = select(self.model).where(self.model.deleted_at.is_(None))

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        # 分页查询
        query = query.order_by(self.model.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        return result.scalars().all(), total

    async def get_all(self, db: AsyncSession) -> Sequence[AssistantType]:
        """获取所有助手类型"""
        result = await db.execute(select(self.model).where(self.model.deleted_at.is_(None)).order_by(self.model.name))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateAssistantTypeParams) -> AssistantType:
        """创建助手类型"""
        # 生成UUID作为主键
        assistant_type_id = str(uuid.uuid4())

        db_obj = self.model(id=assistant_type_id, name=obj_in.name)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: AssistantType, obj_in: UpdateAssistantTypeParams
    ) -> AssistantType:
        """更新助手类型"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除助手类型"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除助手类型"""
        result = await db.execute(
            select(self.model).where(and_(self.model.id.in_(ids), self.model.deleted_at.is_(None)))
        )
        db_objs = result.scalars().all()

        deleted_count = 0
        for db_obj in db_objs:
            db_obj.deleted_at = datetime.now()
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def check_name_exists(self, db: AsyncSession, *, name: str, exclude_id: Optional[str] = None) -> bool:
        """检查助手类型名称是否已存在"""
        query = select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None


crud_assistant_type = CRUDAssistantType(AssistantType)
