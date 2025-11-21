#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量风控用户服务
基于原始风控用户识别脚本优化实现
"""

import asyncio
import logging
import time

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from backend.common.enums import RiskType
from backend.core.conf import settings

logger = logging.getLogger(__name__)


class IncrementalRiskUserService:
    """增量风控用户服务"""

    def __init__(self):
        self.database_name = (
            settings.DATABASE_WAREHOUSE_NAME
            if hasattr(settings, "DATABASE_WAREHOUSE_NAME") and settings.DATABASE_WAREHOUSE_NAME
            else "devapi1_mtarde_c"
        )
        self._engine: Optional[AsyncEngine] = None
        self._engine_lock = asyncio.Lock()

    def _create_warehouse_url(self, database_name: Optional[str] = None) -> URL:
        """创建数据仓库连接URL"""
        return URL.create(
            drivername="mysql+asyncmy",
            username=settings.DATABASE_WAREHOUSE_USER,
            password=settings.DATABASE_WAREHOUSE_PASSWORD,
            host=settings.DATABASE_WAREHOUSE_HOST,
            port=settings.DATABASE_WAREHOUSE_PORT,
            database=database_name or self.database_name,
            query={"charset": settings.DATABASE_WAREHOUSE_CHARSET},
        )

    async def _get_engine(self) -> AsyncEngine:
        """获取或创建数据库引擎（单例模式）"""
        if self._engine is None:
            async with self._engine_lock:
                if self._engine is None:
                    url = self._create_warehouse_url()
                    self._engine = create_async_engine(
                        url,
                        pool_size=15,  # 适中的基本连接池大小
                        max_overflow=25,  # 适中的溢出连接数
                        pool_timeout=30,  # 获取连接超时时间
                        pool_recycle=3600,  # 1小时回收连接
                        pool_pre_ping=True,  # 连接前检测
                        echo=False,
                    )
                    logger.info("Created new database engine for warehouse")
        return self._engine

    @asynccontextmanager
    async def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        engine = await self._get_engine()
        conn = None
        try:
            conn = await engine.connect()
            yield conn
        except Exception as e:
            logger.exception(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                await conn.close()

    # SQLAlchemy 会在进程结束时自动清理连接池，不需要手动管理

    async def get_incremental_risk_users(self, hours: int = 6) -> Dict[str, Any]:
        """
        获取指定时间段内需要风控检查的用户集合（基于原始脚本优化）

        Args:
            hours: 时间范围（小时）

        Returns:
            包含用户ID集合和详细信息的字典
        """
        # 计算时间范围（Unix时间戳）
        end_time = int(time.time())
        start_time = end_time - (hours * 3600)

        logger.info(f"检测时间范围: {datetime.fromtimestamp(start_time)} 到 {datetime.fromtimestamp(end_time)}")
        logger.info(f"时间戳范围: {start_time} 到 {end_time}")

        # 构建查询SQL（基于原始脚本的UNION ALL方式）

        sql = f"""
        -- 汇总所有{hours}小时内有变动的用户ID，去重后形成风控用户集
        SELECT
            user_id,
            GROUP_CONCAT(DISTINCT trigger_type ORDER BY trigger_type) AS trigger_reasons,
            COUNT(DISTINCT trigger_type) AS trigger_count
        FROM (
            -- 1. 新注册用户 (t_member)
            SELECT DISTINCT id AS user_id, 'new_register' AS trigger_type
            FROM {self.database_name}.t_member
            WHERE create_time >= :start_time AND create_time <= :end_time

            UNION ALL

            -- 2. 新登录记录 (t_member_login_log)
            SELECT DISTINCT member_id AS user_id, 'new_login' AS trigger_type
            FROM {self.database_name}.t_member_login_log
            WHERE create_time >= :start_time AND create_time <= :end_time
            AND member_id IS NOT NULL

            UNION ALL

            -- 3. 新转账记录 (t_member_forword_log)
            SELECT DISTINCT member_id AS user_id, 'new_transfer' AS trigger_type
            FROM {self.database_name}.t_member_forword_log
            WHERE create_time >= :start_time AND create_time <= :end_time
            AND member_id IS NOT NULL

            UNION ALL

            -- 4. 新操作记录 (t_operation_log)
            SELECT DISTINCT member_id AS user_id, 'new_operation' AS trigger_type
            FROM {self.database_name}.t_operation_log
            WHERE created_at >= :start_time AND created_at <= :end_time
            AND member_id IS NOT NULL

            UNION ALL

            -- 5. MT4新交易记录 (mt4_trades_194) - OPEN_TIME是UTC时区的datetime格式
            SELECT DISTINCT tml.member_id AS user_id, 'new_mt4_trade' AS trigger_type
            FROM mt4_report_194.mt4_trades mt4
            INNER JOIN {self.database_name}.t_member_mtlogin tml ON mt4.LOGIN = tml.loginid
            INNER JOIN {self.database_name}.t_mt_server tms ON tml.mtserver = tms.id
            WHERE UNIX_TIMESTAMP(mt4.OPEN_TIME) >= :start_time
              AND UNIX_TIMESTAMP(mt4.OPEN_TIME) <= :end_time
              AND tms.db_name = 'mt4_report_194'
              AND tml.member_id IS NOT NULL

            UNION ALL

            -- 6. MT5新交易记录 (mt5_trades_1110) - Time是GMT+5时区的Unix时间戳，需要转换为UTC
            SELECT DISTINCT tml.member_id AS user_id, 'new_mt5_trade' AS trigger_type
            FROM mt5_report_1110.mt4_trades mt5
            INNER JOIN {self.database_name}.t_member_mtlogin tml ON mt5.LOGIN = tml.loginid
            INNER JOIN {self.database_name}.t_mt_server tms ON tml.mtserver = tms.id
            WHERE (mt5.Time - 5*3600) >= :start_time
              AND (mt5.Time - 5*3600) <= :end_time
              AND tms.db_name = 'mt5_report_1110'
              AND tml.member_id IS NOT NULL
        ) risk_users
        WHERE user_id IS NOT NULL
        GROUP BY user_id
        ORDER BY trigger_count DESC, user_id
        """

        # 参数字典
        params = {"start_time": start_time, "end_time": end_time}

        try:
            # 使用单例引擎和连接池（避免资源泄漏）
            async with self._get_connection() as conn:
                result = await conn.execute(text(sql), params)
                rows = result.fetchall()

            # 提取用户ID列表和详细信息
            details = [dict(row._mapping) for row in rows]
            user_ids = [detail["user_id"] for detail in details]

            return {
                "success": True,
                "time_range": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_datetime": datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "end_datetime": datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "hours": hours,
                },
                "risk_users": {"count": len(user_ids), "user_ids": user_ids, "details": details},
            }

        except Exception as e:
            logger.exception(f"查询风控用户错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "time_range": {"start_time": start_time, "end_time": end_time, "hours": hours},
            }

    async def get_simple_risk_users(self, hours: int = 6) -> List[int]:
        """
        获取简单的风控用户ID列表

        Args:
            hours: 时间范围（小时）

        Returns:
            用户ID列表
        """
        result = await self.get_incremental_risk_users(hours)
        if result["success"]:
            return result["risk_users"]["user_ids"]
        else:
            return []

    async def get_incremental_users_by_risk_type(
        self, db: AsyncSession, risk_type: RiskType, hours: int = 6, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        根据风控类型过滤增量用户

        Args:
            db: 数据库会话
            risk_type: 风控类型
            hours: 时间窗口
            limit: 结果限制数量

        Returns:
            过滤后的用户列表，包含user_id和trigger_reasons
        """
        try:
            # 获取风控用户ID列表
            risk_users_result = await self.get_incremental_risk_users(hours=hours)

            if not risk_users_result["success"]:
                logger.error(f"获取增量用户失败: {risk_users_result.get('error', 'Unknown error')}")
                return []

            user_ids = risk_users_result["risk_users"]["user_ids"]
            if not user_ids:
                logger.info("未发现需要风控检查的用户")
                return []

            # 根据风控类型构建用户类型过滤条件
            user_type_condition = ""
            if risk_type == RiskType.ALL_EMPLOYEE:
                # 客户风控：userType='direct'
                user_type_condition = "AND userType = 'direct'"
            elif risk_type == RiskType.CRM_USER:
                # 员工风控：userType='staff'
                user_type_condition = "AND userType = 'staff'"
            elif risk_type == RiskType.AGENT_USER:
                # 代理商风控：userType='agent'
                user_type_condition = "AND userType = 'agent'"
            elif risk_type == RiskType.PAYMENT:
                # 出金风控：包含所有用户类型
                user_type_condition = ""

            # 只查询用户ID和userType进行过滤
            user_ids_str = ",".join(map(str, user_ids))
            query_sql = f"""
            SELECT id
            FROM {self.database_name}.t_member
            WHERE id IN ({user_ids_str})
            {user_type_condition}
            ORDER BY id
            """

            # 使用单例引擎和连接池（避免资源泄漏）
            async with self._get_connection() as conn:
                result = await conn.execute(text(query_sql))
                rows = result.fetchall()

            # 构建过滤后的用户列表
            filtered_users = []
            filtered_user_ids = [row[0] for row in rows]

            for detail in risk_users_result["risk_users"]["details"]:
                if detail["user_id"] in filtered_user_ids:
                    filtered_users.append(
                        {
                            "user_id": detail["user_id"],
                            "trigger_reasons": detail["trigger_reasons"],
                            "trigger_count": detail["trigger_count"],
                            "risk_type": risk_type,
                        }
                    )

            logger.info(f"风控类型 {risk_type} 获取到 {len(filtered_users)} 个增量用户")
            return filtered_users

        except Exception as e:
            logger.exception(f"根据风控类型过滤增量用户失败: {str(e)}")
            return []

    async def demo_risk_detection(self, hours: int = 6) -> Dict[str, Any]:
        """
        演示风控用户检测功能（类似原始脚本的main函数）

        Args:
            hours: 时间范围（小时）

        Returns:
            检测结果摘要
        """
        logger.info("=" * 50)
        logger.info("风控用户识别服务")
        logger.info("=" * 50)

        # 检测风控用户
        result = await self.get_incremental_risk_users(hours=hours)

        if result["success"]:
            logger.info("✅ 检测成功!")
            logger.info(
                f"📅 时间范围: {result['time_range']['start_datetime']} 到 {result['time_range']['end_datetime']}"
            )
            logger.info(f"👥 发现风控用户: {result['risk_users']['count']} 个")

            if result["risk_users"]["count"] > 0:
                logger.info(f"📋 用户ID列表: {result['risk_users']['user_ids']}")

                logger.info("📊 详细触发信息:")
                for user in result["risk_users"]["details"]:
                    logger.info(
                        f"  用户ID: {user['user_id']}, "
                        f"触发次数: {user['trigger_count']}, "
                        f"触发原因: {user['trigger_reasons']}"
                    )
            else:
                logger.info("✨ 在指定时间范围内未发现需要风控检查的用户")

        else:
            logger.error(f"❌ 检测失败: {result.get('error', 'Unknown error')}")

        logger.info("=" * 50)

        # 示例：获取简单的用户ID列表
        logger.info("📝 简单模式示例:")
        simple_users = await self.get_simple_risk_users(hours=hours)
        logger.info(f"风控用户ID列表: {simple_users}")

        return result


# 创建全局实例
incremental_risk_user_service = IncrementalRiskUserService()
