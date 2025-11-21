#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIChatBase(BaseModel):
    """AI聊天基础模型"""

    title: str = Field(..., description="Chat title")
    model_id: Optional[str] = Field(None, description="AI model ID to use for this chat")
    user_id: Optional[int] = Field(None, description="User ID (integer)")
    status: Optional[bool] = Field(True, description="Chat status")

    model_config = ConfigDict(from_attributes=True)


class AIChatCreate(BaseModel):
    title: str = Field(..., description="Chat title")
    model_id: Optional[str] = Field(None, description="AI model ID to use for this chat")
    user_id: Optional[int] = Field(None, description="User ID (integer)")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Chat ID")
    channel: Optional[str] = Field(None, description="Channel identifier for tracking source")


class AIChatUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Chat title")
    status: Optional[bool] = Field(None, description="Chat status")
    model_id: Optional[str] = Field(None, description="AI model ID to use for this chat")
    history_summary: Optional[str] = Field(None, description="历史对话压缩摘要")
    summary_time: Optional[datetime] = Field(None, description="摘要生成时间")


class AIChatResponse(BaseModel):
    id: str = Field(..., description="Chat ID")
    user_id: int = Field(..., description="User ID")
    status: bool = Field(..., description="Chat status")
    title: str = Field(..., description="Chat title")
    model_id: Optional[str] = Field(None, description="AI model ID to use for this chat")
    channel: Optional[str] = Field(None, description="Channel identifier for tracking source")
    history_summary: Optional[str] = Field(None, description="历史对话压缩摘要")
    summary_time: Optional[datetime] = Field(None, description="摘要生成时间")
    created_time: datetime = Field(..., description="Creation timestamp")
    updated_time: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class AIChatMessageBase(BaseModel):
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: Optional[str] = Field("", description="Message content")
    response_data: Optional[Any] = Field(None, description="Query result data")
    is_interrupted: Optional[bool] = Field(False, description="Whether the message was interrupted")


class AIChatMessageCreate(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Message ID")
    chat_id: str = Field(..., description="Chat ID")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: Optional[str] = Field("", description="Message content")
    response_data: Optional[Any] = Field(None, description="Query result data")
    is_interrupted: Optional[bool] = Field(False, description="Whether the message was interrupted")


class AIChatMessageResponse(AIChatMessageBase):
    id: str = Field(..., description="Message ID")
    chat_id: str = Field(..., description="Chat ID")
    created_time: datetime = Field(..., description="Creation timestamp")
    updated_time: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    chat_id: str = Field(..., description="Chat ID", min_length=1)
    message: str = Field(..., description="User message", min_length=1)
    action: Optional[str] = Field(None, description="Action")
    channel: Optional[str] = Field(None, description="Channel")
    result_format: Optional[str] = Field(None, description="Result format")
    model_config = ConfigDict(
        validate_assignment=True,  # 添加验证配置
        extra="forbid",  # 禁止额外字段
    )

    def __init__(self, **data):
        super().__init__(**data)

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError("chat_id cannot be empty or whitespace")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or v.strip() == "":
            raise ValueError("message cannot be empty or whitespace")
        return v.strip()


class ChatCompletionResponse(BaseModel):
    chat_id: str = Field(..., description="Chat ID")
    message_id: str = Field(..., description="Message ID")
    content: str = Field(..., description="AI response content")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Status message")
    channel: str = Field(..., description="Channel")
