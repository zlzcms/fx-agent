#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agents.extract_parameters_agent import ExtractParametersAgent
from backend.agents.config.prompt.extract_parameters import HISTORY_COMPRESSION_PROMPT
from backend.agents.schema.agent import ExecuteStatus
from backend.app.home.crud.crud_ai_chat_message import ai_chat_message
from backend.app.home.model.ai_chat import AIChat
from backend.app.home.model.ai_chat_message import AIChatMessage
from backend.app.home.schema.ai_chat import AIChatUpdate
from backend.app.home.service.ai_chat_service import ai_chat_service
from backend.database.db import get_db


class AgentService:
    """聊天服务类，处理AI对话功能"""

    async def get_history_messages(self, db: AsyncSession, chat: AIChat, limit: int = 6) -> List:
        """获取聊天历史消息"""
        messages = await ai_chat_message.get_history_messages(db, chat, limit)
        history_messages = []
        if chat.history_summary and chat.summary_time:
            history_messages.append(
                {
                    "role": "system",
                    "content": chat.history_summary,
                    "created_time": chat.summary_time,
                }
            )
        for message in messages:
            history_messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                    "created_time": message.created_time,
                }
            )
        # 如果历史消息达到限制，触发后台异步压缩任务，不阻塞当前请求
        if len(history_messages) >= limit:
            # 启动后台任务进行压缩，不等待其完成
            asyncio.create_task(self._background_compress_history(chat.id, history_messages.copy()))
        return history_messages

    async def _background_compress_history(self, chat_id: str, history_messages: List[Dict]) -> None:
        """
        后台异步压缩历史对话任务

        Args:
            chat_id: 聊天会话ID
            history_messages: 历史消息列表
        """
        try:
            # 执行压缩
            compress_history = await self.compress_conversation_history(history_messages)

            if compress_history:
                # 创建新的数据库会话用于后台任务
                async for db in get_db():
                    try:
                        # 更新聊天会话的压缩历史
                        await ai_chat_service.update_chat(
                            db,
                            chat_id=chat_id,
                            data=AIChatUpdate(history_summary=compress_history, summary_time=datetime.now()),
                        )
                    finally:
                        # 确保数据库会话被正确关闭
                        await db.close()
                    break  # 只需要一个会话
        except Exception as e:
            # 后台任务失败不影响主流程，只记录日志
            print(f"后台压缩历史对话失败 (chat_id: {chat_id}): {str(e)}")

    async def compress_conversation_history(self, conversation_history: List[Dict[str, str]]) -> Optional[str]:
        """
        压缩和提纯历史对话

        Args:
            conversation_history: 历史对话列表
            min_rounds: 最小压缩轮数，少于此轮数不压缩（默认3轮）

        Returns:
            压缩后的历史摘要字符串，如果不需要压缩则返回None
        """
        agent = ExtractParametersAgent()
        if not conversation_history:
            # 历史对话太短，不需要压缩
            return None

        try:
            # 构建历史对话的文本表示
            history_text = ""
            for msg in conversation_history:
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                elif isinstance(msg, AIChatMessage):
                    role = msg.role
                    content = msg.content

                if role == "user":
                    history_text += f"用户: {content}\n"
                elif role == "assistant":
                    history_text += f"助手: {content}\n"
            # 构建压缩提示词
            prompt = HISTORY_COMPRESSION_PROMPT.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            data = {}
            async for yieldResponse in agent.execute(history_text, prompt):
                if yieldResponse.status == ExecuteStatus.COMPLETED:
                    data = yieldResponse.output
                    break
            if data:
                # 构建压缩后的摘要文本
                summary = data.get("summary", "")
                key_points = data.get("key_points", [])
                context = data.get("context", {})

                compressed_text = f"**历史对话摘要**\n{summary}\n\n"
                if key_points:
                    compressed_text += "**关键信息**：\n"
                    for point in key_points:
                        compressed_text += f"- {point}\n"

                if context:
                    user_goal = context.get("user_goal", "")

                    if user_goal:
                        compressed_text += f"\n**用户目标**：{user_goal}\n"
                    # if confirmed_params:
                    #     compressed_text += "**已确认参数**：\n"
                    #     for key, value in confirmed_params.items():
                    #         compressed_text += f"  - {key}: {value}\n"
                    # if pending_items:
                    #     compressed_text += "**待确认事项**：\n"
                    #     for item in pending_items:
                    #         compressed_text += f"  - {item}\n"

                return compressed_text
            else:
                # 解析失败，返回None使用原始历史
                return None

        except Exception as e:
            # 压缩失败，记录错误但不影响主流程
            print(f"历史对话压缩失败: {str(e)}")
            return None


agent_service = AgentService()
