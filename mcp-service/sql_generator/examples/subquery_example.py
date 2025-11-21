#!/usr/bin/env python3
"""
Example script demonstrating SQL subquery generation.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the sql_generator package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLGenerator


def main():
    """Main function demonstrating SQL subquery generation."""

    # Get the templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    # Initialize the generator
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # Example 1: Simple subquery
    subquery_config = {
        "type": "subquery",
        "table": "employees",
        "columns": ["employee_id", "name", "department_id", "salary"],
        "where": "salary > 50000",
        "order_by": [{"column": "salary", "direction": "DESC"}],
        "limit": 10,
        "alias": "high_salary_employees",
    }

    sql = generator.generate_subquery(subquery_config)
    print("Simple subquery example (PostgreSQL):")
    print(sql)
    print()

    # Example 2: Subquery with joins
    subquery_with_join = {
        "type": "subquery",
        "table": "orders",
        "table_alias": "o",
        "columns": [
            "o.order_id",
            "o.customer_id",
            "c.customer_name",
            "o.order_date",
            {"expr": "SUM(oi.quantity * oi.price)", "alias": "order_total"},
        ],
        "joins": [
            {
                "type": "INNER",
                "table": "customers",
                "alias": "c",
                "condition": "o.customer_id = c.customer_id",
            },
            {
                "type": "LEFT",
                "table": "order_items",
                "alias": "oi",
                "condition": "o.order_id = oi.order_id",
            },
        ],
        "where": "o.order_date >= '2023-01-01'",
        "group_by": ["o.order_id", "o.customer_id", "c.customer_name", "o.order_date"],
        "having": "SUM(oi.quantity * oi.price) > 1000",
        "alias": "large_orders",
    }

    sql = generator.generate_subquery(subquery_with_join)
    print("Subquery with joins example (PostgreSQL):")
    print(sql)
    print()

    # Example 3: Using subquery in a SELECT statement
    select_with_subquery = {
        "type": "select",
        "columns": [
            "d.department_name",
            {"expr": "COUNT(e.employee_id)", "alias": "employee_count"},
            {"expr": "AVG(e.salary)", "alias": "avg_salary"},
        ],
        "table": "departments",
        "table_alias": "d",
        "joins": [
            {
                "type": "INNER",
                "table": generator.generate_subquery(
                    {
                        "table": "employees",
                        "columns": ["employee_id", "department_id", "salary"],
                        "where": "salary > 50000",
                        "alias": "e",
                    }
                ),
                "condition": "d.department_id = e.department_id",
            }
        ],
        "group_by": ["d.department_name"],
        "order_by": [{"column": "avg_salary", "direction": "DESC"}],
    }

    # Use the custom SQL string directly in the join condition
    sql = generator.generate_from_config(select_with_subquery)
    print("SELECT with subquery example (PostgreSQL):")
    print(sql)
    print()

    # Example 4: Same examples with MySQL dialect
    generator.set_dialect("mysql")

    sql = generator.generate_subquery(subquery_config)
    print("Simple subquery example (MySQL):")
    print(sql)
    print()

    sql = generator.generate_subquery(subquery_with_join)
    print("Subquery with joins example (MySQL):")
    print(sql)


if __name__ == "__main__":
    main()
