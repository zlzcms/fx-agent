# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-06 18:30:43
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:41:42
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.config.prompt.agent import ERROR_SYSTEM_PROMPT
from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.services.assistant_service import assistant_service
from backend.common.log import logger


class AssistantAgent(Base):
    """
    助手智能体，专门负责执行助手任务
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        super().__init__("assistant", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())

    async def execute(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行助手任务"""
        try:
            # self.log.append({"title": "开始执行", "content": user_query})
            self.state = AgentState.RUNNING
            logger.debug("AssistantAgent set to RUNNING")

            assistant = await self.get_assistant(**kwargs)
            if not assistant:
                # print("======助手不存在==========")
                all_assistant = await assistant_service.get_agent_assistant()
                all_assistant_name = [assistant_item.get("name") for assistant_item in all_assistant]
                answer = f"助手不存在，请选择以下助手{all_assistant_name}"
                self.error = "助手不存在"
                self.add_log("执行失败", self.error)

                async for error_message in self.chat_stream(
                    user_query=user_query,
                    conversation_history=conversation_history,
                    system_prompt=ERROR_SYSTEM_PROMPT.format(error_message=answer, user_query=user_query),
                    status=ExecuteStatus.ERROR,
                ):
                    yield error_message

                self.state = AgentState.FAILED
                logger.error(self.error)
                return

            self.result["assistant"] = assistant
            self.add_log("获取助手信息", assistant)
            # assistant_markdown_data = assistant_to_markdown(assistant)

            self.result["output"] = f"助手信息：{assistant.get('name')}\n 助手描述：{assistant.get('description')}"
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=ExecuteStatus.COMPLETED,
                output=assistant,
                message=f"获取[{assistant.get('name')}]助手信息",
            )
            self.state = AgentState.COMPLETED
            logger.info("AssistantAgent execution completed successfully")
            # self.log.append({"title": "执行完成,输出数据", "content": assistant_markdown_data})
        except Exception as e:
            error_msg = f"AssistantAgent execute error: {str(e)}"
            logger.error(error_msg)
            self.error = error_msg
            self.state = AgentState.FAILED
            self.add_log("系统执行失败", self.error)
            yield YieldResponse(
                name=f"{self.name}_error",
                type=ResponseType.ERROR,
                status=ExecuteStatus.ERROR,
                message=error_msg,
            )

    async def get_assistant(self, **kwargs):
        """获取助手信息"""
        assistant_id = kwargs.get("assistant_id")
        assistant_name = kwargs.get("assistant_name")
        # print("assistant_id==========", assistant_id)

        logger.debug(f"Searching for assistant - ID: {assistant_id}, Name: {assistant_name}")

        assistant = None
        if assistant_id:
            logger.debug(f"Looking up assistant by ID: {assistant_id}")
            assistant = await assistant_service.get_assistant_by_id(assistant_id)

        if not assistant and assistant_name:
            logger.debug(f"Looking up assistant by name: {assistant_name}")
            assistant = await assistant_service.get_assistant_by_name(assistant_name)

        if not assistant:
            logger.warning("No assistant found with provided parameters")
        else:
            logger.info(f"Assistant retrieved successfully: {assistant.get('name', 'Unknown')}")

        return assistant
