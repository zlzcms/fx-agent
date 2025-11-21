#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.agents.schema.base_agent import AgentType

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: .env file not found at {env_path}")


class Settings(BaseSettings):
    available_agents: Dict[str, Dict[str, Any]] = {
        "mcp_data": {
            "type": AgentType.MCP_DATA,
            "description": "从MCP服务获取数据",
            "capabilities": ["数据查询", "多表关联", "条件筛选"],
        },
        "data_processing": {
            "type": AgentType.DATA_PROCESSING,
            "description": "数据处理和拆分",
            "capabilities": ["数据清洗", "数据拆分", "格式转换"],
        },
        "ai_analysis": {
            "type": AgentType.AI_ANALYSIS,
            "description": "AI数据分析",
            "capabilities": ["深度分析", "模式识别", "趋势预测", "异常检测"],
        },
        "general_chat": {
            "type": AgentType.GENERAL_CHAT,
            "description": "通用对话",
            "capabilities": ["普通对话", "简单问题", "建议生成"],
        },
    }

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    LOG_FILE: str = os.getenv("LOG_FILE", "agents.log")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # .env MCP 服务
    MCP_SERVICE_URL: str = os.getenv("MCP_SERVICE_URL")  # MCP 服务的 URL
    MCP_API_KEY: str = os.getenv("MCP_API_KEY")  # MCP 服务的 API 密钥

    # 通用对话模型配置
    GENERAL_CHAT_LLM_API_KEY: str = os.getenv("GENERAL_CHAT_LLM_API_KEY", "")
    GENERAL_CHAT_LLM_BASE_URL: str = os.getenv("GENERAL_CHAT_LLM_BASE_URL", "https://api.deepseek.com/v1")
    GENERAL_CHAT_LLM_MODEL_NAME: str = os.getenv("GENERAL_CHAT_LLM_MODEL_NAME", "deepseek-chat")
    GENERAL_CHAT_LLM_TEMPERATURE: float = float(os.getenv("GENERAL_CHAT_LLM_TEMPERATURE", "0.75"))

    # LangSmith 配置
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "ai-agent-system")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_TRACING_V2: bool = os.getenv("LANGSMITH_TRACING_V2", "false").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    # data limit - 减少数据量以避免上下文长度超限
    MAX_USER_COUNT: int = 100  # 减少到50个用户
    MAX_DATA_COUNT: int = 2000  # 减少到1000条数据
    # 针对128k上下文大模型的优化配置
    SPLIT_MAX_TOKEN: int = 100000  # 减少到100k，为系统提示词和输出预留更多空间
    SPLIT_CHUNK_SIZE: int = 100000  # 减少到100k，避免单次请求过大
    SPLIT_CHUNK_OVERLAP: int = 200  # 增加重叠，保证上下文连续性
    SPLIT_MAX_ITEMS_PER_CHUNK: int = 100  # 减少每块处理的项目数
    SPLIT_USE_PARALLEL: bool = True  # 是否使用并行处理
    SPLIT_PARALLEL_MAX_WORKERS: int = 5  # 并行处理的最大worker数量

    # 缓存
    is_cache_request: bool = os.getenv("IS_CACHE_REQUEST", "true").lower() == "true"
    cache_ttl: int = os.getenv("CACHE_TTL", 300)


settings = Settings()
