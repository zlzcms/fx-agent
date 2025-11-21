#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.recommended_question import RecommendedQuestion


class CRUDRecommendedQuestion(CRUDPlus[RecommendedQuestion]):
    """推荐问法 CRUD"""

    def get_select(self, *, title: str | None = None, status: int | None = None, is_default: bool | None = None):
        """获取推荐问法列表查询条件"""
        conditions = [self.model.deleted_at.is_(None)]

        # 如果没有指定状态，默认只显示正常状态的记录
        if status is not None:
            conditions.append(self.model.status == status)
        else:
            conditions.append(self.model.status == 1)

        # 标题模糊查询
        if title:
            conditions.append(self.model.title.contains(title))

        # 是否默认查询
        if is_default is not None:
            conditions.append(self.model.is_default == is_default)

        return (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.sort_order.asc(), self.model.created_time.desc())
        )

    async def get(self, db: AsyncSession, pk: int) -> RecommendedQuestion | None:
        """获取推荐问法详情"""
        return await self.select_model(db, pk)

    async def get_questions_by_roles(
        self,
        db: AsyncSession,
        role_ids: list[int],
        limit: int = 3,
    ) -> Sequence[RecommendedQuestion]:
        """根据角色获取推荐问法"""

        from sqlalchemy import text

        # 构建角色匹配条件：使用PostgreSQL的JSON操作符检查JSON数组是否包含任一指定角色
        role_conditions = []
        for role_id in role_ids:
            # 使用 JSON_ARRAY_ELEMENTS_TEXT 函数来检查JSON数组中是否包含指定角色ID
            role_conditions.append(
                text(f"EXISTS (SELECT 1 FROM json_array_elements_text(role_ids) AS elem WHERE elem = '{role_id}')")
            )

        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == 1,
                    self.model.deleted_at.is_(None),
                    or_(
                        or_(*role_conditions) if role_conditions else False,  # 包含任一角色
                        self.model.is_default.is_(True),  # 默认问法
                    ),
                )
            )
            .order_by(self.model.sort_order.asc(), self.model.created_time.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi_by_status(
        self,
        db: AsyncSession,
        *,
        status: int = 1,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RecommendedQuestion]:
        """根据状态获取推荐问法列表"""
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == status,
                    self.model.deleted_at.is_(None),
                )
            )
            .order_by(self.model.sort_order.asc(), self.model.created_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: Any) -> RecommendedQuestion:
        """创建推荐问法"""
        data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else dict(obj_in)
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, pk: int, obj_in: Any) -> RecommendedQuestion | None:
        """更新推荐问法"""
        db_obj = await self.select_model(db, pk)
        if not db_obj:
            return None
        data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else dict(obj_in)
        for k, v in data.items():
            setattr(db_obj, k, v)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, pk: int) -> int:
        """软删除推荐问法"""
        # 使用更新语句进行软删除
        stmt = (
            update(self.model)
            .where(self.model.id == pk, self.model.deleted_at.is_(None))
            .values(deleted_at=datetime.now())
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    async def remove_multi(self, db: AsyncSession, *, pks: list[int]) -> int:
        """批量软删除推荐问法"""
        stmt = update(self.model).where(self.model.id.in_(pks)).values(deleted_at=datetime.now())
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0


recommended_question_dao: CRUDRecommendedQuestion = CRUDRecommendedQuestion(RecommendedQuestion)
