from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class AgentType(Enum):
    """智能体类型枚举"""

    MCP_DATA = "mcp_data"
    DATA_PROCESSING = "data_processing"
    AI_ANALYSIS = "ai_analysis"
    AI_ASSISTANT_ANALYSIS = "ai_assistant_analysis"  # 新增AI助手分析
    RISK_ANALYSIS = "risk_analysis"  # 新增风控分析
    GENERAL_CHAT = "general_chat"  # 新增通用对话类型
    AI_TASK_PLANNER = "ai_task_planner"  # 新增AI任务规划器
    INTENT_ANALYSIS = "intent_analysis"  # 新增意图分析
    REPORT_AGGREGATION = "report_aggregation"  # 新增报告聚合类型
    DATA_ANALYSIS = "data_analysis"  # 新增数据分析类型
    CUSTOM = "custom"


class AgentState(Enum):
    """智能体状态枚举"""

    INIT = "init"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseAgent(ABC):
    """智能体基类"""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        config: Dict[str, Any] = None,
        conversation_history: Optional[List] = None,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.is_busy = False
        self.conversation_history = conversation_history

    @abstractmethod
    async def execute(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """执行任务的抽象方法"""
        pass

    async def prepare(self, **kwargs) -> bool:
        """任务执行前的准备工作"""
        return True

    async def cleanup(self) -> None:
        """任务执行后的清理工作"""
        pass

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

    def _prepare_graph_state_with_history(
        self, message_content: str, conversation_history: Optional[List] = None, user_query: Optional[str] = None
    ) -> Dict[str, List[BaseMessage]]:
        """Prepare graph state with conversation history and current message"""
        messages = []

        # Add system message if provided
        if self.system_prompt:
            # print("system_prompt======================", self.system_prompt)
            messages.append(SystemMessage(content=self.system_prompt))

        # Add conversation history if available
        if conversation_history:
            history_messages = self._convert_history_to_messages(conversation_history)
            messages.extend(history_messages)

        # Add user query if available
        if user_query:
            messages.append(HumanMessage(content=f"用户问题：{user_query}"))

        # Add current message
        messages.append(HumanMessage(content=message_content))

        return {"messages": messages}
