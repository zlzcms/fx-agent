#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import json
import logging
import re
import sys

from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# 设置路径以便导入backend模块
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))
# 现在导入backend模块
from backend.agents.config.setting import settings  # noqa: E402

# 配置更详细的日志
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MCPClient:
    """用于与MCP服务交互的客户端"""

    def __init__(self, base_url=None, api_key=None, timeout=60):
        """初始化MCP客户端

        参数:
            base_url: MCP服务API的基础URL
            api_key: 用于认证的API密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or settings.MCP_SERVICE_URL
        self.api_key = api_key or settings.MCP_API_KEY
        self.timeout = timeout

    async def query_data(self, request: Dict[str, Any] | list[Dict[str, Any]]) -> Dict[str, Any]:
        """从MCP服务查询数据"""
        result = None
        if isinstance(request, list):
            result = {}
            for item in request:
                if "query_type" not in item or not item["query_type"]:
                    continue
                item_result = await self.call_mcp_tool("execute_query", item)
                # print(f"item_result===========================: {item_result}")
                result[item["query_type"]] = self._data_to_dict(item_result)
                # print(f"result query_type ==============================: {result.get(item['query_type'])}")
        elif isinstance(request, dict):
            if "query_type" in request and request["query_type"]:
                result = await self.call_mcp_tool("execute_query", request)
                result = self._data_to_dict(result)
            if "query_types" in request and request["query_types"]:
                result = await self.call_mcp_tool("execute_query", request)
                result = self._data_to_dict(result)
        if not result:
            return {"success": False, "message": "查询参数为空", "data": None}
        # print("查询数据结果",result)
        return {"success": True, "message": "查询成功", "data": result}

    async def call_mcp_tool(self, tool_name: str, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调用MCP工具

        参数:
            tool_name: 工具名称，例如 "query_user_data"
            parameters: 工具参数

        返回:
            调用结果
        """
        if request is None:
            request = {}

        try:
            # 构建MCP协议格式的请求
            mcp_request = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": request},
            }

            # # 记录请求信息
            # logger.debug(f"发送MCP请求: {json.dumps(mcp_request)}")
            # logger.debug(f"目标URL: {self.base_url}/mcp")

            # MCP服务的端点是 /mcp
            url = f"{self.base_url}/mcp"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

            # logger.debug(f"请求头: {headers}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=mcp_request)

                # # 记录响应状态和头部
                # logger.debug(f"响应状态码: {response.status_code}")
                # logger.debug(f"响应头: {response.headers}")

                # 记录原始响应内容
                raw_content = response.content
                # logger.debug(f"原始响应内容: {raw_content}")

                if not raw_content:
                    logger.error("服务器返回了空响应")
                    return {"success": False, "message": "服务器返回了空响应", "data": None}

                # 检查是否是SSE格式
                content_type = response.headers.get("content-type", "")
                if "text/event-stream" in content_type:
                    # 处理SSE格式
                    return self._parse_sse_response(raw_content)
                else:
                    # 处理普通JSON格式
                    try:
                        response.raise_for_status()
                        result = response.json()
                    except httpx.HTTPStatusError as e:
                        logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
                        return {
                            "success": False,
                            "message": f"HTTP错误: {e.response.status_code}",
                            "data": None,
                            "metadata": {"error": e.response.text},
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析错误: {str(e)}, 内容: {raw_content}")
                        return {
                            "success": False,
                            "message": f"JSON解析错误: {str(e)}",
                            "data": raw_content.decode("utf-8", errors="replace"),
                            "metadata": {"error": "Invalid JSON response"},
                        }

                    # 处理MCP协议返回的结果
                    return self._process_json_result(result)
        except Exception as e:
            logger.exception(f"调用MCP工具时发生错误: {str(e)}")
            return {"success": False, "message": f"错误: {str(e)}", "data": None}

    def _parse_sse_response(self, raw_content: bytes) -> Dict[str, Any]:
        """解析SSE格式的响应"""
        try:
            # 解码为文本
            content = raw_content.decode("utf-8")

            # 使用正则表达式提取data字段
            data_match = re.search(r"data: ({.*})", content)
            if not data_match:
                logger.error(f"无法从SSE响应中提取数据: {content}")
                return {
                    "success": False,
                    "message": "无法从SSE响应中提取数据",
                    "data": content,
                    "metadata": {"error": "Invalid SSE format"},
                }

            # 解析JSON数据
            json_data = json.loads(data_match.group(1))
            # logger.debug(f"从SSE提取的JSON数据: {json_data}")

            return self._process_json_result(json_data)
        except Exception as e:
            logger.exception(f"解析SSE响应时发生错误: {str(e)}")
            return {
                "success": False,
                "message": f"解析SSE响应错误: {str(e)}",
                "data": raw_content.decode("utf-8", errors="replace"),
                "metadata": {"error": "SSE parsing error"},
            }

    def _process_json_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """处理JSON格式的结果"""
        if "result" in result:
            # 检查是否有错误
            if isinstance(result["result"], dict) and result["result"].get("isError"):
                # 提取错误信息
                error_content = result["result"].get("content", [])
                error_message = ""
                for item in error_content:
                    if item.get("type") == "text":
                        error_message = item.get("text", "")
                        break

                return {
                    "success": False,
                    "message": error_message or "调用失败",
                    "data": None,
                    "metadata": {"error": result["result"]},
                }

            # 处理成功结果
            if isinstance(result["result"], dict) and "content" in result["result"]:
                # 处理结构化内容
                content = result["result"]["content"]
                text_content = ""
                for item in content:
                    if item.get("type") == "text":
                        text_content = item.get("text", "")
                        break

                # 如果是查询结果，通常是字符串格式，需要解析
                if text_content:
                    try:
                        data = json.loads(text_content)
                        return {"success": True, "message": "查询成功", "data": data}
                    except json.JSONDecodeError:
                        return {"success": True, "message": "查询成功", "data": text_content}

                # 返回结构化内容
                if "structuredContent" in result["result"]:
                    return {"success": True, "message": "调用成功", "data": result["result"]["structuredContent"]}

                return {"success": True, "message": "调用成功", "data": text_content or content}

            # 直接返回结果
            return {"success": True, "message": "调用成功", "data": result["result"]}
        elif "error" in result:
            return {
                "success": False,
                "message": result["error"].get("message", "调用失败"),
                "data": None,
                "metadata": {"error": result["error"]},
            }
        else:
            return {"success": False, "message": "未知响应格式", "data": result}

    def _data_to_dict(self, result: dict) -> Dict[str, Any]:
        """将返回的字符串数据转换为字典对象

        Args:
            result: 调用MCP工具的原始结果

        Returns:
            解析后的字典数据，如果解析失败则返回原始数据
        """
        if not result.get("success"):
            return None

        data = result.get("data")
        if not data:
            return None

        # 如果已经是字典，直接返回
        if isinstance(data, dict):
            return data

        # 尝试解析字符串
        if isinstance(data, str):
            # 移除可能存在的前缀
            if data.startswith("查询成功："):
                data = data.replace("查询成功：", "")

            try:
                # 使用ast.literal_eval解析Python字典字符串
                return ast.literal_eval(data)
            except (SyntaxError, ValueError) as e:
                logger.warning(f"字典解析错误: {str(e)}")
                try:
                    # 尝试使用json.loads作为备选方案
                    return json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("JSON解析也失败，返回原始数据")
                    return data

        return data


# 创建单例实例
mcp_client = MCPClient()
if __name__ == "__main__":
    import asyncio
    # 设置详细日志级别
    # logging.basicConfig(level=logging.DEBUG)

    # 测试不同的工具调用
    async def test():
        # 尝试调用list_query_types工具
        print("测试list_query_types工具:")
        result = await mcp_client.call_mcp_tool("list_query_types")
        print(f"结果: {result}")

        # 尝试调用query_user_data工具
        print("\n测试query_user_data工具:")
        request = {"query_type": "user_data", "parameters": {"username": "TA001"}, "is_return_Dict": True}
        result = await mcp_client.call_mcp_tool("execute_query", request)
        print(f"结果: {result}")
        print(f"data结果====: {mcp_client._data_to_dict(result)}")

    asyncio.run(test())
