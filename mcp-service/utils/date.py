# -*- coding: utf-8 -*-
# @Author: claude-4-sonnet
# @Date:   2025-06-27 10:00:00
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from dateutil.relativedelta import relativedelta

from utils.data import convert_to_timestamp


def generate_time_range(
    time_range_type: str, time_value: Union[str, int]
) -> Dict[str, str]:
    """
    根据时间范围类型和值生成开始时间和结束时间

    Args:
        time_range_type: 时间范围类型，可选值为 day, month, quarter, year
        time_value: 时间值，例如 7 表示 7 天、7 个月等

    Returns:
        包含开始时间和结束时间的字典，格式为 {"start_time": "YYYY-MM-DD HH:MM:SS", "end_time": "YYYY-MM-DD HH:MM:SS"}
        如果输入无效，则返回空字典
    """
    if not time_range_type or not time_value:
        # 如果未提供时间范围，默认使用2年范围
        time_range_type = "year"
        time_value = 2

    # 获取当前时间作为结束时间
    end_time = datetime.now()

    try:
        # 将时间值转换为整数
        time_value = int(time_value)

        # 根据时间范围类型计算开始时间
        if time_range_type == "day":
            start_time = end_time - timedelta(days=time_value)
        elif time_range_type == "month":
            # 计算月份
            year = end_time.year
            month = end_time.month - time_value

            # 处理月份溢出
            while month <= 0:
                month += 12
                year -= 1

            start_time = datetime(year, month, end_time.day)
            # 处理日期溢出（如2月30日）
            while True:
                try:
                    start_time = datetime(year, month, end_time.day)
                    break
                except ValueError:
                    # 如果日期无效，尝试减少一天
                    end_time = end_time.replace(day=end_time.day - 1)
        elif time_range_type == "quarter":
            # 一个季度按3个月计算
            year = end_time.year
            month = end_time.month - (time_value * 3)

            # 处理月份溢出
            while month <= 0:
                month += 12
                year -= 1

            start_time = datetime(year, month, end_time.day)
            # 处理日期溢出（如2月30日）
            while True:
                try:
                    start_time = datetime(year, month, end_time.day)
                    break
                except ValueError:
                    # 如果日期无效，尝试减少一天
                    end_time = end_time.replace(day=end_time.day - 1)
        elif time_range_type == "year":
            # 处理日期溢出（如闰年的2月29日）
            try:
                start_time = datetime(
                    end_time.year - time_value, end_time.month, end_time.day
                )
            except ValueError:
                # 如果日期无效（如非闰年的2月29日），使用2月28日
                if end_time.month == 2 and end_time.day == 29:
                    start_time = datetime(end_time.year - time_value, 2, 28)
                else:
                    # 其他无效情况，抛出异常
                    raise
        else:
            return None, None

        # 格式化日期时间字符串
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        return start_time_str, end_time_str
    except (ValueError, TypeError):
        # 处理无效的输入值
        return None, None


def convert_relative_date_to_mysql_format(relative_date: str) -> Optional[str]:
    """
    将相对时间表达式转换为MySQL可查询的时间格式（YYYY-MM-DD HH:MM:SS）

    支持的相对时间格式:
    - 数字+时间单位+前，如: "1天前", "3个月前", "2年前"
    - 特殊时间表达，如: "当前日期", "今天", "昨天", "上周", "上个月", "去年"

    参数:
        relative_date: 相对时间表达式

    返回:
        MySQL格式的时间字符串或None（如果无法解析）
    """
    if not relative_date:
        return None

    now = datetime.now()

    # 处理"当前日期"、"今天"、"现在"
    if relative_date in ["当前日期", "今天", "现在"]:
        return now.strftime("%Y-%m-%d %H:%M:%S")

    # 处理"昨天"
    if relative_date == "昨天":
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d %H:%M:%S")

    # 处理"上周"
    if relative_date == "上周":
        last_week = now - timedelta(days=7)
        return last_week.strftime("%Y-%m-%d %H:%M:%S")

    # 处理"上个月"
    if relative_date == "上个月":
        last_month = now - relativedelta(months=1)
        return last_month.strftime("%Y-%m-%d %H:%M:%S")

    # 处理"去年"
    if relative_date == "去年":
        last_year = now - relativedelta(years=1)
        return last_year.strftime("%Y-%m-%d %H:%M:%S")

    # 处理"数字+时间单位+前"格式
    pattern = r"(\d+)(?:个)?([天周月年])前"
    match = re.match(pattern, relative_date)

    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if unit == "天":
            target_date = now - timedelta(days=amount)
        elif unit == "周":
            target_date = now - timedelta(weeks=amount)
        elif unit == "月":
            target_date = now - relativedelta(months=amount)
        elif unit == "年":
            target_date = now - relativedelta(years=amount)
        else:
            return None

        return target_date.strftime("%Y-%m-%d %H:%M:%S")

    # 如果已经是标准格式，直接返回
    date_pattern = r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?"
    if re.fullmatch(date_pattern, relative_date):
        # 如果只有日期部分，添加时间部分
        if len(relative_date) == 10:
            return relative_date + " 00:00:00"
        return relative_date

    return None


