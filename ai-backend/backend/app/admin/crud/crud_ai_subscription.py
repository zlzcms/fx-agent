# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 21:45:00
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.ai_subscription import (
    AISubscription,
    AISubscriptionNotification,
    AISubscriptionNotificationMethod,
)
from backend.app.admin.schema.ai_subscription import (
    AISubscriptionCreate,
    AISubscriptionQueryParams,
    AISubscriptionUpdate,
)
from backend.database.db import uuid4_str as get_uuid


class CRUDAISubscription(CRUDPlus[AISubscription]):
    """AI订阅CRUD操作"""

    async def get(
        self, db: AsyncSession, *, id: int, params: Optional[AISubscriptionQueryParams] = None
    ) -> Optional[AISubscription]:
        """获取AI订阅详情，包含关联数据"""
        from backend.app.admin.model.ai_assistant import AIAssistant

        # 构建查询，包含助手信息
        stmt = (
            select(self.model, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, self.model.assistant_id == AIAssistant.id)
            .where(and_(self.model.id == id, self.model.deleted_at.is_(None)))
            .options(
                selectinload(self.model.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )
        if params:
            conditions = []
            if params.assistant_name:
                # 通过关联ai_assistants表进行助手名称的模糊匹配
                conditions.append(AIAssistant.name.ilike(f"%{params.assistant_name}%"))
            if params.status is not None:
                # 过滤订阅状态
                conditions.append(self.model.status == params.status)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        row = result.first()

        if row:
            subscription = row[0]  # AISubscription对象
            assistant_name = row[1]  # 助手名称
            # 动态添加assistant_name属性
            setattr(subscription, "assistant_name", assistant_name)
            return subscription

        return None

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AISubscription]:
        """根据名称获取AI订阅"""
        stmt = select(self.model).where(self.model.name == name, self.model.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self, db: AsyncSession, *, params: Optional[AISubscriptionQueryParams] = None, skip: int = 0, limit: int = 100
    ) -> Sequence[AISubscription]:
        """获取AI订阅列表，包含关联数据和助手名称"""
        from backend.app.admin.model.ai_assistant import AIAssistant

        # 构建基础查询，总是包含助手信息
        stmt = (
            select(self.model, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, self.model.assistant_id == AIAssistant.id)
            .where(self.model.deleted_at.is_(None))
            .options(
                selectinload(self.model.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )

        if params:
            conditions = []
            if params.name:
                conditions.append(self.model.name.ilike(f"%{params.name}%"))

            if params.assistant_name:
                # 通过关联ai_assistants表进行助手名称的模糊匹配
                conditions.append(AIAssistant.name.ilike(f"%{params.assistant_name}%"))
            if params.status is not None:
                # 过滤订阅状态
                conditions.append(self.model.status == params.status)
            if params.responsible_person:
                # 这里需要查询关联表，暂时简化处理
                pass

            if conditions:
                stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.created_time.desc())
        result = await db.execute(stmt)

        # 处理结果，将assistant_name添加到对象中
        subscriptions = []
        for row in result:
            subscription = row[0]  # AISubscription对象
            assistant_name = row[1]  # 助手名称
            # 动态添加assistant_name属性
            setattr(subscription, "assistant_name", assistant_name)
            subscriptions.append(subscription)

        return subscriptions

    async def get_list_with_assistant_name(
        self, db: AsyncSession, *, params: Optional[AISubscriptionQueryParams] = None, skip: int = 0, limit: int = 100
    ) -> Sequence[AISubscription]:
        """获取AI订阅列表，包含助手名称（专用方法）"""
        return await self.get_list(db, params=params, skip=skip, limit=limit)

    async def get_count(self, db: AsyncSession, *, params: Optional[AISubscriptionQueryParams] = None) -> int:
        """获取AI订阅总数"""
        from backend.app.admin.model.ai_assistant import AIAssistant

        stmt = select(func.count(self.model.id)).where(self.model.deleted_at.is_(None))

        if params:
            conditions = []
            if params.name:
                conditions.append(self.model.name.ilike(f"%{params.name}%"))

            if params.assistant_name:
                # 通过关联ai_assistants表进行助手名称的模糊匹配
                stmt = stmt.join(AIAssistant, self.model.assistant_id == AIAssistant.id)
                conditions.append(AIAssistant.name.ilike(f"%{params.assistant_name}%"))
            if params.status is not None:
                # 过滤订阅状态
                conditions.append(self.model.status == params.status)
            if params.responsible_person:
                # 这里需要查询关联表，暂时简化处理
                pass

            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        return result.scalar()

    async def create(self, db: AsyncSession, *, obj_in: AISubscriptionCreate, user_id: int) -> AISubscription:
        """创建AI订阅"""

        # 构建创建数据，排除init=False的字段
        db_data = {
            **obj_in.model_dump(
                exclude_unset=True,
                exclude={
                    "notification_methods",
                },
            ),
            "user_id": user_id,  # 添加user_id到创建数据中
        }

        # 创建模型对象
        db_obj = self.model(**db_data)

        # 设置init=False的字段（id会自动生成）
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        await db.flush()  # 刷新以获取自动生成的ID

        # 创建关联关系
        await self._create_relations(db, subscription_id=db_obj.id, obj_in=obj_in)

        # 刷新数据库会话以确保关联关系已保存
        await db.flush()

        # 不在这里提交事务，由上层服务控制事务
        await db.refresh(db_obj)

        # 重新获取对象以加载关系和助手名称
        from backend.app.admin.model.ai_assistant import AIAssistant

        result = await db.execute(
            select(self.model, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, self.model.assistant_id == AIAssistant.id)
            .where(self.model.id == db_obj.id)
            .options(
                selectinload(self.model.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )
        row = result.first()
        if row:
            subscription = row[0]
            assistant_name = row[1]
            setattr(subscription, "assistant_name", assistant_name)
            return subscription
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: AISubscription, obj_in: AISubscriptionUpdate) -> AISubscription:
        """更新AI订阅，包含关联关系"""
        # 更新基础字段
        update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)

        # 更新基础字段
        for field, value in update_data.items():
            if hasattr(db_obj, field) and field not in [
                "notification_methods",
            ]:
                setattr(db_obj, field, value)

        db_obj.updated_time = datetime.now()

        # 先更新关联关系（在同一个事务中）
        await self._update_relations(db, subscription_id=db_obj.id, obj_in=obj_in)

        # 不在这里提交事务，由上层服务控制事务
        await db.refresh(db_obj)

        # 获取包含助手名称的对象
        from backend.app.admin.model.ai_assistant import AIAssistant

        result = await db.execute(
            select(self.model, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, self.model.assistant_id == AIAssistant.id)
            .where(self.model.id == db_obj.id)
            .options(
                selectinload(self.model.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )
        row = result.first()
        if row:
            subscription = row[0]
            assistant_name = row[1]
            setattr(subscription, "assistant_name", assistant_name)
            return subscription

        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """删除AI订阅（软删除）"""
        db_obj = await self.get(db, id=id)
        if db_obj:
            db_obj.deleted_at = datetime.now()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[int]) -> int:
        """批量删除AI订阅"""
        count = 0
        for subscription_id in ids:
            if await self.delete(db, id=subscription_id):
                count += 1
        return count

    async def clone(self, db: AsyncSession, *, id: int, new_name: str) -> Optional[AISubscription]:
        """克隆AI订阅"""
        # 获取原始数据
        original = await self.get(db, id=id)
        if not original:
            return None

        # 生成新ID
        new_id = get_uuid()

        # 复制数据，不包含init=False的字段
        obj_data = {
            "assistant_id": original.assistant_id,  # 保持相同的助手ID
            "user_id": original.user_id,  # 保持相同的用户ID
            "name": new_name,
            "subscription_type": original.subscription_type,
            "execution_frequency": original.execution_frequency,
            "execution_time": original.execution_time,
            "execution_minutes": original.execution_minutes,
            "execution_hours": original.execution_hours,
            "execution_weekday": original.execution_weekday,
            "execution_weekly_time": original.execution_weekly_time,
            "execution_day": original.execution_day,
            "execution_monthly_time": original.execution_monthly_time,
            "is_view_myself": original.is_view_myself,
            "setting": original.setting,
            "responsible_persons": original.responsible_persons,
            "ai_analysis_count": 0,  # 重置分析次数
            "last_analysis_time": None,  # 重置最后分析时间
        }

        new_obj = self.model(**obj_data)

        # 设置init=False的字段
        new_obj.id = new_id
        new_obj.created_time = datetime.now()

        db.add(new_obj)
        await db.flush()

        # 复制关联关系
        # ... 复制通知方式关联
        for relation in original.notification_relations:
            notification_relation = AISubscriptionNotification()
            notification_relation.id = get_uuid()
            notification_relation.subscription_id = new_id
            notification_relation.notification_id = relation.notification_id
            notification_relation.created_time = datetime.now()
            db.add(notification_relation)

        await db.refresh(new_obj)

        # 获取包含助手名称的对象
        from backend.app.admin.model.ai_assistant import AIAssistant

        result = await db.execute(
            select(self.model, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, self.model.assistant_id == AIAssistant.id)
            .where(self.model.id == new_obj.id)
            .options(
                selectinload(self.model.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )
        row = result.first()
        if row:
            subscription = row[0]
            assistant_name = row[1]
            setattr(subscription, "assistant_name", assistant_name)
            return subscription

        return new_obj

    async def _create_relations(self, db: AsyncSession, *, subscription_id: int, obj_in: AISubscriptionCreate) -> None:
        """创建关联关系"""
        # 创建通知方式关联
        if obj_in.notification_methods:
            # 检查是否已存在关联关系
            from sqlalchemy import select

            existing_stmt = select(AISubscriptionNotification).where(
                AISubscriptionNotification.subscription_id == subscription_id
            )
            existing_result = await db.execute(existing_stmt)
            existing_relations = existing_result.scalars().all()

            # 如果已存在关联，先删除
            if existing_relations:
                for relation in existing_relations:
                    await db.delete(relation)

            # 创建新关联
            for notification_id in obj_in.notification_methods:
                notification_relation = AISubscriptionNotification()
                notification_relation.id = get_uuid()
                notification_relation.subscription_id = subscription_id
                notification_relation.notification_id = int(notification_id)  # 转换为整数
                notification_relation.created_time = datetime.now()
                db.add(notification_relation)

    async def _update_relations(self, db: AsyncSession, *, subscription_id: int, obj_in: AISubscriptionUpdate) -> None:
        """更新关联关系"""
        # 更新通知方式关联
        if obj_in.notification_methods is not None:
            # 先删除现有关联
            stmt = select(AISubscriptionNotification).where(
                AISubscriptionNotification.subscription_id == subscription_id
            )
            result = await db.execute(stmt)
            existing_relations = result.scalars().all()
            for relation in existing_relations:
                await db.delete(relation)

            # 刷新删除操作，确保删除立即生效
            await db.flush()

            # 创建新关联
            for notification_id in obj_in.notification_methods:
                notification_relation = AISubscriptionNotification()
                notification_relation.id = get_uuid()
                notification_relation.subscription_id = subscription_id
                notification_relation.notification_id = int(notification_id)  # 转换为整数
                notification_relation.created_time = datetime.now()
                db.add(notification_relation)


class CRUDAISubscriptionNotificationMethod(CRUDPlus[AISubscriptionNotificationMethod]):
    """AI订阅通知方式CRUD操作"""

    async def get(self, db: AsyncSession, *, id: int) -> Optional[AISubscriptionNotificationMethod]:
        """根据ID获取通知方式"""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        type: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AISubscriptionNotificationMethod]:
        """获取通知方式列表"""
        stmt = select(self.model)

        if type:
            stmt = stmt.where(self.model.type == type)
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, *, name: str, type: str, config: Optional[dict] = None
    ) -> AISubscriptionNotificationMethod:
        """创建通知方式"""
        # 创建对象（不包含init=False的字段）
        db_obj = self.model(name=name, type=type, config=config, status=True)

        # 设置init=False的字段
        # ID将由数据库自动生成（自增主键）
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        await db.refresh(db_obj)
        return db_obj


# 创建CRUD实例
crud_ai_subscription = CRUDAISubscription(AISubscription)
crud_ai_subscription_notification_method = CRUDAISubscriptionNotificationMethod(AISubscriptionNotificationMethod)
