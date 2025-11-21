#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLBuilder高级功能示例
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Any, Dict, List, Tuple

from sql_generator import SQLBuilder


def print_sql(description: str, sql_tuple: Tuple[str, Dict[str, Any]]) -> None:
    """打印SQL语句和参数"""
    sql, params = sql_tuple
    print(f"\n=== {description} ===")
    print(f"SQL: {sql}")
    print(f"参数: {params}")
    print("=" * 50)


def window_function_examples() -> None:
    """窗口函数示例"""
    # 排名函数
    builder = SQLBuilder(dialect="postgresql")
    builder.select("employee_name", "department", "salary").window(
        "ROW_NUMBER",
        "",
        partition_by=["department"],
        order_by=[{"column": "salary", "direction": "DESC"}],
        alias="salary_rank",
    ).from_table("employees")
    print_sql("排名函数示例", builder.build())

    # 移动平均
    builder = SQLBuilder(dialect="postgresql")
    builder.select("date", "sales").window(
        "AVG",
        "sales",
        order_by=[{"column": "date", "direction": "ASC"}],
        frame_clause="ROWS BETWEEN 2 PRECEDING AND CURRENT ROW",
        alias="moving_avg",
    ).from_table("daily_sales").order_by("date")
    print_sql("移动平均示例", builder.build())


def json_operations_examples() -> None:
    """JSON操作示例"""
    # PostgreSQL JSON提取
    builder = SQLBuilder(dialect="postgresql")
    builder.select("id").json_extract("data", "name", "customer_name").json_extract(
        "data", "address.city", "city"
    ).from_table("customers").where("id > 100")
    print_sql("PostgreSQL JSON提取", builder.build())

    # JSON条件查询
    builder = SQLBuilder(dialect="postgresql")
    builder.select("id", "data").from_table("orders").json_contains(
        "data", {"status": "shipped"}
    )
    print_sql("JSON条件查询", builder.build())


def subquery_examples() -> None:
    """子查询示例"""
    # 子查询
    subquery_builder = SQLBuilder(dialect="postgresql")
    subquery_builder.select("department", "AVG(salary) as avg_salary").from_table(
        "employees"
    ).group_by("department")

    main_builder = SQLBuilder(dialect="postgresql")
    main_builder.select("e.employee_name", "e.salary", "d.avg_salary").from_table(
        "employees", "e"
    ).subquery(subquery_builder, "d").where("e.department = d.department").where(
        "e.salary > d.avg_salary"
    )

    print_sql("子查询示例", main_builder.build())


def cte_examples() -> None:
    """CTE示例"""
    # 简单CTE
    builder = SQLBuilder(dialect="postgresql")
    builder.with_cte(
        "dept_avg",
        "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
    ).select("e.employee_name", "e.salary", "d.avg_salary").from_table(
        "employees", "e"
    ).join(
        "dept_avg", "e.department = d.department", "INNER", "d"
    ).where(
        "e.salary > d.avg_salary"
    )

    print_sql("简单CTE示例", builder.build())

    # 递归CTE (组织结构)
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
    ).select("id", "name", "level").from_table("org_hierarchy").order_by(
        "level"
    ).order_by(
        "name"
    )

    print_sql("递归CTE示例", builder.build())


def ddl_examples() -> None:
    """DDL示例"""
    # 创建表
    builder = SQLBuilder(dialect="postgresql")
    builder.create_table(
        "customers",
        [
            {"name": "id", "type": "SERIAL", "constraints": ["PRIMARY KEY"]},
            {"name": "name", "type": "VARCHAR(100)", "constraints": ["NOT NULL"]},
            {"name": "email", "type": "VARCHAR(255)", "constraints": ["UNIQUE"]},
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "constraints": ["DEFAULT CURRENT_TIMESTAMP"],
            },
            {"name": "data", "type": "JSONB"},
        ],
    )

    print_sql("创建表示例", builder.build())

    # 修改表
    builder = SQLBuilder(dialect="postgresql")
    builder.alter_table("customers").add_column("phone", "VARCHAR(20)").add_constraint(
        "valid_email",
        "CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')",
    )

    print_sql("修改表示例", builder.build())


