#!/usr/bin/env python3
"""
条件构建示例脚本，展示如何使用SQL生成器动态构建WHERE条件
"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLBuilder
from sql_generator.model.builder import ConditionModel, ConditionOperator, Operator


def main():
    """主函数，展示条件构建功能"""

    print("SQL条件构建示例\n")

    # 示例1: 基本条件添加
    print("示例1: 基本条件添加")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("*")
        .from_table("users")
        .add_condition("status = 'active'")
        .add_condition("age > 18")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例2: 使用参数化条件
    print("示例2: 使用参数化条件")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("*")
        .from_table("products")
        .add_condition(
            ConditionModel(column="category_id", value=5, operator=Operator.EQUALS)
        )
        .add_condition(
            ConditionModel(column="price", value=100, operator=Operator.GREATER_THAN)
        )
        .add_condition(
            ConditionModel(column="stock", value=50, operator=Operator.LESS_THAN)
        )
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例3: 条件组
    print("示例3: 条件组")
    builder = SQLBuilder(dialect="postgresql")

    # 创建基本条件
    builder.add_condition(
        ConditionModel(column="status", value="active", operator=Operator.EQUALS)
    )

    # 创建价格条件组
    builder.create_condition_group("price_conditions", ConditionOperator.OR)
    builder.add_condition(
        ConditionModel(column="price", value=100, operator=Operator.GREATER_THAN)
    )
    builder.add_condition(
        ConditionModel(column="price", value=500, operator=Operator.LESS_THAN)
    )

    # 创建类别条件组

    builder.add_condition(
        ConditionModel(column="category_id", value=[1, 2, 3], operator=Operator.IN),
        group_name="category_conditions",
    )
    builder.add_condition(
        ConditionModel(column="featured", value=True, operator=Operator.EQUALS)
    )

    # 构建查询
    sql, params = (
        builder.select("id", "name", "price", "category_id")
        .from_table("products")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例4: 动态条件构建
    print("示例4: 动态条件构建")

    # 模拟用户输入的过滤条件
    filters = {
        "min_price": 50,
        "max_price": 200,
        "categories": [1, 3, 5],
        "in_stock": True,
        "search_term": "laptop",
    }

    builder = SQLBuilder(dialect="postgresql")
    builder.select("*").from_table("products")

    # 动态添加条件
    if "min_price" in filters:
        builder.add_condition(
            ConditionModel(
                column="price",
                value=filters["min_price"],
                operator=Operator.GREATER_EQUALS,
            )
        )

    if "max_price" in filters:
        builder.add_condition(
            ConditionModel(
                column="price",
                value=filters["max_price"],
                operator=Operator.LESS_EQUALS,
            )
        )

    if "categories" in filters and filters["categories"]:
        builder.add_condition(
            ConditionModel(
                column="category_id", value=filters["categories"], operator=Operator.IN
            )
        )

    if "in_stock" in filters and filters["in_stock"]:
        builder.add_condition(
            ConditionModel(column="stock", value=0, operator=Operator.GREATER_THAN)
        )

    if "search_term" in filters and filters["search_term"]:
        builder.add_condition(
            ConditionModel(
                column="name",
                value=f"%{filters['search_term']}%",
                operator=Operator.LIKE,
            )
        )
        builder.add_condition(
            ConditionModel(
                column="description",
                value=f"%{filters['search_term']}%",
                operator=Operator.LIKE,
            ),
            operator=ConditionOperator.OR,
        )

    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例5: 复杂条件组合
    print("示例5: 复杂条件组合")
    builder = SQLBuilder(dialect="postgresql")

    # 主条件
    builder.add_condition(
        ConditionModel(column="is_deleted", value=False, operator=Operator.EQUALS)
    )

    # 创建日期条件组
    builder.create_condition_group("date_filters")
    builder.add_condition(
        ConditionModel(
            column="created_at", value="2023-01-01", operator=Operator.GREATER_EQUALS
        )
    )
    builder.add_condition(
        ConditionModel(
            column="created_at", value="2024-01-01", operator=Operator.LESS_THAN
        )
    )

    # 创建价格范围条件组
    builder.create_condition_group("price_range", ConditionOperator.OR)
    builder.add_condition(
        ConditionModel(column="price", value=[100, 500], operator=Operator.BETWEEN)
    )

    # 创建类别条件组
    builder.create_condition_group("category_filter")
    builder.add_condition(
        ConditionModel(column="category_id", value=[1, 2, 3, 4], operator=Operator.IN)
    )

    # 创建搜索条件组 (使用OR连接)
    builder.create_condition_group("search_filter")
    builder.add_condition(
        ConditionModel(column="name", value="%gamding%", operator=Operator.LIKE)
    )
    builder.add_condition(
        ConditionModel(column="description", value="%gamding%", operator=Operator.LIKE),
        operator=ConditionOperator.OR,
    )
    builder.add_condition(
        ConditionModel(column="tags", value="%gamidngd%", operator=Operator.LIKE),
        operator=ConditionOperator.OR,
    )

    # 构建查询
    sql, params = (
        builder.select("id", "name", "price", "category_id", "created_at")
        .from_table("products")
        .order_by("created_at", "DESC")
        .limit(20)
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例6: 使用原始条件和自定义参数
    print("示例6: 使用原始条件和自定义参数")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("*")
        .from_table("users")
        .add_condition_raw(
            "last_login BETWEEN :start_date AND :end_date",
            {"start_date": "2023-01-01", "end_date": "2023-12-31"},
        )
        .add_condition_raw(
            "email LIKE :email_pattern", {"email_pattern": "%@example.com"}
        )
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例7: 条件组在UPDATE语句中的应用
    print("示例7: 条件组在UPDATE语句中的应用")
    builder = SQLBuilder(dialect="postgresql")

    # 创建条件组
    builder.create_condition_group("update_filter")
    builder.add_condition(
        ConditionModel(column="status", value="pending", operator=Operator.EQUALS)
    )
    builder.add_condition(
        ConditionModel(
            column="last_updated", value="2023-06-01", operator=Operator.LESS_THAN
        )
    )

    sql, params = (
        builder.update("orders")
        .set("status", "expired")
        .set("updated_at", "2023-06-30")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例8: 条件组在DELETE语句中的应用
    print("示例8: 条件组在DELETE语句中的应用")
    builder = SQLBuilder(dialect="postgresql")

    # 创建条件组
    builder.create_condition_group("delete_filter")
    builder.add_condition(
        ConditionModel(column="status", value="temporary", operator=Operator.EQUALS)
    )
    builder.add_condition(
        ConditionModel(
            column="created_at", value="2023-01-01", operator=Operator.LESS_THAN
        )
    )

    sql, params = builder.delete_from("sessions").build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例9: 窗口函数
    print("示例9: 窗口函数")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("employee_id", "department", "salary")
        .window(
            function="ROW_NUMBER",
            column="",
            partition_by=["department"],
            order_by=[{"column": "salary", "direction": "DESC"}],
            alias="salary_rank",
        )
        .window(
            function="AVG",
            column="salary",
            partition_by=["department"],
            alias="dept_avg_salary",
        )
        .from_table("employees")
        .where("salary > 50000")
        .order_by("department")
        .order_by("salary_rank")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例10: JSON操作
    print("示例10: JSON操作")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("id", "name")
        .json_extract("data", "address.city", "city")
        .json_extract("data", "address.country", "country")
        .from_table("customers")
        .json_contains("data", {"status": "active"})
        .where("id > 100")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例11: 子查询
    print("示例11: 子查询")

    # 创建子查询
    subquery_builder = SQLBuilder(dialect="postgresql")
    subquery_builder.select("department", "AVG(salary) as avg_salary").from_table(
        "employees"
    ).group_by("department")

    # 主查询
    main_builder = SQLBuilder(dialect="postgresql")
    sql, params = (
        main_builder.select("e.employee_id", "e.name", "e.salary", "d.avg_salary")
        .from_table("employees", "e")
        .subquery(subquery_builder, "d")
        .where("e.department = d.department")
        .where("e.salary > d.avg_salary")
        .order_by("e.department")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例12: 全文搜索
    print("示例12: 全文搜索")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("id", "title", "content")
        .from_table("articles")
        .full_text_search(["title", "content"], "postgresql database")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例13: 分析函数
    print("示例13: 分析函数")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("date", "stock_id", "price")
        .lag(
            column="price",
            offset=1,
            default_value=0,
            partition_by=["stock_id"],
            order_by=[{"column": "date", "direction": "ASC"}],
            alias="prev_day_price",
        )
        .lead(
            column="price",
            offset=1,
            default_value=0,
            partition_by=["stock_id"],
            order_by=[{"column": "date", "direction": "ASC"}],
            alias="next_day_price",
        )
        .from_table("stock_prices")
        .order_by("stock_id")
        .order_by("date")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例14: 高级分组
    print("示例14: 高级分组")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("region", "product", "year", "SUM(sales) as total_sales")
        .from_table("sales")
        .cube("region", "product", "year")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例15: UPSERT操作
    print("示例15: UPSERT操作")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.insert_into("products", ["id", "name", "price", "stock"])
        .values([1, "Product A", 19.99, 100])
        .upsert(["id"], ["name", "price", "stock"])
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例16: 基本统计查询 - COUNT
    print("示例16: 基本统计查询 - COUNT")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("COUNT(*) AS total_users")
        .from_table("users")
        .where("status = 'active'")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例17: 基本统计查询 - AVG, SUM, MIN, MAX
    print("示例17: 基本统计查询 - AVG, SUM, MIN, MAX")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select(
            "AVG(price) AS avg_price",
            "SUM(price) AS total_price",
            "MIN(price) AS min_price",
            "MAX(price) AS max_price",
            "COUNT(*) AS product_count",
        )
        .from_table("products")
        .where("category_id = 5")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例18: 分组统计
    print("示例18: 分组统计")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select(
            "category_id",
            "COUNT(*) AS product_count",
            "AVG(price) AS avg_price",
            "SUM(stock) AS total_stock",
        )
        .from_table("products")
        .where("price > 0")
        .group_by("category_id")
        .having("COUNT(*) > 5")
        .order_by("category_id")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例19: 高级统计 - 滚动计算
    print("示例19: 高级统计 - 滚动计算")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("date", "sales")
        .window(
            function="AVG",
            column="sales",
            order_by=[{"column": "date", "direction": "ASC"}],
            frame_clause="ROWS BETWEEN 6 PRECEDING AND CURRENT ROW",
            alias="weekly_avg",
        )
        .window(
            function="SUM",
            column="sales",
            order_by=[{"column": "date", "direction": "ASC"}],
            frame_clause="ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW",
            alias="cumulative_sum",
        )
        .from_table("daily_sales")
        .order_by("date")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例20: 统计加条件过滤
    print("示例20: 统计加条件过滤")
    builder = SQLBuilder(dialect="postgresql")

    # 创建日期条件组
    builder.create_condition_group("date_range")
    builder.add_condition(
        ConditionModel(
            column="order_date", value="2023-01-01", operator=Operator.GREATER_EQUALS
        )
    )
    builder.add_condition(
        ConditionModel(
            column="order_date", value="2023-12-31", operator=Operator.LESS_EQUALS
        )
    )

    # 创建状态条件组
    builder.create_condition_group("status_filter", ConditionOperator.OR)
    builder.add_condition(
        ConditionModel(column="status", value="completed", operator=Operator.EQUALS)
    )

    sql, params = (
        builder.select(
            "customer_id",
            "COUNT(*) AS order_count",
            "SUM(total_amount) AS total_spent",
            "AVG(total_amount) AS avg_order_value",
        )
        .from_table("orders")
        .group_by("customer_id")
        .having("COUNT(*) >= 3")  # 只选择至少有3个订单的客户
        .order_by("total_spent", "DESC")
        .limit(10)  # 获取前10名消费最高的客户
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例21: 高级分组 - ROLLUP
    print("示例21: 高级分组 - ROLLUP")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("region", "product", "SUM(sales) AS total_sales")
        .from_table("sales")
        .rollup("region", "product")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print("ROLLUP会生成层次结构的小计和总计，例如按region和product分组，然后是按region分组，最后是总计")
    print()

    # 示例22: 高级分组 - CUBE
    print("示例22: 高级分组 - CUBE")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("region", "product", "year", "SUM(sales) AS total_sales")
        .from_table("sales")
        .cube("region", "product", "year")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print("CUBE会生成所有可能的分组组合的小计和总计")
    print()

    # 示例23: 高级分组 - GROUPING SETS
    print("示例23: 高级分组 - GROUPING SETS")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("region", "product", "year", "SUM(sales) AS total_sales")
        .from_table("sales")
        .grouping_sets(
            [
                ["region", "product", "year"],  # 按region, product, year分组
                ["region", "product"],  # 按region, product分组
                ["region", "year"],  # 按region, year分组
                ["product", "year"],  # 按product, year分组
                ["region"],  # 按region分组
                ["product"],  # 按product分组
                ["year"],  # 按year分组
                [],  # 总计
            ]
        )
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print("GROUPING SETS允许您指定确切的分组组合")
    print()

    # 示例24: 统计摘要
    print("示例24: 统计摘要")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select(
            "COUNT(*) AS count",
            "AVG(price) AS avg",
            "SUM(price) AS sum",
            "MIN(price) AS min",
            "MAX(price) AS max",
            "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median",
            "STDDEV(price) AS stddev",
        )
        .from_table("products")
        .where("category_id = 5")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例25: 交叉表/透视表查询
    print("示例25: 交叉表/透视表查询")
    builder = SQLBuilder(dialect="postgresql")

    # 在PostgreSQL中使用CASE WHEN模拟透视表
    sql, params = (
        builder.select(
            "product_category",
            "SUM(CASE WHEN region = 'North' THEN sales ELSE 0 END) AS north_sales",
            "SUM(CASE WHEN region = 'South' THEN sales ELSE 0 END) AS south_sales",
            "SUM(CASE WHEN region = 'East' THEN sales ELSE 0 END) AS east_sales",
            "SUM(CASE WHEN region = 'West' THEN sales ELSE 0 END) AS west_sales",
            "SUM(sales) AS total_sales",
        )
        .from_table("sales")
        .group_by("product_category")
        .order_by("product_category")
        .build()
    )

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print("这个查询模拟了一个透视表，行是product_category，列是不同的region")
    print()

    # 示例26: 通过配置文件创建SQL - 基本SELECT
    print("示例26: 通过配置文件创建SQL - 基本SELECT")

    # 创建配置字典
    select_config = {
        "type": "select",
        "columns": ["id", "name", "email", "created_at"],
        "table": "users",
        "alias": "u",
        "where": "status = 'active'",
        "order_by": [{"column": "created_at", "direction": "DESC"}],
        "limit": 10,
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(select_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例27: 通过配置文件创建SQL - 复杂查询
    print("示例27: 通过配置文件创建SQL - 复杂查询")

    # 创建配置字典
    complex_config = {
        "type": "select",
        "columns": ["p.id", "p.name", "p.price", "c.name AS category_name"],
        "table": "products",
        "alias": "p",
        "joins": [
            {
                "table": "categories",
                "alias": "c",
                "condition": "p.category_id = c.id",
                "type": "LEFT",
            }
        ],
        "where": "p.price > 100",
        "group_by": ["p.id", "p.name", "p.price", "c.name"],
        "having": "COUNT(*) > 0",
        "order_by": [{"column": "p.price", "direction": "DESC"}],
        "limit": 20,
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(complex_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例28: 通过配置文件创建SQL - 带窗口函数
    print("示例28: 通过配置文件创建SQL - 带窗口函数")

    # 创建配置字典
    window_config = {
        "type": "select",
        "columns": ["employee_id", "department", "salary"],
        "table": "employees",
        "window_functions": [
            {
                "function": "ROW_NUMBER",
                "column": "",
                "partition_by": ["department"],
                "order_by": [{"column": "salary", "direction": "DESC"}],
                "alias": "salary_rank",
            },
            {
                "function": "AVG",
                "column": "salary",
                "partition_by": ["department"],
                "alias": "dept_avg_salary",
            },
        ],
        "where": "salary > 50000",
        "order_by": [
            {"column": "department", "direction": "ASC"},
            {"column": "salary_rank", "direction": "ASC"},
        ],
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(window_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例29: 通过配置文件创建SQL - 统计查询
    print("示例29: 通过配置文件创建SQL - 统计查询")

    # 创建配置字典
    stats_config = {
        "type": "select",
        "columns": [
            "category_id",
            "COUNT(*) AS product_count",
            "AVG(price) AS avg_price",
            "SUM(stock) AS total_stock",
            "MIN(price) AS min_price",
            "MAX(price) AS max_price",
        ],
        "table": "products",
        "where": "price > 0 AND is_active = true",
        "group_by": ["category_id"],
        "having": "COUNT(*) > 5",
        "order_by": [{"column": "total_stock", "direction": "DESC"}],
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(stats_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例30: 通过配置文件创建SQL - 子查询
    print("示例30: 通过配置文件创建SQL - 子查询")

    # 创建子查询配置
    subquery_config = {
        "type": "select",
        "columns": ["department", "AVG(salary) as avg_salary"],
        "table": "employees",
        "group_by": ["department"],
    }

    # 创建子查询构建器
    sub_builder = SQLBuilder(dialect="postgresql")
    sub_builder.build_from_config(subquery_config)
    sub_sql, sub_params = sub_builder.build()

    # 创建主查询配置，使用实际的子查询SQL
    main_query_config = {
        "type": "select",
        "columns": ["e.employee_id", "e.name", "e.salary", "d.avg_salary"],
        "table": "employees",
        "alias": "e",
        "subqueries": {"d": {"sql": sub_sql}},
        "where": "e.department = d.department AND e.salary > d.avg_salary",
        "order_by": [{"column": "e.department", "direction": "ASC"}],
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(main_query_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例31: 通过配置文件创建SQL - 高级分组
    print("示例31: 通过配置文件创建SQL - 高级分组")

    # 创建配置字典
    grouping_config = {
        "type": "select",
        "columns": ["region", "product", "year", "SUM(sales) AS total_sales"],
        "table": "sales",
        "cube": ["region", "product", "year"],  # 也可以使用 "rollup" 或 "grouping_sets"
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(grouping_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例32: 通过配置文件创建SQL - INSERT
    print("示例32: 通过配置文件创建SQL - INSERT")

    # 创建配置字典
    insert_config = {
        "type": "insert",
        "table": "products",
        "columns": ["name", "price", "category_id", "stock"],
        "values": [["New Product", 29.99, 3, 100]],
        "returning": ["id", "created_at"],
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(insert_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例33: 通过配置文件创建SQL - UPSERT
    print("示例33: 通过配置文件创建SQL - UPSERT")

    # 创建配置字典
    upsert_config = {
        "type": "insert",
        "table": "products",
        "columns": ["id", "name", "price", "stock"],
        "values": [[1, "Updated Product", 39.99, 200]],
        "upsert": {
            "conflict_columns": ["id"],
            "update_columns": ["name", "price", "stock"],
        },
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(upsert_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例34: 通过配置文件创建SQL - UPDATE
    print("示例34: 通过配置文件创建SQL - UPDATE")

    # 创建配置字典
    update_config = {
        "type": "update",
        "table": "products",
        "sets": [
            {"column": "price", "value": 49.99},
            {"column": "stock", "value": 50},
            {"column": "updated_at", "value": "2023-06-30"},
        ],
        "where": "id = 1 AND category_id = 3",
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(update_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例35: 通过配置文件创建SQL - DELETE
    print("示例35: 通过配置文件创建SQL - DELETE")

    # 创建配置字典
    delete_config = {
        "type": "delete",
        "table": "products",
        "where": "created_at < '2022-01-01' AND stock = 0",  # 确保日期有引号
    }

    # 使用配置创建SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(delete_config)
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例36: 配置文件和条件组结合使用
    print("示例36: 配置文件和条件组结合使用")

    # 创建基础配置
    base_config = {
        "type": "select",
        "columns": ["p.id", "p.name", "p.price", "p.stock", "c.name AS category_name"],
        "table": "products",
        "alias": "p",
        "joins": [
            {
                "table": "categories",
                "alias": "c",
                "condition": "p.category_id = c.id",
                "type": "INNER",
            }
        ],
        "order_by": [{"column": "p.name", "direction": "ASC"}],
    }

    # 创建构建器并应用基础配置
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(base_config)

    # 模拟用户输入的过滤条件
    filters = {
        "min_price": 50,
        "max_price": 200,
        "categories": [1, 3, 5],
        "in_stock": True,
        "search_term": "premium",
        "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
    }

    # 创建价格条件组
    if "min_price" in filters or "max_price" in filters:
        builder.create_condition_group("price_conditions", ConditionOperator.OR)

        if "min_price" in filters:
            builder.add_condition(
                ConditionModel(
                    column="p.price",
                    value=filters["min_price"],
                    operator=Operator.GREATER_EQUALS,
                )
            )

        if "max_price" in filters:
            builder.add_condition(
                ConditionModel(
                    column="p.price",
                    value=filters["max_price"],
                    operator=Operator.LESS_EQUALS,
                )
            )

    # 创建类别条件组
    if "categories" in filters and filters["categories"]:
        builder.create_condition_group("category_conditions")
        builder.add_condition(
            ConditionModel(
                column="p.category_id",
                value=filters["categories"],
                operator=Operator.IN,
            )
        )

    # 创建库存条件组
    if "in_stock" in filters and filters["in_stock"]:
        builder.create_condition_group("stock_conditions")
        builder.add_condition(
            ConditionModel(column="p.stock", value=0, operator=Operator.GREATER_THAN)
        )

    # 创建搜索条件组 (使用OR连接)
    if "search_term" in filters and filters["search_term"]:
        builder.create_condition_group("search_conditions")
        builder.add_condition(
            ConditionModel(
                column="p.name",
                value=f"%{filters['search_term']}%",
                operator=Operator.LIKE,
            )
        )
        builder.add_condition(
            ConditionModel(
                column="p.description",
                value=f"%{filters['search_term']}%",
                operator=Operator.LIKE,
            ),
            operator=ConditionOperator.OR,
        )

    # 创建日期条件组
    if "date_range" in filters:
        builder.create_condition_group("date_conditions")

        if "start" in filters["date_range"]:
            builder.add_condition(
                ConditionModel(
                    column="p.created_at",
                    value=filters["date_range"]["start"],
                    operator=Operator.GREATER_EQUALS,
                )
            )

        if "end" in filters["date_range"]:
            builder.add_condition(
                ConditionModel(
                    column="p.created_at",
                    value=filters["date_range"]["end"],
                    operator=Operator.LESS_EQUALS,
                )
            )

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例37: 通过配置文件创建条件，然后动态添加更多条件
    print("示例37: 通过配置文件创建条件，然后动态添加更多条件")

    # 创建基础配置，包含一些预设条件
    config_with_conditions = {
        "type": "select",
        "columns": ["*"],
        "table": "orders",
        "where": "status = 'pending'",  # 基础条件
    }

    # 创建构建器并应用基础配置
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(config_with_conditions)

    # 动态添加更多条件
    user_id = 123
    min_amount = 50.0
    max_days = 30

    # 添加用户ID条件
    if user_id:
        builder.add_condition(
            ConditionModel(column="user_id", value=user_id, operator=Operator.EQUALS)
        )

    # 添加订单金额条件
    if min_amount:
        builder.add_condition(
            ConditionModel(
                column="total_amount",
                value=min_amount,
                operator=Operator.GREATER_EQUALS,
            )
        )

    # 添加日期条件
    if max_days:
        builder.add_condition_raw(
            "created_at >= CURRENT_DATE - INTERVAL ':days days'", {"days": max_days}
        )

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    # 示例38: 从配置文件创建条件组，然后应用
    print("示例38: 从配置文件创建条件组，然后应用")

    # 创建基础配置
    base_select_config = {
        "type": "select",
        "columns": ["id", "name", "email", "status"],
        "table": "users",
    }

    # 条件组配置
    condition_groups_config = {
        "status_group": [{"column": "status", "value": "active", "operator": "="}],
        "date_group": [
            {"column": "last_login", "value": "2023-01-01", "operator": ">="},
            {"column": "last_login", "value": "2023-12-31", "operator": "<="},
        ],
        "subscription_group": [
            {
                "column": "subscription_type",
                "value": ["premium", "business"],
                "operator": "IN",
            },
            {"column": "subscription_status", "value": "active", "operator": "="},
        ],
    }

    # 创建构建器并应用基础配置
    builder = SQLBuilder(dialect="postgresql")
    builder.build_from_config(base_select_config)

    # 从配置创建条件组
    for group_name, conditions in condition_groups_config.items():
        builder.create_condition_group(group_name)

        for condition in conditions:
            column = condition["column"]
            value = condition["value"]
            op_str = condition["operator"]

            # 将字符串操作符转换为Operator枚举
            op = Operator.EQUALS
            if op_str == ">":
                op = Operator.GREATER_THAN
            elif op_str == ">=":
                op = Operator.GREATER_EQUALS
            elif op_str == "<":
                op = Operator.LESS_THAN
            elif op_str == "<=":
                op = Operator.LESS_EQUALS
            elif op_str == "IN":
                op = Operator.IN
            elif op_str == "LIKE":
                op = Operator.LIKE

            builder.add_condition(
                ConditionModel(column=column, value=value, operator=op)
            )

    # 构建SQL
    sql, params = builder.build()

    print(sql)
    print(f"参数: {json.dumps(params, indent=2)}")
    print()

    print("所有示例已成功完成！")


if __name__ == "__main__":
    main()
