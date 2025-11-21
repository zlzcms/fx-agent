#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Tuple, Union

from core.config import settings
from core.log import logger
from core.sql_config import SQL_TABLES, VALID_OPERATORS
from utils.date import get_start_and_end_time


class SQLGenerator:
    def __init__(self, table_key: str, conditions_link: str = "AND"):
        """
        初始化SQL生成器
        :param table_key: SQL_TABLES中的表键名
        :param conditions_link: 条件连接符（AND/OR）
        """
        if not table_key:
            raise ValueError("表键名不能为空")

        if table_key not in SQL_TABLES:
            raise ValueError(f"表 {table_key} 不存在于配置中")

        self.table_config = SQL_TABLES[table_key]
        self.database = self.table_config["database_name"]
        self.table_name = self.table_config["table_name"]
        self.fields = self.table_config["fields"].copy()
        self.link_fields: List[Dict[str, str]] = []
        self.conditions: List[str] = []
        self.conditions_link = conditions_link
        self.params: List[Any] = []
        self.join_clauses: List[str] = []
        self.order_by = ""
        self.limit_clause = ""

    def add_join_table(
        self,
        table_key: str,
        main_field: str,
        join_field: str,
        join_type: str = "LEFT JOIN",
        table_alias: Optional[str] = None,
    ) -> "SQLGenerator":
        """
        通过SQL_TABLES的key添加关联表
        :param table_key: SQL_TABLES中的表键名
        :param main_field: 主表关联字段
        :param join_field: 关联表关联字段
        :param join_type: JOIN类型
        :param table_alias: 表别名
        :return: self，支持链式调用
        """
        if table_key not in SQL_TABLES:
            raise ValueError(f"表 {table_key} 不存在于配置中")

        join_table_config = SQL_TABLES[table_key]
        join_table_name = join_table_config["table_name"]
        join_database = join_table_config["database_name"]
        join_fields = join_table_config["fields"]

        # 构建ON条件
        on_condition = f"{self.table_name}.{main_field} = "
        if table_alias:
            on_condition += f"{table_alias}.{join_field}"
        else:
            on_condition += f"{join_table_name}.{join_field}"

        # 添加JOIN
        self.add_join(
            join_table_name,
            on_condition,
            join_type=join_type,
            fields=join_fields,
            table_alias=table_alias,
            database_name=join_database,
        )

        return self

    def add_join(
        self,
        table_name: str,
        on_condition: str,
        join_type: str = "LEFT JOIN",
        fields: Optional[List[str]] = None,
        table_alias: Optional[str] = None,
        database_name: Optional[str] = None,
    ) -> "SQLGenerator":
        """
        添加JOIN子句
        :param table_name: 要关联的表名
        :param on_condition: ON条件（例如："t1.id = t2.t1_id"）
        :param join_type: JOIN类型（LEFT JOIN, RIGHT JOIN, INNER JOIN等）
        :param fields: 要选择的字段列表
        :param table_alias: 表别名
        :param database_name: 数据库名，默认使用主表的数据库
        :return: self，支持链式调用
        """
        # 验证JOIN类型
        join_type = join_type.upper()
        valid_join_types = [
            "LEFT JOIN",
            "RIGHT JOIN",
            "INNER JOIN",
            "JOIN",
            "FULL JOIN",
            "CROSS JOIN",
        ]
        if join_type not in valid_join_types:
            raise ValueError(
                f"无效的JOIN类型: {join_type}，有效类型: {', '.join(valid_join_types)}"
            )

        # 使用主表数据库或指定的数据库
        db_name = database_name if database_name else self.database

        # 构建表引用
        table_ref = f"{db_name}.{table_name}"
        display_name = table_alias if table_alias else table_name

        # 添加别名（如果有）
        if table_alias:
            table_ref = f"{table_ref} AS {table_alias}"

        # 构建JOIN子句
        join_clause = f" {join_type} {table_ref} ON {on_condition}"
        self.join_clauses.append(join_clause)

        # 如果提供了字段列表，添加到link_fields
        if fields:
            for field in fields:
                self.link_fields.append(
                    {"table": display_name, "field": field, "table_alias": table_alias}
                )

        return self

    def add_condition(
        self,
        field: str,
        operator: str,
        value: Any = None,
        table_name: Optional[str] = None,
        subquery_link_field: Optional[str] = None,
    ):
        """
        添加查询条件
        :param field: 字段名
        :param operator: 操作符，必须在VALID_OPERATORS中
        :param value: 值
        :param table_name: 表名，用于处理联立查询中的字段歧义
        :return: self，支持链式调用
        """
        operator = operator.upper()
        if operator not in VALID_OPERATORS:
            raise ValueError(f"无效的操作符: {operator}")

        # 验证字段是否在配置中，除非是EXISTS/NOT EXISTS操作符
        if field is not None:
            field_found = False
            if field in self.table_config["fields"]:
                field_found = True

            else:
                for link_field in self.link_fields:
                    if field == link_field["field"]:
                        field_found = True
                        break

            if not field_found:
                raise ValueError(f"字段 {field} 不在表配置中")

        # 如果指定了表名，添加表名前缀
        qualified_field = field
        if field is not None:  # 对于EXISTS/NOT EXISTS，field可能为None
            if table_name:
                qualified_field = f"{table_name}.{field}"
            elif (
                self.join_clauses
                and not operator.startswith("EXISTS")
                and not operator.startswith("NOT EXISTS")
            ):
                qualified_field = f"{self.table_name}.{field}"

        # 处理不同类型的操作符
        if operator in ("IS NULL", "IS NOT NULL"):
            self.conditions.append(f"{qualified_field} {operator}")
        elif operator == "BETWEEN":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("BETWEEN操作符需要两个值")
            self.conditions.append(f"{qualified_field} BETWEEN %s AND %s")
            self.params.extend(value)
        elif operator == "IN" or operator == "NOT IN":
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"{operator}操作符需要一个列表或元组")
            placeholders = ", ".join(["%s"] * len(value))
            self.conditions.append(f"{qualified_field} {operator} ({placeholders})")
            self.params.extend(value)
        elif operator in ("EXISTS", "NOT EXISTS"):
            if not subquery_link_field:
                raise ValueError("EXISTS/NOT EXISTS操作符需要指定子查询链接字段")

            # 子查询必须是SQLGenerator实例或已生成的SQL字符串
            if isinstance(value, SQLGenerator):
                if subquery_link_field not in value.fields:
                    raise ValueError(f"子查询链接字段 {subquery_link_field} 不在子查询表中")
                value.add_raw_condition(f"{subquery_link_field} = {qualified_field}")
                subquery_sql, subquery_params = value.generate_select()
                # 修复：保留完整的子查询，包括WHERE子句

                self.conditions.append(f"{operator} ({subquery_sql})")
                self.params.extend(subquery_params)
            elif isinstance(value, str):
                self.conditions.append(f"{operator} ({value})")
            else:
                raise ValueError(f"{operator}操作符需要一个子查询")
        elif operator in ("IN SUBQUERY", "NOT IN SUBQUERY"):
            # 处理子查询IN操作
            real_operator = "IN" if operator == "IN SUBQUERY" else "NOT IN"
            if not subquery_link_field:
                raise ValueError("IN SUBQUERY/NOT IN SUBQUERY操作符需要指定子查询链接字段")
            if isinstance(value, SQLGenerator):
                if subquery_link_field not in value.fields:
                    raise ValueError(f"子查询链接字段 {subquery_link_field} 不在子查询表中")
                if isinstance(subquery_link_field, str):
                    subquery_link_field = [subquery_link_field]
                subquery_sql, subquery_params = value.generate_select(
                    selected_fields=subquery_link_field
                )
                # 修复：确保表名前缀正确
                self.conditions.append(
                    f"{qualified_field} {real_operator} ({subquery_sql})"
                )
                self.params.extend(subquery_params)
            elif isinstance(value, str):
                self.conditions.append(f"{qualified_field} {real_operator} ({value})")
            else:
                raise ValueError(f"{operator}操作符需要一个子查询")
        else:
            self.conditions.append(f"{qualified_field} {operator} %s")
            self.params.append(value)

        return self

    def add_subquery_condition(
        self,
        field: str,
        operator: str,
        subquery: Union["SQLGenerator", str],
        table_name: Optional[str] = None,
        subquery_link_field: Optional[str] = None,
    ) -> "SQLGenerator":
        """
        添加子查询条件
        :param field: 字段名
        :param operator: 操作符，例如 IN, NOT IN, =, >, <, 等
        :param subquery: 子查询，可以是SQLGenerator实例或SQL字符串
        :param table_name: 表名，用于处理联立查询中的字段歧义
        :return: self，支持链式调用
        """
        operator = operator.upper()

        # 如果指定了表名，添加表名前缀
        qualified_field = field
        if table_name:
            qualified_field = f"{table_name}.{field}"
        elif self.join_clauses:
            qualified_field = f"{self.table_name}.{field}"

        # 处理子查询
        if isinstance(subquery, SQLGenerator):
            if not subquery_link_field:
                raise ValueError("IN SUBQUERY/NOT IN SUBQUERY操作符需要指定子查询链接字段")
            if isinstance(subquery_link_field, str):
                subquery_link_field = [subquery_link_field]
            subquery_sql, subquery_params = subquery.generate_select(
                selected_fields=subquery_link_field
            )
            # 修复：确保表名前缀正确
            self.conditions.append(f"{qualified_field} {operator} ({subquery_sql})")
            self.params.extend(subquery_params)
        elif isinstance(subquery, str):
            self.conditions.append(f"{qualified_field} {operator} ({subquery})")
        else:
            raise ValueError("子查询必须是SQLGenerator实例或SQL字符串")

        return self

    def add_raw_condition(self, condition: str, *params: Any) -> "SQLGenerator":
        """
        添加原始SQL条件
        :param condition: 原始SQL条件字符串
        :param params: 条件参数
        :return: self，支持链式调用
        """
        self.conditions.append(condition)
        if params:
            self.params.extend(params)
        return self

    def order_by_clause(
        self, field: str, direction: str = "ASC", table_name: Optional[str] = None
    ) -> "SQLGenerator":
        """
        添加排序
        :param field: 排序字段
        :param direction: 排序方向（ASC或DESC）
        :param table_name: 表名，用于处理联立查询中的字段歧义
        :return: self，支持链式调用
        """
        direction = direction.upper()
        if direction not in ("ASC", "DESC"):
            raise ValueError("排序方向必须是'ASC'或'DESC'")

        qualified_field = field
        if table_name:
            qualified_field = f"{table_name}.{field}"
        elif self.join_clauses:
            qualified_field = f"{self.table_name}.{field}"

        self.order_by = f" ORDER BY {qualified_field} {direction}"
        return self

    def limit(self, limit: int, offset: int = 0) -> "SQLGenerator":
        """
        添加LIMIT子句
        :param limit: 限制记录数
        :param offset: 偏移量
        :return: self，支持链式调用
        """
        if limit < 0:
            raise ValueError("限制记录数不能为负数")
        if offset < 0:
            raise ValueError("偏移量不能为负数")
        self.limit_clause = f" LIMIT {offset}, {limit}"
        return self

    def generate_select(
        self, selected_fields: Optional[List[str]] = None
    ) -> Tuple[str, List[Any]]:
        """
        生成SELECT语句
        :param selected_fields: 要选择的字段列表，None表示全部字段
        :return: (SQL语句, 参数列表)
        """
        # 如果没有指定字段，使用全部字段
        if not selected_fields:
            fields = []

            # 添加主表字段
            for field in self.fields:
                fields.append(f"{self.table_name}.{field}")

            # 添加关联表字段
            for link_field in self.link_fields:
                table = link_field["table"]
                field = link_field["field"]
                table_alias = link_field.get("table_alias", "link")
                fields.append(f"{table}.{field} AS {table_alias}_{field}")

            fields_str = ", ".join(fields)
        else:
            fields_str = ", ".join(selected_fields)

        # 合并所有JOIN子句
        join_clause = "".join(self.join_clauses)

        sql = f"SELECT {fields_str} FROM {self.database}.{self.table_name}{join_clause}"

        # 添加WHERE子句
        if self.conditions:
            sql += " WHERE " + f" {self.conditions_link} ".join(self.conditions)

        # 添加ORDER BY和LIMIT子句
        sql += self.order_by + self.limit_clause

        return sql, self.params

    def generate_count(self) -> Tuple[str, List[Any]]:
        """
        生成COUNT语句
        :return: (SQL语句, 参数列表)
        """
        # 合并所有JOIN子句
        join_clause = "".join(self.join_clauses)

        sql = f"SELECT COUNT(*) FROM {self.database}.{self.table_name}{join_clause}"

        # 添加WHERE子句
        if self.conditions:
            sql += " WHERE " + f" {self.conditions_link} ".join(self.conditions)

        return sql, self.params

    def as_subquery(self, alias: Optional[str] = None) -> Tuple[str, List[Any]]:
        """
        将当前查询作为子查询返回
        :param alias: 子查询的别名
        :return: (SQL子查询字符串, 参数列表)
        """
        sql, params = self.generate_select()
        if alias:
            sql = f"({sql}) AS {alias}"
        else:
            sql = f"({sql})"
        return sql, params

    def generate_sql(
        self,
        parameters: Dict[str, Any],
        time_field: str = "create_time",
        isstrptime: bool = False,
        order_by: Optional[Tuple[str, str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        生成完整的SQL查询语句
        :param parameters: 查询参数字典
        :param time_field: 时间字段名
        :param isstrptime: 是否需要转换时间格式
        :param order_by: 排序字段和方向的元组 (field, direction)
        :return: (SQL语句, 参数列表)
        """
        # 处理时间范围条件
        start_time, end_time = get_start_and_end_time(parameters, isstrptime)
        # print("====start_time, end_time====== ", start_time, end_time)
        if start_time and time_field:
            self.add_condition(time_field, ">=", start_time)
        if end_time and time_field:
            self.add_condition(time_field, "<=", end_time)

        # 处理排序
        if order_by:
            self.order_by_clause(*order_by)

        # 处理限制条数
        parameters_limit = parameters.get("limit")
        if parameters_limit is not None:
            if parameters_limit == 0:
                raise ValueError("limit参数不能为0，请指定一个大于0的数值或不传该参数使用默认限制")
            elif parameters_limit > 0:
                self.limit(int(parameters_limit))
            else:
                raise ValueError(f"limit参数必须是正整数，当前值: {parameters_limit}")
        else:
            self.limit(settings.DEFAULT_LIMIT)
        return self.generate_select()
