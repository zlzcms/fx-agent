# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-03 18:36:24
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 16:24:17
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据转Markdown格式显示工具
"""

from datetime import datetime
from typing import Any, Dict, List

# backend_dir = Path(__file__).parent.parent.parent.parent
# sys.path.insert(0, str(backend_dir))
from backend.agents.config.mcp import INTENT_PATTERNS
from backend.agents.config.setting import settings
from backend.agents.utils.token_utils import estimate_tokens
from backend.utils.format_output import extract_json


def format_timestamp(timestamp_str: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str


def format_table_data(columns: List[str], rows: List[List[Any]], is_split: bool = False):
    """格式化表格数据为Markdown表格"""
    if not columns or not rows:
        return "无数据"

    # 创建表头
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    # 创建数据行
    data_rows = []
    current_row = []
    current_rows_count = 0
    for row in rows:
        formatted_row = []
        for cell in row:
            if cell is None:
                formatted_row.append("`null`")
            elif isinstance(cell, str):
                formatted_row.append(f"`{cell}`")
            elif isinstance(cell, (int, float)):
                formatted_row.append(str(cell))
            else:
                formatted_row.append(f"`{str(cell)}`")
        current_row.append("| " + " | ".join(formatted_row) + " |")
        current_rows_count += 1
        current_row_str = "\n".join([header, separator] + current_row)
        # print("current_row_str",estimate_tokens(current_row_str),settings.SPLIT_MAX_TOKEN)
        if is_split and estimate_tokens(current_row_str) > settings.SPLIT_MAX_TOKEN * 0.95:
            data_rows.append({"content": current_row_str, "count": current_rows_count})
            current_row = []
            current_rows_count = 0
    if current_row:
        data_rows.append({"content": "\n".join([header, separator] + current_row), "count": current_rows_count})
    if len(data_rows) == 1:
        return data_rows[0]["content"]
    else:
        return data_rows


def chunk_to_markdown(json_data: Dict[str, Any]) -> str:
    """将JSON数据转换为Markdown格式"""
    markdown_parts = []

    # 添加标题
    markdown_parts.append("# 数据报告\n")

    # 添加元数据信息
    if "metadata" in json_data:
        metadata = json_data["metadata"]
        markdown_parts.append("## 📊 元数据信息\n")
        markdown_parts.append("| 属性 | 值 |")
        markdown_parts.append("|------|-----|")
        markdown_parts.append(f"| 原始大小 | {metadata.get('original_size', 'N/A')} bytes |")
        markdown_parts.append(f"| 分块数量 | {metadata.get('chunk_count', 'N/A')} |")
        markdown_parts.append(f"| 分割策略 | {metadata.get('split_strategy', 'N/A')} |")
        markdown_parts.append(f"| 平均分块大小 | {metadata.get('average_chunk_size', 'N/A')} bytes |")
        markdown_parts.append(f"| 分块类型 | {', '.join(metadata.get('chunk_types', []))} |")

        if "processing_timestamp" in metadata:
            markdown_parts.append(f"| 处理时间 | {format_timestamp(metadata['processing_timestamp'])} |")

        if "config" in metadata:
            config = metadata["config"]
            markdown_parts.append(f"| 最大分块大小 | {config.get('max_chunk_size', 'N/A')} |")
            markdown_parts.append(f"| 最小分块大小 | {config.get('min_chunk_size', 'N/A')} |")
            markdown_parts.append(f"| 重叠大小 | {config.get('overlap_size', 'N/A')} |")

        markdown_parts.append("")

    # 添加时间戳
    if "timestamp" in json_data:
        markdown_parts.append(f"**生成时间:** {format_timestamp(json_data['timestamp'])}\n")

    # 处理数据块
    if "chunks" in json_data:
        markdown_parts.append("## 📋 数据内容\n")

        for i, chunk in enumerate(json_data["chunks"]):
            chunk_id = chunk.get("chunk_id", i)
            chunk_type = chunk.get("type", "unknown")
            table_name = chunk.get("table_name", f"table_{i}")
            row_count = chunk.get("row_count", 0)
            column_count = chunk.get("column_count", 0)

            markdown_parts.append(f"### 数据块 {chunk_id}: {table_name}\n")
            markdown_parts.append(f"**类型:** {chunk_type}  \n")
            markdown_parts.append(f"**行数:** {row_count}  \n")
            markdown_parts.append(f"**列数:** {column_count}  \n")

            if "data_summary" in chunk:
                markdown_parts.append(f"**数据摘要:** {chunk['data_summary']}\n")

            # 处理表格数据
            if "content" in chunk and table_name in chunk["content"]:
                table_data = chunk["content"][table_name]
                columns = table_data.get("columns", [])
                rows = table_data.get("rows", [])

                if columns and rows:
                    markdown_parts.append("**数据表格:**\n")
                    markdown_parts.append(format_table_data(columns, rows))
                    markdown_parts.append("")

            markdown_parts.append("---\n")

    return "\n".join(markdown_parts)


def format_user_timestamp(timestamp: int) -> str:
    """格式化Unix时间戳"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp)


