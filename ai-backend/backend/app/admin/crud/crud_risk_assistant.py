#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.risk_assistant import RiskAssistant
from backend.app.admin.schema.risk_assistant import CreateRiskAssistantParams, UpdateRiskAssistantParams


class CRUDRiskAssistant(CRUDPlus[RiskAssistant]):
    """风控助手CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[RiskAssistant]:
        """根据ID获取风控助手"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_risk_type(self, db: AsyncSession, *, risk_type: str) -> Optional[RiskAssistant]:
        """根据风险类型获取风控助手"""
        result = await db.execute(
            select(self.model).where(and_(self.model.risk_type == risk_type, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[RiskAssistant]:
        """根据名称获取风控助手"""
        result = await db.execute(
            select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[Sequence[RiskAssistant], int]:
        """获取风控助手分页列表"""
        query = select(self.model).where(self.model.deleted_at.is_(None))
        count_query = select(self.model).where(self.model.deleted_at.is_(None))

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))
        if ai_model_id:
            conditions.append(self.model.ai_model_id == ai_model_id)
        if status is not None:
            conditions.append(self.model.status == status)

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

    async def get_all(self, db: AsyncSession) -> Sequence[RiskAssistant]:
        """获取所有风控助手"""
        result = await db.execute(
            select(self.model).where(self.model.deleted_at.is_(None)).order_by(self.model.name.asc())
        )
        return result.scalars().all()

    async def get_all_active(self, db: AsyncSession) -> Sequence[RiskAssistant]:
        """获取所有活跃的风控助手"""
        result = await db.execute(
            select(self.model)
            .where(and_(self.model.status, self.model.deleted_at.is_(None)))
            .order_by(self.model.name.asc())
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateRiskAssistantParams) -> RiskAssistant:
        """创建风控助手"""
        # 生成UUID作为主键
        assistant_id = str(uuid.uuid4())

        db_obj = self.model(
            id=assistant_id,
            name=obj_in.name,
            ai_model_id=obj_in.ai_model_id,
            role=obj_in.role,
            background=obj_in.background,
            task_prompt=obj_in.task_prompt,
            variable_config=obj_in.variable_config,
            report_config=obj_in.report_config,
            status=obj_in.status,
            risk_type=obj_in.risk_type,
            setting=obj_in.setting,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: RiskAssistant, obj_in: UpdateRiskAssistantParams
    ) -> RiskAssistant:
        """更新风控助手"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除风控助手"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除风控助手"""
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
        """检查风控助手名称是否已存在"""
        query = select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None

    async def get_by_ai_model(self, db: AsyncSession, *, ai_model_id: str) -> Sequence[RiskAssistant]:
        """根据AI模型ID获取风控助手列表"""
        result = await db.execute(
            select(self.model).where(and_(self.model.ai_model_id == ai_model_id, self.model.deleted_at.is_(None)))
        )
        return result.scalars().all()

    async def update_status(self, db: AsyncSession, *, id: str, status: bool) -> Optional[RiskAssistant]:
        """更新风控助手状态"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.status = status
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None


crud_risk_assistant = CRUDRiskAssistant(RiskAssistant)
