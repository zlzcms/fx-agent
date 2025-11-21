#!/usr/bin/env python3
"""
统计查询示例脚本，展示如何使用SQL生成器创建各种统计查询
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLGenerator


def main():
    """主函数，展示统计查询功能"""

    # 获取模板目录
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    print("SQL统计查询示例\n")

    # 初始化生成器
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # 示例1: 简单的COUNT查询
    print("示例1: 简单的COUNT查询")
    sql = generator.generate_count(
        table="users", column="id", where="status = 'active'"
    )
    print(sql)
    print()

    # 示例2: 带DISTINCT的COUNT查询
    print("示例2: 带DISTINCT的COUNT查询")
    sql = generator.generate_count(table="orders", column="customer_id", distinct=True)
    print(sql)
    print()

    # 示例3: 分组COUNT查询
    print("示例3: 分组COUNT查询")
    sql = generator.generate_count(
        table="orders", column="id", group_by=["customer_id", "status"]
    )
    print(sql)
    print()

    # 示例4: SUM查询
    print("示例4: SUM查询")
    sql = generator.generate_sum(
        table="order_items", column="price * quantity", where="order_id = 12345"
    )
    print(sql)
    print()

    # 示例5: 分组SUM查询
    print("示例5: 分组SUM查询")
    sql = generator.generate_sum(
        table="order_items", column="price * quantity", group_by=["order_id"]
    )
    print(sql)
    print()

    # 示例6: AVG查询
    print("示例6: AVG查询")
    sql = generator.generate_avg(
        table="products", column="price", where="category_id = 5"
    )
    print(sql)
    print()

    # 示例7: MIN/MAX查询
    print("示例7: MIN/MAX查询")
    sql = generator.generate_min_max(
        table="products", column="price", operation="both", group_by=["category_id"]
    )
    print(sql)
    print()

    # 示例8: 统计摘要查询
    print("示例8: 统计摘要查询")
    sql = generator.generate_stats_summary(
        table="products", column="price", where="category_id = 5"
    )
    print(sql)
    print()

    # 示例9: 复杂分组统计
    print("示例9: 复杂分组统计")
    sql = generator.generate_group_stats(
        table="order_items",
        group_columns=["product_id", "EXTRACT(YEAR FROM order_date) AS year"],
        stat_columns=[
            {"column": "quantity", "function": "SUM", "alias": "total_quantity"},
            {"column": "price * quantity", "function": "SUM", "alias": "total_revenue"},
            {"column": "id", "function": "COUNT", "alias": "order_count"},
        ],
        where="status = 'completed'",
        having="SUM(quantity) > 100",
        order_by=[{"column": "total_revenue", "direction": "DESC"}],
        limit=10,
    )
    print(sql)
    print()

    # 示例10: 数据透视表查询
    print("示例10: 数据透视表查询")
    sql = generator.generate_pivot_table(
        table="sales",
        row_columns=["product_id", "product_name"],
        column_values=["Q1", "Q2", "Q3", "Q4"],
        pivot_column="quarter",
        aggregate_column="amount",
        aggregate_function="SUM",
        where="year = 2023",
    )
    print(sql)
    print()

    # 示例11: 窗口函数查询
    print("示例11: 窗口函数查询")
    sql = generator.generate_window_function(
        table="sales",
        base_columns=["product_id", "product_name", "sale_date", "amount"],
        window_functions=[
            {
                "function": "SUM",
                "column": "amount",
                "alias": "running_total",
                "partition_by": "product_id",
                "order_by": "sale_date",
                "frame": "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW",
            },
            {
                "function": "AVG",
                "column": "amount",
                "alias": "moving_avg",
                "partition_by": "product_id",
                "order_by": "sale_date",
                "frame": "ROWS BETWEEN 2 PRECEDING AND CURRENT ROW",
            },
        ],
        order_by=[
            {"column": "product_id", "direction": "ASC"},
            {"column": "sale_date", "direction": "ASC"},
        ],
    )
    print(sql)
    print()

    # 示例12: 使用ROLLUP的分组统计
    print("示例12: 使用ROLLUP的分组统计")
    config = {
        "type": "statistics",
        "table": "sales",
        "columns": [
            "category",
            "product_id",
            {"expr": "SUM(amount)", "alias": "total_sales"},
        ],
        "group_by": ["category", "product_id"],
        "rollup": True,
    }
    sql = generator.generate_from_config(config)
    print(sql)
    print()

    # 示例13: 使用CUBE的分组统计 (PostgreSQL)
    print("示例13: 使用CUBE的分组统计 (PostgreSQL)")
    config = {
        "type": "statistics",
        "table": "sales",
        "columns": [
            "category",
            "region",
            "year",
            {"expr": "SUM(amount)", "alias": "total_sales"},
        ],
        "group_by": ["category", "region", "year"],
        "cube": True,
    }
    sql = generator.generate_from_config(config)
    print(sql)
    print()

    # 示例14: 百分比统计
    print("示例14: 百分比统计")
    config = {
        "type": "statistics",
        "table": "votes",
        "columns": [
            "candidate",
            {"expr": "COUNT(*)", "alias": "vote_count"},
            {
                "expr": "ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)",
                "alias": "percentage",
            },
        ],
        "group_by": ["candidate"],
        "order_by": [{"column": "vote_count", "direction": "DESC"}],
    }
    sql = generator.generate_from_config(config)
    print(sql)
    print()

    print("所有示例已成功完成！")


if __name__ == "__main__":
    main()
