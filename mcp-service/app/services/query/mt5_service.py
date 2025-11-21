#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict

from app.models.schema import QueryDataResponse

from .base_mt_service import BaseMTService


class Mt5Service(BaseMTService):
    """MT5服务，处理MT5相关查询"""

    def get_mt_config(self) -> Dict[str, Any]:
        """获取MT5配置信息"""
        return {
            "trades": {
                "table_name": "mt4_trades",
                "db_name": "mt5_report_1110",
                "time_field": "Time",
                "order_by": ("Time", "DESC"),
                "isstrptime": True,
                "query_type": "user_mt5_trades",
                "error_message": "未找到mt5_1110交易信息",
            },
            "user": {
                "table_name": "mt4_users",
                "db_name": "mt5_report_1110",
                "time_field": None,
                "order_by": None,
                "isstrptime": False,
                "query_type": "user_mt5_user",
                "error_message": "未找到mt5_1110用户信息",
            },
            "positions": {
                "table_name": "mt_positions",
                "db_name": "mt5_report_1110",
                "login_field": "Login",
                "time_field": "TimeCreate",
                "order_by": ("TimeCreate", "DESC"),
                "isstrptime": True,
                "query_type": "user_mt5_positions",
                "error_message": "未找到mt5_1110持仓信息",
            },
        }

    async def get_mt5_1110_trades(
        self, parameters: Dict[str, Any]
    ) -> QueryDataResponse:
        """查询MT5交易信息"""
        config = self.get_mt_config()["trades"]
        return await self._query_mt_data(
            parameters=parameters,
            table_name=config["table_name"],
            target_db_name=config["db_name"],
            time_field=config["time_field"],
            order_by=config["order_by"],
            isstrptime=config["isstrptime"],
            query_type=config["query_type"],
            error_message=config["error_message"],
        )

    async def get_mt5_1110_user(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询MT5用户信息"""
        config = self.get_mt_config()["user"]
        return await self._query_mt_data(
            parameters=parameters,
            table_name=config["table_name"],
            target_db_name=config["db_name"],
            time_field=config["time_field"],
            order_by=config["order_by"],
            isstrptime=config["isstrptime"],
            query_type=config["query_type"],
            error_message=config["error_message"],
        )

    async def get_mt5_1110_positions(
        self, parameters: Dict[str, Any]
    ) -> QueryDataResponse:
        """查询MT5持仓信息"""
        config = self.get_mt_config()["positions"]
        return await self._query_mt_data(
            parameters=parameters,
            table_name=config["table_name"],
            target_db_name=config["db_name"],
            login_field=config["login_field"],
            time_field=config["time_field"],
            order_by=config["order_by"],
            isstrptime=config["isstrptime"],
            query_type=config["query_type"],
            error_message=config["error_message"],
        )


mt5_service = Mt5Service()
