#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
槽位服务层，处理槽位相关的业务逻辑 - 简化版本
"""

from typing import Any, Callable, Dict, List, Optional

from backend.agents.agents.slot_extraction_agent import SlotExtractionAgent

from ..schema.slot import SlotConstraint, SlotStatus, ValidationResult


class Slot:
    """对话槽位 - 简化版本，不包含约束验证"""

    def __init__(
        self,
        name: str,
        description: str,
        constraint: List[SlotConstraint] | SlotConstraint = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
    ):
        self.name = name
        self.description = description
        self.constraint = constraint
        self.status = SlotStatus.EMPTY
        self.value = None
        self.agent = SlotExtractionAgent(
            agent_id="slot_extractor",
            config={"temperature": 0.1},  # 低温度以获得确定性结果
        )
        self.llm_response = None
        self.reasoning = []
        self.confidence = 0.0
        self.custom_validator: Optional[Callable[[Any], bool]] = custom_validator
        self.validation_result: Optional[ValidationResult] = None

    def fill(self, user_input: str, conversation_history: Optional[List] = None) -> bool:
        """填充槽位值，返回是否成功"""
        try:
            result = self.get_value(user_input, conversation_history)
            if not result:
                return False
            value = result.get("value")
            # 如果有自定义验证器，先进行验证
            if self.custom_validator:
                self.validation_result: ValidationResult = self.custom_validator(value)
                if not self.validation_result.status:
                    return False

                if self.validation_result.value:
                    value = self.validation_result.value

            # 直接填充值，不进行类型转换
            self.value = value
            self.status = SlotStatus.FILLED
            self.llm_response = result.get("llm_response")
            self.reasoning = result.get("reasoning", [])
            self.confidence = result.get("confidence", 0.0)

            return True

        except Exception:
            return False

    def get_value(self, user_input: str, conversation_history: Optional[List] = None) -> Any:
        """获取槽位值"""
        if isinstance(self.constraint, list):
            result = self.agent.extract_multiple_slots(user_input, self.constraint, conversation_history)
            return result
        elif isinstance(self.constraint, SlotConstraint):
            result = self.agent.extract_slot_value(user_input, self.constraint, conversation_history)
            return result
        else:
            return None


class SlotFrame:
    """槽位框架，管理一组相关槽位"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.slots: Dict[str, Slot] = {}
        self.reasoning = []
        self.validation_result: Optional[ValidationResult] = None

    def add_slot(self, slot: Slot) -> None:
        """添加槽位"""
        self.slots[slot.name] = slot

    def extract_slots(self, user_input: str, conversation_history: Optional[List] = None) -> bool:
        """提取槽位"""
        if not self.slots:
            self.validation_result = ValidationResult(status=False, value=None, message="没有添加槽位")
            return False
        for slot in self.slots.values():
            if slot.status == SlotStatus.EMPTY:
                if not slot.fill(user_input, conversation_history):
                    self.validation_result = slot.validation_result
                    return False
            self.reasoning.extend(slot.reasoning)
        return True
