# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:02:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 17:20:14
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.config.prompt.general_chat import GENERAL_CHAT_SYSTEM_PROMPT
from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.services.assistant_service import assistant_service
from backend.agents.utils.format_output import convert_list_to_dict
from backend.common.log import logger


class GeneralChatAgent(Base):
    """
    通用聊天智能体，专门负责聊天
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        super().__init__("data_analyze", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())

    async def execute(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行通用聊天任务"""
        try:
            interruption_checker = kwargs.get("interruption_checker")
            if interruption_checker:
                self.set_interruption_checker(interruption_checker)
            self.state = AgentState.RUNNING
            logger.debug("GeneralChatAgent set to RUNNING")

            llm_response_type = kwargs.get("llm_response_type", "stream")
            assistants = await assistant_service.get_agent_assistant()
            assistants_prompt = [f"【{assistant.get('name')}】服务" for assistant in assistants]
            prompt = kwargs.get(
                "system_prompt",
                GENERAL_CHAT_SYSTEM_PROMPT.format(
                    assistants="\n".join(assistants_prompt),
                ),
            )
            self.result["prompt"] = prompt

            self.add_log("组装提示词", prompt)

            messages = self._get_history_messages(user_query, conversation_history, prompt)
            logger.debug(f"GeneralChatAgent Prepared {len(messages)} messages for LLM")

            if llm_response_type == "stream":
                all_chunk = ""
                chunk_count = 0
                async for chunk in self.stream(messages, f"通用聊天【{user_query}】"):
                    all_chunk += chunk.content
                    chunk_count += 1
                    yield YieldResponse(
                        name=f"{self.name}_chat",
                        type=ResponseType.CHAT,
                        status=ExecuteStatus.RUNNING,
                        message=chunk.content,
                    )
                self.result["data"] = all_chunk
                self.result["response"] = {"content": all_chunk}
            else:
                response = await self.ainvoke(messages, f"通用聊天【{user_query}】")
                yield YieldResponse(
                    name=f"{self.name}_chat",
                    type=ResponseType.CHAT,
                    status=ExecuteStatus.RUNNING,
                    message=response.content,
                )
                self.result["data"] = response.content
                self.result["response"] = convert_list_to_dict(response)
            logger.debug(f"GeneralChatAgent Response: {self.result['response']}")
            self.add_log("执行完成,输出数据", self.result["data"])
            self.state = AgentState.COMPLETED
            self.result["output"] = self.result["data"]
            logger.info("GeneralChatAgent execution completed successfully")
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=ExecuteStatus.COMPLETED,
                output=self.result["output"],
                message="AI对话完成",
            )
        except Exception as e:
            error_msg = f"GeneralChatAgent execution failed:{str(e)}"
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
