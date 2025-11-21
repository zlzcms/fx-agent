#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict

from app.models.schema import QueryDataResponse
from app.services.query.warehouse_user_service import warehouse_user_service
from app.services.sql_generate_service import SQLGenerator
from core.log import logger
from core.query_logger import QueryTimer
from db.warehouse import warehouse_db as base_db
from utils.date import get_start_and_end_time


class StatisticsService:
    """
    资金统计服务：统计入金和出金数据
    """

    async def get_statistics(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """
        获取入金和出金统计数据

        参数:
            parameters: 查询参数，包含时间范围等

        返回:
            包含统计结果的QueryDataResponse对象
        """
        sql_info = {}
        # print("=========parameters===============", parameters)
        # if parameters.get("crm_user_id") == 1:
        #     del parameters["crm_user_id"]
        #     del parameters["user_id"]
        #     del parameters["user_name"]
        # 获取入金账号数（direction=1的唯一member_id数量）
        (
            deposit_accounts,
            deposit_amount,
            sql_info["deposit_sql"],
        ) = await self.get_fund_statistics(parameters, 1)

        # 获取出金金额（根据source_currency联立t_currency_rate表计算）
        (
            withdrawal_accounts,
            withdrawal_amount,
            sql_info["withdrawal_sql"],
        ) = await self.get_fund_statistics(parameters, 2)

        # 获取登录统计数据
        (
            login_accounts,
            login_count,
            sql_info["login_sql"],
        ) = await self.get_login_statistics(parameters)

        statistics_data = {
            "deposit_accounts": deposit_accounts,
            "withdrawal_accounts": withdrawal_accounts,
            "deposit_amount": deposit_amount,
            "withdrawal_amount": withdrawal_amount,
            "login_accounts": login_accounts,
            "login_count": login_count,
        }

        statistics_name = parameters.get("statistics_name")
        if statistics_name:
            data = []
            if isinstance(statistics_name, str) and statistics_name in statistics_data:
                data = [{statistics_name: statistics_data[statistics_name]}]
            elif isinstance(statistics_name, list):
                data = [{name: statistics_data[name] for name in statistics_name}]
            if len(data) == 0:
                return QueryDataResponse(
                    success=False,
                    message="获取统计数据为0",
                    data=0,
                    parameters=parameters,
                    sql_info=sql_info,
                    query_metadata={
                        "query_type": "statistics",
                        "statistics_name": statistics_name,
                    },
                )
            # 返回包装后的单个值
            return QueryDataResponse(
                success=True,
                message="获取统计数据成功",
                data=data,
                parameters=parameters,
                sql_info=sql_info,
                query_metadata={
                    "query_type": "statistics",
                    "statistics_name": statistics_name,
                },
            )
        else:
            # 返回所有统计数据
            return QueryDataResponse(
                success=True,
                message="获取统计数据成功",
                data=[statistics_data],
                parameters=parameters,
                sql_info=sql_info,
                query_metadata={
                    "query_type": "statistics",
                },
            )

    async def get_fund_statistics(
        self, parameters: Dict[str, Any], direction: int = 1
    ) -> tuple[int, float, str]:
        """获取出入金统计"""
        # 创建SQLGenerator实例
        sql_gen = SQLGenerator("t_member_amount_log")

        sql_gen.add_condition("direction", "=", direction)

        # 添加条件：member_id
        member_id = None
        try:
            # 优先使用显式用户筛选（会自动进行层级校验）
            member_id = await warehouse_user_service._get_user_id(parameters)
        except Exception:
            member_id = None
        crm_user_id = parameters.get("crm_user_id")
        if crm_user_id == 1:
            pass
        else:
            if member_id:
                sql_gen.add_condition("member_id", "in", member_id)
            else:
                # 未提供用户筛选时，使用 crm_user_id 的层级范围（含本人）
                if crm_user_id is not None and str(crm_user_id).strip():
                    accessible_ids = (
                        await warehouse_user_service._get_accessible_member_ids_by_crm(
                            crm_user_id
                        )
                    )
                    # 若无可访问成员，则返回0统计（避免全库查询）
                    if not accessible_ids:
                        return 0, 0, ""
                    sql_gen.add_condition("member_id", "in", accessible_ids)
                else:
                    # 没有 crm_user_id，无法进行授权范围限制
                    return 0, 0, ""

        start_time, end_time = get_start_and_end_time(parameters, False)

        if start_time:
            sql_gen.add_condition("created_at", ">=", start_time)
        if end_time:
            sql_gen.add_condition("created_at", "<=", end_time)

        sql, params = sql_gen.generate_select(
            [
                "COUNT(DISTINCT member_id) as total_accounts",
                "SUM(destination_money_usd) as total_amounts",
            ]
        )

        # 使用查询计时器记录SQL执行情况
        with QueryTimer(
            "fund_statistics",
            parameters,
            sql,
            "t_fund_changes_history",
            sql_params=params,
        ) as timer:
            # print("=========sql===============", sql)
            # print("=========params===============", params)
            results = await base_db.execute_query(sql, params)
            timer.log_result(len(results) if results else 0, results)

        if results and results[0]:
            return results[0]["total_accounts"], results[0]["total_amounts"], sql
        else:
            return 0, 0, sql

    async def get_login_statistics(
        self, parameters: Dict[str, Any]
    ) -> tuple[int, int, str]:
        """
        获取登录统计数据

        参数:
            parameters: 查询参数，包含时间范围等

        返回:
            (登录用户数, 登录次数)
        """
        # 创建SQLGenerator实例
        sql_gen = SQLGenerator("t_member_login_log")

        # 添加条件：member_id
        member_id = None
        try:
            # 优先使用显式用户筛选（会自动进行层级校验）
            member_id = await warehouse_user_service._get_user_id(parameters)
        except Exception:
            member_id = None

        crm_user_id = parameters.get("crm_user_id")
        if crm_user_id == 1:
            pass
        else:
            if member_id:
                sql_gen.add_condition("member_id", "in", member_id)
            else:
                # 未提供用户筛选时，使用 crm_user_id 的层级范围（含本人）
                if crm_user_id is not None and str(crm_user_id).strip():
                    accessible_ids = (
                        await warehouse_user_service._get_accessible_member_ids_by_crm(
                            crm_user_id
                        )
                    )
                    # 若无可访问成员，则返回0统计（避免全库查询）
                    if not accessible_ids:
                        return 0, 0, ""
                    sql_gen.add_condition("member_id", "in", accessible_ids)
                else:
                    # 没有 crm_user_id，无法进行授权范围限制
                    return 0, 0, ""

        start_time, end_time = get_start_and_end_time(parameters, True)

        if start_time:
            sql_gen.add_condition("create_time", ">=", start_time)
        if end_time:
            sql_gen.add_condition("create_time", "<=", end_time)

        sql, params = sql_gen.generate_select(
            ["COUNT(DISTINCT member_id) as unique_users", "COUNT(*) as total_logins"]
        )

        # 使用查询计时器记录SQL执行情况
        with QueryTimer(
            "login_statistics", parameters, sql, "t_member_login_log", sql_params=params
        ) as timer:
            results = await base_db.execute_query(sql, params)
            timer.log_result(len(results) if results else 0, results)

        if results and results[0]:
            return results[0]["unique_users"], results[0]["total_logins"], sql
        else:
            return 0, 0, sql

    async def get_ib_statistics(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """
        获取IB代理统计数据，包括客户数、入金、出金、返佣和交易统计

        参数:
            parameters: 查询参数，包含partner_member_id和时间范围等

        返回:
            包含统计结果的QueryDataResponse对象
        """

        # 添加条件：partner_member_id（代理ID）。
        # 支持两种方式：
        # 1) 明确提供代理筛选（user_id/username等），自动进行层级校验
        # 2) 未提供代理筛选时，根据 crm_user_id 的层级范围（含本人）限定代理集合
        parameters["user_type"] = "agent"
        member_id = None
        if crm_user_id == 1:
            pass
        else:
            try:
                member_id = await warehouse_user_service._get_user_id(parameters)
            except Exception:
                member_id = None
            if not member_id:
                crm_user_id = parameters.get("crm_user_id")
                if crm_user_id is not None and str(crm_user_id).strip():
                    accessible_ids = (
                        await warehouse_user_service._get_accessible_member_ids_by_crm(
                            crm_user_id
                        )
                    )
                    if not accessible_ids:
                        return QueryDataResponse(
                            success=True,
                            message="未找到IB代理统计数据",
                            data=[],
                            parameters=parameters,
                            sql_info={"ib_statistics_sql": ""},
                            query_metadata={"query_type": "ib_statistics"},
                        )
                    member_id = accessible_ids
                else:
                    return QueryDataResponse(
                        success=False,
                        message="缺少crm_user_id参数",
                        data=[],
                        parameters=parameters,
                        query_metadata={"query_type": "ib_statistics"},
                    )

        # 获取时间范围
        start_time, end_time = get_start_and_end_time(parameters)

        # 构建SQL查询
        sql = """
        SELECT
            -- 客户数统计
            COUNT(DISTINCT rca.member_id) AS customer_count,

            -- 入金统计
            SUM(CASE
                WHEN fc.type = 'deposit' AND fc.status = 'done' THEN fc.destination_money_usd
                ELSE 0
            END) AS total_deposit_usd,

            -- 出金统计
            SUM(CASE
                WHEN fc.type = 'withdrawal' AND fc.status = 'done' THEN fc.destination_money_usd
                ELSE 0
            END) AS total_withdrawal_usd,

            -- 返佣统计
            SUM(CASE
                WHEN fc.type in ('reward','rebate','multi_commission') AND fc.status = 'done' THEN fc.destination_money_usd
                ELSE 0
            END) AS total_rebate_usd,

            -- 交易统计(百万交易量)
            SUM(t.volume_mln_usd) AS total_trading_volume_usd,
            -- 交易统计(利润)
            SUM(t.profit_usd) AS total_trading_profit_usd,
            -- 交易统计(交易数量)
            COUNT(t.id) AS total_trades

        FROM {warehouse_name}.t_ib_reports_client_accounts_main rca

        -- 关联资金变动历史表
        LEFT JOIN {warehouse_name}.t_fund_changes_history fc
            ON rca.member_id = fc.member_id

        -- 关联交易记录表
        LEFT JOIN {warehouse_name}.t_mt_trade_real_logs t
            ON rca.member_id = t.member_id

        WHERE
            -- 指定代理ID
        """.format(
            warehouse_name="devapi1_mtarde_c"
        )

        crm_user_id = (
            str(parameters.get("crm_user_id"))
            if parameters.get("crm_user_id")
            else None
        )
        if member_id:
            # 处理member_id参数
            if isinstance(member_id, list):
                if len(member_id) == 1:
                    sql += "rca.partner_member_id = %s"
                    params = [member_id[0]]
                else:
                    placeholders = ", ".join(["%s"] * len(member_id))
                    sql += f"rca.partner_member_id IN ({placeholders})"
                    params = member_id
            else:
                sql += "rca.partner_member_id = %s"
                params = [member_id]

        # 添加时间条件
        time_conditions = []
        if start_time:
            time_conditions.append(
                "(fc.created_at >= %s OR t.close_time >= %s OR rca.created_at >= %s)"
            )
            params.extend([start_time, start_time, start_time])

        if end_time:
            time_conditions.append(
                "(fc.created_at <= %s OR t.close_time <= %s OR rca.created_at <= %s)"
            )
            params.extend([end_time, end_time, end_time])

        if time_conditions:
            sql += " AND " + " AND ".join(time_conditions)

        # 添加分组
        sql += "\nGROUP BY rca.partner_member_id"

        # 使用查询计时器记录SQL执行情况
        with QueryTimer(
            "ib_statistics",
            parameters,
            sql,
            "t_ib_reports_client_accounts_main",
            sql_params=params,
        ) as timer:
            results = await base_db.execute_query(sql, params)
            timer.log_result(len(results) if results else 0, results)
        # 处理结果
        statistics_data = {
            "customer_count": results[0].get("customer_count", 0) if results else 0,
            "total_deposit_usd": results[0].get("total_deposit_usd", 0)
            if results
            else 0,
            "total_withdrawal_usd": results[0].get("total_withdrawal_usd", 0)
            if results
            else 0,
            "total_rebate_usd": results[0].get("total_rebate_usd", 0) if results else 0,
            "total_trading_volume_usd": results[0].get("total_trading_volume_usd", 0)
            if results
            else 0,
            "total_trading_profit_usd": results[0].get("total_trading_profit_usd", 0)
            if results
            else 0,
            "total_trades": results[0].get("total_trades", 0) if results else 0,
        }

        return QueryDataResponse(
            success=True,
            message="获取IB代理统计数据成功",
            data=[statistics_data],
            parameters=parameters,
            sql_info={"ib_statistics_sql": sql},
            query_metadata={"query_type": "ib_statistics"},
        )


statistics_service = StatisticsService()
