#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import time

from typing import Any, Dict, List, Optional

import httpx

from backend.common.mcp_logger import mcp_logger
from backend.core.conf import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MCPClient:
    """用于与MCP服务交互的客户端"""

    def __init__(self, base_url=None, api_key=None, timeout=90):
        """初始化MCP客户端

        参数:
            base_url: MCP服务API的基础URL
            api_key: 用于认证的API密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or settings.MCP_SERVICE_URL
        self.api_key = api_key or settings.MCP_API_KEY
        self.timeout = timeout

    async def _make_request(self, url: str, payload: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """通用的HTTP请求方法，包含日志记录"""
        start_time = time.time()
        request_id = None

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            # 记录MCP请求
            request_id = mcp_logger.log_mcp_request(
                url=url, headers=headers, payload=payload, timeout=self.timeout, agent_id="HomeMCPClient_UNUSED"
            )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=payload)
                else:
                    response = await client.get(url, headers=headers, params=payload)

                response.raise_for_status()
                result = response.json()

                # 记录MCP响应
                response_time_ms = (time.time() - start_time) * 1000
                mcp_logger.log_mcp_response(
                    request_id=request_id,
                    response=result,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                )

                return result

        except httpx.HTTPStatusError as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"HTTP错误: {e.response.status_code} - {e.response.text}"

            logger.error(error_msg)

            # 记录MCP错误
            if request_id:
                mcp_logger.log_mcp_error(request_id, e, response_time_ms, url)

            return {
                "success": False,
                "message": f"HTTP错误: {e.response.status_code}",
                "data": None,
                "metadata": {"error": e.response.text},
            }
        except httpx.RequestError as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"请求错误: {str(e)}"

            logger.error(error_msg)

            # 记录MCP错误
            if request_id:
                mcp_logger.log_mcp_error(request_id, e, response_time_ms, url)

            return {"success": False, "message": error_msg, "data": None, "metadata": {"error": str(e)}}
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"意外错误: {str(e)}"

            logger.error(error_msg)

            # 记录MCP错误
            if request_id:
                mcp_logger.log_mcp_error(request_id, e, response_time_ms, url)

            return {"success": False, "message": error_msg, "data": None, "metadata": {"error": str(e)}}

    async def query_data(
        self, query_type: str, parameters: Dict[str, Any], context: Optional[str] = None
    ) -> Dict[str, Any]:
        """从MCP服务查询数据

        参数:
            query_type: 查询类型（如customer_data, transaction_data）
            parameters: 查询参数
            context: 可选的查询上下文

        返回:
            包含查询结果的字典
        """
        url = f"{self.base_url}/api/v1/query/{query_type}"
        payload = {"parameters": parameters}

        if context:
            payload["context"] = context

        return await self._make_request(url, payload)

    async def analyze_query_intent(self, user_message: str, conversation_history=None) -> Dict[str, Any]:
        """分析用户消息以提取查询意图

        参数:
            user_message: 需要分析的用户消息
            conversation_history: 对话历史记录，格式为[{"role": "user/assistant", "content": "消息内容"}, ...]

        返回:
            包含查询意图分析的字典
        """
        url = f"{self.base_url}/api/v1/analyze/intent"
        payload = {"message": user_message}

        # 如果提供了对话历史，添加到请求中
        if conversation_history:
            payload["conversation_history"] = conversation_history

        result = await self._make_request(url, payload)
        return result

    async def get_data(
        self, query_types: List[str], parameters: Dict[str, Any], context: Optional[str] = None
    ) -> Dict[str, Any]:
        """从MCP服务获取数据

        参数:
            query_types: 查询类型列表
            parameters: 查询参数
            context: 可选的查询上下文

        返回:
            包含查询结果的字典
        """
        url = f"{self.base_url}/api/v1/getdata/querys"
        payload = {"query_types": query_types, "parameters": parameters}

        if context:
            payload["context"] = context

        return await self._make_request(url, payload)


# 创建单例实例
mcp_client = MCPClient()
