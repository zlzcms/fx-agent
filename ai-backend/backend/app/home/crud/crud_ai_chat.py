# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:12:05
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from typing import List, Optional

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.model.ai_chat import AIChat
from backend.app.home.schema.ai_chat import AIChatCreate, AIChatUpdate


class CRUDAIChat:
    """AI聊天CRUD操作"""

    async def create(self, db: AsyncSession, *, obj_in: AIChatCreate) -> AIChat:
        """创建新的聊天会话

        参数:
            db: 数据库会话
            obj_in: 聊天创建数据

        返回:
            创建的聊天会话
        """
        # 生成聊天ID
        chat_id = obj_in.id or str(uuid.uuid4())
        print(f"使用的聊天ID: {chat_id}")

        # 打印调试信息
        print(f"创建AI聊天 - 用户ID类型: {type(obj_in.user_id)}, 值: {obj_in.user_id}")

        # 确保user_id是整数类型
        user_id = int(obj_in.user_id) if obj_in.user_id is not None else None
        if user_id is None:
            raise ValueError("用户ID不能为空")

        print(f"转换后的用户ID类型: {type(user_id)}, 值: {user_id}")

        try:
            # 创建对象，只传入允许在构造函数中初始化的参数
            db_obj = AIChat(title=obj_in.title, status=True)

            # 手动设置其他属性
            db_obj.id = chat_id
            db_obj.user_id = user_id
            db_obj.model_id = obj_in.model_id
            db_obj.channel = obj_in.channel

            # 打印创建的对象信息
            print(f"创建的AIChat对象: id={db_obj.id}, user_id={db_obj.user_id}, title={db_obj.title}")

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            # 验证提交后的对象
            print(f"提交后的AIChat对象: id={db_obj.id}, user_id={db_obj.user_id}, title={db_obj.title}")

            return db_obj
        except Exception as e:
            print(f"创建AIChat对象时出错: {str(e)}")
            raise

    async def get(self, db: AsyncSession, *, chat_id: str) -> Optional[AIChat]:
        """获取聊天会话

        参数:
            db: 数据库会话
            chat_id: 聊天ID

        返回:
            找到的聊天会话，如果不存在则返回None
        """
        stmt = select(AIChat).where(AIChat.id == chat_id, AIChat.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_multi_by_user(self, db: AsyncSession, *, user_id: str) -> List[AIChat]:
        """获取用户的所有聊天会话

        参数:
            db: 数据库会话
            user_id: 用户ID

        返回:
            用户的聊天会话列表
        """
        # 确保user_id是整数类型
        user_id_int = int(user_id) if user_id else None
        if user_id_int is None:
            return []

        # 通过查询获取聊天会话（不使用关系预加载）
        stmt = (
            select(AIChat)
            .where(AIChat.user_id == user_id_int, AIChat.deleted_at.is_(None))
            .order_by(desc(AIChat.created_time))
        )
        result = await db.execute(stmt)
        # 使用unique()方法确保每个AIChat实体只返回一次
        return list(result.unique().scalars().all())

    def get_multi_by_user_query(self, *, user_id: str):
        """获取用户聊天会话的查询语句（用于分页）

        参数:
            user_id: 用户ID

        返回:
            SQLAlchemy查询语句
        """
        # 确保user_id是整数类型
        user_id_int = int(user_id) if user_id else None
        if user_id_int is None:
            # 返回一个空查询
            return select(AIChat).where(False)

        # 返回查询语句（不使用关系预加载）
        return (
            select(AIChat)
            .where(AIChat.user_id == user_id_int, AIChat.deleted_at.is_(None))
            .order_by(desc(AIChat.created_time))
        )

    async def update(self, db: AsyncSession, *, chat_id: str, obj_in: AIChatUpdate) -> Optional[AIChat]:
        """更新聊天会话

        参数:
            db: 数据库会话
            chat_id: 聊天ID
            obj_in: 聊天更新数据

        返回:
            更新后的聊天会话，如果不存在则返回None
        """
        update_data = obj_in.dict(exclude_unset=True)
        stmt = update(AIChat).where(AIChat.id == chat_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        return await self.get(db, chat_id=chat_id)

    async def remove(self, db: AsyncSession, *, chat_id: str) -> bool:
        """删除聊天会话

        参数:
            db: 数据库会话
            chat_id: 聊天ID

        返回:
            是否成功删除
        """
        chat = await self.get(db, chat_id=chat_id)
        if not chat:
            return False

        await db.delete(chat)
        await db.commit()
        return True


ai_chat = CRUDAIChat()
