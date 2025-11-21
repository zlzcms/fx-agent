# SQL Generator

A Python library for generating SQL statements based on templates and configurations. Supports both PostgreSQL and MySQL dialects.

## Features

- Generate SQL statements from templates
- Support for PostgreSQL and MySQL dialects
- Programmatic SQL query building
- Configuration-based SQL generation
- Complex subqueries, joins, and CTEs
- Parameter binding for safe SQL execution

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from sql_generator import SQLGenerator

# Initialize the generator with the templates directory
generator = SQLGenerator("templates", dialect="postgresql")

# Generate a SELECT statement
select_config = {
    "table": "users",
    "columns": ["id", "name", "email"],
    "where": "age > 18",
    "order_by": [{"column": "name", "direction": "ASC"}],
    "limit": 10
}
sql = generator.generate_select(select_config)
print(sql)
```

### Using the SQL Builder

```python
from sql_generator import SQLBuilder

# Initialize the builder
builder = SQLBuilder(dialect="postgresql")

# Build a SELECT statement
sql, params = (
    builder.select("id", "name", "email")
    .from_table("users")
    .where_equals("status", "active")
    .order_by("created_at", "DESC")
    .limit(10)
    .build()
)
print(sql)
print(params)
```

### Using SQL Configuration

```python
from sql_generator import SQLConfig, SQLGenerator

# Load configuration from a JSON file
config = SQLConfig.from_json_file("query_config.json")

# Initialize the generator
generator = SQLGenerator("templates", dialect="postgresql")

# Generate SQL from configuration
sql = generator.generate_from_config(config.to_dict())
print(sql)
```

### Complex Queries with Subqueries

```python
from sql_generator import SQLGenerator

# Initialize the generator
generator = SQLGenerator("templates", dialect="postgresql")

# Define a configuration with subqueries
config = {
    "type": "select",
    "table": "orders",
    "columns": ["id", "customer_id", "total"],
    "joins": [
        {
            "type": "LEFT",
            "table": "customers",
            "alias": "c",
            "condition": "orders.customer_id = c.id"
        }
    ],
    "where": "orders.total > 100 AND c.status = 'active'",
    "with_clauses": {
        "recent_orders": "SELECT id FROM orders WHERE created_at > NOW() - INTERVAL '30 days'"
    }
}

sql = generator.generate_from_config(config)
print(sql)
```

## Templates

The library includes the following templates:

- `select.sql.j2`: Template for SELECT statements
- `insert.sql.j2`: Template for INSERT statements
- `update.sql.j2`: Template for UPDATE statements
- `delete.sql.j2`: Template for DELETE statements
- `subquery.sql.j2`: Template for subqueries

You can create custom templates by adding them to the templates directory.

## License

MIT
