#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
槽位相关的数据模型定义
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SlotStatus(Enum):
    """槽位状态"""

    EMPTY = "empty"  # 空槽位
    FILLED = "filled"  # 已填充


class ValidationResult(BaseModel):
    """槽位验证结果"""

    status: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    suggestion: Optional[str] = None
    value: Optional[Any] = None
    field_errors: Optional[Dict[str, str]] = None


class SlotConstraint(BaseModel):
    """槽位约束条件"""

    name: str
    description: str
    data_type: str = "string"  # string, number, boolean, dict, list
    required_format: str = "无"
    validator_rules: Optional[List[str]] = []
    example_value: Optional[str] = None

    def to_prompt(self) -> str:
        """将槽位约束条件转换为提示词"""
        prompt = f"""
        名称: {self.name}
        描述: {self.description}
        数据类型: {self.data_type}
        所需格式: {self.required_format}
        验证规则:
            {[f"*{rule}*" for rule in self.validator_rules] if self.validator_rules else "无"}
        示例值: {self.example_value if self.example_value else "无"}
        """
        return prompt
