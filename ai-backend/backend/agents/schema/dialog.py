#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话状态管理模型
仅包含数据模型定义，不包含业务逻辑
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DialogState(Enum):
    """对话状态枚举"""

    INIT = "init"  # 初始状态
    SLOT_FILLING = "slot_filling"  # 槽位填充中
    CONFIRMING = "confirming"  # 确认中
    EXECUTING = "executing"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    INTERRUPTED = "interrupted"  # 被用户中断


class DialogResponse(BaseModel):
    """对话响应模型"""

    type: str  # prompt, confirmation, result, error
    message: str
    next_action: str
    data: Optional[Dict[str, Any]] = None


class IntentType(Enum):
    """意图类型枚举"""

    QUERY = "query"
    REPORT = "report"
    CHAT = "chat"

    @property
    def description(self) -> str:
        """获取意图类型的中文描述"""
        descriptions = {"query": "数据查询", "report": "报表生成", "chat": "对话聊天"}
        return descriptions.get(self.value, self.value)

    @property
    def name_cn(self) -> str:
        """获取意图类型的中文名称"""
        names = {"query": "查询", "report": "报表", "chat": "聊天"}
        return names.get(self.value, self.value)


class DialogParam(BaseModel):
    """对话参数模型"""

    intent_type: IntentType
    query_user_condition: Optional[str] = None
    query_user_condition_value: Optional[Any] = None
    query_data: Optional[List[Dict[str, Any]]] = None
    query_data_condition: Optional[Dict[str, Any]] = None
    assistant_name: Optional[str] = None
