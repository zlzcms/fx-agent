# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:13:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 20:55:31
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
意图处理器基类
定义所有意图处理器的通用接口和功能
"""

import asyncio

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Protocol

from backend.agents.config.prompt.handler import DEFAULT_CONFIG


class IntentHandler(Protocol):
    """意图处理器协议"""

    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]: ...


class BaseIntentHandler(ABC, IntentHandler):
    """意图处理器基类"""

    def __init__(self, agent: Any):
        self.agent = agent
        self.max_retries = DEFAULT_CONFIG.get("max_retry_attempts", 3)
        self.log = []

    @abstractmethod
    async def handle(
        self, user_query: str, conversation_history: Optional[List], intent_data: Dict, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    def cleanup(self):
        pass

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """带重试机制的执行方法"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.log.append(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # 指数退避
                continue

        raise last_error

    def _log_operation(self, operation: str, details: str):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log.append(f"[{timestamp}] {operation}: {details}")

    async def _validate_intent_data(self, intent_data: Dict) -> bool:
        """验证意图数据的完整性"""
        required_fields = ["intent_type", "query_type", "data_params"]
        return all(field in intent_data for field in required_fields)
