#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能代理主类
使用模块化的管理器结构
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.agents.intent_recognition_agent import IntentRecognitionAgent
from backend.agents.manager.factories.intent_factory import IntentHandlerFactory
from backend.agents.schema.agent import AgentState
from backend.common.log import logger

# 导入新的模块化组件


class Agent:
    """智能代理主类"""

    def __init__(
        self, conversation_history: Optional[List] = None, chat_id: str = None, config: Optional[Dict[str, Any]] = None
    ):
        self.conversation_history = conversation_history
        self.chat_id = chat_id
        self.intent_agent = None
        self.intent_result = {}
        self.messages = []
        self.config = config or {}
        self.intent_recognition_agent = IntentRecognitionAgent(config=self.config)

    async def auto_orchestrate(
        self, user_query: str, conversation_history: Optional[List] = None, action: str = "auto", **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """智能编排主方法"""
        from backend.agents.schema.agent import InterruptedException

        try:
            async for intent_message in self.intent_recognition_agent.execute(
                user_query=user_query,
                conversation_history=conversation_history,
                action=action,
                **kwargs,
            ):
                yield intent_message

            yield {
                "type": "log",
                "title": "意图识别",
                "content": self.intent_recognition_agent.log,
            }
            bebug = self.intent_recognition_agent.bebug
            if self.intent_recognition_agent.state != AgentState.COMPLETED:
                return
            # return
            # 检查意图识别结果是否有效
            intent_data = self.intent_recognition_agent.result.get("output", {})
            # print('=======intent_result=========',intent_result)
            if not intent_data or not isinstance(intent_data, dict) or not intent_data.get("selected_service"):
                error_msg = "意图识别结果为空或格式不正确"
                logger.error(error_msg)
                yield {"type": "error", "message": error_msg}
                return

            try:
                handler = IntentHandlerFactory.create_handler(intent_data["selected_service"], self)
                # kwargs 中已经包含了 interruption_checker，直接传递
                async for message in handler.handle(user_query, conversation_history, intent_data, **kwargs):
                    yield message

                bebug = bebug + handler.task_manager.bebug if handler.task_manager.bebug else []
                yield {
                    "type": "log",
                    "title": "bebug信息",
                    "content": [{"title": "耗时信息", "content": "\n".join(bebug)}],
                }
            except InterruptedException:
                # 捕获中断异常并向上传播
                raise

            except Exception as e:
                error_msg = f"创建或执行处理器失败: {str(e)}"
                logger.error(error_msg)
                yield {"type": "error", "message": error_msg}

        except InterruptedException:
            # 捕获中断异常并向上传播
            raise
        except Exception as e:
            logger.error(f"❌ intent result is None: {str(e)}")
            yield {"type": "error", "message": f"❌ intent result is None: {str(e)}"}


# 创建全局代理实例
agent = Agent()
