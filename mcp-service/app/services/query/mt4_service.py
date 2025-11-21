#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from app.models.schema import QueryDataResponse

from .base_mt_service import BaseMTService


class Mt4Service(BaseMTService):
    """MT4服务，处理MT4相关查询"""

    def get_mt_config(self) -> Dict[str, Any]:
        """获取MT4配置信息"""
        return {
            "trades": {
                "table_name": "mt4_trades_194",
                "db_name": "mt4_report_194",
                "time_field": "OPEN_TIME",
                "order_by": ("OPEN_TIME", "DESC"),
                "isstrptime": False,
                "query_type": "user_mt4_trades",
                "error_message": "未找到mt4_194交易信息",
            },
            "user": {
                "table_name": "mt4_users_194",
                "db_name": "mt4_report_194",
                "time_field": None,
                "order_by": None,
                "isstrptime": False,
                "query_type": "user_mt4_user",
                "error_message": "未找到mt4_194用户信息",
            },
        }

    async def get_mt4_194_trades(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询MT4交易信息"""
        config = self.get_mt_config()["trades"]
        # print("=====查询MT4交易信息=======",config)
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

    async def get_mt4_194_user(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询MT4用户信息"""
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


mt4_service = Mt4Service()
