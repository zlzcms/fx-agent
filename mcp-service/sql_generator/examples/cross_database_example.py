#!/usr/bin/env python3
"""
跨数据库查询示例脚本，展示如何使用SQL生成器创建跨数据库查询
"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLBuilder, SQLGenerator


def main():
    """主函数，展示跨数据库查询功能"""

    print("SQL跨数据库查询示例\n")

    # 示例1: PostgreSQL跨Schema查询
    print("示例1: PostgreSQL跨Schema查询")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("u.id", "u.username", "u.email", "p.full_name", "p.phone")
        .from_table("users", "u", "public")  # public schema
        .join(
            "profiles", "u.id = p.user_id", "LEFT", "p", "customer"
        )  # customer schema
        .where_equals("u.status", "active")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例2: MySQL跨数据库查询
    print("示例2: MySQL跨数据库查询")
    builder = SQLBuilder(dialect="mysql")

    sql, params = (
        builder.select("o.*", "c.name AS customer_name", "p.name AS product_name")
        .from_table("orders", "o", "sales")  # sales database
        .join("customers", "o.customer_id = c.id", "INNER", "c", "crm")  # crm database
        .join(
            "products", "o.product_id = p.id", "INNER", "p", "inventory"
        )  # inventory database
        .where_equals("o.status", "completed")
        .order_by("o.order_date", "DESC")
        .limit(10)
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例3: 跨数据库INSERT查询
    print("示例3: 跨数据库INSERT查询")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.insert_into(
            "order_history", ["order_id", "status", "updated_at"], "archive"
        )
        .values([1001, "completed", "2023-06-15 14:30:00"])
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例4: 跨数据库UPDATE查询
    print("示例4: 跨数据库UPDATE查询")
    builder = SQLBuilder(dialect="mysql")

    sql, params = (
        builder.update("products", "inventory")
        .set("stock", 0)
        .set("status", "discontinued")
        .where_equals("category_id", 5)
        .add_condition_less_equals("last_ordered", "2022-12-31")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例5: 跨数据库DELETE查询
    print("示例5: 跨数据库DELETE查询")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.delete_from("user_sessions", "security")
        .add_condition_less_than("last_activity", "2023-01-01")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例6: 复杂跨数据库查询
    print("示例6: 复杂跨数据库查询")
    builder = SQLBuilder(dialect="postgresql")

    # 创建条件组
    builder.create_condition_group("date_filter")
    builder.use_condition_group("date_filter")
    builder.add_condition_greater_equals("o.order_date", "2023-01-01")
    builder.add_condition_less_than("o.order_date", "2023-07-01")

    # 创建金额条件组
    builder.create_condition_group("amount_filter")
    builder.use_condition_group("amount_filter")
    builder.add_condition_greater_than("o.total_amount", 1000)

    sql, params = (
        builder.select(
            "o.id AS order_id",
            "o.order_date",
            "c.name AS customer_name",
            "c.email AS customer_email",
            "SUM(oi.quantity * oi.price) AS total",
            "p.name AS payment_method",
        )
        .from_table("orders", "o", "sales")
        .join("customers", "o.customer_id = c.id", "INNER", "c", "crm")
        .join("order_items", "o.id = oi.order_id", "INNER", "oi", "sales")
        .join("payments", "o.payment_id = p.id", "LEFT", "p", "finance")
        .apply_condition_group("date_filter")
        .apply_condition_group("amount_filter")
        .group_by("o.id", "o.order_date", "c.name", "c.email", "p.name")
        .having("COUNT(oi.id) > 3")
        .order_by("o.order_date", "DESC")
        .limit(20)
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例7: 使用SQLGenerator进行跨数据库查询
    print("示例7: 使用SQLGenerator进行跨数据库查询")

    # 获取模板目录
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # 定义查询配置
    config = {
        "type": "select",
        "table": "transactions",
        "table_alias": "t",
        "database": "finance",  # 指定数据库/schema
        "columns": [
            "t.id",
            "t.transaction_date",
            "t.amount",
            "a.name AS account_name",
            "c.name AS category_name",
        ],
        "joins": [
            {
                "type": "INNER",
                "table": "accounts",
                "database": "banking",  # 跨数据库
                "alias": "a",
                "condition": "t.account_id = a.id",
            },
            {
                "type": "LEFT",
                "table": "categories",
                "database": "finance",  # 同一数据库
                "alias": "c",
                "condition": "t.category_id = c.id",
            },
        ],
        "where": "t.amount > 1000 AND t.transaction_date >= '2023-01-01'",
        "order_by": [{"column": "t.transaction_date", "direction": "DESC"}],
        "limit": 50,
    }

    # 生成SQL
    sql = generator.generate_from_config(config)

    print(sql)
    print()

    print("所有示例已成功完成！")


if __name__ == "__main__":
    main()
