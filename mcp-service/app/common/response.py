#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional

from app.models.schema import QueryMetadata, QueryResponse


class ResponseFactory:
    """统一响应工厂类"""

    @staticmethod
    def error_response(
        message: str,
        error_code: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueryResponse:
        """创建错误响应"""
        query_metadata = QueryMetadata(
            parameters=parameters,
            **metadata if metadata else {"error": error_code or message}
        )
        return QueryResponse(
            success=False, message=message, data=None, metadata=query_metadata
        )

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "操作成功",
        metadata: Optional[QueryMetadata] = None,
    ) -> QueryResponse:
        """创建成功响应"""
        return QueryResponse(
            success=True, message=message, data=data, metadata=metadata
        )

    @staticmethod
    def create_error_dict(
        message: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """创建错误字典（用于内部组件）"""
        return {
            "success": False,
            "message": message,
            "data": None,
            "metadata": metadata or {"error": error_code or message},
        }
