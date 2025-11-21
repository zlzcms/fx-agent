#!/usr/bin/env python3
"""
结合配置文件和动态条件构建的示例脚本
"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLBuilder, SQLGenerator


def main():
    """主函数，展示结合配置和动态条件构建的功能"""

    # 获取模板目录
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    print("SQL配置与动态条件结合示例\n")

    # 示例1: 基本配置转换为SQLBuilder
    print("示例1: 基本配置转换为SQLBuilder")

    # 创建一个基本的查询配置
    config = {
        "type": "select",
        "table": "products",
        "table_alias": "p",
        "columns": ["p.id", "p.name", "p.price", "c.name as category_name"],
        "joins": [
            {
                "type": "INNER",
                "table": "categories",
                "alias": "c",
                "condition": "p.category_id = c.id",
            }
        ],
        "order_by": [{"column": "p.name", "direction": "ASC"}],
    }

    # 初始化生成器
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # 从配置创建SQLBuilder
    builder = generator.create_builder_from_config(config)

    # 动态添加条件
    builder.add_condition_greater_than("p.price", 100)
    builder.add_condition_equals("p.active", True)

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例2: 复杂查询配置与条件组结合
    print("示例2: 复杂查询配置与条件组结合")

    # 创建一个复杂的查询配置
    config = {
        "type": "select",
        "table": "orders",
        "table_alias": "o",
        "columns": [
            "o.id",
            "o.order_date",
            "c.name as customer_name",
            {"expr": "SUM(oi.quantity * oi.price)", "alias": "total_amount"},
        ],
        "joins": [
            {
                "type": "INNER",
                "table": "customers",
                "alias": "c",
                "condition": "o.customer_id = c.id",
            },
            {
                "type": "LEFT",
                "table": "order_items",
                "alias": "oi",
                "condition": "o.id = oi.order_id",
            },
        ],
        "group_by": ["o.id", "o.order_date", "c.name"],
        "order_by": [{"column": "o.order_date", "direction": "DESC"}],
    }

    # 从配置创建SQLBuilder
    builder = generator.create_builder_from_config(config)

    # 创建日期条件组
    builder.create_condition_group("date_filter")
    builder.use_condition_group("date_filter")
    builder.add_condition_greater_equals("o.order_date", "2023-01-01")
    builder.add_condition_less_than("o.order_date", "2023-07-01")

    # 创建金额条件组
    builder.create_condition_group("amount_filter")
    builder.use_condition_group("amount_filter")
    builder.add_condition_greater_than("total_amount", 1000)

    # 应用条件组
    builder.apply_condition_group("date_filter")
    builder.apply_condition_group("amount_filter")

    # 添加HAVING条件
    builder.having("COUNT(oi.id) > 3")

    # 添加LIMIT
    builder.limit(20)

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例3: 跨数据库查询配置与动态条件
    print("示例3: 跨数据库查询配置与动态条件")

    # 创建跨数据库查询配置
    config = {
        "type": "select",
        "table": "transactions",
        "table_alias": "t",
        "database": "finance",  # 指定数据库/schema
        "columns": ["t.id", "t.transaction_date", "t.amount", "a.name AS account_name"],
        "joins": [
            {
                "type": "INNER",
                "table": "accounts",
                "database": "banking",  # 跨数据库
                "alias": "a",
                "condition": "t.account_id = a.id",
            }
        ],
    }

    # 从配置创建SQLBuilder
    builder = generator.create_builder_from_config(config)

    # 模拟用户输入的过滤条件
    filters = {
        "min_amount": 1000,
        "max_amount": 10000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "account_types": [1, 2, 3],
    }

    # 动态添加条件
    if "min_amount" in filters:
        builder.add_condition_greater_equals("t.amount", filters["min_amount"])

    if "max_amount" in filters:
        builder.add_condition_less_equals("t.amount", filters["max_amount"])

    if "start_date" in filters and "end_date" in filters:
        builder.add_condition_between(
            "t.transaction_date", filters["start_date"], filters["end_date"]
        )

    if "account_types" in filters and filters["account_types"]:
        builder.add_condition_in("a.type_id", filters["account_types"])

    # 添加排序和分页
    builder.order_by("t.transaction_date", "DESC")
    builder.limit(50)

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例4: 更新语句配置与动态条件
    print("示例4: 更新语句配置与动态条件")

    # 创建更新语句配置
    config = {
        "type": "update",
        "table": "products",
        "database": "inventory",
        "set_values": {"status": "discontinued"},
    }

    # 从配置创建SQLBuilder
    builder = generator.create_builder_from_config(config)

    # 添加SET子句
    builder.set("updated_at", "NOW()")

    # 添加条件
    builder.add_condition_equals("category_id", 5)
    builder.add_condition_less_equals("stock", 0)
    builder.add_condition_less_than("last_ordered", "2023-01-01")

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例5: 统计查询配置与动态条件
    print("示例5: 统计查询配置与动态条件")

    # 创建统计查询配置
    config = {
        "type": "statistics",
        "table": "sales",
        "table_alias": "s",
        "columns": [
            "s.product_id",
            "p.name as product_name",
            {"expr": "SUM(s.quantity)", "alias": "total_quantity"},
            {"expr": "SUM(s.quantity * s.price)", "alias": "total_revenue"},
        ],
        "joins": [
            {
                "type": "INNER",
                "table": "products",
                "alias": "p",
                "condition": "s.product_id = p.id",
            }
        ],
        "group_by": ["s.product_id", "p.name"],
    }

    # 从配置创建SQLBuilder
    builder = generator.create_builder_from_config(config)

    # 添加时间范围条件
    builder.add_condition_between("s.sale_date", "2023-01-01", "2023-12-31")

    # 添加产品类别条件
    builder.add_condition_in("p.category_id", [1, 2, 3])

    # 添加HAVING条件
    builder.having("SUM(s.quantity) > 100")

    # 添加排序和分页
    builder.order_by("total_revenue", "DESC")
    builder.limit(10)

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例6: 窗口函数
    print("示例6: 窗口函数")

    # 直接使用SQLBuilder创建窗口函数查询
    builder = SQLBuilder(dialect="postgresql")
    builder.select("employee_id", "employee_name", "department", "salary")
    builder.window(
        "ROW_NUMBER",
        "",
        partition_by=["department"],
        order_by=[{"column": "salary", "direction": "DESC"}],
        alias="salary_rank",
    )
    builder.window(
        "AVG", "salary", partition_by=["department"], alias="dept_avg_salary"
    )
    builder.from_table("employees")
    builder.where("salary > 50000")
    builder.order_by("department")
    builder.order_by("salary_rank")

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例7: JSON操作
    print("示例7: JSON操作")

    builder = SQLBuilder(dialect="postgresql")
    builder.select("id", "name")
    builder.json_extract("profile_data", "address.city", "city")
    builder.json_extract("profile_data", "contact.email", "email")
    builder.from_table("users")
    builder.json_contains("profile_data", {"status": "active"})
    builder.where("created_at > '2023-01-01'")

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例8: 子查询和CTE
    print("示例8: 子查询和CTE")

    # 创建子查询
    subquery_builder = SQLBuilder(dialect="postgresql")
    subquery_builder.select("department", "AVG(salary) as avg_salary")
    subquery_builder.from_table("employees")
    subquery_builder.group_by("department")

    # 创建主查询
    main_builder = SQLBuilder(dialect="postgresql")
    main_builder.select("e.employee_id", "e.employee_name", "e.salary", "d.avg_salary")
    main_builder.from_table("employees", "e")
    main_builder.subquery(subquery_builder, "d")
    main_builder.where("e.department = d.department")
    main_builder.where("e.salary > d.avg_salary")
    main_builder.order_by("e.department")
    main_builder.order_by("e.salary", "DESC")

    # 构建SQL
    sql, params = main_builder.build()

    print("子查询示例:")
    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # CTE示例
    builder = SQLBuilder(dialect="postgresql")
    builder.with_cte(
        "dept_avg",
        "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
    )
    builder.select("e.employee_id", "e.employee_name", "e.salary", "d.avg_salary")
    builder.from_table("employees", "e")
    builder.join("dept_avg", "e.department = d.department", "INNER", "d")
    builder.where("e.salary > d.avg_salary")

    # 构建SQL
    sql, params = builder.build()

    print("CTE示例:")
    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 递归CTE示例
    builder = SQLBuilder(dialect="postgresql")
    builder.with_recursive(
        "org_hierarchy",
        """
                         SELECT id, name, manager_id, 1 as level
                         FROM employees
                         WHERE manager_id IS NULL
                         UNION ALL
                         SELECT e.id, e.name, e.manager_id, oh.level + 1
                         FROM employees e
                         JOIN org_hierarchy oh ON e.manager_id = oh.id
                         """,
    )
    builder.select("id", "name", "level")
    builder.from_table("org_hierarchy")
    builder.order_by("level")
    builder.order_by("name")

    # 构建SQL
    sql, params = builder.build()

    print("递归CTE示例:")
    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例9: 全文搜索
    print("示例9: 全文搜索")

    builder = SQLBuilder(dialect="postgresql")
    builder.select("id", "title", "content", "created_at")
    builder.from_table("articles")
    builder.full_text_search(["title", "content"], "postgresql database")
    builder.order_by("created_at", "DESC")
    builder.limit(10)

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例10: 高级分析函数
    print("示例10: 高级分析函数")

    builder = SQLBuilder(dialect="postgresql")
    builder.select("date", "stock_id", "price")
    builder.lag(
        "price",
        1,
        0,
        partition_by=["stock_id"],
        order_by=[{"column": "date", "direction": "ASC"}],
        alias="prev_price",
    )
    builder.lead(
        "price",
        1,
        0,
        partition_by=["stock_id"],
        order_by=[{"column": "date", "direction": "ASC"}],
        alias="next_price",
    )
    builder.select(
        {"expr": "(price - prev_price) / prev_price * 100", "alias": "daily_change_pct"}
    )
    builder.from_table("stock_prices")
    builder.where("date >= '2023-01-01'")
    builder.order_by("stock_id")
    builder.order_by("date")

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例11: UPSERT操作
    print("示例11: UPSERT操作")

    builder = SQLBuilder(dialect="postgresql")
    builder.insert_into("products", ["id", "name", "price", "stock"])
    builder.values([1, "Product A", 19.99, 100])
    builder.upsert(["id"], ["name", "price", "stock"])

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 新增示例12: 高级分组
    print("示例12: 高级分组")

    builder = SQLBuilder(dialect="postgresql")
    builder.select("region", "product", "year", "SUM(sales) as total_sales")
    builder.from_table("sales")
    builder.cube("region", "product", "year")

    # 构建SQL
    sql, params = builder.build()

    print("CUBE分组示例:")
    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    builder = SQLBuilder(dialect="postgresql")
    builder.select("region", "product", "year", "SUM(sales) as total_sales")
    builder.from_table("sales")
    builder.grouping_sets(
        [
            ["region", "product", "year"],
            ["region", "product"],
            ["region", "year"],
            ["product", "year"],
            ["region"],
            ["product"],
            ["year"],
            [],
        ]
    )

    # 构建SQL
    sql, params = builder.build()

    print("GROUPING SETS示例:")
    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    print("所有示例已成功完成！")


if __name__ == "__main__":
    main()
