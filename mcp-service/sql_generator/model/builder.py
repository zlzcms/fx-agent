from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field


# 有效的SQL操作符枚举
class Operator(str, Enum):
    EQUALS = "="
    NOT_EQUALS = "<>"
    NOT_EQUALS_ALT = "!="
    GREATER_THAN = ">"
    GREATER_EQUALS = ">="
    LESS_THAN = "<"
    LESS_EQUALS = "<="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT EXISTS"

    @classmethod
    def values(cls) -> tuple:
        """返回所有操作符的值"""
        return tuple(item.value for item in cls)


class ConditionOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    @classmethod
    def values(cls) -> tuple:
        """返回所有操作符的值"""
        return tuple(item.value for item in cls)


# 保留VALID_OPERATORS元组以保持向后兼容性
VALID_OPERATORS = Operator.values()


class ConditionModel(BaseModel):
    column: str = Field(..., description="列名")
    value: Any = Field(None, description="值")
    operator: Union[Operator, str] = Field(Operator.EQUALS, description="操作符")

    class Config:
        use_enum_values = False  # 保留枚举对象而不是转换为值
