# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-06 10:10:32
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 21:08:06
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.manager.factories.base_handler import BaseIntentHandler
from backend.agents.tools.task_manager import TaskManager
from backend.common.log import logger


class ReportIntentHandler(BaseIntentHandler):
    """报告处理器"""

    def __init__(self, agent: Any):
        super().__init__(agent)
        self.task_manager = TaskManager()

    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理报告意图"""
        try:
            self.task_manager.is_plan = True
            logger.debug("ReportIntentHandler Enabled task planning mode")

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
                executor="data_analyze_agent",
                parameters={"llm_response_type": "report", "intent_data": intent_data, "config": agent_config},
            )

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
            # print(f"last_task_result===============: {last_task_result}")
            if last_task_result and last_task_result.get("file"):
                logger.info(f"Report completed with file: {last_task_result.get('file', {}).get('filename')}")
                yield {
                    "type": "final",
                    "status": "success",
                    "message": user_query,
                    "file": last_task_result.get("file"),
                }

            logger.info("Report intent handling completed successfully")
        except Exception as e:
            error_msg = f"报告处理器异常：{str(e)}"
            logger.error(error_msg)
            yield {"type": "error", "message": error_msg}
