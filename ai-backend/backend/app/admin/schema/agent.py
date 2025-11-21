# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-29 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-05 15:46:11
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Optional

from pydantic import BaseModel, Field


class SmartAssistantCreateRequest(BaseModel):
    """智能创建助手请求"""

    question: str = Field(..., description="问题")


class SmartAssistantCreateResponse(BaseModel):
    name: str = Field(..., description="助手名称")
    description: Optional[str] = Field(None, description="助手描述")
    model_definition: Optional[str] = Field(None, description="模型定义")

    # 输出相关配置
    table_output: Optional[Any] = Field(None, description="表格输出数据")
    document_output: Optional[Any] = Field(None, description="文档输出数据")


class ContentPolishRequest(BaseModel):
    """内容润色请求"""

    content: str = Field(..., description="需要润色的内容")
    role: Optional[str] = Field(None, description="助手角色")
    task: Optional[str] = Field(None, description="助手任务")


class ContentPolishResponse(BaseModel):
    """内容润色响应"""

    original_content: str = Field(..., description="原始内容")
    polished_content: str = Field(..., description="润色后的内容")
