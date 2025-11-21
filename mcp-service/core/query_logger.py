#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据湖查询统计日志系统
专门用于记录SQL查询的执行情况、耗时统计等信息
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from core.config import settings
from utils.json_encoder import safe_json_dumps
from utils.timezone import timezone

# 配置专门的查询日志文件
QUERY_LOG_FILE = os.path.join(settings.LOG_DIR, settings.LOG_QUERY_FILENAME)

# 创建独立的查询日志记录器
query_stats_logger = logger.bind(query_stats=True)

# 添加专门的查询日志处理器，使用更精确的过滤器
query_stats_logger.add(
    QUERY_LOG_FILE,
    level=settings.LOG_QUERY_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event_type]}: {message}",
    rotation="00:00",  # 每天轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    filter=lambda record: record["extra"].get("query_stats") is True,
    enqueue=True,
)


class QueryLogger:
    """数据湖查询统计日志记录器"""

    def __init__(self):
        self.log_file = QUERY_LOG_FILE
        self._ensure_log_file()

    def _ensure_log_file(self):
        """确保日志文件存在"""
        if not os.path.exists(settings.LOG_DIR):
            os.makedirs(settings.LOG_DIR)

    def log_query_start(
        self,
        query_type: str,
        parameters: Dict[str, Any],
        sql: str,
        table_name: str,
        db_name: Optional[str] = None,
        sql_params: Optional[List[Any]] = None,
    ) -> str:
        """记录查询开始

        Args:
            query_type: 查询类型
            parameters: 查询参数
            sql: SQL语句（模板或最终SQL）
            table_name: 表名
            db_name: 数据库名
            sql_params: SQL参数列表，如果提供则生成最终SQL

        Returns:
            查询ID，用于后续关联
        """
        query_id = f"{int(time.time() * 1000)}"

        # 如果有SQL参数，生成最终的SQL语句
        final_sql = sql
        if sql_params is not None:
            try:
                # 替换SQL模板中的占位符
                final_sql = self._format_sql_with_params(sql, sql_params)
            except Exception as e:
                # 如果格式化失败，记录错误但继续使用原始SQL
                final_sql = f"{sql} [格式化失败: {str(e)}]"

        log_data = {
            "query_id": query_id,
            "event": "QUERY_START",
            "timestamp": timezone.now().isoformat(),
            "query_type": query_type,
            "table_name": table_name,
            "db_name": db_name,
            "sql": final_sql,
            "parameters": parameters,
            "execution_time": None,
            "row_count": None,
            "status": "STARTED",
        }

        query_stats_logger.bind(event_type="QUERY_START").info(
            safe_json_dumps(log_data)
        )
        return query_id

    def _format_sql_with_params(self, sql_template: str, params: List[Any]) -> str:
        """将SQL模板和参数组合成最终的SQL语句

        Args:
            sql_template: SQL模板（包含%s占位符）
            params: 参数列表

        Returns:
            最终的SQL语句
        """
        if not params:
            return sql_template

        # 简单的参数替换，处理常见的SQL参数类型
        formatted_params = []
        for param in params:
            if param is None:
                formatted_params.append("NULL")
            elif isinstance(param, str):
                # 转义单引号并添加引号
                escaped_param = param.replace("'", "''")
                formatted_params.append(f"'{escaped_param}'")
            elif isinstance(param, (int, float)):
                formatted_params.append(str(param))
            elif isinstance(param, bool):
                formatted_params.append("1" if param else "0")
            else:
                # 其他类型转换为字符串并添加引号
                formatted_params.append(f"'{str(param)}'")

        # 替换占位符
        try:
            return sql_template % tuple(formatted_params)
        except (TypeError, ValueError) as e:
            # 如果格式化失败，返回带错误信息的SQL
            return f"{sql_template} [参数格式化失败: {str(e)}, 参数: {params}]"

    def log_query_end(
        self,
        query_id: str,
        execution_time: float,
        row_count: int,
        query_data: Optional[List[Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ):
        """记录查询结束

        Args:
            query_id: 查询ID
            execution_time: 执行时间（秒）
            row_count: 返回行数
            query_data: 查询结果数据
            status: 状态（SUCCESS/ERROR）
            error_message: 错误信息（如果有）
        """
        log_data = {
            "query_id": query_id,
            "event": "QUERY_END",
            "timestamp": timezone.now().isoformat(),
            "execution_time": round(execution_time, 4),
            "row_count": row_count,
            "query_data": query_data,
            "status": status,
            "error_message": error_message,
        }

        query_stats_logger.bind(event_type="QUERY_END").info(safe_json_dumps(log_data))


# 创建全局查询日志记录器实例
query_logger = QueryLogger()


class QueryTimer:
    """查询计时器上下文管理器"""

    def __init__(
        self,
        query_type: str,
        parameters: Dict[str, Any],
        sql: str,
        table_name: str,
        db_name: Optional[str] = None,
        sql_params: Optional[List[Any]] = None,
    ):
        self.query_type = query_type
        self.parameters = parameters
        self.sql = sql
        self.table_name = table_name
        self.db_name = db_name
        self.sql_params = sql_params
        self.query_id = None
        self.start_time = None
        self._logged_end = False  # 防止重复记录标志

    def __enter__(self):
        self.start_time = time.time()
        logger_instance = QueryLogger()
        self.query_id = logger_instance.log_query_start(
            self.query_type,
            self.parameters,
            self.sql,
            self.table_name,
            self.db_name,
            self.sql_params,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time

        # 只有在没有通过 log_result 记录时才记录 QUERY_END
        if not self._logged_end:
            if exc_type is None:
                # 查询成功
                logger_instance = QueryLogger()
                logger_instance.log_query_end(
                    self.query_id, execution_time, 0, None, "SUCCESS"  # 默认行数为0  # 没有数据
                )
            else:
                # 查询失败
                logger_instance = QueryLogger()
                logger_instance.log_query_end(
                    self.query_id,
                    execution_time,
                    0,
                    None,  # 没有数据
                    "ERROR",
                    str(exc_val),
                )
            self._logged_end = True

    def log_result(self, row_count: int, query_data: Optional[List[Any]] = None):
        """记录查询结果行数和数据"""
        if self.query_id and not self._logged_end:
            execution_time = time.time() - self.start_time
            logger_instance = QueryLogger()
            logger_instance.log_query_end(
                self.query_id, execution_time, row_count, query_data, "SUCCESS"
            )
            self._logged_end = True
