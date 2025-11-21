#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from core.config import settings

logger = logging.getLogger(__name__)


class AdminDB:
    """管理数据库连接管理器 (PostgreSQL)"""

    def __init__(self):
        self.host = settings.ADMIN_HOST
        self.port = settings.ADMIN_PORT
        self.user = settings.ADMIN_USER
        self.password = settings.ADMIN_PASSWORD
        self.dbname = settings.ADMIN_DBNAME

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        connection = None
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname,
                connect_timeout=60,
            )
            yield connection
        except psycopg2.Error as e:
            logger.error(f"管理数据库连接错误: {e}")
            raise
        finally:
            if connection:
                connection.close()

    async def execute_query(self, sql, params=None):
        """执行SQL查询

        参数:
            sql: SQL查询语句
            params: 查询参数

        返回:
            查询结果列表
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql, params or ())
                    result = cursor.fetchall()
                    return result
        except Exception as e:
            logger.error(f"执行查询错误: {e}")
            raise e

    async def execute_batch_query(self, queries):
        """执行批量查询

        参数:
            queries: 查询字典列表，每个字典包含sql和params

        返回:
            查询结果字典，键为查询ID，值为结果
        """
        results = {}
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    for query_id, query_info in queries.items():
                        sql = query_info.get("sql")
                        params = query_info.get("params", ())
                        try:
                            cursor.execute(sql, params)
                            results[query_id] = cursor.fetchall()
                        except Exception as e:
                            logger.error(f"查询 {query_id} 执行错误: {e}")
                            results[query_id] = {"error": str(e)}
            return results
        except Exception as e:
            logger.error(f"批量查询执行错误: {e}")
            raise

    async def execute_modification(self, sql, params=None):
        """执行数据修改操作（插入、更新、删除）

        参数:
            sql: SQL语句
            params: SQL参数

        返回:
            受影响的行数
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or ())
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"执行修改错误: {e}")
            raise e


# 创建单例实例
admin_db = AdminDB()