def format_user_data_table(table_name: str, table_data: Dict[str, Any], is_split: bool = False):
    """格式化用户数据表格"""
    mcp_table_name = INTENT_PATTERNS.get(table_name, {}).get("name", table_name)
    if not table_data or "rows" not in table_data or "columns" not in table_data:
        return f"**{mcp_table_name}:** 无数据\n"
    columns_description = INTENT_PATTERNS.get(table_name, {}).get("fields", {})
    # 创建中英文结合的列名：英文字段名(中文描述)
    columns = []
    for column in table_data["columns"]:
        chinese_name = columns_description.get(column, column)
        # print(''======================="",chinese_name)
        if chinese_name != column:
            # 如果找到了中文描述，显示为：英文字段名(中文描述)
            columns.append(f"{column}({chinese_name})")
        else:
            # 如果没有找到中文描述，只显示英文字段名
            columns.append(column)
    rows = table_data["rows"]
    count = table_data.get("count", len(rows))

    markdown_parts = []
    markdown_parts_str = ""
    if columns and rows:
        table_data = format_table_data(columns, rows, is_split)
        if isinstance(table_data, list):
            for item in table_data:
                markdown_parts.append(f"**{mcp_table_name}** (共 {item['count']} 条记录):\n{item['content']}\n")
        else:
            markdown_parts_str += f"**{mcp_table_name}** (共 {count} 条记录):\n{table_data}\n"
    else:
        markdown_parts_str = f"**{mcp_table_name}**: 无数据\n"
    if markdown_parts:
        return markdown_parts
    else:
        return markdown_parts_str


def get_table_display_order() -> List[str]:
    """获取表的显示顺序

    返回:
        List[str]: 按INTENT_PATTERNS中定义的顺序排列的表名列表
    """
    # 直接使用INTENT_PATTERNS中定义的顺序
    return list(INTENT_PATTERNS.keys())


def users_to_markdown(users_data: Dict[str, Any]) -> str:
    """将表转换为Markdown格式"""
    result_markdown = []

    markdown_parts = []

    # 获取所有查询的表名（包括成功和失败的查询）
    all_queried_tables = set()

    # 从成功查询中收集表名
    data_dict = users_data.get("data", {})
    for table_name in data_dict.keys():
        all_queried_tables.add(table_name)

    # 从失败查询中收集表名
    for table_name in users_data.get("failed_queries", {}).keys():
        all_queried_tables.add(table_name)

    # 从查询条件中收集表名（确保所有查询的表都被显示）
    query_conditions = users_data.get("query_conditions", {})
    for table_name in query_conditions.keys():
        all_queried_tables.add(table_name)

    # 获取表的显示顺序
    table_order = get_table_display_order()

    # 用于记录已经处理过的表，避免重复
    processed_tables = set()

    # 先显示有序的表
    for table_name in table_order:
        # 如果表不在查询列表中，跳过
        if table_name not in all_queried_tables:
            continue

        # 避免重复处理同一个表
        if table_name in processed_tables:
            continue

        processed_tables.add(table_name)

        table_data = data_dict.get(table_name)
        if table_data and isinstance(table_data, dict) and "columns" in table_data:
            # 有数据的表
            user_data_table = format_user_data_table(table_name, table_data, is_split=True)
            if isinstance(user_data_table, list):
                # 列表类型的数据需要分段处理
                for item in user_data_table:
                    # 检查添加当前item后是否会超过token限制
                    is_split, combined_str = split_markdown_parts(markdown_parts, [item])
                    if is_split:
                        # 需要分割，先保存之前的 markdown_parts
                        if markdown_parts:
                            markdown_parts_str = "\n".join(markdown_parts)
                            result_markdown.append(markdown_parts_str)
                            markdown_parts = []
                        # 将当前item添加到新的段落
                        markdown_parts.append(item)
                    else:
                        # 不需要分割，直接添加到当前段落
                        markdown_parts.append(item)
            else:
                # 非列表类型，直接处理
                is_split, combined_str = split_markdown_parts(markdown_parts, [user_data_table])
                if is_split:
                    # 需要分割，先保存之前的 markdown_parts
                    if markdown_parts:
                        markdown_parts_str = "\n".join(markdown_parts)
                        result_markdown.append(markdown_parts_str)
                        markdown_parts = []
                    # 将当前表添加到新的段落
                    markdown_parts.append(user_data_table)
                else:
                    markdown_parts.append(user_data_table)
        elif table_name in users_data.get("failed_queries", {}):
            # 查询失败的表
            failed_data = users_data.get("failed_queries", {}).get(table_name)
            failed_msg = f"**{INTENT_PATTERNS.get(table_name, {}).get('name', table_name)}**: {failed_data.get('message', '查询失败')}\n"

            is_split, combined_str = split_markdown_parts(markdown_parts, [failed_msg])
            if is_split:
                # 需要分割，先保存之前的 markdown_parts
                if markdown_parts:
                    markdown_parts_str = "\n".join(markdown_parts)
                    result_markdown.append(markdown_parts_str)
                    markdown_parts = []
                # 将当前失败信息添加到新的段落
                markdown_parts.append(failed_msg)
            else:
                markdown_parts.append(failed_msg)
        else:
            # 查询成功但无数据的表（0条记录）或者数据格式不正确（如空列表）
            # 处理数据格式为列表的情况
            if isinstance(table_data, list) or (table_data is None):
                empty_table_data = {"columns": [], "rows": [], "count": 0}
                formatted = format_user_data_table(table_name, empty_table_data)

                is_split, combined_str = split_markdown_parts(markdown_parts, [formatted])
                if is_split:
                    # 需要分割，先保存之前的 markdown_parts
                    if markdown_parts:
                        markdown_parts_str = "\n".join(markdown_parts)
                        result_markdown.append(markdown_parts_str)
                        markdown_parts = []
                    # 将当前空表信息添加到新的段落
                    markdown_parts.append(formatted)
                else:
                    markdown_parts.append(formatted)
    if markdown_parts:
        markdown_parts_str = "\n".join(markdown_parts)
        result_markdown.append(markdown_parts_str)
    return result_markdown


