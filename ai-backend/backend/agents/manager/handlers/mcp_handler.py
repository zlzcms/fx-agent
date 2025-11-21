# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:02:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 15:30:40
# !/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.manager.factories.base_handler import BaseIntentHandler
from backend.agents.tools.task_manager import TaskManager
from backend.common.log import logger


class McpIntentHandler(BaseIntentHandler):
    """MCP意图处理器"""

    def __init__(self, agent: Any):
        super().__init__(agent)
        self.task_manager = TaskManager()

    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理MCP意图"""

        try:
            logger.debug("McpIntentHandler Enabled task planning mode")

            # 从 agent 中获取 config，传递给子任务
            agent_config = getattr(self.agent, "config", {})

            # 创建获取用户数据任务
            self.task_manager.create_task(
                name="获取用户数据",
                description="查询用户信息",
                executor_type="agent",
                executor="get_users_agent",  # 使用字符串名称代替直接实例化
                parameters={"data_sources": intent_data.get("data_sources", {}), "config": agent_config},
                executor_link_param=[("output", "analyze_data"), ("request", "data_request")],
            )

            # 创建数据分析任务
            self.task_manager.create_task(
                name="数据分析",
                description="数据分析",
                executor_type="agent",
                executor="data_analyze_agent",  # 使用字符串名称代替直接实例化
                parameters={"config": agent_config},
            )
            kwargs["is_save_file"] = False
            kwargs["llm_response_type"] = "stream"
            async for task_message in self.task_manager.execute_tasks(user_query, conversation_history, **kwargs):
                if task_message.get("type") == "step":
                    task_message["type"] = "chat"
                yield task_message

            logger.info("MCP intent handling completed successfully")
        except Exception as e:
            error_msg = f"MCP处理器异常：{str(e)}"
            logger.error(error_msg)
            yield {"type": "error", "message": error_msg}
