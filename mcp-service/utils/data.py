#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
from typing import Any, Dict, List, Optional, Union


def filter_null_values(value: Any) -> Any:
    """
    过滤null和None值，包括字符串形式的"null"和"none"，替换为空字符串

    参数:
        value: 任意值

    返回:
        如果值为None、"null"或"none"（不区分大小写），则返回空字符串，否则返回原值
    """
    if value is None:
        return ""
    if isinstance(value, str):
        if value.lower() in ["null", "none"]:
            return ""
    return value


def compress_data(
    data: Union[List[Dict[str, Any]], Dict[str, Any]]
) -> Dict[str, Union[List[str], List[List[Any]]]]:
    """
    将字典列表或单个字典格式的数据压缩成更紧凑的格式

    参数:
        data: 字典列表或单个字典格式的数据
            如 [{'col1': val1, 'col2': val2}, {'col1': val3, 'col2': val4}]
            或 {'col1': val1, 'col2': val2}

    返回:
        压缩后的数据，格式为 {'columns': ['col1', 'col2'], 'rows': [[val1, val2], [val3, val4]]}
    """
    # 如果输入是字典，将其转换为只有一个元素的列表
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list) or not data or len(data) == 0:
        return data

    # 提取列名（使用第一行数据的键）
    columns = list(data[0].keys())

    # 提取每行的数据
    rows = []
    for item in data:
        row = [filter_null_values(item.get(col)) for col in columns]
        rows.append(row)

    return {"columns": columns, "rows": rows, "count": len(rows)}


def decompress_data(
    compressed_data: Dict[str, Union[List[str], List[List[Any]]]]
) -> List[Dict[str, Any]]:
    """
    将压缩格式的数据转换回字典列表格式

    参数:
        compressed_data: 压缩格式的数据，如 {'columns': ['col1', 'col2'], 'rows': [[val1, val2], [val3, val4]]}

    返回:
        字典列表格式的数据，如 [{'col1': val1, 'col2': val2}, {'col1': val3, 'col2': val4}]
    """
    columns = compressed_data.get("columns", [])
    rows = compressed_data.get("rows", [])

    result = []
    for row in rows:
        item = {}
        for i, col in enumerate(columns):
            if i < len(row):
                item[col] = filter_null_values(row[i])
        result.append(item)

    return result


def extract_limit(text: str) -> Optional[int]:
    """从文本中提取限制数量

    参数:
        text: 文本

    返回:
        提取的限制数量，如果未找到则返回None
    """
    pattern = r"(?:限制|最多|前)(?:显示|返回|查询)?\s*(\d+)\s*(?:条|笔|个|记录)?"
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def extract_userid(text: str) -> Optional[str]:
    """从文本中提取用户ID

    参数:
        text: 文本

    返回:
        提取的用户ID，如果未找到则返回None
    """
    pattern = r"(?:用户|客户)(?:ID|id|编号)[是为:：]?\s*[\"\'](.*?)[\"\']"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def convert_to_list(data: Any) -> List[str]:
    """将字符串转换为列表"""
    if data is None:
        return []
    if isinstance(data, str):
        return [data]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.keys())
    if isinstance(data, int):
        return [str(data)]
    if isinstance(data, float):
        return [str(data)]
    return []


def convert_to_timestamp(date_string: str) -> int:
    """将日期字符串转换为时间戳"""
    try:
        # 自动检测时间格式
        time_formats = [
            "%Y-%m-%d %H:%M:%S",  # 2025-08-01 12:30:45
            "%Y-%m-%d",  # 2025-08-01
            "%Y/%m/%d %H:%M:%S",  # 2025/08/01 12:30:45
            "%Y/%m/%d",  # 2025/08/01
        ]

        parsed_time = None
        for fmt in time_formats:
            try:
                parsed_time = time.strptime(date_string, fmt)
                break
            except ValueError:
                continue

        if parsed_time is None:
            raise ValueError(f"无法解析时间格式: {date_string}")

        date_string = int(time.mktime(parsed_time))
    except Exception as e:
        raise ValueError(f"无法解析时间格式: {date_string}")
    return date_string


# # 示例用法
# if __name__ == "__main__":
#     # 示例数据
#     sample_data = [
#         {
#             'TICKET': 46470636,
#             'LOGIN': 888068169,
#             'SYMBOL': '',
#             'CMD': 6,
#             'VOLUME': 1,
#             'OPEN_TIME': '2025-07-17T11:00:40',
#             'PROFIT': '1000.00000000',
#             'COMMENT': 'Pamm Dep 20250717',
#             'MODIFY_TIME': '2025-07-17T16:00:40'
#         },
#         {
#             'TICKET': 46570636,
#             'LOGIN': 888055569,
#             'SYMBOL': 'EURUSD',
#             'CMD': 2,
#             'VOLUME': 0.5,
#             'OPEN_TIME': '2025-06-17T11:00:40',
#             'PROFIT': '500.00000000',
#             'COMMENT': 'Pamm Dep 20250617',
#             'MODIFY_TIME': '2025-06-17T16:00:40'
#         }
#     ]

#     # 压缩数据
#     compressed = compress_data(sample_data)
#     print("压缩后的数据:")
#     print(compressed)

#     # 解压数据
#     decompressed = decompress_data(compressed)
#     print("\n解压后的数据:")
#     print(decompressed)
