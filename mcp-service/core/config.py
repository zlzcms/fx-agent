#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import secrets
from pathlib import Path
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 显式加载.env文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: .env file not found at {env_path}")


class Settings(BaseSettings):
    # 项目根目录
    BASE_PATH: Path = Path(__file__).resolve().parent.parent
    # 日志文件路径
    LOG_DIR: Path = BASE_PATH / "logs"

    # Trace ID
    TRACE_ID_REQUEST_HEADER_KEY: str = "X-Request-ID"
    TRACE_ID_LOG_LENGTH: int = 32  # UUID 长度，必须小于等于 32
    TRACE_ID_LOG_DEFAULT_VALUE: str = "-"

    # 日志
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | <cyan>{correlation_id}</> | <lvl>{message}</>"

    # 日志（控制台）
    LOG_STD_LEVEL: str = "INFO"

    # 日志（文件）
    LOG_FILE_ACCESS_LEVEL: str = "INFO"
    LOG_FILE_ERROR_LEVEL: str = "ERROR"
    LOG_ACCESS_FILENAME: str = "mcp_access.log"
    LOG_ERROR_FILENAME: str = "mcp_error.log"

    # 查询统计日志
    LOG_QUERY_FILENAME: str = "query_statistics.log"
    LOG_QUERY_LEVEL: str = "INFO"

    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MCP Service"

    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_KEY: str = os.getenv("MCP_API_KEY", "default-api-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 服务器配置
    PORT: int = int(os.getenv("MCP_PORT", "8008"))
    DEBUG: bool = os.getenv("MCP_DEBUG", "False").lower() == "true"

    # 时间配置
    DATETIME_TIMEZONE: str = "Asia/Shanghai"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # CORS配置
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], List[str]] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # 处理 JSON 字符串格式
                import json

                try:
                    parsed = json.loads(v)
                    return parsed
                except json.JSONDecodeError:
                    return [i.strip() for i in v.split(",")]
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # 数据仓库配置
    WAREHOUSE_HOST: str = os.getenv("DATABASE_WAREHOUSE_HOST", "localhost")
    WAREHOUSE_PORT: int = int(os.getenv("DATABASE_WAREHOUSE_PORT", "3306"))
    WAREHOUSE_USER: str = os.getenv("DATABASE_WAREHOUSE_USER", "root")
    WAREHOUSE_PASSWORD: str = os.getenv("DATABASE_WAREHOUSE_PASSWORD", "password")
    WAREHOUSE_CHARSET: str = os.getenv("DATABASE_WAREHOUSE_CHARSET", "utf8mb4")

    # 管理员配置
    ADMIN_HOST: str = os.getenv("DATABASE_ADMIN_HOST", "localhost")
    ADMIN_PORT: int = int(os.getenv("DATABASE_ADMIN_PORT", "5432"))
    ADMIN_USER: str = os.getenv("DATABASE_ADMIN_USER", "admin")
    ADMIN_PASSWORD: str = os.getenv("DATABASE_ADMIN_PASSWORD", "password")
    ADMIN_DBNAME: str = os.getenv("DATABASE_ADMIN_DBNAME", "admin")

    # 数据源配置
    DEFAULT_LIMIT: int = 1000


settings = Settings()
