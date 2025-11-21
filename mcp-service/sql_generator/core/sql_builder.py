from typing import Any, Dict, List, Optional, Tuple, Union

from ..model.builder import VALID_OPERATORS, ConditionModel, ConditionOperator, Operator
from ..utils.sql_dialect import SQLDialect


class SQLBuilder:
    """
    SQL Builder class for programmatically constructing SQL queries.
    """

    def __init__(self, dialect: str = "postgresql"):
        """
        Initialize the SQL builder.

        Args:
            dialect: SQL dialect to use ('postgresql' or 'mysql')
        """
        self.dialect = dialect.lower()
        self.reset()

    def reset(self) -> "SQLBuilder":
        """Reset the builder to its initial state."""
        self.select_parts = []
        self.from_parts = []
        self.join_parts = []
        self.where_parts = []
        self.group_by_parts = []
        self.having_parts = []
        self.order_by_parts = []
        self.limit_val = None
        self.offset_val = None
        self.distinct = False
        self.insert_table = ""
        self.insert_database = None
        self.insert_columns = []
        self.insert_values = []
        self.update_table = ""
        self.update_database = None
        self.update_sets = []
        self.delete_table = ""
        self.delete_database = None
        self.returning_parts = []
        self.with_parts = []
        self.parameters = {}
        self.param_counter = 0
        self.condition_groups = {}  # 用于存储分组条件
        self.current_condition_group = "default"  # 默认条件组
        # 新增属性
        self.upsert_clause = None
        self.create_table_name = None
        self.create_table_columns = None
        self.dialect_specific_parts = []
        self.window_functions = []
        return self

    def _add_parameter(self, value: Any) -> str:
        """
        Add a parameter to the parameters dictionary.

        Args:
            value: Parameter value

        Returns:
            Parameter placeholder
        """
        self.param_counter += 1
        param_name = f"p{self.param_counter}"
        self.parameters[param_name] = value
        return f"%({param_name})s"

    def _format_table_reference(
        self, table: str, database: Optional[str] = None
    ) -> str:
        """
        Format a table reference with optional database name.

        Args:
            table: Table name
            database: Optional database name

        Returns:
            Formatted table reference
        """
        if database:
            if self.dialect == "postgresql":
                # PostgreSQL uses schema.table format
                return f"{database}.{table}"
            else:
                # MySQL uses database.table format
                return f"{database}.{table}"
        return table

    def select(self, *columns: str) -> "SQLBuilder":
        """
        Add columns to the SELECT clause.

        Args:
            *columns: Column names or expressions

        Returns:
            Self for method chaining
        """
        self.select_parts.extend(columns)
        return self

    def distinct(self) -> "SQLBuilder":
        """
        Make the SELECT DISTINCT.

        Returns:
            Self for method chaining
        """
        self.distinct = True
        return self

    def from_table(
        self, table: str, alias: Optional[str] = None, database: Optional[str] = None
    ) -> "SQLBuilder":
        """
        Add a table to the FROM clause.

        Args:
            table: Table name
            alias: Optional table alias
            database: Optional database name

        Returns:
            Self for method chaining
        """
        table_ref = self._format_table_reference(table, database)

        if alias:
            self.from_parts.append(f"{table_ref} AS {alias}")
        else:
            self.from_parts.append(table_ref)
        return self

    def join(
        self,
        table: str,
        condition: str,
        join_type: str = "INNER",
        alias: Optional[str] = None,
        database: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        Add a JOIN clause.

        Args:
            table: Table name to join
            condition: Join condition
            join_type: Type of join (INNER, LEFT, RIGHT, FULL)
            alias: Optional table alias
            database: Optional database name

        Returns:
            Self for method chaining
        """
        table_ref = self._format_table_reference(table, database)
        table_part = f"{table_ref} AS {alias}" if alias else table_ref
        self.join_parts.append(f"{join_type} JOIN {table_part} ON {condition}")
        return self

    def where(self, condition: str) -> "SQLBuilder":
        """
        Add a condition to the WHERE clause.

        Args:
            condition: WHERE condition

        Returns:
            Self for method chaining
        """
        self.where_parts.append(condition)
        return self

    def where_equals(self, column: str, value: Any) -> "SQLBuilder":
        """
        Add an equality condition to the WHERE clause.

        Args:
            column: Column name
            value: Value to compare with

        Returns:
            Self for method chaining
        """
        param = self._add_parameter(value)
        return self.where(f"{column} = {param}")

    def where_in(self, column: str, values: List[Any]) -> "SQLBuilder":
        """
        Add an IN condition to the WHERE clause.

        Args:
            column: Column name
            values: List of values

        Returns:
            Self for method chaining
        """
        if not values:
            return self.where("1 = 0")  # Always false when empty list

        params = [self._add_parameter(v) for v in values]
        return self.where(f"{column} IN ({', '.join(params)})")

    # 新增条件组管理方法
    def create_condition_group(
        self,
        group_name: str,
        condition_operator: ConditionOperator = ConditionOperator.AND,
    ) -> "SQLBuilder":
        """
        创建一个新的条件组

        Args:
            group_name: 条件组名称

        Returns:
            Self for method chaining
        """
        self.condition_groups[group_name] = {
            "conditions": [],
            "operator": condition_operator.value,
        }
        self.current_condition_group = group_name
        return self

    def use_condition_group(
        self,
        group_name: str,
        condition_operator: ConditionOperator = ConditionOperator.AND,
    ) -> "SQLBuilder":
        """
        切换到指定的条件组

        Args:
            group_name: 条件组名称

        Returns:
            Self for method chaining
        """
        if group_name not in self.condition_groups:
            self.condition_groups[group_name] = {
                "conditions": [],
                "operator": condition_operator.value,
            }
        self.current_condition_group = group_name
        return self

    def add_condition(
        self,
        condition: ConditionModel | str,
        operator: ConditionOperator = ConditionOperator.AND,
        group_name: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加条件到当前或指定条件组

        Args:
            condition: 条件表达式，ConditionModel对象
            operator: 连接操作符，默认为"AND"
            group_name: 条件组名称，默认为当前条件组

        Returns:
            Self for method chaining
        """
        target_group = group_name or self.current_condition_group

        if target_group not in self.condition_groups:
            self.condition_groups[target_group] = {
                "conditions": [],
                "operator": operator.value,
            }
            self.current_condition_group = group_name
        if isinstance(condition, ConditionModel):
            if condition.value is None:
                raise ValueError(
                    f"Value is required for condition: {condition.column} {condition.operator}"
                )
            condition_str = self.get_condition_str(condition)
        else:
            condition_str = condition

        self.condition_groups[target_group]["conditions"].append(
            {"condition": condition_str, "operator": operator.value}
        )

        return self

    def get_condition_str(self, condition: ConditionModel) -> str:
        """
        获取条件字符串
        """
        operator = condition.operator.value
        # 验证操作符是否有效
        if operator not in VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator: {operator}. Valid operators are: {', '.join(VALID_OPERATORS)}"
            )
        # 处理不需要值的操作符
        if operator in (Operator.IS_NULL.value, Operator.IS_NOT_NULL.value):
            return f"{condition.column} {operator}"

        # 处理需要两个值的操作符
        if operator == Operator.BETWEEN.value:
            value_1 = value_2 = ""
            if isinstance(condition.value, (list, tuple)):
                value_1 = str(condition.value[0])
                value_2 = str(condition.value[1])
            elif isinstance(condition.value, str):
                split_value = condition.value.split(",")
                value_1 = split_value[0]
                value_2 = split_value[1]
            if value_1 and value_2:
                value_1 = self._add_parameter(value_1)
                value_2 = self._add_parameter(value_2)
                return f"{condition.column} BETWEEN {value_1} AND {value_2}"
            else:
                raise ValueError(
                    f"Invalid value: {condition.value}. Value must be a list or tuple or string."
                )

        # 处理列表值的操作符
        if operator in (Operator.IN.value, Operator.NOT_IN.value):
            value_str = ""
            if isinstance(condition.value, (list, tuple)):
                # 将列表中的每个元素转换为字符串，然后连接
                value_str = ", ".join(str(v) for v in condition.value)
            elif isinstance(condition.value, str):
                value_str = condition.value
            else:
                raise ValueError(
                    f"Invalid value: {condition.value}. Value must be a list or tuple or string."
                )
            value_str = self._add_parameter(value_str)
            return f"{condition.column} {operator} ({value_str})"

        # 处理其他操作符
        value_str = self._add_parameter(condition.value)
        return f"{condition.column} {operator} {value_str}"

    def add_condition_raw(
        self,
        raw_condition: str,
        params: Dict[str, Any] = None,
        operator: str = "AND",
        group_name: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加原始条件到条件组，可以包含自定义参数

        Args:
            raw_condition: 原始条件字符串，可以包含参数占位符
            params: 参数字典
            operator: 连接操作符，默认为"AND"
            group_name: 条件组名称，默认为当前条件组

        Returns:
            Self for method chaining
        """
        if params:
            for key, value in params.items():
                param_placeholder = self._add_parameter(value)
                raw_condition = raw_condition.replace(f":{key}", param_placeholder)

        # 将字符串operator转换为ConditionOperator枚举
        condition_operator = ConditionOperator.AND
        if operator.upper() == "OR":
            condition_operator = ConditionOperator.OR
        elif operator.upper() == "NOT":
            condition_operator = ConditionOperator.NOT

        return self.add_condition(raw_condition, condition_operator, group_name)

    def apply_condition_group(self, group_name: str) -> "SQLBuilder":
        """
        将指定条件组应用到WHERE子句

        Args:
            group_name: 条件组名称
            condition_operator: 与现有WHERE条件的连接操作符

        Returns:
            Self for method chaining
        """
        if (
            group_name not in self.condition_groups
            or not self.condition_groups[group_name]
        ):
            return self

        conditions = self.condition_groups[group_name]["conditions"]
        condition_operator = self.condition_groups[group_name]["operator"]
        if not conditions:
            return self

        # 构建条件组表达式
        group_parts = []
        for i, cond in enumerate(conditions):
            if i == 0:
                group_parts.append(cond["condition"])
            else:
                group_parts.append(f"{cond['operator']} {cond['condition']}")

        group_expr = f"({' '.join(group_parts)})"

        # 添加到WHERE子句
        if self.where_parts:
            self.where_parts.append(f"{condition_operator} {group_expr}")
        else:
            self.where_parts.append(group_expr)

        return self

    def apply_all_condition_groups(self) -> "SQLBuilder":
        """
        将所有条件组应用到WHERE子句

        Returns:
            Self for method chaining
        """
        # 修复：跟踪已应用的条件组，避免重复应用
        applied_groups = set()

        for group_name in self.condition_groups.keys():
            if group_name not in applied_groups and self.condition_groups[group_name]:
                self.apply_condition_group(group_name)
                applied_groups.add(group_name)

        return self

    def group_by(self, *columns: str) -> "SQLBuilder":
        """
        Add columns to the GROUP BY clause.

        Args:
            *columns: Column names

        Returns:
            Self for method chaining
        """
        self.group_by_parts.extend(columns)
        return self

    def having(self, condition: str) -> "SQLBuilder":
        """
        Add a condition to the HAVING clause.

        Args:
            condition: HAVING condition

        Returns:
            Self for method chaining
        """
        self.having_parts.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "SQLBuilder":
        """
        Add a column to the ORDER BY clause.

        Args:
            column: Column name
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for method chaining
        """
        self.order_by_parts.append(f"{column} {direction}")
        return self

    def limit(self, limit: int) -> "SQLBuilder":
        """
        Set the LIMIT clause.

        Args:
            limit: Maximum number of rows to return

        Returns:
            Self for method chaining
        """
        self.limit_val = limit
        return self

    def offset(self, offset: int) -> "SQLBuilder":
        """
        Set the OFFSET clause.

        Args:
            offset: Number of rows to skip

        Returns:
            Self for method chaining
        """
        self.offset_val = offset
        return self

    def returning(self, *columns: str) -> "SQLBuilder":
        """
        Add columns to the RETURNING clause.

        Args:
            *columns: Column names

        Returns:
            Self for method chaining
        """
        self.returning_parts.extend(columns)
        return self

    def with_cte(self, name: str, query: str) -> "SQLBuilder":
        """
        Add a Common Table Expression (CTE).

        Args:
            name: CTE name
            query: CTE query

        Returns:
            Self for method chaining
        """
        self.with_parts.append(f"{name} AS ({query})")
        return self

    def insert_into(
        self, table: str, columns: List[str], database: Optional[str] = None
    ) -> "SQLBuilder":
        """
        Start an INSERT statement.

        Args:
            table: Table name
            columns: Column names
            database: Optional database name

        Returns:
            Self for method chaining
        """
        self.insert_table = table
        self.insert_database = database
        self.insert_columns = columns
        return self

    def values(self, *rows: List[Any]) -> "SQLBuilder":
        """
        Add values to an INSERT statement.

        Args:
            *rows: Rows of values to insert

        Returns:
            Self for method chaining
        """
        for row in rows:
            if len(row) != len(self.insert_columns):
                raise ValueError("Number of values must match number of columns")
            params = [self._add_parameter(v) for v in row]
            self.insert_values.append(f"({', '.join(params)})")
        return self

    def update(self, table: str, database: Optional[str] = None) -> "SQLBuilder":
        """
        Start an UPDATE statement.

        Args:
            table: Table name
            database: Optional database name

        Returns:
            Self for method chaining
        """
        self.update_table = table
        self.update_database = database
        return self

    def set(self, column: str, value: Any) -> "SQLBuilder":
        """
        Add a SET clause to an UPDATE statement.

        Args:
            column: Column name
            value: New value

        Returns:
            Self for method chaining
        """
        param = self._add_parameter(value)
        self.update_sets.append(f"{column} = {param}")
        return self

    def delete_from(self, table: str, database: Optional[str] = None) -> "SQLBuilder":
        """
        Start a DELETE statement.

        Args:
            table: Table name
            database: Optional database name

        Returns:
            Self for method chaining
        """
        self.delete_table = table
        self.delete_database = database
        return self

    def build_select(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build a SELECT statement.

        Returns:
            Tuple of (SQL statement, parameters)
        """

        parts = []

        # WITH clause
        if self.with_parts:
            parts.append(f"WITH {', '.join(self.with_parts)}")

        # SELECT clause
        select_clause = "SELECT"
        if self.distinct:
            select_clause += " DISTINCT"

        if self.select_parts:
            select_clause += f" {', '.join(self.select_parts)}"
        else:
            select_clause += " *"
        parts.append(select_clause)

        # FROM clause
        if self.from_parts:
            parts.append(f"FROM {', '.join(self.from_parts)}")

        # JOIN clauses
        if self.join_parts:
            parts.extend(self.join_parts)

        # WHERE clause
        if self.where_parts:
            # 修复：确保WHERE子句中不会出现连续的AND
            where_clause = self.where_parts[0]
            for i in range(1, len(self.where_parts)):
                where_clause += f" {self.where_parts[i]}"
            parts.append(f"WHERE {where_clause}")

        # GROUP BY clause
        if self.group_by_parts:
            parts.append(f"GROUP BY {', '.join(self.group_by_parts)}")

        # HAVING clause
        if self.having_parts:
            parts.append(f"HAVING {' AND '.join(self.having_parts)}")

        # ORDER BY clause
        if self.order_by_parts:
            parts.append(f"ORDER BY {', '.join(self.order_by_parts)}")

        # LIMIT/OFFSET clause
        limit_offset = SQLDialect.get_limit_offset(
            self.dialect, self.limit_val, self.offset_val
        )
        if limit_offset:
            parts.append(limit_offset)

        return " ".join(parts), self.parameters

    # 新增高级功能

    # 1. 窗口函数支持
    def window(
        self,
        function: str,
        column: str,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        frame_clause: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加窗口函数

        Args:
            function: 窗口函数名称 (如 ROW_NUMBER, RANK, DENSE_RANK, etc.)
            column: 函数应用的列
            partition_by: PARTITION BY 子句的列
            order_by: ORDER BY 子句的配置
            frame_clause: 窗口框架子句
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        window_parts = []
        if partition_by:
            window_parts.append(f"PARTITION BY {', '.join(partition_by)}")

        if order_by:
            order_parts = []
            for part in order_by:
                col = part["column"]
                direction = part.get("direction", "ASC")
                order_parts.append(f"{col} {direction}")
            window_parts.append(f"ORDER BY {', '.join(order_parts)}")

        if frame_clause:
            window_parts.append(frame_clause)

        window_spec = " ".join(window_parts)
        expr = f"{function}({column}) OVER ({window_spec})"

        if alias:
            self.select_parts.append(f"{expr} AS {alias}")
        else:
            self.select_parts.append(expr)

        # 记录窗口函数以便后续可能的处理
        self.window_functions.append(
            {
                "function": function,
                "column": column,
                "partition_by": partition_by,
                "order_by": order_by,
                "frame_clause": frame_clause,
                "alias": alias,
            }
        )

        return self

    # 2. 子查询支持
    def subquery(self, subquery_builder: "SQLBuilder", alias: str) -> "SQLBuilder":
        """
        添加子查询到FROM子句

        Args:
            subquery_builder: 用于构建子查询的SQLBuilder实例
            alias: 子查询的别名

        Returns:
            Self for method chaining
        """
        sql, params = subquery_builder.build_select()
        self.parameters.update(params)
        self.from_parts.append(f"({sql}) AS {alias}")
        return self

    # 3. 递归CTE支持
    def with_recursive(self, name: str, query: str) -> "SQLBuilder":
        """
        添加递归公共表表达式(CTE)

        Args:
            name: CTE名称
            query: CTE查询语句

        Returns:
            Self for method chaining
        """
        self.with_parts.append(f"{name} AS RECURSIVE ({query})")
        return self

    # 4. JSON操作支持
    def json_extract(
        self, column: str, path: str, alias: Optional[str] = None
    ) -> "SQLBuilder":
        """
        从JSON列提取数据

        Args:
            column: JSON列名
            path: JSON路径
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        if self.dialect == "postgresql":
            expr = f"{column}->>{path}"
        else:  # MySQL
            expr = f"JSON_EXTRACT({column}, '$.{path}')"

        if alias:
            self.select_parts.append(f"{expr} AS {alias}")
        else:
            self.select_parts.append(expr)
        return self

    def json_contains(
        self, column: str, value: Any, path: Optional[str] = None
    ) -> "SQLBuilder":
        """
        检查JSON列是否包含指定值

        Args:
            column: JSON列名
            value: 要检查的值
            path: JSON路径，如果为None则检查整个JSON

        Returns:
            Self for method chaining
        """
        param = self._add_parameter(value)

        if self.dialect == "postgresql":
            if path:
                condition = f"{column}->>{path} @> {param}::jsonb"
            else:
                condition = f"{column} @> {param}::jsonb"
        else:  # MySQL
            if path:
                condition = f"JSON_CONTAINS({column}, {param}, '$.{path}')"
            else:
                condition = f"JSON_CONTAINS({column}, {param})"

        return self.where(condition)

    # 5. 数据定义语言(DDL)支持
    def create_table(self, table: str, columns: List[Dict[str, Any]]) -> "SQLBuilder":
        """
        创建表

        Args:
            table: 表名
            columns: 列定义列表，格式为[{"name": "col_name", "type": "data_type", "constraints": ["NOT NULL", ...]}]

        Returns:
            Self for method chaining
        """
        self.reset()
        self.create_table_name = table
        self.create_table_columns = columns
        return self

    def build_create_table(self) -> Tuple[str, Dict[str, Any]]:
        """
        构建CREATE TABLE语句

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if not self.create_table_name or not self.create_table_columns:
            raise ValueError("CREATE TABLE statement requires table name and columns")

        column_defs = []
        for col in self.create_table_columns:
            name = col["name"]
            data_type = col["type"]
            constraints = col.get("constraints", [])
            column_defs.append(f"{name} {data_type} {' '.join(constraints)}".strip())

        sql = f"CREATE TABLE {self.create_table_name} ({', '.join(column_defs)})"
        return sql, {}

    # 6. UPSERT功能
    def upsert(
        self, conflict_columns: List[str], update_columns: List[str]
    ) -> "SQLBuilder":
        """
        添加UPSERT功能

        Args:
            conflict_columns: 冲突判断列
            update_columns: 需要更新的列

        Returns:
            Self for method chaining
        """
        if self.dialect == "postgresql":
            conflict_cols = ", ".join(conflict_columns)
            updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
            self.upsert_clause = (
                f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {updates}"
            )
        else:  # MySQL
            updates = ", ".join([f"{col} = VALUES({col})" for col in update_columns])
            self.upsert_clause = f"ON DUPLICATE KEY UPDATE {updates}"
        return self

    # 7. 批量操作支持
    def bulk_insert(
        self, table: str, columns: List[str], value_lists: List[List[Any]]
    ) -> "SQLBuilder":
        """
        批量插入数据

        Args:
            table: 表名
            columns: 列名列表
            value_lists: 值列表的列表

        Returns:
            Self for method chaining
        """
        self.insert_into(table, columns)
        for values in value_lists:
            if len(values) != len(columns):
                raise ValueError("Number of values must match number of columns")
            params = [self._add_parameter(v) for v in values]
            self.insert_values.append(f"({', '.join(params)})")
        return self

    # 8. 数据库特定功能
    def dialect_specific(self, dialect: str, sql_fragment: str) -> "SQLBuilder":
        """
        添加特定数据库方言的SQL片段

        Args:
            dialect: 数据库方言名称
            sql_fragment: SQL片段

        Returns:
            Self for method chaining
        """
        if self.dialect.lower() == dialect.lower():
            self.dialect_specific_parts.append(sql_fragment)
        return self

    # 修改build_insert方法以支持UPSERT
    def build_insert(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build an INSERT statement.

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if not self.insert_table or not self.insert_columns or not self.insert_values:
            raise ValueError("INSERT statement requires table, columns, and values")

        table_ref = self._format_table_reference(
            self.insert_table, self.insert_database
        )

        parts = [
            f"INSERT INTO {table_ref}",
            f"({', '.join(self.insert_columns)})",
            f"VALUES {', '.join(self.insert_values)}",
        ]

        # UPSERT clause
        if self.upsert_clause:
            parts.append(self.upsert_clause)

        # RETURNING clause
        if self.returning_parts:
            returning = SQLDialect.get_returning(self.dialect, self.returning_parts)
            if returning:
                parts.append(returning)

        return " ".join(parts), self.parameters

    def build_update(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build an UPDATE statement.

        Returns:
            Tuple of (SQL statement, parameters)
        """

        if not self.update_table or not self.update_sets:
            raise ValueError("UPDATE statement requires table and SET clauses")

        table_ref = self._format_table_reference(
            self.update_table, self.update_database
        )

        parts = [f"UPDATE {table_ref}", f"SET {', '.join(self.update_sets)}"]

        # WHERE clause
        if self.where_parts:
            parts.append(f"WHERE {' AND '.join(self.where_parts)}")

        # RETURNING clause
        if self.returning_parts:
            returning = SQLDialect.get_returning(self.dialect, self.returning_parts)
            if returning:
                parts.append(returning)

        return " ".join(parts), self.parameters

    def build_delete(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build a DELETE statement.

        Returns:
            Tuple of (SQL statement, parameters)
        """

        if not self.delete_table:
            raise ValueError("DELETE statement requires table")

        table_ref = self._format_table_reference(
            self.delete_table, self.delete_database
        )

        parts = [f"DELETE FROM {table_ref}"]

        # WHERE clause
        if self.where_parts:
            parts.append(f"WHERE {' AND '.join(self.where_parts)}")

        # RETURNING clause
        if self.returning_parts:
            returning = SQLDialect.get_returning(self.dialect, self.returning_parts)
            if returning:
                parts.append(returning)

        return " ".join(parts), self.parameters

    # 9. 全文搜索支持
    def full_text_search(
        self, columns: List[str], search_term: str, alias: Optional[str] = None
    ) -> "SQLBuilder":
        """
        添加全文搜索功能

        Args:
            columns: 要搜索的列
            search_term: 搜索词
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        param = self._add_parameter(search_term)

        if self.dialect == "postgresql":
            # PostgreSQL使用tsvector和tsquery
            column_list = " || ' ' || ".join(
                [f"COALESCE({col}, '')" for col in columns]
            )
            expr = (
                f"to_tsvector('simple', {column_list}) @@ to_tsquery('simple', {param})"
            )
            if alias:
                self.select_parts.append(f"{expr} AS {alias}")
            else:
                self.where(expr)
        else:  # MySQL
            # MySQL使用MATCH AGAINST
            column_list = ", ".join(columns)
            expr = f"MATCH({column_list}) AGAINST({param} IN BOOLEAN MODE)"
            if alias:
                self.select_parts.append(f"{expr} AS {alias}")
            else:
                self.where(expr)

        return self

    # 10. 高级连接支持
    def natural_join(
        self, table: str, alias: Optional[str] = None, database: Optional[str] = None
    ) -> "SQLBuilder":
        """
        添加NATURAL JOIN

        Args:
            table: 表名
            alias: 可选的表别名
            database: 可选的数据库名

        Returns:
            Self for method chaining
        """
        table_ref = self._format_table_reference(table, database)
        table_part = f"{table_ref} AS {alias}" if alias else table_ref
        self.join_parts.append(f"NATURAL JOIN {table_part}")
        return self

    def cross_join(
        self, table: str, alias: Optional[str] = None, database: Optional[str] = None
    ) -> "SQLBuilder":
        """
        添加CROSS JOIN

        Args:
            table: 表名
            alias: 可选的表别名
            database: 可选的数据库名

        Returns:
            Self for method chaining
        """
        table_ref = self._format_table_reference(table, database)
        table_part = f"{table_ref} AS {alias}" if alias else table_ref
        self.join_parts.append(f"CROSS JOIN {table_part}")
        return self

    # 11. 分析函数支持
    def add_analytic_function(
        self,
        function: str,
        column: str,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        alias: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加分析函数

        Args:
            function: 分析函数名称 (如 LAG, LEAD, FIRST_VALUE, LAST_VALUE)
            column: 函数应用的列
            partition_by: PARTITION BY 子句的列
            order_by: ORDER BY 子句的配置
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        return self.window(function, column, partition_by, order_by, None, alias)

    def lag(
        self,
        column: str,
        offset: int = 1,
        default_value: Optional[Any] = None,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        alias: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加LAG分析函数

        Args:
            column: 列名
            offset: 偏移量
            default_value: 默认值
            partition_by: PARTITION BY 子句的列
            order_by: ORDER BY 子句的配置
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        function_args = [column, str(offset)]
        if default_value is not None:
            param = self._add_parameter(default_value)
            function_args.append(param)

        function = f"LAG({', '.join(function_args)})"
        return self.add_analytic_function(function, "", partition_by, order_by, alias)

    def lead(
        self,
        column: str,
        offset: int = 1,
        default_value: Optional[Any] = None,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        alias: Optional[str] = None,
    ) -> "SQLBuilder":
        """
        添加LEAD分析函数

        Args:
            column: 列名
            offset: 偏移量
            default_value: 默认值
            partition_by: PARTITION BY 子句的列
            order_by: ORDER BY 子句的配置
            alias: 结果列的别名

        Returns:
            Self for method chaining
        """
        function_args = [column, str(offset)]
        if default_value is not None:
            param = self._add_parameter(default_value)
            function_args.append(param)

        function = f"LEAD({', '.join(function_args)})"
        return self.add_analytic_function(function, "", partition_by, order_by, alias)

    # 12. 动态SQL支持
    def execute_raw(self, sql: str, params: Dict[str, Any] = None) -> "SQLBuilder":
        """
        执行原始SQL

        Args:
            sql: SQL语句
            params: 参数字典

        Returns:
            Self for method chaining
        """
        self.raw_sql = sql
        if params:
            for key, value in params.items():
                self.parameters[key] = value
        return self

    def build_raw(self) -> Tuple[str, Dict[str, Any]]:
        """
        构建原始SQL语句

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if not hasattr(self, "raw_sql"):
            raise ValueError("No raw SQL statement specified")
        return self.raw_sql, self.parameters

    # 13. 高级分组功能
    def rollup(self, *columns: str) -> "SQLBuilder":
        """
        添加ROLLUP分组

        Args:
            *columns: 分组列

        Returns:
            Self for method chaining
        """
        self.group_by_parts = [f"ROLLUP({', '.join(columns)})"]
        return self

    def cube(self, *columns: str) -> "SQLBuilder":
        """
        添加CUBE分组

        Args:
            *columns: 分组列

        Returns:
            Self for method chaining
        """
        if self.dialect == "postgresql":
            self.group_by_parts = [f"CUBE({', '.join(columns)})"]
        else:  # MySQL 8.0+
            self.group_by_parts = [f"WITH ROLLUP"]  # MySQL不直接支持CUBE，使用ROLLUP代替
        return self

    def grouping_sets(self, sets: List[List[str]]) -> "SQLBuilder":
        """
        添加GROUPING SETS

        Args:
            sets: 分组集合列表

        Returns:
            Self for method chaining
        """
        if self.dialect != "postgresql":
            raise ValueError("GROUPING SETS is only supported in PostgreSQL")

        formatted_sets = []
        for s in sets:
            if s:
                formatted_sets.append(f"({', '.join(s)})")
            else:
                formatted_sets.append("()")

        self.group_by_parts = [f"GROUPING SETS({', '.join(formatted_sets)})"]
        return self

    # 14. 表结构操作
    def alter_table(self, table: str) -> "SQLBuilder":
        """
        开始一个ALTER TABLE语句

        Args:
            table: 表名

        Returns:
            Self for method chaining
        """
        self.reset()
        self.alter_table_name = table
        self.alter_operations = []
        return self

    def add_column(
        self, column_name: str, data_type: str, constraints: List[str] = None
    ) -> "SQLBuilder":
        """
        添加列

        Args:
            column_name: 列名
            data_type: 数据类型
            constraints: 约束列表

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "alter_table_name"):
            raise ValueError("Must call alter_table() before add_column()")

        constraint_str = " ".join(constraints) if constraints else ""
        self.alter_operations.append(
            f"ADD COLUMN {column_name} {data_type} {constraint_str}".strip()
        )
        return self

    def drop_column(self, column_name: str) -> "SQLBuilder":
        """
        删除列

        Args:
            column_name: 列名

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "alter_table_name"):
            raise ValueError("Must call alter_table() before drop_column()")

        self.alter_operations.append(f"DROP COLUMN {column_name}")
        return self

    def rename_column(self, old_name: str, new_name: str) -> "SQLBuilder":
        """
        重命名列

        Args:
            old_name: 旧列名
            new_name: 新列名

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "alter_table_name"):
            raise ValueError("Must call alter_table() before rename_column()")

        if self.dialect == "postgresql":
            self.alter_operations.append(f"RENAME COLUMN {old_name} TO {new_name}")
        else:  # MySQL
            self.alter_operations.append(f"CHANGE COLUMN {old_name} {new_name}")
        return self

    def add_constraint(self, constraint_name: str, constraint_def: str) -> "SQLBuilder":
        """
        添加约束

        Args:
            constraint_name: 约束名称
            constraint_def: 约束定义

        Returns:
            Self for method chaining
        """
        if not hasattr(self, "alter_table_name"):
            raise ValueError("Must call alter_table() before add_constraint()")

        self.alter_operations.append(
            f"ADD CONSTRAINT {constraint_name} {constraint_def}"
        )
        return self

    def build_alter_table(self) -> Tuple[str, Dict[str, Any]]:
        """
        构建ALTER TABLE语句

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if not hasattr(self, "alter_table_name") or not self.alter_operations:
            raise ValueError("ALTER TABLE statement requires table name and operations")

        sql = f"ALTER TABLE {self.alter_table_name} {', '.join(self.alter_operations)}"
        return sql, {}

    # 15. 事务支持
    def begin_transaction(self) -> "SQLBuilder":
        """
        开始事务

        Returns:
            Self for method chaining
        """
        self.reset()
        self.transaction_command = "BEGIN"
        return self

    def commit_transaction(self) -> "SQLBuilder":
        """
        提交事务

        Returns:
            Self for method chaining
        """
        self.reset()
        self.transaction_command = "COMMIT"
        return self

    def rollback_transaction(self) -> "SQLBuilder":
        """
        回滚事务

        Returns:
            Self for method chaining
        """
        self.reset()
        self.transaction_command = "ROLLBACK"
        return self

    def savepoint(self, name: str) -> "SQLBuilder":
        """
        创建保存点

        Args:
            name: 保存点名称

        Returns:
            Self for method chaining
        """
        self.reset()
        self.transaction_command = f"SAVEPOINT {name}"
        return self

    def rollback_to_savepoint(self, name: str) -> "SQLBuilder":
        """
        回滚到保存点

        Args:
            name: 保存点名称

        Returns:
            Self for method chaining
        """
        self.reset()
        self.transaction_command = f"ROLLBACK TO SAVEPOINT {name}"
        return self

    def build_transaction(self) -> Tuple[str, Dict[str, Any]]:
        """
        构建事务命令

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if not hasattr(self, "transaction_command"):
            raise ValueError("No transaction command specified")

        return self.transaction_command, {}

    # 16. 数据导入导出
    def copy_from(
        self, table: str, file_path: str, delimiter: str = ",", header: bool = True
    ) -> "SQLBuilder":
        """
        从文件导入数据 (PostgreSQL)

        Args:
            table: 表名
            file_path: 文件路径
            delimiter: 分隔符
            header: 是否有标题行

        Returns:
            Self for method chaining
        """
        if self.dialect != "postgresql":
            raise ValueError("COPY is only supported in PostgreSQL")

        self.reset()
        header_option = "HEADER" if header else ""
        self.copy_command = f"COPY {table} FROM '{file_path}' WITH (FORMAT CSV, DELIMITER '{delimiter}', {header_option})"
        return self

    def copy_to(
        self, table: str, file_path: str, delimiter: str = ",", header: bool = True
    ) -> "SQLBuilder":
        """
        导出数据到文件 (PostgreSQL)

        Args:
            table: 表名
            file_path: 文件路径
            delimiter: 分隔符
            header: 是否有标题行

        Returns:
            Self for method chaining
        """
        if self.dialect != "postgresql":
            raise ValueError("COPY is only supported in PostgreSQL")

        self.reset()
        header_option = "HEADER" if header else ""
        self.copy_command = f"COPY {table} TO '{file_path}' WITH (FORMAT CSV, DELIMITER '{delimiter}', {header_option})"
        return self

    def load_data(
        self,
        table: str,
        file_path: str,
        local: bool = True,
        fields_terminated_by: str = ",",
        lines_terminated_by: str = "\n",
        ignore_lines: int = 0,
    ) -> "SQLBuilder":
        """
        从文件导入数据 (MySQL)

        Args:
            table: 表名
            file_path: 文件路径
            local: 是否是本地文件
            fields_terminated_by: 字段分隔符
            lines_terminated_by: 行分隔符
            ignore_lines: 忽略的行数

        Returns:
            Self for method chaining
        """
        if self.dialect != "mysql":
            raise ValueError("LOAD DATA is only supported in MySQL")

        self.reset()
        local_option = "LOCAL" if local else ""
        ignore_option = f"IGNORE {ignore_lines} LINES" if ignore_lines > 0 else ""

        self.load_data_command = f"""
        LOAD DATA {local_option} INFILE '{file_path}'
        INTO TABLE {table}
        FIELDS TERMINATED BY '{fields_terminated_by}'
        LINES TERMINATED BY '{lines_terminated_by}'
        {ignore_option}
        """
        return self

    def build_copy(self) -> Tuple[str, Dict[str, Any]]:
        """
        构建COPY或LOAD DATA命令

        Returns:
            Tuple of (SQL statement, parameters)
        """
        if hasattr(self, "copy_command"):
            return self.copy_command, {}
        elif hasattr(self, "load_data_command"):
            return self.load_data_command, {}
        else:
            raise ValueError("No COPY or LOAD DATA command specified")

    # 修改build方法以支持所有新功能
    def build(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build a SQL statement based on the current state.

        Returns:
            Tuple of (SQL statement, parameters)
        """
        # 如果有条件组但WHERE子句为空，应用所有条件组
        if self.condition_groups and not self.where_parts:
            self.apply_all_condition_groups()

        if hasattr(self, "raw_sql"):
            return self.build_raw()
        elif hasattr(self, "transaction_command"):
            return self.build_transaction()
        elif hasattr(self, "copy_command") or hasattr(self, "load_data_command"):
            return self.build_copy()
        elif hasattr(self, "alter_table_name"):
            return self.build_alter_table()
        elif self.create_table_name:
            return self.build_create_table()
        elif self.select_parts or self.from_parts:
            return self.build_select()
        elif self.insert_table:
            return self.build_insert()
        elif self.update_table:
            return self.build_update()
        elif self.delete_table:
            return self.build_delete()
        else:
            raise ValueError("No SQL statement type specified")

    def build_from_config(self, config: Dict[str, Any]):
        sql_type = config.get("type", "").lower()

        if sql_type == "select":
            self._build_select_from_config(config)
        elif sql_type == "insert":
            self._build_insert_from_config(config)
        elif sql_type == "update":
            self._build_update_from_config(config)
        elif sql_type == "delete":
            self._build_delete_from_config(config)
        elif sql_type == "create_table":
            self._build_create_table_from_config(config)
        elif sql_type == "alter_table":
            self._build_alter_table_from_config(config)
        elif sql_type == "sql":
            self._build_sql_from_config(config)
        else:
            raise ValueError(f"Unsupported SQL type: {sql_type}")

    # 辅助方法：构建SELECT查询
    def _build_select_from_config(self, config: Dict[str, Any]) -> None:
        """构建SELECT查询"""
        # 处理CTE
        ctes = config.get("ctes", {})
        for name, cte_config in ctes.items():
            if isinstance(cte_config, str):
                # 原始SQL CTE
                self.with_cte(name, cte_config)
            elif isinstance(cte_config, dict) and cte_config.get("recursive", False):
                # 递归CTE
                self.with_recursive(name, cte_config["query"])
            elif isinstance(cte_config, dict) and "query" in cte_config:
                self.with_cte(name, cte_config["query"])

        # 处理列
        columns = config.get("columns", ["*"])
        for col in columns:
            self.select(col)

        # DISTINCT
        if config.get("distinct", False):
            self.distinct()

        # 处理窗口函数
        window_funcs = config.get("window_functions", [])
        for wf in window_funcs:
            function = wf.get("function")
            column = wf.get("column", "")
            partition_by = wf.get("partition_by")
            order_by = wf.get("order_by")
            frame_clause = wf.get("frame")
            alias = wf.get("alias")

            self.window(function, column, partition_by, order_by, frame_clause, alias)

        # 处理JSON提取
        json_extracts = config.get("json_extracts", [])
        for je in json_extracts:
            self.json_extract(je["column"], je["path"], je.get("alias"))

        # 处理表
        table = config.get("table")
        alias = config.get("alias")
        database = config.get("database")

        if table:
            self.from_table(table, alias, database)

        # 处理子查询
        subqueries = config.get("subqueries", {})
        for sq_alias, sq_config in subqueries.items():
            if isinstance(sq_config, dict) and "builder" in sq_config:
                # 已有构建器的子查询
                self.subquery(sq_config["builder"], sq_alias)
            elif isinstance(sq_config, dict) and "sql" in sq_config:
                # 原始SQL子查询
                sub_builder = SQLBuilder(dialect=self.dialect)
                sub_builder.execute_raw(sq_config["sql"])
                self.subquery(sub_builder, sq_alias)

        # 处理连接
        joins = config.get("joins", [])
        for join in joins:
            join_table = join["table"]
            join_condition = join["condition"]
            join_type = join.get("type", "INNER")
            join_alias = join.get("alias")
            join_database = join.get("database")

            self.join(join_table, join_condition, join_type, join_alias, join_database)

        # 处理自然连接
        natural_joins = config.get("natural_joins", [])
        for nj in natural_joins:
            self.natural_join(nj["table"], nj.get("alias"), nj.get("database"))

        # 处理交叉连接
        cross_joins = config.get("cross_joins", [])
        for cj in cross_joins:
            self.cross_join(cj["table"], cj.get("alias"), cj.get("database"))

        # 处理WHERE条件
        where = config.get("where")
        if where:
            self.where(where)

        # 处理JSON条件
        json_conditions = config.get("json_conditions", [])
        for jc in json_conditions:
            self.json_contains(jc["column"], jc["value"], jc.get("path"))

        # 处理全文搜索
        full_text_search = config.get("full_text_search")
        if full_text_search:
            columns = full_text_search["columns"]
            search_term = full_text_search["term"]
            alias = full_text_search.get("alias")

            self.full_text_search(columns, search_term, alias)

        # 处理GROUP BY
        group_by = config.get("group_by", [])
        if group_by:
            for col in group_by:
                self.group_by(col)

        # 处理高级分组
        if "rollup" in config:
            self.rollup(*config["rollup"])
        elif "cube" in config:
            self.cube(*config["cube"])
        elif "grouping_sets" in config:
            self.grouping_sets(config["grouping_sets"])

        # 处理HAVING
        having = config.get("having")
        if having:
            self.having(having)

        # 处理ORDER BY
        order_by = config.get("order_by", [])
        for order in order_by:
            if isinstance(order, dict):
                self.order_by(order["column"], order.get("direction", "ASC"))
            else:
                self.order_by(order)

        # 处理LIMIT和OFFSET
        limit = config.get("limit")
        if limit is not None:
            self.limit(limit)

        offset = config.get("offset")
        if offset is not None:
            self.offset(offset)

    # 辅助方法：构建INSERT查询
    def _build_insert_from_config(self, config: Dict[str, Any]) -> None:
        """构建INSERT查询"""
        table = config["table"]
        columns = config["columns"]
        database = config.get("database")

        self.insert_into(table, columns, database)

        # 处理VALUES
        values = config.get("values", [])
        for row in values:
            self.values(row)

        # 处理UPSERT
        upsert = config.get("upsert")
        if upsert:
            conflict_columns = upsert.get("conflict_columns", [])
            update_columns = upsert.get("update_columns", [])
            self.upsert(conflict_columns, update_columns)

        # 处理RETURNING
        returning = config.get("returning", [])
        if returning:
            for col in returning:
                self.returning(col)

    # 辅助方法：构建UPDATE查询
    def _build_update_from_config(self, config: Dict[str, Any]) -> None:
        """构建UPDATE查询"""
        table = config["table"]
        database = config.get("database")

        self.update(table, database)

        # 处理SET子句
        sets = config["sets"]
        for set_item in sets:
            self.set(set_item["column"], set_item["value"])

        # 处理WHERE条件
        where = config.get("where")
        if where:
            self.where(where)

        # 处理RETURNING
        returning = config.get("returning", [])
        if returning:
            for col in returning:
                self.returning(col)

    # 辅助方法：构建DELETE查询
    def _build_delete_from_config(self, config: Dict[str, Any]) -> None:
        """构建DELETE查询"""
        table = config["table"]
        database = config.get("database")

        self.delete_from(table, database)

        # 处理WHERE条件
        where = config.get("where")
        if where:
            self.where(where)

        # 处理RETURNING
        returning = config.get("returning", [])
        if returning:
            for col in returning:
                self.returning(col)

    # 辅助方法：构建CREATE TABLE语句
    def _build_create_table_from_config(self, config: Dict[str, Any]) -> None:
        """构建CREATE TABLE语句"""
        table = config["table"]
        columns = config["columns"]

        self.create_table(table, columns)

    # 辅助方法：构建ALTER TABLE语句
    def _build_alter_table_from_config(self, config: Dict[str, Any]) -> None:
        """构建ALTER TABLE语句"""
        table = config["table"]

        self.alter_table(table)

        # 处理添加列
        add_columns = config.get("add_columns", [])
        for col in add_columns:
            self.add_column(col["name"], col["type"], col.get("constraints"))

        # 处理删除列
        drop_columns = config.get("drop_columns", [])
        for col in drop_columns:
            self.drop_column(col)

        # 处理重命名列
        rename_columns = config.get("rename_columns", [])
        for rename in rename_columns:
            self.rename_column(rename["old_name"], rename["new_name"])

        # 处理添加约束
        add_constraints = config.get("add_constraints", [])
        for constraint in add_constraints:
            self.add_constraint(constraint["name"], constraint["definition"])

    def _build_sql_from_config(self, config: Dict[str, Any]) -> None:
        """构建SQL语句"""
        sql = config["sql"]
        self.execute_raw(sql)
