#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询类型描述帮助工具
"""


def get_query_type_description(query_type: str) -> str:
    """获取查询类型描述"""
    descriptions = {
        # 用户相关
        "user_data": "用户信息",
        "user_op_log": "用户操作日志",
        "user_amount_log": "用户资金情况",
        "user_login_log": "用户登录日志",
        "user_forword_log": "用户转账日志",
        "user_mtlogin": "用户mt登录日志",
        # MT4相关
        "user_mt4_trades": "MT4交易信息",
        "user_mt4_user": "MT4用户信息",
        # MT5相关
        "user_mt5_trades": "MT5交易信息",
        "user_mt5_user": "MT5用户信息",
        "user_mt5_positions": "MT5持仓信息",
    }
    return descriptions.get(query_type, "数据")
