#!/usr/bin/env python3
"""
Example script demonstrating the SQL generator functionality.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the sql_generator package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sql_generator import SQLBuilder, SQLConfig, SQLDialect, SQLGenerator


def main():
    """Main function demonstrating SQL generator functionality."""

    # Get the templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")

    print("SQL Generator Example\n")

    # Example 1: Basic SELECT using SQLGenerator
    print("Example 1: Basic SELECT using SQLGenerator")
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    select_config = {
        "table": "users",
        "columns": ["id", "name", "email"],
        "where": "age > 18",
        "order_by": [{"column": "name", "direction": "ASC"}],
        "limit": 10,
    }

    sql = generator.generate_select(select_config)
    print(sql)
    print()

    # Example 2: Same query with MySQL dialect
    print("Example 2: Same query with MySQL dialect")
    generator.set_dialect("mysql")
    sql = generator.generate_select(select_config)
    print(sql)
    print()

    # Example 3: Using SQLBuilder for programmatic query building
    print("Example 3: Using SQLBuilder for programmatic query building")
    builder = SQLBuilder(dialect="postgresql")

    sql, params = (
        builder.select("id", "name", "email")
        .from_table("users", "u")
        .join("user_profiles", "u.id = user_profiles.user_id", "LEFT", "up")
        .where_equals("u.status", "active")
        .where("up.verified = TRUE")
        .group_by("u.id", "u.name", "u.email")
        .having("COUNT(up.id) > 0")
        .order_by("u.created_at", "DESC")
        .limit(10)
        .build()
    )

    print(sql)
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print()

    # Example 4: Complex query with subqueries and CTEs
    print("Example 4: Complex query with subqueries and CTEs")
    complex_config = {
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
        "where": "o.order_date >= '2023-01-01' AND c.status = 'active'",
        "group_by": ["o.id", "o.order_date", "c.name"],
        "having": "SUM(oi.quantity * oi.price) > 100",
        "order_by": [{"column": "o.order_date", "direction": "DESC"}],
        "limit": 20,
        "with_clauses": {
            "active_customers": "SELECT id, name FROM customers WHERE status = 'active'"
        },
    }

    generator.set_dialect("postgresql")
    sql = generator.generate_from_config(complex_config)
    print(sql)
    print()

    # Example 5: INSERT statement with returning clause (PostgreSQL)
    print("Example 5: INSERT statement with returning clause (PostgreSQL)")
    insert_config = {
        "type": "insert",
        "table": "users",
        "columns": ["name", "email", "created_at"],
        "values": [
            ["'John Doe'", "'john@example.com'", "NOW()"],
            ["'Jane Smith'", "'jane@example.com'", "NOW()"],
        ],
        "returning": ["id", "created_at"],
    }

    sql = generator.generate_from_config(insert_config)
    print(sql)
    print()

    # Example 6: UPDATE with joins (MySQL)
    print("Example 6: UPDATE with joins (MySQL)")
    generator.set_dialect("mysql")
    update_config = {
        "type": "update",
        "table": "products",
        "table_alias": "p",
        "set_values": {"p.stock": "p.stock - oi.quantity", "p.last_ordered": "NOW()"},
        "joins": [
            {
                "type": "INNER",
                "table": "order_items",
                "alias": "oi",
                "condition": "p.id = oi.product_id",
            },
            {
                "type": "INNER",
                "table": "orders",
                "alias": "o",
                "condition": "oi.order_id = o.id",
            },
        ],
        "where": "o.id = 12345",
    }

    sql = generator.generate_from_config(update_config)
    print(sql)
    print()

    # Example 7: DELETE with using clause (PostgreSQL)
    print("Example 7: DELETE with using clause (PostgreSQL)")
    generator.set_dialect("postgresql")
    delete_config = {
        "type": "delete",
        "table": "order_items",
        "table_alias": "oi",
        "using": [{"table": "orders", "alias": "o"}],
        "where": "oi.order_id = o.id AND o.status = 'cancelled'",
        "returning": ["oi.id", "oi.product_id"],
    }

    sql = generator.generate_from_config(delete_config)
    print(sql)
    print()

    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
