from enum import Enum
from typing import Annotated, Any, Dict, Optional, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    """Agent state is a list of messages."""

    messages: Annotated[list, add_messages]


class AIResponse(BaseModel):
    """AI响应Schema"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Any = Field(..., description="数据")
    error: str = Field(None, description="错误信息")

    def to_dict(self):
        """将响应转换为字典"""
        # 处理IntentAnalysisResult
        if hasattr(self.data, "query_type") and hasattr(self.data, "parameters") and hasattr(self.data, "confidence"):
            data_dict = {
                "query_type": self.data.query_type,
                "parameters": self.data.parameters,
                "confidence": self.data.confidence,
            }
        # 处理其他对象
        elif hasattr(self.data, "to_dict"):
            data_dict = self.data.to_dict()
        else:
            data_dict = self.data

        return {"success": self.success, "message": self.message, "data": data_dict}


class ExecuteStatus(str, Enum):
    """执行状态枚举"""

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RUNNING = "running"


class ExecuteType(str, Enum):
    """执行类型枚举"""

    PROGRESS = "progress"  # 进度更新
    RESULT = "result"  # 最终结果
    ERROR = "error"  # 错误信息
    INFO = "info"  # 信息通知
    WARNING = "warning"  # 警告信息
    EXECUTE = "execute"  # 执行信息
    MD_INFO = "md_info"
    FINAL = "final"


class AgentExecuteResponse(BaseModel):
    """智能体执行统一响应模型"""

    type: ExecuteType = Field(..., description="响应类型")
    type_name: Optional[str] = Field(None, description="响应类型名称")
    status: ExecuteStatus = Field(..., description="执行状态")
    message: str = Field(..., description="响应消息")
    progress: Optional[int] = Field(None, description="执行进度(0-100)", ge=0, le=100)
    result_type: Optional[str] = Field(None, description="结果类型")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    timestamp: Optional[str] = Field(None, description="时间戳")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    file: Optional[dict] = Field(None, description="文件路径")
    success: Optional[bool] = Field(None, description="是否成功")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result_dict = {"type": self.type.value, "status": self.status.value, "message": self.message}

        if self.progress is not None:
            result_dict["progress"] = self.progress
        if self.result is not None:
            # 处理result对象
            if hasattr(self.result, "to_dict"):
                result_dict["result"] = self.result.to_dict()
            else:
                result_dict["result"] = self.result
        if self.error is not None:
            result_dict["error"] = self.error
        if self.metadata is not None:
            result_dict["metadata"] = self.metadata
        if self.timestamp is not None:
            result_dict["timestamp"] = self.timestamp
        if self.agent_id is not None:
            result_dict["agent_id"] = self.agent_id
        if self.type_name is not None:
            result_dict["type_name"] = self.type_name
        if self.file is not None:
            result_dict["file"] = self.file
        if self.success is not None:
            result_dict["success"] = self.success
        return result_dict
