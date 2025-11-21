# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 14:45:35
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 21:08:19
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询意图处理器
处理数据查询相关的意图
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.manager.factories.base_handler import BaseIntentHandler
from backend.agents.tools.task_manager import TaskManager
from backend.common.log import logger


class AgentIntentHandler(BaseIntentHandler):
    """智能体意图处理器"""

    def __init__(self, agent: Any):
        super().__init__(agent)
        self.task_manager = TaskManager()

    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理智能体意图"""

        try:
            self.create_tasks(intent_data)
            logger.info(f"Created {len(self.task_manager.tasks)} tasks")

            self.task_manager.is_plan = True

            # 执行任务
            async for task_message in self.task_manager.execute_tasks(user_query, conversation_history, **kwargs):
                # 转换消息类型
                if task_message.get("type") == "plan":
                    task_message["type"] = "md_info"
                elif (task_message.get("type") == "chat" and task_message.get("status") == "error") or (
                    task_message.get("type") == "summarize" and task_message.get("status") == "running"
                ):
                    task_message["type"] = "step"
                    task_message["type_name"] = "completion"
                elif task_message.get("type") == "summarize" and task_message.get("status") == "completed":
                    task_message["type"] = "step"
                    task_message["type_name"] = "success"
                elif task_message.get("type") == "file":
                    task_message["type"] = "step"
                    task_message["type_name"] = "execute"

                yield task_message

            last_task_result = self.task_manager.last_result

            if last_task_result and last_task_result.get("file"):
                yield {
                    "type": "final",
                    "status": "success",
                    "message": user_query,
                    "file": last_task_result.get("file"),
                }

            logger.info("Agent intent handling completed successfully")
        except Exception as e:
            import traceback

            error_msg = f"智能体处理器异常：{str(e)}"
            logger.error(error_msg)
            logger.error(f"堆栈信息：\n{traceback.format_exc()}")
            yield {"type": "error", "message": error_msg}

    def create_tasks(self, intent_data: Dict):
        """创建任务"""
        assistant_id = intent_data.get("value")

        # 从 agent 中获取 config，传递给子任务
        agent_config = getattr(self.agent, "config", {})

        # 创建获取助手任务
        self.task_manager.create_task(
            name="获取助手",
            description="查询助手信息",
            executor_type="agent",
            executor="assistant_agent",
            parameters={"assistant_id": assistant_id, "config": agent_config},
            executor_link_param=[("assistant", "assistant")],
        )

        # 创建获取用户数据任务
        self.task_manager.create_task(
            name="获取用户数据",
            description="查询用户信息",
            executor_type="agent",
            executor="get_users_agent",  # 使用字符串名称代替直接实例化
            parameters={"data_sources": intent_data.get("data_sources", {}), "config": agent_config},
            executor_link_param=[("output", "analyze_data"), ("assistant", "assistant"), ("request", "data_request")],
        )

        # 创建数据分析任务
        self.task_manager.create_task(
            name="数据分析",
            description="分析用户数据",
            executor_type="agent",
            executor="data_analyze_agent",
            parameters={"llm_response_type": "report", "intent_data": intent_data, "config": agent_config},
        )

        logger.info(f"AgentIntentHandler Created {len(self.task_manager.tasks)} tasks successfully")
        return self.task_manager.tasks
