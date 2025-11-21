# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:58:04
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 13:32:21

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.risk_level import RiskLevel
from backend.app.admin.schema.risk_level import CreateRiskLevelParams, UpdateRiskLevelParams


class CRUDRiskLevel(CRUDPlus[RiskLevel]):
    """风控等级CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[RiskLevel]:
        """根据ID获取风控等级"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[RiskLevel]:
        """根据名称获取风控等级"""
        result = await db.execute(
            select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[Sequence[RiskLevel], int]:
        """获取风控等级分页列表"""
        query = select(self.model).where(self.model.deleted_at.is_(None))
        count_query = select(self.model).where(self.model.deleted_at.is_(None))

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))
        if min_score is not None:
            conditions.append(self.model.end_score >= min_score)
        if max_score is not None:
            conditions.append(self.model.start_score <= max_score)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        # 分页查询
        query = query.order_by(self.model.start_score.asc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        return result.scalars().all(), total

    async def get_all(self, db: AsyncSession) -> Sequence[RiskLevel]:
        """获取所有风控等级"""
        result = await db.execute(
            select(self.model).where(self.model.deleted_at.is_(None)).order_by(self.model.start_score.asc())
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateRiskLevelParams) -> RiskLevel:
        """创建风控等级"""
        # 生成UUID作为主键
        risk_level_id = str(uuid.uuid4())

        db_obj = self.model(
            id=risk_level_id,
            name=obj_in.name,
            start_score=obj_in.start_score,
            end_score=obj_in.end_score,
            description=obj_in.description,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: RiskLevel, obj_in: UpdateRiskLevelParams) -> RiskLevel:
        """更新风控等级"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除风控等级"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除风控等级"""
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
        """检查风控等级名称是否已存在"""
        query = select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None

    async def check_score_range_overlap(
        self, db: AsyncSession, *, start_score: int, end_score: int, exclude_id: Optional[str] = None
    ) -> bool:
        """检查分数范围是否与现有记录重叠"""
        query = select(self.model).where(
            and_(
                # 检查是否有重叠：排除边界相接的情况，只有真正重叠才算重叠
                ((self.model.start_score < start_score) & (start_score < self.model.end_score))
                | ((self.model.start_score < end_score) & (end_score < self.model.end_score))
                | ((start_score < self.model.start_score) & (self.model.end_score < end_score)),
                self.model.deleted_at.is_(None),
            )
        )

        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None

    async def get_by_score(self, db: AsyncSession, *, score: float) -> Optional[RiskLevel]:
        """根据分数获取对应的风险等级"""
        query = select(self.model).where(
            and_(self.model.start_score <= score, self.model.end_score > score, self.model.deleted_at.is_(None))
        )
        result = await db.execute(query)
        return result.scalars().first()


crud_risk_level = CRUDRiskLevel(RiskLevel)
