# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-08-06 11:05:04
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:36:53
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

from typing import Any, AsyncGenerator, Dict

from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.utils.format_output import convert_to_dict, response_to_json
from backend.common.log import logger


class ExtractParametersAgent(Base):
    """
    提取参数智能体，专门负责提取参数
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        super().__init__("extract_parameters", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())

    async def execute(self, message_content: str, prompt: str = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """提取参数"""
        try:
            interruption_checker = kwargs.get("interruption_checker")
            if interruption_checker:
                self.set_interruption_checker(interruption_checker)
            self.state = AgentState.RUNNING
            logger.debug("ExtractParametersAgent set to RUNNING")
            self.add_log("提示词", prompt)
            messages = self._get_history_messages(message_content, None, prompt)
            # print("参数提取messages=========", messages)
            response = await self.ainvoke(messages, f"提取参数【{message_content}】")
            success, data = response_to_json(response.content)
            self.add_log("执行完成,输出数据", data)
            if success:
                status = ExecuteStatus.COMPLETED
                message = "参数提取完成"
            else:
                status = ExecuteStatus.ERROR
                message = "参数提取失败"
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=status,
                output=data,
                result=convert_to_dict(response),
                message=message,
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