def split_markdown_parts(old_markdown_parts: [list, str], new_markdown_parts: [list, str]):
    all_tokens = 0
    all_str = ""
    if old_markdown_parts:
        old_markdown_parts_str = (
            "\n".join(old_markdown_parts) if isinstance(old_markdown_parts, list) else old_markdown_parts
        )
        all_tokens += estimate_tokens(old_markdown_parts_str)
        all_str += f"\n{old_markdown_parts_str}" if all_str else old_markdown_parts_str
    if new_markdown_parts:
        new_markdown_parts_str = (
            "\n".join(new_markdown_parts) if isinstance(new_markdown_parts, list) else new_markdown_parts
        )
        all_tokens += estimate_tokens(new_markdown_parts_str)
        all_str += f"\n{new_markdown_parts_str}" if all_str else new_markdown_parts_str

    # print("all_tokens,SPLIT_MAX_TOKEN",all_tokens,settings.SPLIT_MAX_TOKEN)
    if all_tokens > settings.SPLIT_MAX_TOKEN:
        return True, all_str
    else:
        return False, all_str


def assistant_to_markdown(assistants_data) -> str:
    """将AI助手信息转换为Markdown格式，支持单个字典或字典列表"""
    markdown_parts = []

    # 确保 assistants_data 是列表格式
    if isinstance(assistants_data, dict):
        assistants_list = [assistants_data]
    elif isinstance(assistants_data, list):
        assistants_list = assistants_data
    else:
        raise ValueError(f"assistants_data must be a dict or list, got {type(assistants_data)}")

    # 添加标题
    markdown_parts.append("# AI助手信息\n")
    markdown_parts.append(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    markdown_parts.append(f"**助手总数:** {len(assistants_list)}\n")

    # 处理每个助手
    for i, assistant in enumerate(assistants_list):
        assistant_id = assistant.get("assistant_id", i)
        name = assistant.get("name", "未命名助手")

        markdown_parts.append(f"## {name}\n")

        # 显式定义表头与单行数据，确保结构为：第一行表头，第二行对应的值
        basic_columns = ["助手ID", "名称", "模型", "输出格式"]
        basic_values = [
            assistant_id,
            name,
            assistant.get("model", {}).get("name", ""),
            assistant.get("output_format", ""),
        ]
        header = "| " + " | ".join(basic_columns) + " |"
        separator = "| " + " | ".join(["---"] * len(basic_columns)) + " |"
        row = "| " + " | ".join([str(v) if v is not None else "" for v in basic_values]) + " |"
        markdown_parts.append("\n".join([header, separator, row]))

        # 处理查询类型
        query_types = assistant.get("query_types", [])
        markdown_parts.append("### 🔍 查询类型\n")
        markdown_parts.append(
            ",".join([INTENT_PATTERNS.get(query_type, {}).get("name", query_type) for query_type in query_types])
        )

        # 处理输出格式表格
        output_format_table = assistant.get("output_format_table", [])
        if output_format_table:
            markdown_parts.append("### 📊 输出格式表格\n")
            # print("=========output_format_table===============", output_format_table)
            output_format_table = extract_json(output_format_table)
            if isinstance(output_format_table, list):
                columns = ["字段", "类型", "描述"]
                rows = []
                for field in output_format_table:
                    if isinstance(field, dict):
                        rows.append(
                            [
                                field.get("fieldName", ""),
                                field.get("fieldType", ""),
                                field.get("fieldDesc", ""),
                            ]
                        )

                if rows:
                    markdown_parts.append(format_table_data(columns, rows))
                    markdown_parts.append("")

        # 处理输出格式文档
        output_format_document = assistant.get("output_format_document", "")
        if output_format_document:
            markdown_parts.append("### 📄 输出格式文档\n")
            markdown_parts.append(f"{output_format_document}\n")
            markdown_parts.append("")

        # 处理模型定义
        # model_definition = assistant.get("model_definition", "")
        # if model_definition:
        #     markdown_parts.append("### 🧠 模型定义\n")
        #     markdown_parts.append(f"```\n{model_definition}\n```\n")

        markdown_parts.append("---\n")

    return "\n".join(markdown_parts)


def report_to_markdown(report_data: Dict[str, Any], title: str = "数据分析报告") -> str:
    """将数据分析报告转换为Markdown格式

    参数:
        report_data: 包含分析报告数据的字典，结构如下:
            {
                "analytical_report": str,  # Markdown格式的分析报告
                "property_analysis": Dict,  # 属性分析结果
                "recommendations": List[str],  # 建议列表
                "confidence": float  # 置信度
            }
        title: 报告标题

    返回:
        str: Markdown格式的报告
    """
    markdown_parts = []

    # 添加分析报告主体内容
    analytical_report = report_data.get("analytical_report", "")
    if analytical_report:
        # 如果analytical_report已经是markdown格式，直接添加
        markdown_parts.append(f"\n{analytical_report}\n")
    else:
        markdown_parts.append("没有可分析的报告！")

    return "\n".join(markdown_parts)


if __name__ == "__main__":
    users_data = {
        "success": True,
        "message": "查询成功",
        "data": {
            "user_data": {
                "columns": [
                    "id",
                    "nickname",
                    "register_ip",
                    "register_group",
                    "register_area",
                    "email",
                    "d_code",
                    "country",
                    "banned_login",
                    "remark",
                    "login_error_used",
                    "login_error_time",
                    "leverage",
                    "update_time",
                    "mlevel",
                    "userType",
                    "kyc_status",
                    "Iscertified",
                    "commission_value",
                    "create_time",
                ],
                "rows": [
                    [
                        4011,
                        "ooooo yyyy",
                        "240e:382:839:a100:a109:7922:577f:ad7b",
                        "TEST\\TESTSR-USD",
                        "China|China|China",
                        "ouyang001@max.com",
                        "86",
                        "Albania",
                        "0",
                        "",
                        0,
                        0,
                        "",
                        1761962018,
                        1,
                        "direct",
                        9,
                        0,
                        0,
                        1761918270,
                    ]
                ],
                "count": 1,
            },
            "user_mt4_trades": [],
            "user_mt5_trades": [],
            "user_mt5_positions": [],
            "user_amount_log": [],
        },
        "metadata": {
            "query_time": None,
            "count": None,
            "parameters": {
                "user_mt4_trades": {
                    "email": ["ouyang001@max.com"],
                    "range_time": {"data_start_date": "2025-10-01 00:00:00", "data_end_date": "2025-11-01 10:58:27"},
                    "user_id": [4011],
                },
                "user_mt5_trades": {
                    "email": ["ouyang001@max.com"],
                    "range_time": {"data_start_date": "2025-10-01 00:00:00", "data_end_date": "2025-11-01 10:58:27"},
                    "user_id": [4011],
                },
                "user_mt5_positions": {
                    "email": ["ouyang001@max.com"],
                    "range_time": {"data_start_date": "2025-10-01 00:00:00", "data_end_date": "2025-11-01 10:58:27"},
                    "user_id": [4011],
                },
                "user_amount_log": {
                    "email": ["ouyang001@max.com"],
                    "range_time": {"data_start_date": "2025-10-01 00:00:00", "data_end_date": "2025-11-01 10:58:27"},
                    "user_id": [4011],
                },
                "crm_user_id": 1,
            },
            "failed_queries": {},
            "successful_queries": None,
        },
    }
    user_data_list = users_to_markdown(users_data)
    from backend.agents.tools.data_export_tool import DataExportTool

    tool = DataExportTool("data_reduce_strategy")
    ind = 1
    for user_data_item in user_data_list:
        tool.export_to_markdown(user_data_item, "ll", f"ggg{ind}")
        ind += 1
