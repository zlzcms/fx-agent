#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import uuid

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.crud.crud_ai_chat import ai_chat
from backend.app.home.crud.crud_ai_chat_message import ai_chat_message
from backend.app.home.model.ai_chat import AIChat
from backend.app.home.model.ai_chat_message import AIChatMessage
from backend.app.home.schema.ai_chat import AIChatCreate, AIChatMessageCreate, AIChatUpdate
from backend.common.pagination import PageData

logger = logging.getLogger(__name__)


class AIChatService:
    """聊天服务类，处理AI对话功能"""

    async def create_chat(self, db: AsyncSession, *, data: AIChatCreate) -> AIChat:
        """创建新的聊天会话"""
        chat = await ai_chat.create(db, obj_in=data)

        # 确保chat.id不为None
        if chat.id is None:
            # print("警告: 聊天ID为None，将使用UUID生成新ID")
            chat.id = str(uuid.uuid4())
            # print(f"生成的新聊天ID: {chat.id}")
            await db.commit()

        return chat

    async def create_message(self, db: AsyncSession, *, data: AIChatMessageCreate) -> AIChatMessage:
        """创建新的聊天消息

        参数:
            db: 数据库会话
            data: 消息创建数据

        返回:
            创建的聊天消息对象
        """
        return await ai_chat_message.create(db, obj_in=data)

    async def create_system_message(
        self,
        db: AsyncSession,
        *,
        chat_id: str,
        content: str = None,
        response_data: Optional[dict] = None,
        is_interrupted: bool = False,
    ) -> AIChatMessage:
        """创建系统消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            content: 系统消息内容，如果为None则使用默认内容

        返回:
            创建的系统消息对象
        """
        if content is None:
            content = "您好，我是智能助手，可以提供信息并回答问题。我还可以通过MCP服务查询数据来帮助您。"

        message_data = AIChatMessageCreate(
            chat_id=chat_id, role="system", content=content, response_data=response_data, is_interrupted=is_interrupted
        )
        return await self.create_message(db, data=message_data)

    async def create_user_message(
        self, db: AsyncSession, *, chat_id: str, content: str, is_interrupted: bool = False
    ) -> AIChatMessage:
        """创建用户消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            content: 用户消息内容

        返回:
            创建的用户消息对象
        """
        message_data = AIChatMessageCreate(chat_id=chat_id, role="user", content=content, is_interrupted=is_interrupted)
        return await self.create_message(db, data=message_data)

    async def create_assistant_message(
        self,
        db: AsyncSession,
        *,
        chat_id: str,
        content: str,
        response_data: Optional[dict] = None,
        is_interrupted: bool = False,
    ) -> AIChatMessage:
        """创建AI助手消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            content: AI助手消息内容
            query_data: MCP查询数据
            response_data: 查询结果数据

        返回:
            创建的AI助手消息对象
        """
        message_data = AIChatMessageCreate(
            chat_id=chat_id,
            role="assistant",
            content=content,
            response_data=response_data,
            is_interrupted=is_interrupted,
        )
        return await self.create_message(db, data=message_data)

    async def get_chat(self, db: AsyncSession, *, chat_id: str) -> Optional[AIChat]:
        """通过ID获取聊天会话"""
        return await ai_chat.get(db, chat_id=chat_id)

    async def list_chats(self, db: AsyncSession, *, user_id: str) -> List[AIChat]:
        """获取用户的所有聊天会话"""
        return await ai_chat.get_multi_by_user(db, user_id=user_id)

    async def list_chats_paginated(
        self, db: AsyncSession, *, user_id: str, page: int = 1, size: int = 20
    ) -> PageData[AIChat]:
        """获取用户聊天会话的分页列表

        参数:
            db: 数据库会话
            user_id: 用户ID
            page: 页码，从1开始
            size: 每页数量

        返回:
            分页数据
        """
        from math import ceil

        from sqlalchemy import func, select

        # 获取查询语句
        stmt = ai_chat.get_multi_by_user_query(user_id=user_id)

        # 计算总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 计算分页参数
        offset = (page - 1) * size
        total_pages = ceil(total / size) if total > 0 else 1

        # 执行分页查询
        paginated_stmt = stmt.limit(size).offset(offset)
        result = await db.execute(paginated_stmt)
        items = list(result.unique().scalars().all())

        # 构建分页链接
        links = {
            "first": f"?page=1&size={size}",
            "last": f"?page={total_pages}&size={size}",
            "self": f"?page={page}&size={size}",
            "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
            "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
        }

        # 转换为 PageData 对象
        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links=links,
        )

    async def update_chat(self, db: AsyncSession, *, chat_id: str, data: AIChatUpdate) -> Optional[AIChat]:
        """更新聊天

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            data: 更新数据

        返回:
            更新后的聊天对象，如果不存在则返回None
        """
        return await ai_chat.update(db, chat_id=chat_id, obj_in=data)

    async def delete_chat(self, db: AsyncSession, *, chat_id: str) -> bool:
        """删除聊天

        参数:
            db: 数据库会话
            chat_id: 聊天ID

        返回:
            是否删除成功
        """
        return await ai_chat.remove(db, chat_id=chat_id)

    async def get_chat_messages(self, db: AsyncSession, *, chat_id: str, limit: int = 6) -> List[AIChatMessage]:
        """获取聊天消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            limit: 消息数量限制

        返回:
            聊天消息列表
        """
        return await ai_chat_message.get_multi_by_chat(db, chat_id=chat_id, limit=limit)

    async def get_chat_messages_paginated(
        self, db: AsyncSession, *, chat_id: str, page: int = 1, size: int = 20
    ) -> PageData[AIChatMessage]:
        """获取聊天消息的分页列表

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            page: 页码，从1开始
            size: 每页数量

        返回:
            分页数据
        """
        from math import ceil

        from sqlalchemy import func, select

        # 获取查询语句
        stmt = ai_chat_message.get_multi_by_chat_query(chat_id=chat_id)

        # 计算总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 计算分页参数
        offset = (page - 1) * size
        total_pages = ceil(total / size) if total > 0 else 1

        # 执行分页查询
        paginated_stmt = stmt.limit(size).offset(offset)
        result = await db.execute(paginated_stmt)
        items = list(result.scalars().all())

        # 构建分页链接
        links = {
            "first": f"?page=1&size={size}",
            "last": f"?page={total_pages}&size={size}",
            "self": f"?page={page}&size={size}",
            "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
            "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
        }

        # 转换为 PageData 对象
        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links=links,
        )

    async def get_last_assistant_message(self, db: AsyncSession, *, chat_id: str) -> Optional[AIChatMessage]:
        """获取聊天会话中最后一条AI助手消息

        参数:
            db: 数据库会话
            chat_id: 聊天ID

        返回:
            最后一条AI助手消息，如果不存在则返回None
        """
        return await ai_chat_message.get_last_assistant_message(db, chat_id=chat_id)

    async def interrupt_message(self, db: AsyncSession, *, message_id: str) -> bool:
        """中断指定的聊天消息

        参数:
            db: 数据库会话
            message_id: 消息ID

        返回:
            是否成功中断
        """
        try:
            # 获取消息
            message = await ai_chat_message.get(db, message_id=message_id)
            if not message:
                logger.warning(f"Message not found: {message_id}")
                return False

            # 检查消息是否为AI助手消息且未被中断
            if message.role != "assistant" or message.is_interrupted:
                logger.warning(
                    f"Message {message_id} cannot be interrupted: role={message.role}, already_interrupted={message.is_interrupted}"
                )
                return False

            # 标记消息为已中断
            message.is_interrupted = True
            await db.commit()

            logger.info(f"Successfully interrupted message: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to interrupt message {message_id}: {str(e)}")
            await db.rollback()
            return False

    async def is_message_interrupted(self, db: AsyncSession, *, message_id: str) -> bool:
        """检查指定消息是否已被中断

        参数:
            db: 数据库会话
            message_id: 消息ID

        返回:
            消息是否被中断
        """
        try:
            message = await ai_chat_message.get(db, message_id=message_id)
            if not message:
                return False
            return message.is_interrupted
        except Exception as e:
            logger.error(f"Failed to check message interruption status {message_id}: {str(e)}")
            return False

    async def update_message_content(
        self,
        db: AsyncSession,
        *,
        message_id: str,
        content: str = None,
        response_data: Optional[dict] = None,
        is_interrupted: bool = False,
    ) -> bool:
        """更新消息内容和中断状态

        参数:
            db: 数据库会话
            message_id: 消息ID
            content: 新的消息内容
            is_interrupted: 是否被中断

        返回:
            是否更新成功
        """
        try:
            message = await ai_chat_message.get(db, message_id=message_id)
            if not message:
                logger.warning(f"Message_id not found: {message_id}")
                return False

            # 更新消息内容和中断状态
            if content:
                message.content = content
            if response_data:
                message.response_data = response_data
            message.is_interrupted = is_interrupted
            await db.commit()

            logger.info(f"Successfully updated message content: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update message content {message_id}: {str(e)}")
            await db.rollback()
            return False


# 创建单例实例
ai_chat_service = AIChatService()
