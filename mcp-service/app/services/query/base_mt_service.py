#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT服务基类，提取MT4和MT5的公共功能
"""
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from numbers import Number
from typing import Any, Dict, List, Optional, Tuple

from app.models.schema import QueryDataResponse
from app.services.query.warehouse_user_service import warehouse_user_service
from app.services.sql_generate_service import SQLGenerator
from core.log import logger
from core.query_logger import QueryTimer
from db.warehouse import warehouse_db as base_db
from utils.query_type_helper import get_query_type_description


class BaseMTService(ABC):
    """MT服务基类"""

    def __init__(self):
        self._query_start_time: Optional[float] = None
        self._mtlogin_cache: Dict[str, List[Any]] = {}  # 缓存user_mtlogin结果

    def _build_response_with_sql_info(
        self,
        sql_generator: SQLGenerator,
        sql: str,
        params: List[Any],
        results: List[Any],
        query_type: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """构建包含SQL信息的响应"""
        execution_time = time.time() - getattr(self, "_query_start_time", time.time())
        sql_info = {
            "table": sql_generator.table_name,
            "sql": sql,
            "parameters": params,
            "execution_time": execution_time,
            "row_count": len(results) if results else 0,
        }

        return {
            "sql_info": sql_info,
            "query_metadata": {
                "query_type": query_type,
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def _get_user_mtlogin(
        self, parameters: Dict[str, Any], is_create_time: bool = False
    ) -> Optional[List[Any]]:
        """查询用户mt交易账号信息（带缓存）"""
        # 生成缓存键：将parameters的所有值组成字符串
        cache_key = json.dumps(parameters, sort_keys=True, ensure_ascii=False)

        # 检查缓存
        if cache_key in self._mtlogin_cache:
            logger.info(f"使用缓存的user_mtlogin结果: {cache_key}")
            return self._mtlogin_cache[cache_key]

        try:
            mtlogin_response: QueryDataResponse = (
                await warehouse_user_service.get_user_mtlogin(
                    parameters, log_query=False, is_create_time=is_create_time
                )
            )
            if mtlogin_response.success:
                # 缓存结果
                self._mtlogin_cache[cache_key] = mtlogin_response.data
                logger.info(f"缓存user_mtlogin结果: {cache_key}")
                return mtlogin_response.data
            return None
        except Exception as e:
            logger.error(f"查询用户mt交易账号信息错误: {str(e)}")
            return None

    def _get_table_name_by_db_name(self, db_name: str, default_table_name: str) -> str:
        """根据数据库名获取正确的表配置名"""
        # 数据库名到表配置名的映射
        db_to_table_mapping = {
            "ib_report": {
                "mt4_trades": "ib_report_trades",
                "mt4_users": "ib_report_users",
            },
            "mt4_report_194": {
                "mt4_trades": "mt4_trades_194",
                "mt4_users": "mt4_users_194",
            },
            "mt5_report": {
                "mt4_trades": "mt5_report_trades",
                "mt4_users": "mt5_report_users",
                "mt_positions": "mt5_report_positions",
            },
            "mt5_report_1110": {
                "mt4_trades": "mt5_trades_1110",
                "mt4_users": "mt5_users_1110",
                "mt_positions": "mt5_positions_1110",
            },
        }

        # 获取数据库对应的表映射
        table_mapping = db_to_table_mapping.get(db_name, {})
        # 返回映射的表名，如果没有映射则返回默认表名
        return table_mapping.get(default_table_name, default_table_name)

    def _filter_mtlogins_by_db_name(
        self, mtlogins: List[Any], target_db_name: str
    ) -> tuple[List[int], str]:
        """根据数据库名过滤登录ID，并返回匹配的数据库名"""
        loginids = []
        matched_db_name = None

        for mtlogin in mtlogins:
            loginid = mtlogin.get("loginid")
            db_name = mtlogin.get("link_db_name")
            if db_name == target_db_name:
                loginids.append(loginid)
                if matched_db_name is None:
                    matched_db_name = db_name

        return loginids, matched_db_name

    async def _query_mt_data(
        self,
        parameters: Dict[str, Any],
        table_name: str,
        target_db_name: str,
        login_field: str = "LOGIN",
        time_field: Optional[str] = None,
        order_by: Optional[Tuple[str, str]] = None,
        isstrptime: bool = False,
        query_type: str = "mt_data",
        error_message: str = "未找到数据",
    ) -> QueryDataResponse:
        """通用MT数据查询方法"""
        try:
            mtlogins = await self._get_user_mtlogin(parameters)
            # print('======mtlogins=====',mtlogins)
            if not mtlogins:
                return QueryDataResponse(
                    success=True,
                    message=f"未找到{get_query_type_description(query_type)}",
                    data=[],
                    parameters=parameters,
                    sql_info=None,
                    query_metadata={
                        "query_type": query_type,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            loginids, matched_db_name = self._filter_mtlogins_by_db_name(
                mtlogins, target_db_name
            )
            # print('======loginids=====',mtlogins)
            if not loginids:
                return QueryDataResponse(
                    success=True,
                    message=f"未找到{get_query_type_description(query_type)}",
                    data=[],
                    parameters=parameters,
                    sql_info=None,
                    query_metadata={
                        "query_type": query_type,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # 根据匹配的数据库名选择正确的表配置
            actual_table_name = self._get_table_name_by_db_name(
                matched_db_name, table_name
            )

            # 生成SQL
            sql_generator = SQLGenerator(actual_table_name)
            sql_generator.add_condition(login_field, "IN", loginids)
            # 限制仅查询交易方向为买卖的记录（CMD=0或CMD=1）
            if query_type in ["user_mt4_trades", "user_mt5_trades"]:
                sql_generator.add_condition("CMD", "IN", [0, 1])

            # 用户基本信息查询默认只返回一条记录
            # 如果需要查询多条记录，请在参数中明确指定 limit
            if (
                query_type in ["user_data", "user_mt4_user", "user_mt5_user"]
                and "limit" not in parameters
            ):
                parameters["limit"] = 1

            sql, params = sql_generator.generate_sql(
                parameters,
                time_field=time_field,
                isstrptime=isstrptime,
                order_by=order_by,
            )
            # print('========isstrptime======',isstrptime)
            # print('========time_field======',time_field)
            # print('========sql======',sql)
            # print("=======params=====",params)
            # 使用查询计时器记录SQL执行情况
            with QueryTimer(
                query_type,
                parameters,
                sql,
                table_name,
                target_db_name,
                sql_params=params,
            ) as timer:
                self._query_start_time = time.time()
                results = await base_db.execute_query(sql, params)
                if results:
                    for row in results:
                        if isinstance(row, dict) and "VOLUME" in row:
                            volume_value = row.get("VOLUME")
                            if volume_value is None:
                                continue
                            if isinstance(volume_value, Number):
                                row["VOLUME"] = volume_value / 100
                            else:
                                try:
                                    row["VOLUME"] = float(volume_value) / 100
                                except (TypeError, ValueError):
                                    continue

                execution_time = time.time() - self._query_start_time

                # 记录查询结果
                timer.log_result(len(results) if results else 0, results)

            sql_data = self._build_response_with_sql_info(
                sql_generator, sql, params, results, query_type, parameters
            )

            # 无论是否有结果，都返回success=True，没有数据时返回空列表
            return QueryDataResponse(
                success=True,
                message="查询成功"
                if results
                else f"未找到{get_query_type_description(query_type)}",
                data=results if results else [],
                parameters=parameters,
                **sql_data,
            )

        except Exception as e:
            logger.error(f"查询{query_type}错误: {str(e)}")

            return QueryDataResponse(
                success=False,
                message=str(e),
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": query_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    @abstractmethod
    def get_mt_config(self) -> Dict[str, Any]:
        """获取MT配置信息，子类必须实现"""
        pass
