# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-19 11:36:53
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-20 18:50:53
"""
AI 助手关联关系 CRUD 操作
"""

from typing import Any, List, Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.ai_assistant import (
    AIAssistantNotification,
    AIAssistantPermission,
    AIAssistantPersonnel,
    AIAssistantTemplate,
)
from backend.database.db import uuid4_str as get_uuid


class CRUDAIAssistantPersonnel(CRUDPlus[AIAssistantPersonnel]):
    """AI助手-人员关联 CRUD"""

    async def create_relations(
        self, db: AsyncSession, *, assistant_id: str, personnel_data: List[Any]
    ) -> List[AIAssistantPersonnel]:
        """创建助手-人员关联关系"""
        from datetime import datetime

        relations = []
        for personnel in personnel_data:
            try:
                # 创建关联对象（不包含init=False的字段）
                relation = AIAssistantPersonnel()

                # 设置init=False的字段
                relation.id = get_uuid()
                relation.assistant_id = assistant_id

                # 根据personnel的类型进行不同的处理
                if isinstance(personnel, dict):
                    # 如果是字典类型，使用字典访问方式
                    relation.personnel_id = personnel["personnel_id"]
                    relation.username = personnel["username"]
                    relation.email = personnel["email"]
                else:
                    # 如果是对象类型，使用属性访问方式
                    relation.personnel_id = personnel.personnel_id
                    relation.username = personnel.username
                    relation.email = personnel.email

                relation.created_time = datetime.now()

                # 直接添加关系，不再检查ai_personnel表
                # 因为ai_personnel表已经废弃，我们直接使用传入的人员数据
                db.add(relation)
                relations.append(relation)
            except Exception as e:
                print(f"创建助手-人员关联关系失败: {e}")
                # 继续处理下一个，不中断整个流程
                continue

        # 不在这里commit，让上层事务统一commit
        return relations

    async def update_relations(
        self, db: AsyncSession, *, assistant_id: str, personnel_data: List[Any]
    ) -> List[AIAssistantPersonnel]:
        """更新助手-人员关联关系"""
        # 先删除现有关联
        await self.delete_by_assistant(db, assistant_id=assistant_id)

        # 创建新关联
        if personnel_data:
            return await self.create_relations(db, assistant_id=assistant_id, personnel_data=personnel_data)
        return []

    async def delete_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> int:
        """删除指定助手的所有人员关联"""
        stmt = delete(AIAssistantPersonnel).where(AIAssistantPersonnel.assistant_id == assistant_id)
        result = await db.execute(stmt)
        # 不在这里commit，让上层事务统一commit
        return result.rowcount

    async def get_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> Sequence[AIAssistantPersonnel]:
        """获取指定助手的所有人员关联"""
        stmt = select(AIAssistantPersonnel).where(AIAssistantPersonnel.assistant_id == assistant_id)

        result = await db.execute(stmt)
        return result.scalars().all()


class CRUDAIAssistantNotification(CRUDPlus[AIAssistantNotification]):
    """AI助手-通知方式关联 CRUD"""

    async def create_relations(
        self, db: AsyncSession, *, assistant_id: str, notification_ids: List[str]
    ) -> List[AIAssistantNotification]:
        """创建助手-通知方式关联关系"""
        from datetime import datetime

        relations = []
        for notification_id in notification_ids:
            # 创建关联对象（不包含init=False的字段）
            relation = AIAssistantNotification()

            # 设置init=False的字段
            relation.id = get_uuid()
            relation.assistant_id = assistant_id
            relation.notification_id = notification_id
            relation.created_time = datetime.now()

            db.add(relation)
            relations.append(relation)

        # 不在这里commit，让上层事务统一commit
        return relations

    async def delete_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> int:
        """删除指定助手的所有通知方式关联"""
        stmt = delete(AIAssistantNotification).where(AIAssistantNotification.assistant_id == assistant_id)
        result = await db.execute(stmt)
        # 不在这里commit，让上层事务统一commit
        return result.rowcount

    async def update_relations(
        self, db: AsyncSession, *, assistant_id: str, notification_ids: List[str]
    ) -> List[AIAssistantNotification]:
        """更新助手-通知方式关联关系"""
        # 先删除现有关联
        await self.delete_by_assistant(db, assistant_id=assistant_id)

        # 创建新关联
        if notification_ids:
            return await self.create_relations(db, assistant_id=assistant_id, notification_ids=notification_ids)
        return []

    async def get_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> Sequence[AIAssistantNotification]:
        """获取指定助手的所有通知方式关联"""
        stmt = (
            select(AIAssistantNotification)
            .where(AIAssistantNotification.assistant_id == assistant_id)
            .options(selectinload(AIAssistantNotification.notification_method))
        )

        result = await db.execute(stmt)
        return result.scalars().all()