def get_mysql_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple:
    """
    获取MySQL格式的日期范围

    参数:
        start_date: 开始日期（相对或绝对）
        end_date: 结束日期（相对或绝对）

    返回:
        转换后的MySQL格式日期范围元组 (start_date, end_date)
    """
    mysql_start_date = (
        convert_relative_date_to_mysql_format(start_date) if start_date else None
    )
    mysql_end_date = (
        convert_relative_date_to_mysql_format(end_date) if end_date else None
    )

    return mysql_start_date, mysql_end_date


def get_register_time(register_time: Dict[str, Any] | str):
    start_date, end_date = None, None
    if isinstance(register_time, Dict):
        if register_time.get("start_date"):
            start_date = convert_to_timestamp(register_time.get("start_date"))
        elif register_time.get("register_start_date"):
            start_date = convert_to_timestamp(register_time.get("register_start_date"))
        if register_time.get("end_date"):
            end_date = convert_to_timestamp(register_time.get("end_date"))
        elif register_time.get("register_end_date"):
            end_date = convert_to_timestamp(register_time.get("register_end_date"))
    elif isinstance(register_time, str):
        start_date = convert_to_timestamp(register_time)
    return start_date, end_date


def get_start_and_end_time(parameters: Dict[str, Any], isstrptime=False):
    start_date, end_date = None, None
    if parameters.get("range_time"):
        range_time = parameters.get("range_time")
        if range_time.get("start_date"):
            start_date = range_time.get("start_date")
        elif range_time.get("data_start_date"):
            start_date = range_time.get("data_start_date")
        if range_time.get("end_date"):
            end_date = range_time.get("end_date")
        elif range_time.get("data_end_date"):
            end_date = range_time.get("data_end_date")
    if parameters.get("start_date"):
        start_date = parameters.get("start_date")
    if parameters.get("end_date"):
        end_date = parameters.get("end_date")

    if isstrptime:
        if start_date:
            start_date = convert_to_timestamp(start_date)
        if end_date:
            end_date = convert_to_timestamp(end_date)
    return start_date, end_date


def extract_date(self, text: str, date_type: str) -> Optional[str]:
    """从文本中提取日期

    参数:
        text: 文本
        date_type: 日期类型（开始/结束）

    返回:
        提取的日期，格式为YYYY-MM-DD或相对时间表达式，如果未找到则返回None
    """
    # 先尝试匹配标准日期格式
    pattern = rf"(?:{date_type})(?:日期|时间)[是为:：]?\s*(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})"
    match = re.search(pattern, text)
    if match:
        # 标准化日期格式
        date_str = match.group(1).replace("/", "-")
        # 确保月和日是两位数
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"

    # 匹配相对时间表达式
    relative_pattern = rf"(?:{date_type})(?:日期|时间)[是为:：]?\s*([^,，\s]+(?:天|周|月|年)前|当前日期|今天|昨天|上周|上个月|去年)"
    relative_match = re.search(relative_pattern, text)
    if relative_match:
        return relative_match.group(1)

    # 直接查找文本中的相对时间表达式，不依赖日期类型前缀
    if date_type == "开始":
        direct_pattern = r"(\d+个?(?:天|周|月|年)前|上周|上个月|去年)"
        direct_match = re.search(direct_pattern, text)
        if direct_match:
            return direct_match.group(1)
    elif date_type == "结束|截止":
        direct_pattern = r"(当前日期|今天|现在)"
        direct_match = re.search(direct_pattern, text)
        if direct_match:
            return direct_match.group(1)

    return None
