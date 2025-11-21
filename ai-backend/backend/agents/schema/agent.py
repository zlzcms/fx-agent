# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-05 16:19:47
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 21:22:40
import asyncio
import time

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, Generator, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.agents.config.prompt.agent import (
    CHAT_SYSTEM_PROMPT,
)
from backend.agents.config.setting import settings
from backend.agents.tools.data_export_tool import DataExportTool
from backend.agents.utils.format_output import convert_to_dict
from backend.common.logging_chatopenai import LoggingChatOpenAI


class AgentState(Enum):
    """智能体状态枚举"""

    INIT = "init"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InterruptedException(Exception):
    """中断异常，用于处理用户主动中断"""

    pass


class ExecuteStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ResponseType(Enum):
    CHAT = "chat"
    ERROR = "error"
    FILE = "file"
    COMPLETED = "completed"
    INFO = "info"
    WARNING = "warning"
    EXECUTE = "execute"
    MD_INFO = "md_info"
    FINAL = "final"
    PLAN = "plan"
    SUMMARIZE = "summarize"


class YieldResponse(BaseModel):
    name: str
    type: ResponseType
    status: ExecuteStatus
    message: str
    file: Optional[dict] = None
    result: Optional[Any] = None
    output: Optional[Any] = None

    def to_dict(self):
        result = {
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "message": self.message,
        }
        if self.file:
            result["file"] = self.file
        if self.result:
            result["result"] = self.result
        if self.output:
            result["output"] = self.output
        return result