def advanced_grouping_examples() -> None:
    """高级分组示例"""
    # ROLLUP
    builder = SQLBuilder(dialect="postgresql")
    builder.select("region", "product", "SUM(sales) as total_sales").from_table(
        "sales"
    ).rollup("region", "product")

    print_sql("ROLLUP分组示例", builder.build())

    # CUBE
    builder = SQLBuilder(dialect="postgresql")
    builder.select("region", "product", "year", "SUM(sales) as total_sales").from_table(
        "sales"
    ).cube("region", "product", "year")

    print_sql("CUBE分组示例", builder.build())

    # GROUPING SETS
    builder = SQLBuilder(dialect="postgresql")
    builder.select("region", "product", "year", "SUM(sales) as total_sales").from_table(
        "sales"
    ).grouping_sets(
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

    print_sql("GROUPING SETS示例", builder.build())


def upsert_examples() -> None:
    """UPSERT示例"""
    # PostgreSQL UPSERT
    builder = SQLBuilder(dialect="postgresql")
    builder.insert_into("products", ["id", "name", "price", "stock"]).values(
        [1, "Product A", 19.99, 100]
    ).upsert(["id"], ["name", "price", "stock"])

    print_sql("PostgreSQL UPSERT示例", builder.build())

    # MySQL UPSERT
    builder = SQLBuilder(dialect="mysql")
    builder.insert_into("products", ["id", "name", "price", "stock"]).values(
        [1, "Product A", 19.99, 100]
    ).upsert(
        [], ["name", "price", "stock"]
    )  # MySQL不需要指定冲突列

    print_sql("MySQL UPSERT示例", builder.build())


def transaction_examples() -> None:
    """事务示例"""
    # 开始事务
    builder = SQLBuilder(dialect="postgresql")
    builder.begin_transaction()
    print_sql("开始事务", builder.build())

    # 保存点
    builder = SQLBuilder(dialect="postgresql")
    builder.savepoint("before_update")
    print_sql("创建保存点", builder.build())

    # 回滚到保存点
    builder = SQLBuilder(dialect="postgresql")
    builder.rollback_to_savepoint("before_update")
    print_sql("回滚到保存点", builder.build())

    # 提交事务
    builder = SQLBuilder(dialect="postgresql")
    builder.commit_transaction()
    print_sql("提交事务", builder.build())


def data_import_export_examples() -> None:
    """数据导入导出示例"""
    # PostgreSQL COPY导入
    builder = SQLBuilder(dialect="postgresql")
    builder.copy_from("customers", "/tmp/customers.csv", delimiter=",", header=True)
    print_sql("PostgreSQL COPY导入", builder.build())

    # PostgreSQL COPY导出
    builder = SQLBuilder(dialect="postgresql")
    builder.copy_to(
        "customers", "/tmp/customers_export.csv", delimiter="|", header=True
    )
    print_sql("PostgreSQL COPY导出", builder.build())

    # MySQL LOAD DATA
    builder = SQLBuilder(dialect="mysql")
    builder.load_data(
        "customers",
        "/tmp/customers.csv",
        local=True,
        fields_terminated_by=",",
        lines_terminated_by="\n",
        ignore_lines=1,
    )
    print_sql("MySQL LOAD DATA", builder.build())


def full_text_search_examples() -> None:
    """全文搜索示例"""
    # PostgreSQL全文搜索
    builder = SQLBuilder(dialect="postgresql")
    builder.select("id", "title", "content").from_table("articles").full_text_search(
        ["title", "content"], "postgresql database"
    )

    print_sql("PostgreSQL全文搜索", builder.build())

    # MySQL全文搜索
    builder = SQLBuilder(dialect="mysql")
    builder.select("id", "title", "content").from_table("articles").full_text_search(
        ["title", "content"], "+mysql -oracle"
    )

    print_sql("MySQL全文搜索", builder.build())


def analytic_functions_examples() -> None:
    """分析函数示例"""
    # LAG函数
    builder = SQLBuilder(dialect="postgresql")
    builder.select("date", "stock_price").lag(
        "stock_price",
        1,
        0,
        partition_by=["stock_id"],
        order_by=[{"column": "date", "direction": "ASC"}],
        alias="prev_price",
    ).from_table("stock_history").order_by("stock_id").order_by("date")

    print_sql("LAG函数示例", builder.build())

    # LEAD函数
    builder = SQLBuilder(dialect="postgresql")
    builder.select("date", "stock_price").lead(
        "stock_price",
        1,
        0,
        partition_by=["stock_id"],
        order_by=[{"column": "date", "direction": "ASC"}],
        alias="next_price",
    ).from_table("stock_history").order_by("stock_id").order_by("date")

    print_sql("LEAD函数示例", builder.build())


def raw_sql_examples() -> None:
    """原始SQL示例"""
    # 执行原始SQL
    builder = SQLBuilder(dialect="postgresql")
    builder.execute_raw(
        "SELECT * FROM users WHERE age > %(min_age)s AND status = %(status)s",
        {"min_age": 18, "status": "active"},
    )

    print_sql("原始SQL示例", builder.build())


def main() -> None:
    """主函数"""
    print("\n===== SQLBuilder高级功能示例 =====\n")

    window_function_examples()
    json_operations_examples()
    subquery_examples()
    cte_examples()
    ddl_examples()
    advanced_grouping_examples()
    upsert_examples()
    transaction_examples()
    data_import_export_examples()
    full_text_search_examples()
    analytic_functions_examples()
    raw_sql_examples()


if __name__ == "__main__":
    main()
