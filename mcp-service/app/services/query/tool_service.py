#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import sys
from datetime import datetime
from pathlib import Path

# backend_dir = Path(__file__).parent.parent.parent.parent
# print(backend_dir)
# sys.path.insert(0, str(backend_dir))
from typing import Any, Dict

import pytz
import requests

from app.models.schema import QueryDataResponse


def get_period_str(period):
    """将时间周期转换为字符串表示"""
    if isinstance(period, str):
        period = int(period)
    if period < 60:
        return f"{period}m"
    elif period < 1440:
        return f"{math.floor(period / 60)}h"
    elif period < 10080:
        return f"{math.floor(period / 1440)}d"
    elif period < 43200:
        return f"{math.floor(period / 10080)}w,259200000"
    else:
        return f"{math.floor(period / 43200)}n"


class ToolService:
    async def get_wh_data(self, parameters: Dict[str, Any]):
        code = parameters.get("code")
        if isinstance(code, list):
            code = code[0]
        days = parameters.get("days", "30")
        period = get_period_str(parameters.get("period", "1"))
        url = "http://122.51.27.47:6041/rest/sql"
        sql = f" select _wstart as t,FIRST(o) as o, MAX(h) as h, MIN(l) as l, LAST(c) as c, SUM(v) as v from `GTC-Demo_5`.`{code}_m1`  where t > now()-{days}*86400*1000 INTERVAL({period})  ORDER by _wstart desc  limit 200"
        parameters = {"code": code, "days": days, "period": period}
        if not code:
            return QueryDataResponse(
                success=False,
                message="没有对应的品种",
                data=0,
                parameters=parameters,
                sql_info={"sql": sql},
                query_metadata={"query_type": "tool_get_wh_data"},
            )

        response = requests.post(url, data=sql, auth=("root", "taosdata"))
        if response.status_code == 200:
            resault = response.json()
            column_meta = resault.get("column_meta", [])
            columns = []
            for column in column_meta:
                if column[0] == "t":
                    columns.append("MT_DATE")
                elif column[0] == "o":
                    columns.append("OPEN")
                elif column[0] == "h":
                    columns.append("HIGH")
                elif column[0] == "l":
                    columns.append("LOW")
                elif column[0] == "c":
                    columns.append("CLOSE")
                elif column[0] == "v":
                    columns.append("VOLUME")
                else:
                    columns.append(column[0])

            data = {"columns": columns, "rows": resault.get("data")}
            return QueryDataResponse(
                success=True,
                message="获取行情数据成功",
                data=data,
                parameters=parameters,
                sql_info={"sql": sql},
                query_metadata={"query_type": "statistics"},
            )
        else:
            return QueryDataResponse(
                success=True,
                message="获取行情据成功",
                data=None,
                parameters=parameters,
                sql_info={"sql": sql},
                query_metadata={"query_type": "statistics"},
            )


tool_service = ToolService()

# import asyncio

# if __name__ == "__main__":
#     print(asyncio.run(tool_service.get_wh_data(parameters={"code":"GBPUSD"})))


#     # 获取UTC时间
#     utc_now = datetime.now(pytz.utc)
#     print("=========utc_now===============", utc_now)
# url = "http://122.51.27.47:6041/rest/sql"
# # 查询系统表获取表名列表
# sql = "SELECT table_name FROM information_schema.ins_tables WHERE db_name = 'GTC-Demo_5'"
# response = requests.post(url, data=sql, auth=("root", "taosdata"))
# data = response.json()
# name = []
# for row in data.get("data",[]):
#     name.append(row[0].replace("_m1",""))
# print(name)
