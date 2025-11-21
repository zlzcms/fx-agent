#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务请求日志记录器
专门记录MCP客户端的请求和响应信息
"""

import json
import logging
import time

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class MCPLogger:
    """MCP服务请求日志记录器"""

    def __init__(self, log_file: str = "backend/log/mcp_service.log"):
        """初始化MCP日志记录器

        参数:
            log_file: 日志文件路径
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建独立的logger实例
        self.logger = logging.getLogger("mcp_service")
        self.logger.setLevel(logging.INFO)

        # 清除现有的handlers
        self.logger.handlers.clear()

        # 创建文件handler
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # 创建格式器
        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f")
        file_handler.setFormatter(formatter)

        # 添加handler到logger
        self.logger.addHandler(file_handler)

        # 防止日志传播到父logger
        self.logger.propagate = False

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        return f"mcp_req_{int(time.time() * 1000)}"

    def _extract_request_info(self, url: str, headers: Dict[str, str], payload: Any) -> Dict[str, Any]:
        """提取请求信息"""
        request_info = {
            "url": url,
            "method": "POST",
            "headers": {k: v for k, v in headers.items() if k.lower() != "authorization"},  # 隐藏API密钥
            "has_auth": "Authorization" in headers,
            "payload_size": len(json.dumps(payload)) if payload else 0,
            "payload_type": type(payload).__name__,
            "payload": payload,  # 添加完整的请求载荷
        }

        # 如果是查询请求，提取关键信息
        if isinstance(payload, dict):
            if "parameters" in payload:
                request_info["query_type"] = payload.get("parameters", {}).get("query_type", "unknown")
                request_info["user_count"] = len(payload.get("parameters", {}).get("user_id", []))
            elif "query_type" in payload:
                request_info["query_type"] = payload.get("query_type")

        return request_info

    def _extract_response_info(self, response: Any, response_time_ms: float) -> Dict[str, Any]:
        """提取响应信息"""
        response_info = {
            "response_time_ms": response_time_ms,
            "response_type": type(response).__name__,
            "has_data": False,
            "data_size": 0,
            "success": False,
            "response": response,  # 添加完整的响应数据
        }

        if isinstance(response, dict):
            response_info["success"] = response.get("success", False)
            response_info["has_data"] = bool(response.get("data"))
            response_info["message"] = response.get("message", "")

            if response.get("data"):
                data_str = json.dumps(response["data"])
                response_info["data_size"] = len(data_str)
                response_info["data_type"] = type(response["data"]).__name__

                # 如果是列表，记录数量
                if isinstance(response["data"], list):
                    response_info["data_count"] = len(response["data"])

        return response_info

    def log_mcp_request(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Any,
        timeout: float,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """记录MCP请求

        参数:
            url: 请求URL
            headers: 请求头
            payload: 请求载荷
            timeout: 超时时间
            user_id: 用户ID（可选）
            agent_id: 代理ID（可选）

        返回:
            请求ID
        """
        request_id = self._generate_request_id()
        request_info = self._extract_request_info(url, headers, payload)

        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "service_name": "MCPClient",
            "request_type": "REQUEST",
            "user_id": user_id,
            "agent_id": agent_id,
            "timeout": timeout,
            "request_data": request_info,
        }

        self.logger.info(f"MCP_REQUEST | {json.dumps(log_data, ensure_ascii=False)}")
        return request_id

    def log_mcp_response(
        self,
        request_id: str,
        response: Any,
        response_time_ms: float,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
    ):
        """记录MCP响应

        参数:
            request_id: 请求ID
            response: 响应数据
            response_time_ms: 响应时间（毫秒）
            status_code: HTTP状态码（可选）
            error_message: 错误消息（可选）
        """
        response_info = self._extract_response_info(response, response_time_ms)

        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_info,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "response_type": "RESPONSE",
        }

        # self.logger.info(f"MCP_RESPONSE | {json.dumps(log_data, ensure_ascii=False)}")

    def log_mcp_error(self, request_id: str, error: Exception, response_time_ms: float, url: str):
        """记录MCP错误

        参数:
            request_id: 请求ID
            error: 异常对象
            response_time_ms: 响应时间（毫秒）
            url: 请求URL
        """
        error_info = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "error_message": str(error),
            "error_type": type(error).__name__,
            "response_time_ms": response_time_ms,
            "url": url,
            "response_type": "ERROR",
        }

        self.logger.error(f"MCP_ERROR | {json.dumps(error_info, ensure_ascii=False)}")


# 创建全局MCP日志记录器实例
mcp_logger = MCPLogger()
