#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from data_export_tool import export_data_to_json, export_mcp_data_to_csv

# 示例数据（来自您的测试文件）
example_mcp_data = {
    "user_info": {
        "columns": ["user_id", "name", "age", "city", "registration_date"],
        "rows": [
            [1, "张三", 25, "北京", "2023-01-15"],
            [2, "李四", 30, "上海", "2023-02-20"],
            [3, "王五", 28, "广州", "2023-03-10"],
            [4, "赵六", 35, "深圳", "2023-04-05"],
            [5, "钱七", 22, "杭州", "2023-05-12"],
        ],
    },
    "user_behavior": {
        "columns": ["behavior_id", "user_id", "action", "timestamp", "page_url"],
        "rows": [
            [1, 1, "page_view", "2024-01-01 10:05:00", "/home"],
            [2, 1, "click", "2024-01-01 10:06:00", "/products"],
            [3, 2, "search", "2024-01-01 11:02:00", "/search?q=laptop"],
            [4, 3, "purchase", "2024-01-02 14:35:00", "/checkout"],
            [5, 2, "page_view", "2024-01-03 08:20:00", "/profile"],
        ],
    },
}


async def test_export():
    """测试数据导出功能"""
    task_id = "test_task_001"

    print("开始测试数据导出...")

    # 导出为CSV文件
    csv_files = export_mcp_data_to_csv(example_mcp_data, task_id)
    print(f"CSV文件导出完成: {csv_files}")

    # 导出为JSON文件
    json_file = export_data_to_json(example_mcp_data, task_id)
    print(f"JSON文件导出完成: {json_file}")

    print("数据导出测试完成！")


if __name__ == "__main__":
    asyncio.run(test_export())
