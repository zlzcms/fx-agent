# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-14 13:39:14
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-19 11:42:26

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.ai_model import AIModel
from backend.app.admin.schema.ai_model import CreateAIModelParams, ModelTypeEnum, UpdateAIModelParams


class CRUDAIModel(CRUDPlus[AIModel]):
    """AI模型CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[AIModel]:
        """根据ID获取AI模型"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AIModel]:
        """根据名称获取AI模型"""
        result = await db.execute(
            select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        model_type: Optional[ModelTypeEnum] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[Sequence[AIModel], int]:
        """获取AI模型分页列表"""
        query = select(self.model).where(self.model.deleted_at.is_(None))
        count_query = select(self.model).where(self.model.deleted_at.is_(None))

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))
        if model_type:
            conditions.append(self.model.model_type == model_type)
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

    async def get_all_enabled(self, db: AsyncSession) -> Sequence[AIModel]:
        """获取所有启用的AI模型"""
        result = await db.execute(
            select(self.model)
            .where(self.model.status == True, self.model.deleted_at.is_(None))
            .order_by(self.model.created_time.desc())
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateAIModelParams) -> AIModel:
        """创建AI模型"""
        import uuid

        # 生成UUID作为模型ID
        model_id = str(uuid.uuid4())

        # 加密存储API Key（这里先简单处理，实际应该使用加密算法）
        encrypted_api_key = obj_in.api_key  # TODO: 实现加密存储

        db_obj = self.model(
            id=model_id,
            name=obj_in.name,
            api_key=encrypted_api_key,
            base_url=obj_in.base_url,
            model_type=obj_in.model_type,
            model=obj_in.model,
            temperature=obj_in.temperature,
            status=obj_in.status,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: AIModel, obj_in: UpdateAIModelParams) -> AIModel:
        """更新AI模型"""
        update_data = obj_in.model_dump(exclude_unset=True)

        # 如果更新API Key，需要重新加密
        if "api_key" in update_data:
            update_data["api_key"] = update_data["api_key"]  # TODO: 实现加密存储

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除AI模型"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除AI模型"""
        result = await db.execute(
            select(self.model).where(and_(self.model.id.in_(ids), self.model.deleted_at.is_(None)))
        )
        db_objs = result.scalars().all()

        deleted_count = 0
        for db_obj in db_objs:
            # TODO: 检查模型是否被其他功能使用
            db_obj.deleted_at = datetime.now()
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def update_status(self, db: AsyncSession, *, id: str, status: bool) -> Optional[AIModel]:
        """更新AI模型状态"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()

        if db_obj:
            db_obj.status = status
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    async def check_name_exists(self, db: AsyncSession, *, name: str, exclude_id: Optional[str] = None) -> bool:
        """检查模型名称是否已存在"""
        query = select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None


crud_ai_model = CRUDAIModel(AIModel)
