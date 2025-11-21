#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import aiomysql

from core.config import settings

logger = logging.getLogger(__name__)


class WarehouseDB:
    """数据仓库连接管理器 - 异步版本"""

    def __init__(self):
        self.host = settings.WAREHOUSE_HOST
        self.port = settings.WAREHOUSE_PORT
        self.user = settings.WAREHOUSE_USER
        self.password = settings.WAREHOUSE_PASSWORD
        self.charset = settings.WAREHOUSE_CHARSET
        self.pool = None
        self.min_size = 10  # 连接池最小连接数（提高最小连接数）
        self.max_size = 50  # 连接池最大连接数（适应当前连接负载）
        self.query_timeout = 60  # 查询超时时间（秒）- 给复杂查询更多时间
        self.connection_timeout = 10  # 连接超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        # 连接验证超时时间
        self.verify_timeout = 2  # 验证连接有效性时的超时时间
        logger.info(
            f"数据库配置: {self.host}:{self.port}, 用户: {self.user}, 字符集: {self.charset}"
        )

    async def refresh_pool(self):
        """刷新连接池"""
        logger.info("刷新连接池...")
        if self.pool is not None and not self.pool.closed:
            old_pool = self.pool
            try:
                # 创建新的连接池（优化参数以匹配MySQL服务器配置）
                new_pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    charset=self.charset,
                    minsize=self.min_size,
                    maxsize=self.max_size,
                    autocommit=True,
                    pool_recycle=3600,  # 1小时后回收连接（比MySQL默认wait_timeout更保守）
                    connect_timeout=self.connection_timeout,
                    echo=False,  # 关闭SQL回显，提高性能
                )

                # 测试新连接池（使用连接验证方法）
                conn = await new_pool.acquire()
                try:
                    # 验证连接是否有效
                    async with conn.cursor() as cursor:
                        await asyncio.wait_for(
                            cursor.execute("SELECT 1"), timeout=self.verify_timeout
                        )
                        await cursor.fetchone()
                    logger.debug("新连接池连接验证通过")
                except Exception as e:
                    logger.error(f"新连接池连接验证失败: {e}")
                    raise
                finally:
                    new_pool.release(conn)

                # 替换旧连接池
                self.pool = new_pool
                logger.info("连接池刷新成功")

                # 关闭旧连接池
                old_pool.close()
                await old_pool.wait_closed()
            except Exception as e:
                logger.error(f"刷新连接池失败: {e}")
                # 如果创建新连接池失败，保留旧连接池
        else:
            # 如果没有连接池，则初始化
            await self.initialize()

    async def initialize(self):
        """初始化连接池"""
        if self.pool is None or self.pool.closed:
            try:
                self.pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    charset=self.charset,
                    minsize=self.min_size,
                    maxsize=self.max_size,
                    autocommit=True,
                    pool_recycle=3600,  # 1小时后回收连接（比MySQL默认wait_timeout更保守）
                    connect_timeout=self.connection_timeout,  # 连接超时
                    echo=False,  # 关闭SQL回显，提高性能
                )
                logger.info("数据库连接池初始化成功")
            except Exception as e:
                logger.error(f"数据库连接池初始化失败: {e}")
                raise

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("数据库连接池已关闭")

    async def check_connection(self):
        """检查连接池是否健康"""
        if self.pool is None or self.pool.closed:
            logger.warning("连接池不存在或已关闭，尝试重新初始化")
            await self.initialize()
            return False
        return True

    async def verify_connection(self, conn) -> bool:
        """验证连接是否有效"""
        try:
            async with conn.cursor() as cursor:
                await asyncio.wait_for(
                    cursor.execute("SELECT 1"), timeout=self.verify_timeout
                )
                return True
        except Exception as e:
            logger.debug(f"连接验证失败: {e}")
            return False

    async def get_valid_connection(self):
        """获取有效的数据库连接（带验证和重试机制）"""
        retries = 0

        while retries < self.max_retries:
            try:
                # 检查连接池
                if self.pool is None or self.pool.closed:
                    await self.initialize()

                # 获取连接
                conn = await asyncio.wait_for(
                    self.pool.acquire(), timeout=self.connection_timeout
                )

                # 验证连接有效性
                if await self.verify_connection(conn):
                    return conn
                else:
                    # 连接无效，释放并继续
                    self.pool.release(conn)
                    logger.warning("获取到的连接无效，重新获取")

            except Exception as e:
                logger.error(f"获取数据库连接失败: {e}")

            retries += 1

            # 如果不是最后一次重试，刷新连接池
            if retries < self.max_retries:
                logger.info(f"尝试重新获取连接，第{retries}次重试")
                await self.refresh_pool()
                await asyncio.sleep(0.5)  # 短暂等待

        raise RuntimeError("无法获取有效的数据库连接")

    @asynccontextmanager
    async def connection(self):
        """获取数据库连接的上下文管理器（确保连接被正确释放）"""
        conn = None
        try:
            conn = await self.get_valid_connection()
            yield conn
        finally:
            if conn and self.pool and not self.pool.closed:
                try:
                    self.pool.release(conn)
                except Exception as e:
                    logger.error(f"释放数据库连接时出错: {e}")

    async def get_connection(self):
        """获取数据库连接（向后兼容，推荐使用 connection 上下文管理器）"""
        return await self.get_valid_connection()

    async def execute_query(
        self, sql: str, params: Optional[tuple] = None, timeout: Optional[int] = None
    ) -> List[Dict]:
        """执行SQL查询 - 异步版本

        参数:
            sql: SQL查询语句
            params: 查询参数
            timeout: 查询超时时间（秒），None表示使用默认值

        返回:
            查询结果列表
        """
        if timeout is None:
            timeout = self.query_timeout

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                # 使用上下文管理器确保连接被正确释放
                async with self.connection() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await asyncio.wait_for(
                            cursor.execute(sql, params or ()), timeout=timeout
                        )
                        result = await asyncio.wait_for(
                            cursor.fetchall(), timeout=timeout
                        )
                        return result
            except (asyncio.TimeoutError, aiomysql.OperationalError) as e:
                logger.error(f"查询超时或连接错误: {sql[:100]}... 错误: {e}")
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.info(f"尝试重新执行查询，第{retries}次重试")
                    # 如果是连接错误，强制刷新连接池
                    await self.refresh_pool()
                    await asyncio.sleep(1)  # 等待1秒后重试
                else:
                    if isinstance(e, asyncio.TimeoutError):
                        raise TimeoutError(f"数据库查询超时（{timeout}秒）") from e
                    else:
                        raise e
            except Exception as e:
                logger.error(f"查询执行错误: {e}, SQL: {sql[:100]}...")
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.info(f"尝试重新执行查询，第{retries}次重试")
                    await asyncio.sleep(1)  # 等待1秒后重试
                else:
                    raise last_error

        # 如果所有重试都失败
        if last_error:
            raise last_error
        return []

    async def execute_batch_query(
        self, queries: Dict[str, Dict[str, Any]], timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行批量查询 - 异步版本

        参数:
            queries: 查询字典列表，每个字典包含sql和params
            timeout: 查询超时时间（秒），None表示使用默认值

        返回:
            查询结果字典，键为查询ID，值为结果
        """
        if timeout is None:
            timeout = self.query_timeout

        results = {}

        try:
            # 使用上下文管理器确保连接被正确释放
            async with self.connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    for query_id, query_info in queries.items():
                        sql = query_info.get("sql")
                        params = query_info.get("params", ())
                        try:
                            await asyncio.wait_for(
                                cursor.execute(sql, params), timeout=timeout
                            )
                            result = await asyncio.wait_for(
                                cursor.fetchall(), timeout=timeout
                            )
                            results[query_id] = result
                        except asyncio.TimeoutError:
                            logger.error(f"查询 {query_id} 超时")
                            results[query_id] = {"error": f"查询超时（{timeout}秒）"}
                        except Exception as e:
                            logger.error(f"查询 {query_id} 执行错误: {e}")
                            results[query_id] = {"error": str(e)}
            return results
        except Exception as e:
            logger.error(f"批量查询执行错误: {e}")
            # 如果是连接错误，尝试刷新连接池
            if isinstance(e, (aiomysql.OperationalError, asyncio.TimeoutError)):
                await self.refresh_pool()
            raise

    async def execute_paginated_query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        page_size: int = 100,
        page: int = 1,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """执行分页查询 - 为大数据集优化

        参数:
            sql: 基础SQL查询语句（不包含LIMIT）
            params: 查询参数
            page_size: 每页记录数
            page: 页码（从1开始）
            timeout: 查询超时时间（秒）

        返回:
            包含分页数据和元信息的字典
        """
        if timeout is None:
            timeout = self.query_timeout

        # 计算总记录数
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as t"

        # 添加分页
        offset = (page - 1) * page_size
        paginated_sql = f"{sql} LIMIT {offset}, {page_size}"

        try:
            # 使用上下文管理器确保连接被正确释放
            async with self.connection() as conn:
                total_count = 0

                # 获取总记录数
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await asyncio.wait_for(
                        cursor.execute(count_sql, params or ()), timeout=timeout
                    )
                    count_result = await asyncio.wait_for(
                        cursor.fetchone(), timeout=timeout
                    )
                    if count_result:
                        total_count = count_result["total"]

                # 获取分页数据
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await asyncio.wait_for(
                        cursor.execute(paginated_sql, params or ()), timeout=timeout
                    )
                    data = await asyncio.wait_for(cursor.fetchall(), timeout=timeout)

                total_pages = (
                    (total_count + page_size - 1) // page_size if page_size > 0 else 0
                )

                return {
                    "data": data,
                    "metadata": {
                        "page": page,
                        "page_size": page_size,
                        "total_pages": total_pages,
                        "total_count": total_count,
                    },
                }
        except asyncio.TimeoutError:
            logger.error(f"分页查询超时: {paginated_sql[:100]}...")
            raise TimeoutError(f"分页查询超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"分页查询错误: {e}, SQL: {paginated_sql[:100]}...")
            # 如果是连接错误，尝试刷新连接池
            if isinstance(e, aiomysql.OperationalError):
                await self.refresh_pool()
            raise


# 创建单例实例
warehouse_db = WarehouseDB()
