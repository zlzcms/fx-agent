#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_recommended_question import recommended_question_dao
from backend.app.admin.model.recommended_question import RecommendedQuestion
from backend.app.admin.schema.recommended_question import (
    CreateRecommendedQuestionParam,
    UpdateRecommendedQuestionParam,
)


class RecommendedQuestionService:
    """推荐问法服务"""

    def get_select(
        self, *, title: str | None = None, status: int | None = None, is_default: bool | None = None
    ) -> Select:
        """获取推荐问法列表查询条件"""
        return recommended_question_dao.get_select(title=title, status=status, is_default=is_default)

    async def get_questions_by_roles(
        self,
        db: AsyncSession,
        role_ids: list[int],
        limit: int = 3,
    ) -> Sequence[RecommendedQuestion]:
        """根据角色获取推荐问法"""
        return await recommended_question_dao.get_questions_by_roles(db, role_ids, limit)

    async def get_recommended_question(
        self,
        db: AsyncSession,
        *,
        pk: int,
    ) -> RecommendedQuestion | None:
        """获取推荐问法详情"""
        return await recommended_question_dao.get(db, pk)

    async def get_recommended_questions(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RecommendedQuestion]:
        """获取推荐问法列表"""
        return await recommended_question_dao.get_multi_by_status(db, skip=skip, limit=limit)

    async def create_recommended_question(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateRecommendedQuestionParam,
    ) -> RecommendedQuestion:
        """创建推荐问法"""
        return await recommended_question_dao.create(db, obj_in=obj_in)

    async def update_recommended_question(
        self,
        db: AsyncSession,
        *,
        pk: int,
        obj_in: UpdateRecommendedQuestionParam,
    ) -> RecommendedQuestion | None:
        """更新推荐问法"""
        return await recommended_question_dao.update(db, pk=pk, obj_in=obj_in)

    async def delete_recommended_question(
        self,
        db: AsyncSession,
        *,
        pk: int,
    ) -> int:
        """删除推荐问法"""
        return await recommended_question_dao.remove(db, pk=pk)

    async def delete_recommended_questions(
        self,
        db: AsyncSession,
        *,
        pks: list[int],
    ) -> int:
        """批量删除推荐问法"""
        return await recommended_question_dao.remove_multi(db, pks=pks)


recommended_question_service = RecommendedQuestionService()
