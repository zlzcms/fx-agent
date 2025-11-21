# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:02:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:38:59
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import uuid

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.agents.extract_parameters_agent import ExtractParametersAgent
from backend.agents.config.examples import intent_examples, intent_parameters_examples
from backend.agents.config.mcp import get_data_sources_prompt
from backend.agents.config.prompt.agent import ERROR_SYSTEM_PROMPT
from backend.agents.config.prompt.extract_parameters import INTENT_PARAMETERS_PROMPT
from backend.agents.config.prompt.intent_analysis import INTENT_PROMPT
from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.services.assistant_service import assistant_service
from backend.agents.utils.format_output import convert_to_dict, response_to_json, simulate_stream
from backend.common.log import logger


class IntentRecognitionAgent(Base):
    """
    意图识别智能体，专门负责识别用户意图
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        # 确保有 llm 配置，但保留已有的配置
        if "llm" not in config:
            config["llm"] = {}
        super().__init__("intent_recognition", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.extract_parameters_agent = ExtractParametersAgent(task_id=task_id, config=config)

    async def get_intent_prompt(self, user_query: str):
        """获取意图识别提示词"""
        try:
            agent_assistant = await assistant_service.get_agent_assistant()
            data_sources = get_data_sources_prompt()

            prompt = INTENT_PROMPT.substitute(
                user_query=user_query,
                agent_assistant=agent_assistant,
                data_sources=data_sources,
                examples=intent_examples,
                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            return prompt
        except Exception as e:
            error_msg = f"获取意图提示词失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def get_intent_parameters_prompt(self, user_query: str, intent_data: Dict[str, Any]):
        """获取意图识别提示词"""
        try:
            parameters = get_data_sources_prompt(intent_data.get("data_sources"))
            if intent_data.get("selected_service") in ["agent", "report"]:
                next_step = "正在获取数据"
            else:
                next_step = "正在制定任务计划"
            prompt = INTENT_PARAMETERS_PROMPT.substitute(
                parameters=parameters,
                examples=intent_parameters_examples,
                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_query=user_query,
                next_step=next_step,
            )

            return prompt
        except Exception as e:
            error_msg = f"获取意图参数提示词失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def execute(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行意图识别任务"""
        try:
            interruption_checker = kwargs.get("interruption_checker")
            if interruption_checker:
                self.set_interruption_checker(interruption_checker)
            self.log = []
            self.state = AgentState.RUNNING
            logger.info("Extracting intent parameters")

            action = kwargs.get("action")
            prompt = await self.get_intent_prompt(user_query)
            self.add_log("提示词模板", INTENT_PROMPT.template)
            self.add_log("组装提示词", prompt)

            # print("intent_recognition_agent prompt=========", prompt)

            messages = self._get_history_messages(user_query, conversation_history, prompt)
            # print("=========extract_intent messages=========", messages)
            response = await self.ainvoke(messages, f"意图识别【{user_query}】")
            # print("意图识别response=========", response.content)
            logger.info(f"extract_intent LLM response received, length: {len(response.content)}")

            success, data = response_to_json(response.content)
            logger.debug(f"extract_intent Response JSON conversion success: {success}")

            self.result["prompt"] = prompt
            self.result["response"] = convert_to_dict(response)
            # print("self.result=========", self.result["response"])
            # self.add_log("输出返回的结果", self.result["response"])
            log_result = self.result["response"]
            if not success:
                error_msg = f"JSON解析失败，原始内容: {response.content[:200]}..."
                logger.error(error_msg)
                yield YieldResponse(
                    name=f"{self.name}_error",
                    type=ResponseType.ERROR,
                    status=ExecuteStatus.ERROR,
                    message=error_msg,
                )
                return

            if not data or not isinstance(data, dict):
                error_msg = "解析后的数据为空或不是字典格式"
                logger.error(error_msg)
                yield YieldResponse(
                    name=f"{self.name}_error",
                    type=ResponseType.ERROR,
                    status=ExecuteStatus.ERROR,
                    message=error_msg,
                )
                return

            if data.get("tip") and data.get("selected_service") != "chat":
                async for chunk in simulate_stream(f"{data.get('tip')}\n"):
                    yield YieldResponse(
                        name=f"{self.name}_tip",
                        type=ResponseType.CHAT,
                        status=ExecuteStatus.RUNNING,
                        message=chunk,
                    )

            data = self.check_action(action, data)
            # print("intent_recognition_agent data=========", data)

            if data.get("data_sources", []) and data.get("selected_service") != "chat":
                prompt = await self.get_intent_parameters_prompt(user_query, data)
                # print("参数提取prompt=========", prompt)
                parameters_data = {}
                async for yieldResponse in self.extract_parameters_agent.execute(user_query, prompt):
                    if yieldResponse.status == ExecuteStatus.COMPLETED:
                        parameters_data = yieldResponse.output
                        break
                self.bebug = self.bebug + self.extract_parameters_agent.bebug
                if parameters_data.get("tip") and data.get("selected_service") != "chat":
                    async for chunk in simulate_stream(f"{parameters_data.get('tip')}\n"):
                        yield YieldResponse(
                            name=f"{self.name}_tip",
                            type=ResponseType.CHAT,
                            status=ExecuteStatus.RUNNING,
                            message=chunk,
                        )
                data["data_sources"] = parameters_data.get("data_sources")
                # print("参数提取data_sources=========", data["data_sources"])

            if data["data_sources"] and data.get("do_next") == False:
                data["do_next"] = True
            log_result["content"] = json.dumps(data, ensure_ascii=False, indent=2)
            # print("log_result=========", log_result)
            self.add_log("输出返回的结果", log_result)
            intent_result = {"success": success, "data": data}

            self.result["data"] = intent_result
            # print("intent_result=========", intent_result)
            logger.debug(f"Intent extraction result: {intent_result.get('success', False)}")

            intent_chat = ""
            intent_data = intent_result["data"]

            if not intent_result["success"]:
                intent_chat = intent_result.get("error")

            if intent_chat:
                self.error = f"Intent recognition failed: {intent_chat}"
                logger.error(self.error)
                self.add_log("返回失败", intent_chat)

                async for error_message in self.chat_stream(
                    user_query=user_query,
                    conversation_history={},
                    system_prompt=ERROR_SYSTEM_PROMPT.format(error_message=intent_chat, user_query=user_query),
                    status=ExecuteStatus.ERROR,
                ):
                    yield error_message
                self.state = AgentState.FAILED
                return

            # Add streaming simulation for intent data
            if intent_data.get("do_next") == False:
                if intent_data.get("suggested_response"):
                    async for chunk in simulate_stream(intent_data.get("suggested_response")):
                        yield YieldResponse(
                            name=f"{self.name}_suggested_response",
                            type=ResponseType.CHAT,
                            status=ExecuteStatus.RUNNING,
                            message=chunk,
                        )
                logger.info(
                    f"do_next:{intent_data.get('do_next')},suggested_response:{intent_data.get('suggested_response')}"
                )
                return

            logger.info("Intent recognition completed successfully")
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=ExecuteStatus.COMPLETED,
                output=intent_data,
                message="意图识别完成",
            )

            self.result["output"] = intent_data
            self.state = AgentState.COMPLETED

        except Exception as e:
            error_msg = f"execute error: {str(e)}"
            logger.error(f"IntentRecognitionAgent execution failed: {error_msg}")
            self.error = error_msg
            self.state = AgentState.FAILED
            self.add_log("系统执行失败", self.error)
            yield YieldResponse(
                name=f"{self.name}_error",
                type=ResponseType.ERROR,
                status=ExecuteStatus.ERROR,
                message=error_msg,
            )

    def check_action(self, action: str, intent_data: Dict[str, Any]):
        """检查动作"""
        selected_service = intent_data.get("selected_service")
        if action == "agent" and selected_service and selected_service in ["mcp"]:
            intent_data["selected_service"] = "report"
        if action == "chat" and selected_service and selected_service in ["agent", "report"]:
            intent_data["selected_service"] = "mcp"
        return intent_data