class CRUDAIAssistantPermission(CRUDPlus[AIAssistantPermission]):
    """AI助手-数据权限关联 CRUD"""

    async def create_relations(
        self, db: AsyncSession, *, assistant_id: str, permission_ids: List[str]
    ) -> List[AIAssistantPermission]:
        """创建助手-数据权限关联关系"""
        from datetime import datetime

        relations = []
        for permission_id in permission_ids:
            # 创建关联对象（不包含init=False的字段）
            relation = AIAssistantPermission()

            # 设置init=False的字段
            relation.id = get_uuid()
            relation.assistant_id = assistant_id
            relation.permission_id = permission_id
            relation.created_time = datetime.now()

            db.add(relation)
            relations.append(relation)

        # 不在这里commit，让上层事务统一commit
        return relations

    async def delete_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> int:
        """删除指定助手的所有数据权限关联"""
        stmt = delete(AIAssistantPermission).where(AIAssistantPermission.assistant_id == assistant_id)
        result = await db.execute(stmt)
        # 不在这里commit，让上层事务统一commit
        return result.rowcount

    async def update_relations(
        self, db: AsyncSession, *, assistant_id: str, permission_ids: List[str]
    ) -> List[AIAssistantPermission]:
        """更新助手-数据权限关联关系"""
        # 先删除现有关联
        await self.delete_by_assistant(db, assistant_id=assistant_id)

        # 创建新关联
        if permission_ids:
            return await self.create_relations(db, assistant_id=assistant_id, permission_ids=permission_ids)
        return []

    async def get_by_assistant(self, db: AsyncSession, *, assistant_id: str) -> Sequence[AIAssistantPermission]:
        """获取指定助手的所有数据权限关联"""
        stmt = (
            select(AIAssistantPermission)
            .where(AIAssistantPermission.assistant_id == assistant_id)
            .options(selectinload(AIAssistantPermission.permission))
        )

        result = await db.execute(stmt)
        return result.scalars().all()


class CRUDAIAssistantTemplate(CRUDPlus[AIAssistantTemplate]):
    """AI助手模板CRUD操作"""

    async def get_by_assistant_id(self, db: AsyncSession, *, assistant_id: str) -> Optional[AIAssistantTemplate]:
        """根据助手ID获取模板"""
        stmt = select(self.model).where(self.model.assistant_id == assistant_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_template(
        self, db: AsyncSession, *, assistant_id: str, is_open: bool = True
    ) -> AIAssistantTemplate:
        """创建助手模板记录"""
        from datetime import datetime

        # 创建模板对象（不包含init=False的字段）
        db_obj = self.model()

        # 设置init=False的字段
        db_obj.id = get_uuid()
        db_obj.assistant_id = assistant_id
        db_obj.is_open = is_open
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        # 不在这里commit，让上层事务统一commit
        return db_obj

    async def delete_by_assistant_id(self, db: AsyncSession, *, assistant_id: str) -> bool:
        """根据助手ID删除模板"""
        stmt = select(self.model).where(self.model.assistant_id == assistant_id)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if db_obj:
            await db.delete(db_obj)
            # 不在这里commit，让上层事务统一commit
            return True
        return False

    async def toggle_template_status(
        self, db: AsyncSession, *, assistant_id: str, is_open: bool
    ) -> Optional[AIAssistantTemplate]:
        """切换模板开启状态"""
        stmt = select(self.model).where(self.model.assistant_id == assistant_id)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if db_obj:
            db_obj.is_open = is_open
            # 不在这里commit，让上层事务统一commit
            return db_obj
        return None


# 创建CRUD实例
crud_ai_assistant_personnel = CRUDAIAssistantPersonnel(AIAssistantPersonnel)
crud_ai_assistant_notification = CRUDAIAssistantNotification(AIAssistantNotification)
crud_ai_assistant_permission = CRUDAIAssistantPermission(AIAssistantPermission)
crud_ai_assistant_template = CRUDAIAssistantTemplate(AIAssistantTemplate)
