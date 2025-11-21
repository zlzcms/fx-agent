#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GetDataRequest(BaseModel):
    query_type: Optional[str] = Field(None, description="查询类型")
    query_types: Optional[List[str]] = Field(None, description="查询类型列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    context: Optional[str] = Field(None, description="查询上下文，用于理解查询意图")
    is_compress_data: Optional[bool] = Field(True, description="是否压缩数据")


# class QueryRequest(BaseModel):
#     data_sources: Optional[Dict[str, Any]] = Field(None, description="查询数据源")


# SSE请求模型
class SSERequest(BaseModel):
    query_type: str = Field(..., description="查询类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    interval: Optional[int] = Field(5, description="数据推送间隔，单位：秒")
    max_events: Optional[int] = Field(0, description="最大事件数量，0表示不限制")
    is_compress_data: Optional[bool] = Field(True, description="是否压缩数据")


# 查询元数据模型
class QueryMetadata(BaseModel):
    query_time: Optional[str] = Field(None, description="查询耗时（秒）")
    count: Optional[int] = Field(None, description="数据条数")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    failed_queries: Optional[Dict[str, Any]] = Field(None, description="失败的查询类型列表")
    successful_queries: Optional[List[str]] = Field(None, description="成功的查询类型列表")


# 查询响应模型
class QueryResponse(BaseModel):
    success: bool = Field(..., description="查询是否成功")
    message: str = Field(..., description="查询结果消息")
    data: Optional[Any] = Field(None, description="查询结果数据")
    metadata: Optional[QueryMetadata] = Field(None, description="查询元数据")


# 查询数据响应模型
class QueryDataResponse(BaseModel):
    success: bool = Field(..., description="查询是否成功")
    message: str = Field(..., description="查询结果消息")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    data: Optional[Any] = Field(None, description="查询结果数据")
    sql_info: Optional[Dict[str, Any]] = Field(None, description="SQL查询信息")
    query_metadata: Optional[Dict[str, Any]] = Field(None, description="查询元数据")

    def to_dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "parameters": self.parameters,
            "data": self.data,
            "sql_info": self.sql_info,
            "query_metadata": self.query_metadata,
        }


# 对话消息模型
class ConversationMessage(BaseModel):
    role: str = Field(..., description="消息角色，如'user'或'assistant'")
    content: str = Field(..., description="消息内容")


# 意图分析请求模型
class IntentAnalysisRequest(BaseModel):
    message: str = Field(..., description="需要分析的用户消息")
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=None, description="对话历史记录，用于上下文理解"
    )


# 意图分析响应模型
class IntentAnalysisResponse(BaseModel):
    success: bool = Field(..., description="分析是否成功")
    message: Optional[str] = Field(None, description="分析结果消息")
    query_type: Optional[str] = Field(None, description="识别的查询类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="提取的查询参数")
    confidence: float = Field(..., description="分析结果的置信度")
