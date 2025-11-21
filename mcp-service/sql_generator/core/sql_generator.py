import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from jinja2 import Environment, FileSystemLoader, Template

from .sql_builder import SQLBuilder


class SQLGenerator:
    """
    SQL Generator class that creates SQL statements based on templates and configurations.
    Supports PostgreSQL and MySQL dialects.
    """

    def __init__(self, templates_dir: str, dialect: str = "postgresql"):
        """
        Initialize the SQL generator.

        Args:
            templates_dir: Directory containing SQL template files
            dialect: SQL dialect to use ('postgresql' or 'mysql')
        """
        self.templates_dir = templates_dir
        self.set_dialect(dialect)
        self.sql_builder = SQLBuilder(dialect=dialect)
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )
        self.env.filters["quote_identifier"] = self.quote_identifier

    def set_dialect(self, dialect: str) -> None:
        """Set the SQL dialect to use."""
        if dialect.lower() not in ["postgresql", "mysql"]:
            raise ValueError("Dialect must be either 'postgresql' or 'mysql'")
        self.dialect = dialect.lower()

    def quote_identifier(self, identifier: str) -> str:
        """Quote an identifier according to the current dialect."""
        if self.dialect == "postgresql":
            return f'"{identifier}"'
        else:  # MySQL
            return f"`{identifier}`"

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a SQL template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary with variables to be used in the template

        Returns:
            Rendered SQL statement
        """
        # Add dialect to context
        context["dialect"] = self.dialect

        # Load and render the template
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_template_string(
        self, template_string: str, context: Dict[str, Any]
    ) -> str:
        """
        Render a SQL template string with the given context.

        Args:
            template_string: String containing the template
            context: Dictionary with variables to be used in the template

        Returns:
            Rendered SQL statement
        """
        # Add dialect to context
        context["dialect"] = self.dialect

        # Create and render the template
        template = self.env.from_string(template_string)
        return template.render(**context)

    # 新增方法：直接使用SQLBuilder生成SQL
    def generate_with_builder(self, config: Dict[str, Any]) -> SQLBuilder:
        """
        使用SQLBuilder生成SQL语句

        Args:
            config: 包含SQL配置的字典

        Returns:
            生成的SQL语句
        """
        # 重置构建器
        self.sql_builder.reset()

        # 根据配置构建SQL
        sql_type = config.get("type", "").lower()

        if sql_type == "select":
            self._build_select(self.sql_builder, config)
        elif sql_type == "insert":
            self._build_insert(self.sql_builder, config)
        elif sql_type == "update":
            self._build_update(self.sql_builder, config)
        elif sql_type == "delete":
            self._build_delete(self.sql_builder, config)
        elif sql_type == "create_table":
            self._build_create_table(self.sql_builder, config)
        elif sql_type == "alter_table":
            self._build_alter_table(self.sql_builder, config)
        else:
            raise ValueError(f"Unsupported SQL type: {sql_type}")

        # 构建SQL
        sql, _ = self.sql_builder.build()
        return sql

    # 高级功能：窗口函数
    def generate_window_function(
        self,
        table: str,
        base_columns: List[str],
        window_functions: List[Dict[str, Any]],
        where: Optional[str] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        生成窗口函数查询

        Args:
            table: 表名
            base_columns: 基础列
            window_functions: 窗口函数配置列表
            where: WHERE条件
            order_by: ORDER BY配置

        Returns:
            窗口函数SQL语句
        """
        config = {
            "type": "select",
            "table": table,
            "columns": base_columns,
            "window_functions": window_functions,
        }

        if where:
            config["where"] = where

        if order_by:
            config["order_by"] = order_by

        return self.generate_with_builder(config)

    # 高级功能：JSON查询
    def generate_json_query(
        self,
        table: str,
        base_columns: List[str],
        json_extracts: List[Dict[str, Any]],
        json_conditions: List[Dict[str, Any]] = None,
        where: Optional[str] = None,
    ) -> str:
        """
        生成JSON查询

        Args:
            table: 表名
            base_columns: 基础列
            json_extracts: JSON提取配置
            json_conditions: JSON条件配置
            where: 其他WHERE条件

        Returns:
            JSON查询SQL语句
        """
        config = {
            "type": "select",
            "table": table,
            "columns": base_columns,
            "json_extracts": json_extracts,
        }

        if json_conditions:
            config["json_conditions"] = json_conditions

        if where:
            config["where"] = where

        return self.generate_with_builder(config)

    # 高级功能：子查询和CTE
    def generate_with_subquery(
        self, main_config: Dict[str, Any], subqueries: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        生成带有子查询的SQL

        Args:
            main_config: 主查询配置
            subqueries: 子查询配置字典，键为子查询别名

        Returns:
            带有子查询的SQL语句
        """
        # 创建子查询构建器
        processed_subqueries = {}
        for alias, config in subqueries.items():
            sub_builder = SQLBuilder(dialect=self.dialect)
            self._build_select(sub_builder, config)
            processed_subqueries[alias] = {"builder": sub_builder}

        # 更新主配置中的子查询引用
        if "subqueries" not in main_config:
            main_config["subqueries"] = {}

        main_config["subqueries"].update(processed_subqueries)

        return self.generate_with_builder(main_config)

    # 高级功能：事务支持
    def generate_transaction(
        self, transaction_type: str, savepoint_name: Optional[str] = None
    ) -> str:
        """
        生成事务SQL

        Args:
            transaction_type: 事务类型 ('begin', 'commit', 'rollback', 'savepoint', 'rollback_to_savepoint')
            savepoint_name: 保存点名称（仅用于savepoint和rollback_to_savepoint）

        Returns:
            事务SQL语句
        """
        builder = SQLBuilder(dialect=self.dialect)

        if transaction_type == "begin":
            builder.begin_transaction()
        elif transaction_type == "commit":
            builder.commit_transaction()
        elif transaction_type == "rollback":
            builder.rollback_transaction()
        elif transaction_type == "savepoint" and savepoint_name:
            builder.savepoint(savepoint_name)
        elif transaction_type == "rollback_to_savepoint" and savepoint_name:
            builder.rollback_to_savepoint(savepoint_name)
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        sql, _ = builder.build()
        return sql

    # 高级功能：数据导入导出
    def generate_data_import(
        self,
        table: str,
        file_path: str,
        delimiter: str = ",",
        header: bool = True,
        ignore_lines: int = 0,
    ) -> str:
        """
        生成数据导入SQL

        Args:
            table: 表名
            file_path: 文件路径
            delimiter: 分隔符
            header: 是否有标题行
            ignore_lines: 忽略的行数（仅用于MySQL）

        Returns:
            数据导入SQL语句
        """
        builder = SQLBuilder(dialect=self.dialect)

        if self.dialect == "postgresql":
            builder.copy_from(table, file_path, delimiter, header)
        else:  # MySQL
            builder.load_data(
                table, file_path, True, delimiter, "\n", ignore_lines if header else 0
            )

        sql, _ = builder.build()
        return sql

    def generate_data_export(
        self, table: str, file_path: str, delimiter: str = ",", header: bool = True
    ) -> str:
        """
        生成数据导出SQL（仅PostgreSQL支持）

        Args:
            table: 表名
            file_path: 文件路径
            delimiter: 分隔符
            header: 是否有标题行

        Returns:
            数据导出SQL语句
        """
        if self.dialect != "postgresql":
            raise ValueError("Data export is only supported in PostgreSQL")

        builder = SQLBuilder(dialect=self.dialect)
        builder.copy_to(table, file_path, delimiter, header)

        sql, _ = builder.build()
        return sql

    # 现有方法保持不变
    def generate_select(self, config: Dict[str, Any]) -> str:
        """
        Generate a SELECT statement based on configuration.

        Args:
            config: Dictionary with SELECT configuration

        Returns:
            SQL SELECT statement
        """
        return self.render_template("select.sql.j2", config)

    def generate_insert(self, config: Dict[str, Any]) -> str:
        """
        Generate an INSERT statement based on configuration.

        Args:
            config: Dictionary with INSERT configuration

        Returns:
            SQL INSERT statement
        """
        return self.render_template("insert.sql.j2", config)

    def generate_update(self, config: Dict[str, Any]) -> str:
        """
        Generate an UPDATE statement based on configuration.

        Args:
            config: Dictionary with UPDATE configuration

        Returns:
            SQL UPDATE statement
        """
        return self.render_template("update.sql.j2", config)

    def generate_delete(self, config: Dict[str, Any]) -> str:
        """
        Generate a DELETE statement based on configuration.

        Args:
            config: Dictionary with DELETE configuration

        Returns:
            SQL DELETE statement
        """
        return self.render_template("delete.sql.j2", config)

    def generate_statistics(self, config: Dict[str, Any]) -> str:
        """
        Generate a statistics SQL statement based on configuration.

        Args:
            config: Dictionary with statistics configuration

        Returns:
            SQL statistics statement
        """
        return self.render_template("statistics.sql.j2", config)

    def generate_subquery(self, config: Dict[str, Any]) -> str:
        """
        Generate a subquery SQL statement based on configuration.

        Args:
            config: Dictionary with subquery configuration

        Returns:
            SQL subquery statement
        """
        return self.render_template("subquery.sql.j2", config)

    def generate_from_config(self, config: Dict[str, Any]) -> str:
        """
        Generate a SQL statement based on a complete configuration.

        Args:
            config: Dictionary with SQL configuration including type

        Returns:
            SQL statement
        """
        sql_type = config.get("type", "").lower()

        # 检查是否使用新的基于Builder的方法
        use_builder = config.get("use_builder", False)

        if use_builder:
            return self.generate_with_builder(config)

        # 原有的基于模板的方法
        if sql_type == "select":
            return self.generate_select(config)
        elif sql_type == "insert":
            return self.generate_insert(config)
        elif sql_type == "update":
            return self.generate_update(config)
        elif sql_type == "delete":
            return self.generate_delete(config)
        elif sql_type == "statistics":
            return self.generate_statistics(config)
        elif sql_type == "subquery":
            return self.generate_subquery(config)
        else:
            raise ValueError(f"Unsupported SQL type: {sql_type}")

    # 统计相关方法保持不变
    def generate_count(
        self,
        table: str,
        column: str = "*",
        where: Optional[str] = None,
        distinct: bool = False,
        group_by: Optional[List[str]] = None,
    ) -> str:
        """
        生成COUNT统计查询

        Args:
            table: 表名
            column: 要计数的列名，默认为"*"
            where: WHERE条件
            distinct: 是否使用DISTINCT
            group_by: GROUP BY子句的列

        Returns:
            COUNT统计SQL语句
        """
        config = {
            "table": table,
            "columns": [
                {
                    "expr": f"COUNT({'' if not distinct else 'DISTINCT '}{column})",
                    "alias": "count_result",
                }
            ],
        }

        if where:
            config["where"] = where

        if group_by:
            config["group_by"] = group_by
            config["columns"].extend(group_by)

        return self.generate_statistics(config)

    def generate_sum(
        self,
        table: str,
        column: str,
        where: Optional[str] = None,
        group_by: Optional[List[str]] = None,
    ) -> str:
        """
        生成SUM统计查询

        Args:
            table: 表名
            column: 要求和的列名
            where: WHERE条件
            group_by: GROUP BY子句的列

        Returns:
            SUM统计SQL语句
        """
        config = {
            "table": table,
            "columns": [{"expr": f"SUM({column})", "alias": "sum_result"}],
        }

        if where:
            config["where"] = where

        if group_by:
            config["group_by"] = group_by
            config["columns"].extend(group_by)

        return self.generate_statistics(config)

    def generate_avg(
        self,
        table: str,
        column: str,
        where: Optional[str] = None,
        group_by: Optional[List[str]] = None,
    ) -> str:
        """
        生成AVG统计查询

        Args:
            table: 表名
            column: 要求平均值的列名
            where: WHERE条件
            group_by: GROUP BY子句的列

        Returns:
            AVG统计SQL语句
        """
        config = {
            "table": table,
            "columns": [{"expr": f"AVG({column})", "alias": "avg_result"}],
        }

        if where:
            config["where"] = where

        if group_by:
            config["group_by"] = group_by
            config["columns"].extend(group_by)

        return self.generate_statistics(config)

    def generate_min_max(
        self,
        table: str,
        column: str,
        operation: str = "both",
        where: Optional[str] = None,
        group_by: Optional[List[str]] = None,
    ) -> str:
        """
        生成MIN/MAX统计查询

        Args:
            table: 表名
            column: 要求最小/最大值的列名
            operation: 操作类型，可选值为"min"、"max"或"both"
            where: WHERE条件
            group_by: GROUP BY子句的列

        Returns:
            MIN/MAX统计SQL语句
        """
        config = {"table": table, "columns": []}

        if operation.lower() in ["min", "both"]:
            config["columns"].append({"expr": f"MIN({column})", "alias": "min_result"})

        if operation.lower() in ["max", "both"]:
            config["columns"].append({"expr": f"MAX({column})", "alias": "max_result"})

        if where:
            config["where"] = where

        if group_by:
            config["group_by"] = group_by
            config["columns"].extend(group_by)

        return self.generate_statistics(config)

    def generate_stats_summary(
        self, table: str, column: str, where: Optional[str] = None
    ) -> str:
        """
        生成统计摘要查询，包括COUNT、AVG、SUM、MIN、MAX

        Args:
            table: 表名
            column: 要统计的列名
            where: WHERE条件

        Returns:
            统计摘要SQL语句
        """
        config = {
            "table": table,
            "columns": [
                {"expr": f"COUNT({column})", "alias": "count"},
                {"expr": f"AVG({column})", "alias": "avg"},
                {"expr": f"SUM({column})", "alias": "sum"},
                {"expr": f"MIN({column})", "alias": "min"},
                {"expr": f"MAX({column})", "alias": "max"},
            ],
        }

        if where:
            config["where"] = where

        return self.generate_statistics(config)

    def generate_group_stats(
        self,
        table: str,
        group_columns: List[str],
        stat_columns: List[Dict[str, str]],
        where: Optional[str] = None,
        having: Optional[str] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        生成分组统计查询

        Args:
            table: 表名
            group_columns: 分组列
            stat_columns: 统计列配置，格式为[{"column": "col_name", "function": "SUM|AVG|MIN|MAX|COUNT", "alias": "result_name"}]
            where: WHERE条件
            having: HAVING条件
            order_by: ORDER BY配置
            limit: LIMIT限制

        Returns:
            分组统计SQL语句
        """
        config = {"table": table, "columns": [], "group_by": group_columns}

        # 添加分组列到选择列
        for col in group_columns:
            config["columns"].append(col)

        # 添加统计列
        for stat in stat_columns:
            column = stat["column"]
            func = stat["function"].upper()
            alias = stat.get("alias", f"{func.lower()}_{column}")

            config["columns"].append({"expr": f"{func}({column})", "alias": alias})

        if where:
            config["where"] = where

        if having:
            config["having"] = having

        if order_by:
            config["order_by"] = order_by

        if limit:
            config["limit"] = limit

        return self.generate_statistics(config)

    def generate_pivot_table(
        self,
        table: str,
        row_columns: List[str],
        column_values: List[str],
        pivot_column: str,
        aggregate_column: str,
        aggregate_function: str = "SUM",
        where: Optional[str] = None,
    ) -> str:
        """
        生成数据透视表查询（PostgreSQL实现）

        Args:
            table: 表名
            row_columns: 行标签列
            column_values: 列值列表
            pivot_column: 透视列
            aggregate_column: 聚合列
            aggregate_function: 聚合函数
            where: WHERE条件

        Returns:
            数据透视表SQL语句
        """
        if self.dialect != "postgresql":
            raise ValueError("Pivot tables are currently only supported in PostgreSQL")

        # 构建选择列
        columns = row_columns.copy()

        for val in column_values:
            columns.append(
                {
                    "expr": f"{aggregate_function}(CASE WHEN {pivot_column} = '{val}' THEN {aggregate_column} ELSE 0 END)",
                    "alias": f"{val}",
                }
            )

        config = {"table": table, "columns": columns, "group_by": row_columns}

        if where:
            config["where"] = where

        return self.generate_statistics(config)
