#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangSmith 配置和初始化模块
用于追踪和监控 LLM 调用
"""

import os

from typing import Optional

from backend.agents.config.setting import settings
from backend.common.log import logger


class LangSmithConfig:
    """LangSmith 配置管理类"""

    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """
        初始化 LangSmith 追踪

        Returns:
            bool: 是否成功初始化
        """
        if cls._initialized:
            logger.info("LangSmith already initialized")
            return True

        try:
            # 检查是否启用追踪
            if not settings.LANGSMITH_TRACING_V2:
                logger.info("LangSmith tracing is disabled")
                return False

            # 检查 API Key
            if not settings.LANGSMITH_API_KEY:
                logger.warning("LANGSMITH_API_KEY not set, tracing will be disabled")
                return False

            # 设置环境变量（LangChain 会自动读取）
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT

            cls._initialized = True
            logger.info(
                f"✅ LangSmith tracing initialized successfully. "
                f"Project: {settings.LANGSMITH_PROJECT}, "
                f"Endpoint: {settings.LANGSMITH_ENDPOINT}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {str(e)}")
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        """检查 LangSmith 追踪是否启用"""
        return cls._initialized and settings.LANGSMITH_TRACING_V2

    @classmethod
    def get_project_name(cls) -> str:
        """获取当前项目名称"""
        return settings.LANGSMITH_PROJECT

    @classmethod
    def disable(cls) -> None:
        """禁用 LangSmith 追踪"""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        cls._initialized = False
        logger.info("LangSmith tracing disabled")

    @classmethod
    def set_project(cls, project_name: str) -> None:
        """
        设置项目名称

        Args:
            project_name: 新的项目名称
        """
        os.environ["LANGCHAIN_PROJECT"] = project_name
        logger.info(f"LangSmith project changed to: {project_name}")

    @classmethod
    def get_trace_url(cls, run_id: Optional[str] = None) -> Optional[str]:
        """
        获取追踪 URL

        Args:
            run_id: 运行 ID

        Returns:
            追踪 URL 或 None
        """
        if not cls.is_enabled():
            return None

        base_url = settings.LANGSMITH_ENDPOINT.replace("api.smith", "smith")
        project = settings.LANGSMITH_PROJECT

        if run_id:
            return f"{base_url}/o/default/projects/p/{project}/r/{run_id}"
        else:
            return f"{base_url}/o/default/projects/p/{project}"


# 自动初始化（在模块导入时）
def auto_initialize():
    """自动初始化 LangSmith"""
    try:
        if settings.LANGSMITH_TRACING_V2:
            LangSmithConfig.initialize()
    except Exception as e:
        logger.warning(f"Failed to auto-initialize LangSmith: {str(e)}")


# 在模块加载时自动初始化
auto_initialize()
