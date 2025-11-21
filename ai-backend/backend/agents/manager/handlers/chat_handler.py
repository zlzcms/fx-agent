# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-08 21:20:49
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:48:01
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
聊天意图处理器
处理一般对话相关的意图
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.manager.factories.base_handler import BaseIntentHandler
from backend.agents.tools.task_manager import TaskManager
from backend.common.log import logger


class ChatIntentHandler(BaseIntentHandler):
    """聊天意图处理器"""

    def __init__(self, agent: Any):
        super().__init__(agent)
        self.task_manager = TaskManager()

    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理聊天意图"""

        try:
            logger.debug("ChatIntentHandler Enabled task planning mode")
            self.create_tasks(intent_data)
            # 执行任务
            async for task_message in self.task_manager.execute_tasks(user_query, conversation_history, **kwargs):
                yield task_message
        except Exception as e:
            error_msg = f"聊天处理器异常：{str(e)}"
            logger.error(error_msg)
            yield {"type": "error", "message": error_msg}

    def create_tasks(self, intent_data: Dict):
        agent_config = getattr(self.agent, "config", {})
        # 创建通用聊天任务
        self.task_manager.create_task(
            name="通用聊天",
            description="通用聊天",
            executor_type="agent",
            executor="general_chat_agent",
            parameters={"config": agent_config},
        )
