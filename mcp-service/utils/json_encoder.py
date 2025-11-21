#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的JSON编码器，只处理Decimal和datetime类型
"""

import json
from datetime import date, datetime
from decimal import Decimal


class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理特殊类型"""

    def default(self, obj):
        """处理无法直接序列化的对象"""
        if isinstance(obj, Decimal):
            # Decimal转换为字符串，保持完整精度
            return str(obj)
        elif isinstance(obj, (datetime, date)):
            # datetime保持原始格式，转换为字符串
            return str(obj)
        return super().default(obj)


def safe_json_dumps(data, **kwargs):
    """
    安全的JSON序列化函数

    参数:
        data: 需要序列化的数据
        **kwargs: 传递给json.dumps的其他参数

    返回:
        JSON字符串
    """
    # 设置默认参数
    default_kwargs = {"ensure_ascii": False, "cls": CustomJSONEncoder}
    default_kwargs.update(kwargs)

    return json.dumps(data, **default_kwargs)
