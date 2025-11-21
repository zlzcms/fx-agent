# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:12:05
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.model.ai_chat import AIChat
from backend.app.home.model.ai_chat_message import AIChatMessage
from backend.app.home.schema.ai_chat import AIChatMessageCreate


class CRUDAIChatMessage:
    """AI聊天消息CRUD操作"""

    async def create(self, db: AsyncSession, *, obj_in: AIChatMessageCreate) -> AIChatMessage:
        """创建新的聊天消息

        参数:
            db: 数据库会话
            obj_in: 消息创建数据

        返回:
            创建的聊天消息
        """
        message_id = obj_in.id or str(uuid.uuid4())

        # 验证chat_id不为None或空字符串
        chat_id = obj_in.chat_id
        if chat_id is None or chat_id == "":
            raise ValueError(f"聊天ID不能为空，原始值: {obj_in.chat_id}")

        db_obj = AIChatMessage(
            id=message_id,
            chat_id=chat_id,
            role=obj_in.role,
            content=obj_in.content,
        )
        # 手动设置不能在构造函数中初始化的属性
        db_obj.is_interrupted = obj_in.is_interrupted
        db_obj.response_data = obj_in.response_data

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, *, message_id: str) -> Optional[AIChatMessage]:
        """获取聊天消息

        参数:
            db: 数据库会话
            message_id: 消息ID

        返回:
            找到的聊天消息，如果不存在则返回None
        """
        stmt = select(AIChatMessage).where(AIChatMessage.id == message_id, AIChatMessage.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history_messages(self, db: AsyncSession, chat: AIChat, limit: int = 6) -> List[AIChatMessage]:
        """获取聊天会话的历史消息

        参数:
            db: 数据库会话
            chat: 聊天会话
            limit: 限制返回的消息数量

        返回:
            聊天会话的消息列表
        """
        conditions = [AIChatMessage.chat_id == chat.id, AIChatMessage.deleted_at.is_(None)]

        if chat.history_summary and chat.summary_time:
            conditions.append(AIChatMessage.created_time >= chat.summary_time)

        stmt = select(AIChatMessage).where(*conditions).order_by(AIChatMessage.created_time).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_multi_by_chat(self, db: AsyncSession, *, chat_id: str, limit: int = 4) -> List[AIChatMessage]:
        """获取聊天会话的所有消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            limit: 限制返回的消息数量

        返回:
            聊天会话的消息列表
        """
        stmt = (
            select(AIChatMessage)
            .where(AIChatMessage.chat_id == chat_id, AIChatMessage.deleted_at.is_(None))
            .order_by(AIChatMessage.created_time.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def get_multi_by_chat_query(self, *, chat_id: str):
        """获取聊天会话消息的查询语句（用于分页）

        参数:
            chat_id: 聊天ID

        返回:
            SQLAlchemy查询语句
        """
        return (
            select(AIChatMessage)
            .where(AIChatMessage.chat_id == chat_id, AIChatMessage.deleted_at.is_(None))
            .order_by(AIChatMessage.created_time.desc())
        )

    async def get_last_assistant_message(self, db: AsyncSession, *, chat_id: str) -> Optional[AIChatMessage]:
        """获取聊天会话中最后一条AI助手消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID

        返回:
            最后一条AI助手消息，如果不存在则返回None
        """
        stmt = (
            select(AIChatMessage)
            .where(AIChatMessage.chat_id == chat_id, AIChatMessage.role == "assistant")
            .order_by(AIChatMessage.created_time.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


ai_chat_message = CRUDAIChatMessage()
