#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
整合高级功能的SQLGenerator示例
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入sql_generator包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Any, Dict, List

from sql_generator.core.sql_generator import SQLGenerator


def print_sql(description: str, sql: str) -> None:
    """打印SQL语句"""
    print(f"\n=== {description} ===")
    print(f"SQL: {sql}")
    print("=" * 50)


def window_function_example(generator: SQLGenerator) -> None:
    """窗口函数示例"""
    # 使用高级API
    sql = generator.generate_window_function(
        table="employees",
        base_columns=["employee_name", "department", "salary"],
        window_functions=[
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
        where="salary > 50000",
        order_by=[
            {"column": "department", "direction": "ASC"},
            {"column": "salary_rank", "direction": "ASC"},
        ],
    )
    print_sql("窗口函数示例 (高级API)", sql)

    # 使用配置文件
    config = {
        "type": "select",
        "use_builder": True,
        "table": "employees",
        "columns": ["employee_name", "department", "salary"],
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
    sql = generator.generate_from_config(config)
    print_sql("窗口函数示例 (配置文件)", sql)


def json_query_example(generator: SQLGenerator) -> None:
    """JSON查询示例"""
    # 使用高级API
    sql = generator.generate_json_query(
        table="customers",
        base_columns=["id", "name"],
        json_extracts=[
            {"column": "data", "path": "address.city", "alias": "city"},
            {"column": "data", "path": "address.country", "alias": "country"},
        ],
        json_conditions=[{"column": "data", "value": {"status": "active"}}],
        where="id > 100",
    )
    print_sql("JSON查询示例 (高级API)", sql)

    # 使用配置文件
    config = {
        "type": "select",
        "use_builder": True,
        "table": "customers",
        "columns": ["id", "name"],
        "json_extracts": [
            {"column": "data", "path": "address.city", "alias": "city"},
            {"column": "data", "path": "address.country", "alias": "country"},
        ],
        "json_conditions": [{"column": "data", "value": {"status": "active"}}],
        "where": "id > 100",
    }
    sql = generator.generate_from_config(config)
    print_sql("JSON查询示例 (配置文件)", sql)


def subquery_example(generator: SQLGenerator) -> None:
    """子查询示例"""
    # 使用高级API
    main_config = {
        "type": "select",
        "columns": ["e.employee_name", "e.salary", "d.avg_salary"],
        "table": "employees",
        "alias": "e",
        "where": "e.salary > d.avg_salary",
    }

    subqueries = {
        "d": {
            "type": "select",
            "columns": ["department", "AVG(salary) as avg_salary"],
            "table": "employees",
            "group_by": ["department"],
        }
    }

    sql = generator.generate_with_subquery(main_config, subqueries)
    print_sql("子查询示例 (高级API)", sql)

    # 使用配置文件
    config = {
        "type": "select",
        "use_builder": True,
        "columns": ["e.employee_name", "e.salary", "d.avg_salary"],
        "table": "employees",
        "alias": "e",
        "where": "e.salary > d.avg_salary",
        "ctes": {
            "dept_avg": {
                "query": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department"
            }
        },
        "joins": [
            {
                "table": "dept_avg",
                "alias": "d",
                "condition": "e.department = d.department",
                "type": "INNER",
            }
        ],
    }
    sql = generator.generate_from_config(config)
    print_sql("CTE示例 (配置文件)", sql)


def ddl_example(generator: SQLGenerator) -> None:
    """DDL示例"""
    # 创建表
    config = {
        "type": "create_table",
        "use_builder": True,
        "table": "customers",
        "columns": [
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
    }
    sql = generator.generate_from_config(config)
    print_sql("创建表示例", sql)

    # 修改表
    config = {
        "type": "alter_table",
        "use_builder": True,
        "table": "customers",
        "add_columns": [{"name": "phone", "type": "VARCHAR(20)"}],
        "add_constraints": [
            {
                "name": "valid_email",
                "definition": "CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')",
            }
        ],
    }
    sql = generator.generate_from_config(config)
    print_sql("修改表示例", sql)


def advanced_grouping_example(generator: SQLGenerator) -> None:
    """高级分组示例"""
    # ROLLUP
    config = {
        "type": "select",
        "use_builder": True,
        "table": "sales",
        "columns": ["region", "product", "SUM(sales) as total_sales"],
        "rollup": ["region", "product"],
    }
    sql = generator.generate_from_config(config)
    print_sql("ROLLUP分组示例", sql)

    # CUBE
    config = {
        "type": "select",
        "use_builder": True,
        "table": "sales",
        "columns": ["region", "product", "year", "SUM(sales) as total_sales"],
        "cube": ["region", "product", "year"],
    }
    sql = generator.generate_from_config(config)
    print_sql("CUBE分组示例", sql)

    # GROUPING SETS
    config = {
        "type": "select",
        "use_builder": True,
        "table": "sales",
        "columns": ["region", "product", "year", "SUM(sales) as total_sales"],
        "grouping_sets": [
            ["region", "product", "year"],
            ["region", "product"],
            ["region", "year"],
            ["product", "year"],
            ["region"],
            ["product"],
            ["year"],
            [],
        ],
    }
    sql = generator.generate_from_config(config)
    print_sql("GROUPING SETS示例", sql)


def upsert_example(generator: SQLGenerator) -> None:
    """UPSERT示例"""
    config = {
        "type": "insert",
        "use_builder": True,
        "table": "products",
        "columns": ["id", "name", "price", "stock"],
        "values": [[1, "Product A", 19.99, 100]],
        "upsert": {
            "conflict_columns": ["id"],
            "update_columns": ["name", "price", "stock"],
        },
    }
    sql = generator.generate_from_config(config)
    print_sql("UPSERT示例", sql)


def transaction_example(generator: SQLGenerator) -> None:
    """事务示例"""
    # 开始事务
    sql = generator.generate_transaction("begin")
    print_sql("开始事务", sql)

    # 保存点
    sql = generator.generate_transaction("savepoint", "before_update")
    print_sql("创建保存点", sql)

    # 回滚到保存点
    sql = generator.generate_transaction("rollback_to_savepoint", "before_update")
    print_sql("回滚到保存点", sql)

    # 提交事务
    sql = generator.generate_transaction("commit")
    print_sql("提交事务", sql)


def data_import_export_example(generator: SQLGenerator) -> None:
    """数据导入导出示例"""
    # 导入数据
    sql = generator.generate_data_import(
        table="customers", file_path="/tmp/customers.csv", delimiter=",", header=True
    )
    print_sql("数据导入示例", sql)

    # 导出数据 (仅PostgreSQL)
    if generator.dialect == "postgresql":
        sql = generator.generate_data_export(
            table="customers",
            file_path="/tmp/customers_export.csv",
            delimiter="|",
            header=True,
        )
        print_sql("数据导出示例", sql)


def full_text_search_example(generator: SQLGenerator) -> None:
    """全文搜索示例"""
    config = {
        "type": "select",
        "use_builder": True,
        "table": "articles",
        "columns": ["id", "title", "content"],
        "full_text_search": {
            "columns": ["title", "content"],
            "term": "postgresql database",
        },
    }
    sql = generator.generate_from_config(config)
    print_sql("全文搜索示例", sql)


def main() -> None:
    """主函数"""
    # 创建SQLGenerator实例
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
    )

    # 确保模板目录存在
    os.makedirs(templates_dir, exist_ok=True)

    generator = SQLGenerator(templates_dir=templates_dir, dialect="postgresql")

    print("\n===== 整合高级功能的SQLGenerator示例 =====\n")

    window_function_example(generator)
    json_query_example(generator)
    subquery_example(generator)
    ddl_example(generator)
    advanced_grouping_example(generator)
    upsert_example(generator)
    transaction_example(generator)
    data_import_export_example(generator)
    full_text_search_example(generator)


if __name__ == "__main__":
    main()