class ExtractParametersConstraint(BaseModel):
    """提取参数"""

    name: str
    description: str
    required: bool = False
    data_type: str = "string"
    validator_rules: Optional[List[str]] = []
    example_value: Optional[str] = None

    def to_prompt(self) -> str:
        """参数约束条件转换为提示词"""
        prompt = f"""
        名称: {self.name}
        描述: {self.description}
        是否必填: {self.required}
        值的类型: {self.data_type}
        提取规则:
            {"。".join(self.validator_rules) if self.validator_rules else "无"}
        提取到值的示例: {f"{self.name}: {self.example_value}" if self.example_value else "无"}
        """
        return prompt

    def to_dict(self) -> Dict[str, Any]:
        """参数约束条件转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "data_type": self.data_type,
            "validator_rules": self.validator_rules,
            "example_value": self.example_value,
        }


class Base(ABC):
    """智能体基类"""

    def __init__(self, name: str, config: Dict[str, Any] = {}):
        self.name = name
        self.config = config
        self.state = AgentState.INIT
        self.llm = None
        self.data_export_tool = DataExportTool(name, self.config.get("export_base_path"))
        self.execute_info = []
        self.error = None
        self.result = {}
        self.log = []
        self.bebug = []
        self.interruption_checker: Optional[Callable[[], bool]] = None  # 中断检查函数
        self._init_instance()

    def _init_instance(self):
        """Initialize the LLM and state graph"""
        try:
            llm_config = self.config.get("llm", {})
            api_key = llm_config.get("api_key", settings.GENERAL_CHAT_LLM_API_KEY)
            base_url = llm_config.get("base_url", settings.GENERAL_CHAT_LLM_BASE_URL)
            model_name = llm_config.get("model_name", settings.GENERAL_CHAT_LLM_MODEL_NAME)
            temperature = llm_config.get("temperature", settings.GENERAL_CHAT_LLM_TEMPERATURE)
            model_id = llm_config.get("id")  # 获取模型ID
            # Initialize LLM with logging
            self.llm = LoggingChatOpenAI(
                intent_name=self.name,
                model_alias_name=llm_config.get("name", "unknown"),
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                temperature=temperature,
                timeout=llm_config.get("timeout", 60),
                max_retries=llm_config.get("max_retries", 2),
                model_id=model_id,  # 传递模型ID
            )
        except Exception as e:
            raise e

    @abstractmethod
    async def execute(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """执行任务的抽象方法"""
        pass

    def cleanup(self) -> None:
        """任务执行后的清理工作"""
        self.result = {}
        self.state = AgentState.INIT

    def add_log(self, title: str, content: Any):
        self.log.append({"title": title, "content": content})

    def set_interruption_checker(self, checker: Callable[[], bool]):
        """设置中断检查函数"""
        self.interruption_checker = checker

    def check_interruption(self):
        """检查是否需要中断执行"""
        if self.interruption_checker and self.interruption_checker():
            raise InterruptedException("任务已被用户中断")

    def _convert_history_to_messages(self, conversation_history: List[Dict[str, str]]) -> List[BaseMessage]:
        """Convert conversation history to LangChain message objects"""
        messages = []
        for msg in conversation_history:
            if isinstance(msg, dict):
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
            elif isinstance(msg, BaseMessage):
                messages.append(msg)
        return messages

    def _get_history_messages(
        self, user_query: str, conversation_history: Optional[List] = None, system_prompt: str = None
    ) -> List[BaseMessage]:
        """
        Prepare graph state with conversation history and current message

        Args:
            user_query: 用户当前的查询
            conversation_history: 历史对话列表
            system_prompt: 系统提示词
            enable_compression: 是否启用历史对话压缩（默认False）
            min_rounds: 压缩的最小轮数阈值（默认3轮）

        Returns:
            准备好的消息列表
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        if conversation_history:
            history_messages = self._convert_history_to_messages(conversation_history)
            messages.extend(history_messages)

        messages.append(HumanMessage(content=user_query))

        return messages

    async def chat_stream(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        try:
            status = kwargs.get("status", ExecuteStatus.RUNNING)
            system_prompt = kwargs.get("system_prompt", CHAT_SYSTEM_PROMPT)
            print("=========system_prompt===============", system_prompt)
            messages = self._get_history_messages(user_query, [], system_prompt)
            async for chunk in self.stream(messages, f"对话【{user_query}】"):
                yield YieldResponse(
                    name=f"{self.name}_{status.value}_chat",
                    type=ResponseType.CHAT,
                    status=status,
                    message=chunk.content,
                ).to_dict()
        except Exception as e:
            raise Exception(f"对话失败: {str(e)}")

    def chat_stream_sync(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> Generator[YieldResponse, None, None]:
        """同步流式对话"""
        try:
            status = kwargs.get("status", ExecuteStatus.RUNNING)
            system_prompt = kwargs.get("system_prompt", CHAT_SYSTEM_PROMPT)
            messages = self._get_history_messages(user_query, [], system_prompt)

            for chunk in self.stream_sync(messages, f"对话【{user_query}】"):
                yield YieldResponse(
                    name=f"{self.name}_{status.value}_chat",
                    type=ResponseType.CHAT,
                    status=status,
                    message=chunk.content,
                )
        except Exception as e:
            raise Exception(f"对话失败: {str(e)}")

    async def _invoke_with_interruption_check(self, messages: List[BaseMessage]) -> AIMessage:
        """
        带中断检查的异步 invoke
        使用 asyncio.Task 包装，支持中断取消
        """
        # 创建异步调用任务
        task = asyncio.create_task(self.llm.ainvoke(messages))

        # 定期检查中断状态，同时等待任务完成
        check_interval = 0.1  # 每0.1秒检查一次
        while not task.done():
            try:
                # 检查中断
                self.check_interruption()
                # 等待一小段时间或任务完成
                await asyncio.wait({task}, timeout=check_interval)
            except InterruptedException:
                # 取消任务
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise

        # 返回结果
        return await task

    def invoke(self, messages: List[BaseMessage], log: str = "") -> AIMessage:
        """
        同步 invoke 方法
        注意：在异步环境中应该使用 ainvoke 以支持中断
        """
        try:
            if log:
                self.bebug.append(log)
            start_time = time.time()

            # 调用前检查中断
            self.check_interruption()

            # 使用同步调用
            response = self.llm.invoke(messages)

            response_dict = convert_to_dict(response)
            duration = time.time() - start_time
            self.bebug.append(f"耗时: {duration} 秒")
            del response_dict["content"]
            self.bebug.append(f"响应信息：{response_dict}")
            self.bebug.append("\n")
            return response
        except InterruptedException:
            # 中断异常需要向上传播
            raise
        except Exception as e:
            raise Exception(str(e))

    async def ainvoke(self, messages: List[BaseMessage], log: str = "") -> AIMessage:
        """异步 invoke 方法，支持中断"""
        try:
            if log:
                self.bebug.append(log)
            start_time = time.time()

            # 使用带中断检查的异步调用
            response = await self._invoke_with_interruption_check(messages)

            response_dict = convert_to_dict(response)
            duration = time.time() - start_time
            self.bebug.append(f"耗时: {duration} 秒")
            del response_dict["content"]
            self.bebug.append(f"响应信息：{response_dict}")
            self.bebug.append("\n")
            return response
        except InterruptedException:
            # 中断异常需要向上传播
            raise
        except Exception as e:
            raise Exception(str(e))

    def stream_sync(self, messages: List[BaseMessage], log: str = "") -> Generator[AIMessage, None, None]:
        """
        同步流式返回AI响应

        返回:
            Generator[AIMessage]: 同步生成器，每次yield一个AIMessage对象
        """
        try:
            if log:
                self.bebug.append(log)
            start_time = time.time()
            # stream 返回的是同步生成器
            for chunk in self.llm.stream(messages):
                yield chunk
            duration = time.time() - start_time
            self.bebug.append(f"耗时: {duration} 秒")
            self.bebug.append("\n")
        except Exception as e:
            raise Exception(str(e))

    async def stream(self, messages: List[BaseMessage], log: str = "") -> AsyncGenerator:
        """
        异步流式返回AI响应，支持中断
        """
        try:
            if log:
                self.bebug.append(log)
            start_time = time.time()

            # 使用异步流 - astream() 现在是真正的异步生成器
            async for chunk in self.llm.astream(messages):
                # 每次输出前检查中断
                self.check_interruption()
                yield chunk

            duration = time.time() - start_time
            self.bebug.append(f"耗时: {duration} 秒")
            self.bebug.append("\n")
        except InterruptedException:
            # 中断异常需要向上传播
            raise
        except Exception as e:
            raise Exception(str(e))
