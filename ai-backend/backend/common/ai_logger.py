#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务调用日志记录器
记录所有AI服务的请求、响应、状态和时间等信息
"""

import json
import os
import uuid

from typing import Any, Dict, List, Optional

from loguru import logger

from backend.core.path_conf import LOG_DIR
from backend.utils.timezone import timezone


class AIServiceLogger:
    """AI服务调用日志记录器"""

    def __init__(self):
        self.logger = logger
        self.log_requests = os.getenv("AI_LOG_REQUESTS", "false").lower() == "true"  # 默认不记录请求
        self._setup_ai_logger()

    def _setup_ai_logger(self):
        """设置AI服务专用日志文件"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)

        # AI服务日志文件路径
        ai_log_file = os.path.join(LOG_DIR, "ai_service.log")

        # 添加AI服务专用日志处理器
        self.logger.add(
            str(ai_log_file),
            level="WARNING",  # 改为WARNING级别，减少AI请求日志
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
            enqueue=False,  # 同步写入，确保日志立即写入文件
            rotation="00:00",  # 每天轮转
            retention="30 days",  # 保留30天
            compression="zip",  # 压缩旧日志
            filter=lambda record: record["extra"].get("ai_service", False),
            backtrace=False,
            diagnose=False,
        )

    def log_ai_request(
        self,
        request_id: str,
        service_name: str,
        model_name: str,
        base_url: str,
        request_data: Dict[str, Any],
        user_id: Optional[str] = None,
        chat_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs,
    ):
        """记录AI服务请求"""
        # 如果设置了不记录请求，则跳过
        if not self.log_requests:
            return

        log_data = {
            "request_id": request_id,
            "timestamp": timezone.now().isoformat(),
            "service_name": service_name,
            "model_name": model_name,
            "base_url": base_url,
            "request_data": request_data,
            "user_id": user_id,
            "chat_id": chat_id,
            "agent_id": agent_id,
            "request_type": "REQUEST",
        }

        # 添加额外的配置信息，避免重复的关键字参数
        for key, value in kwargs.items():
            if key not in log_data:
                log_data[key] = value
            else:
                # 如果键已存在，记录警告但不覆盖
                self.logger.warning(f"Duplicate key '{key}' in log_ai_request kwargs, ignoring kwargs value")

        self.logger.bind(ai_service=True).info(f"AI_REQUEST | {json.dumps(log_data, ensure_ascii=False)}")

    def log_ai_response(
        self,
        request_id: str,
        response_data: Dict[str, Any],
        status_code: int = 200,
        response_time: float = 0.0,
        error_message: Optional[str] = None,
        **kwargs,
    ):
        """记录AI服务响应"""
        log_data = {
            "request_id": request_id,
            "timestamp": timezone.now().isoformat(),
            "response_data": response_data,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "error_message": error_message,
            "response_type": "RESPONSE",
            **kwargs,
        }

        self.logger.bind(ai_service=True).info(f"AI_RESPONSE | {json.dumps(log_data, ensure_ascii=False)}")

    def log_ai_error(self, request_id: str, error_message: str, error_type: str, **kwargs):
        """记录AI服务错误"""
        log_data = {
            "request_id": request_id,
            "timestamp": timezone.now().isoformat(),
            "error_message": error_message,
            "error_type": error_type,
            **kwargs,
        }

        self.logger.bind(ai_service=True).error(f"AI_ERROR | {json.dumps(log_data, ensure_ascii=False)}")


# 创建全局AI服务日志记录器实例
ai_service_logger = AIServiceLogger()


def get_ai_request_id() -> str:
    """生成AI请求唯一ID"""
    return f"ai_req_{uuid.uuid4().hex[:16]}"


def extract_request_info(messages: List[Any], **kwargs) -> Dict[str, Any]:
    """提取请求信息"""
    request_info = {"message_count": len(messages), "total_tokens": 0, "messages": []}

    for i, msg in enumerate(messages):
        # 获取消息内容
        content = ""
        role = "unknown"

        if hasattr(msg, "content"):
            content = str(msg.content)
        elif isinstance(msg, dict):
            content = str(msg.get("content", ""))
            role = msg.get("role", "unknown")
        elif hasattr(msg, "type"):
            role = msg.type

        msg_info = {
            "index": i,
            "role": role,
            "content": content,  # 添加实际内容
            "content_length": len(content),
        }

        # 计算token数量（简单估算）
        if content:
            msg_info["estimated_tokens"] = len(content.split()) * 1.3  # 简单估算
            request_info["total_tokens"] += msg_info["estimated_tokens"]

        request_info["messages"].append(msg_info)

    return request_info


def extract_response_info(response: Any) -> Dict[str, Any]:
    """提取响应信息"""
    response_info = {
        "response_type": type(response).__name__,
        "has_content": hasattr(response, "content"),
        "content_length": 0,
        "estimated_tokens": 0,
    }

    if hasattr(response, "content"):
        content = str(response.content)
        response_info["content"] = content  # 添加实际内容
        response_info["content_length"] = len(content)
        response_info["estimated_tokens"] = len(content.split()) * 1.3  # 简单估算

    # 提取其他可能的属性
    if hasattr(response, "usage"):
        response_info["usage"] = response.usage

    if hasattr(response, "model"):
        response_info["model"] = response.model

    return response_info
