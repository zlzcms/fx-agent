#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional, Sequence

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.admin.model.ai_assistant import AIAssistant
from backend.app.admin.model.ai_subscription import AISubscription, AISubscriptionNotification


class HomeSubscriptionCRUD:
    """Home订阅CRUD操作"""

    async def get_user_subscriptions(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        name: Optional[str] = None,
        subscription_type: Optional[str] = None,
        assistant_name: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AISubscription]:
        """
        获取用户的订阅列表

        根据responsible_persons字段中的personnel_id与用户ID匹配进行过滤
        """
        # 构建基础查询，包含助手信息
        stmt = (
            select(AISubscription, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, AISubscription.assistant_id == AIAssistant.id)
            .where(
                and_(
                    AISubscription.deleted_at.is_(None),
                    # 使用PostgreSQL的JSONB查询过滤responsible_persons中包含当前用户ID的记录
                    text(
                        "EXISTS (SELECT 1 FROM jsonb_array_elements(responsible_persons::jsonb) AS elem WHERE elem->>'personnel_id' = :user_id)"
                    ),
                )
            )
            .params(user_id=user_id)
            .options(
                selectinload(AISubscription.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )

        # 添加过滤条件
        conditions = []
        if name:
            conditions.append(AISubscription.name.ilike(f"%{name}%"))
        if subscription_type:
            conditions.append(AISubscription.subscription_type == subscription_type)
        if assistant_name:
            conditions.append(AIAssistant.name.ilike(f"%{assistant_name}%"))
        if status is not None:
            conditions.append(AISubscription.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit).order_by(AISubscription.created_time.desc())
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

    async def get_user_subscriptions_count(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        name: Optional[str] = None,
        subscription_type: Optional[str] = None,
        assistant_name: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> int:
        """获取用户的订阅总数"""
        # 构建计数查询
        stmt = (
            select(func.count(AISubscription.id))
            .where(
                and_(
                    AISubscription.deleted_at.is_(None),
                    # 使用PostgreSQL的JSONB查询过滤responsible_persons中包含当前用户ID的记录
                    text(
                        "EXISTS (SELECT 1 FROM jsonb_array_elements(responsible_persons::jsonb) AS elem WHERE elem->>'personnel_id' = :user_id)"
                    ),
                )
            )
            .params(user_id=user_id)
        )

        # 添加过滤条件
        conditions = []
        if name:
            conditions.append(AISubscription.name.ilike(f"%{name}%"))
        if subscription_type:
            conditions.append(AISubscription.subscription_type == subscription_type)
        if assistant_name:
            # 需要JOIN助手表进行名称过滤
            stmt = stmt.join(AIAssistant, AISubscription.assistant_id == AIAssistant.id)
            conditions.append(AIAssistant.name.ilike(f"%{assistant_name}%"))
        if status is not None:
            conditions.append(AISubscription.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        return result.scalar()

    async def get_user_subscription_by_id(
        self,
        db: AsyncSession,
        *,
        subscription_id: int,
        user_id: str,
        status: Optional[bool] = None,
    ) -> Optional[AISubscription]:
        """
        根据ID获取用户的订阅详情

        仅当用户是该订阅的通知对象时才返回结果
        """
        # 构建查询，包含助手信息
        stmt = (
            select(AISubscription, AIAssistant.name.label("assistant_name"))
            .join(AIAssistant, AISubscription.assistant_id == AIAssistant.id)
            .where(
                and_(
                    AISubscription.id == subscription_id,
                    AISubscription.deleted_at.is_(None),
                    # 使用PostgreSQL的JSONB查询过滤responsible_persons中包含当前用户ID的记录
                    text(
                        "EXISTS (SELECT 1 FROM jsonb_array_elements(responsible_persons::jsonb) AS elem WHERE elem->>'personnel_id' = :user_id)"
                    ),
                )
            )
            .params(user_id=user_id)
            .options(
                selectinload(AISubscription.notification_relations).selectinload(
                    AISubscriptionNotification.notification_method
                ),
            )
        )

        # 添加状态过滤
        if status is not None:
            stmt = stmt.where(AISubscription.status == status)

        result = await db.execute(stmt)
        row = result.first()

        if row:
            subscription = row[0]  # AISubscription对象
            assistant_name = row[1]  # 助手名称
            # 动态添加assistant_name属性
            setattr(subscription, "assistant_name", assistant_name)
            return subscription

        return None


# 创建CRUD实例
home_subscription_dao = HomeSubscriptionCRUD()
