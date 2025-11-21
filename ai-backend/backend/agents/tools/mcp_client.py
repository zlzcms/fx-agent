#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import time

from typing import Any, Dict

import httpx

from backend.agents.config.setting import settings
from backend.agents.utils.cache import check_cache, set_cache
from backend.common.log import logger
from backend.common.mcp_logger import mcp_logger


class MCPClient:
    """用于与MCP服务交互的客户端"""

    def __init__(self, base_url=None, api_key=None, timeout=120):
        """初始化MCP客户端

        参数:
            base_url: MCP服务API的基础URL
            api_key: 用于认证的API密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or settings.MCP_SERVICE_URL
        self.api_key = api_key or settings.MCP_API_KEY
        self.timeout = timeout

    def _generate_request_hash(self, request: Dict[str, Any]) -> str:
        """生成请求的唯一哈希值用于去重"""
        # 将请求数据序列化为JSON字符串，确保键的顺序一致
        request_str = json.dumps(request, sort_keys=True, ensure_ascii=False)
        # 生成MD5哈希值
        return hashlib.md5(request_str.encode("utf-8")).hexdigest()

    def _log_cached_request(self, request: Dict[str, Any], request_hash: str) -> None:
        """记录缓存请求的日志"""
        try:
            url = f"{self.base_url}/api/v1/getdata/data"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            # 记录MCP请求（标记为缓存）
            request_id = mcp_logger.log_mcp_request(
                url=url,
                headers=headers,
                payload=request,
                timeout=self.timeout,
                agent_id="AgentsMCPClient_ACTIVE_CACHED",
            )

            # 记录MCP响应（标记为缓存）
            mcp_logger.log_mcp_response(
                request_id=request_id,
                response={"success": True, "message": "查询成功（缓存）", "data": "CACHED"},
                response_time_ms=0.1,  # 缓存响应时间很短
                status_code=200,
                error_message=None,
            )
        except Exception as e:
            logger.warning(f"Failed to log cached request: {e}")

    async def query_data(self, request: Dict[str, Any] | list[Dict[str, Any]]) -> Dict[str, Any]:
        """从MCP服务查询数据（带请求去重）"""
        try:
            # 生成请求哈希值用于去重
            request_hash = self._generate_request_hash(request)

            # 检查是否存在重复请求
            cached_result = await check_cache(f"mcp_request_{request_hash}")
            if cached_result:
                # 对于缓存的结果，我们需要记录一个特殊的日志
                self._log_cached_request(request, f"mcp_request_{request_hash}")
                return cached_result

            # 执行实际请求
            result = await self._http_client("getdata/data", request)

            # 缓存请求结果
            await set_cache(f"mcp_request_{request_hash}", result)

            return result
        except Exception as e:
            logger.error(f"mcp client getdata_data error: {e}")
            raise e

    async def get_data(self, request: Dict[str, Any] | list[Dict[str, Any]]) -> Dict[str, Any]:
        """从MCP服务查询数据"""
        try:
            result = None
            if isinstance(request, list):
                result = {}
                for item in request:
                    if "query_type" not in item or not item["query_type"]:
                        continue
                    item_result = await self._http_client("getdata/query", item)
                    if item_result["success"]:
                        result[item["query_type"]] = item_result["data"]
                    else:
                        result[item["query_type"]] = {}
            elif isinstance(request, dict):
                if "query_type" in request and request["query_type"]:
                    result = await self._http_client("getdata/query", request)
                if "query_types" in request and request["query_types"]:
                    result = await self._http_client("getdata/querys", request)

            if not result:
                return {
                    "success": False,
                    "message": "查询数据为空",
                    "data": None,
                    "metadata": {"error": "query_type is empty"},
                }
            return result
        except Exception as e:
            raise e

    async def _http_client(self, route: str, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """从MCP服务查询数据

        参数:
            route: 查询路由（如customer_data, transaction_data）
            parameters: 查询参数
        返回:
            包含查询结果的字典
        """
        start_time = time.time()
        request_id = None

        try:
            if not route:
                return {
                    "success": False,
                    "message": "路由不能为空",
                    "data": None,
                    "metadata": {"error": "route is empty"},
                }
            if route.startswith("/"):
                route = route[1:]
            url = f"{self.base_url}/api/v1/{route}"

            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            # 记录MCP请求
            request_id = mcp_logger.log_mcp_request(
                url=url, headers=headers, payload=request, timeout=self.timeout, agent_id="AgentsMCPClient_ACTIVE"
            )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=request)
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

            # 详细调试异常信息
            error_type = type(e).__name__
            error_str = str(e)
            error_repr = repr(e)
            error_args = getattr(e, "args", ())

            logger.error(f"请求错误: {error_type} - {error_str}")

            # 记录MCP错误
            if request_id:
                mcp_logger.log_mcp_error(request_id, e, response_time_ms, url)

            return {
                "success": False,
                "message": f"mcp_client网络请求失败: {error_str or error_type}",
                "data": None,
                "metadata": {
                    "error_type": error_type,
                    "error": error_str,
                    "error_repr": error_repr,
                    "error_args": error_args,
                },
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"意外错误: {str(e)}"

            logger.error(error_msg)

            # 记录MCP错误
            if request_id:
                mcp_logger.log_mcp_error(request_id, e, response_time_ms, url)

            return {"success": False, "message": error_msg, "data": None, "metadata": {"error": str(e)}}


# 创建单例实例
mcp_client = MCPClient()
