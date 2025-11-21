#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.risk_tag import RiskTag
from backend.app.admin.schema.risk_tag import CreateRiskTagParams, UpdateRiskTagParams
from backend.common.enums import RiskType


class CRUDRiskTag(CRUDPlus[RiskTag]):
    """风控标签CRUD操作"""

    async def get(self, db: AsyncSession, *, id: int) -> Optional[RiskTag]:
        """根据ID获取风控标签（排除已删除）"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_risk_type(self, db: AsyncSession, *, risk_type: RiskType) -> Sequence[RiskTag]:
        """根据风控类型获取风控标签（排除已删除）"""
        query = (
            select(self.model)
            .where(and_(self.model.risk_type == risk_type, self.model.deleted_at.is_(None)))
            .order_by(self.model.name.asc())
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        risk_type: Optional[RiskType] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[Sequence[RiskTag], int]:
        """获取风控标签分页列表（排除已删除）"""
        query = select(self.model)

        conditions = [self.model.deleted_at.is_(None)]  # 基础条件：未删除
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))
        if risk_type:
            conditions.append(self.model.risk_type == risk_type)

        if conditions:
            query = query.where(and_(*conditions))

        # 获取总数 - 使用 func.count() 进行高效计数
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.order_by(self.model.risk_type.asc(), self.model.name.asc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        tags = result.scalars().all()

        return tags, total

    async def get_all(self, db: AsyncSession, *, risk_type: Optional[RiskType] = None) -> Sequence[RiskTag]:
        """获取所有风控标签（排除已删除）"""
        query = select(self.model)

        conditions = [self.model.deleted_at.is_(None)]
        if risk_type:
            conditions.append(self.model.risk_type == risk_type)

        query = query.where(and_(*conditions))
        query = query.order_by(self.model.risk_type.asc(), self.model.name.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateRiskTagParams) -> RiskTag:
        """创建风控标签"""
        # 使用自增主键，不需要手动设置ID
        db_obj = self.model(risk_type=obj_in.risk_type, name=obj_in.name, description=obj_in.description)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: RiskTag, obj_in: UpdateRiskTagParams) -> RiskTag:
        """更新风控标签"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)

        # 重新查询以获取数据
        return await self.get(db, id=db_obj.id)

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除风控标签"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除风控标签"""
        result = await db.execute(
            select(self.model).where(and_(self.model.id.in_(ids), self.model.deleted_at.is_(None)))
        )
        db_objs = result.scalars().all()

        deleted_count = 0
        current_time = datetime.now()
        for db_obj in db_objs:
            db_obj.deleted_at = current_time
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def check_name_exists(
        self, db: AsyncSession, *, name: str, risk_type: RiskType, exclude_id: Optional[str] = None
    ) -> bool:
        """检查风控标签名称在指定风控类型下是否已存在（排除已删除）"""
        conditions = [self.model.name == name, self.model.risk_type == risk_type, self.model.deleted_at.is_(None)]
        if exclude_id:
            conditions.append(self.model.id != exclude_id)

        query = select(self.model).where(and_(*conditions))
        result = await db.execute(query)
        return result.scalars().first() is not None

    async def get_by_id_include_deleted(self, db: AsyncSession, *, id: int) -> Optional[RiskTag]:
        """根据ID获取风控标签（包含已删除的标签，用于历史记录查询）"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_by_ids_include_deleted(self, db: AsyncSession, *, ids: List[int]) -> Sequence[RiskTag]:
        """根据ID列表获取风控标签（包含已删除的标签，用于历史记录查询）"""
        result = await db.execute(select(self.model).where(self.model.id.in_(ids)))
        return result.scalars().all()


crud_risk_tag = CRUDRiskTag(RiskTag)
