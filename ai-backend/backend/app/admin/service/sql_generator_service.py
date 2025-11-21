# -*- coding: utf-8 -*-
# @Author: claude-4-sonnet
# @Date:   2025-06-27 10:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

from typing import List, Optional, Set, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.sql_generator import (
    ConditionField,
    DataSourceLinkRequest,
    SqlGenerateRequest,
    SqlGenerateResponse,
    TableDataSource,
)
from backend.common.enums import RiskType


class SQLGeneratorService:
    """SQL生成服务"""

    # 合法的SQL操作符集合
    VALID_OPERATORS = {
        "=",
        ">",
        "<",
        ">=",
        "<=",
        "<>",
        "!=",
        "LIKE",
        "IN",
        "NOT IN",
        "IS NULL",
        "IS NOT NULL",
        "BETWEEN",
        "AND",
        "OR",
        "NOT",
        "(",
        ")",
    }

    async def generate_sql(self, db: AsyncSession, request: SqlGenerateRequest) -> SqlGenerateResponse:
        """
        生成SQL查询

        Args:
            db: 数据库会话
            request: SQL生成请求

        Returns:
            SQL生成响应
        """
        database_name = request.database_name
        tables = request.tables
        condition = request.condition
        order_by = request.order_by
        order_direction = request.order_direction or "DESC"
        try:
            # 确保每个表的relation_field都在selected_field_names中
            for table in tables:
                if (
                    table.relation_field
                    and table.relation_field not in table.selected_field_names
                    and len(table.selected_field_names) > 0
                ):
                    table.selected_field_names.append(table.relation_field)

            # 确保dataSourcesLinkField的来源字段在selected_field_names中
            if hasattr(request, "dataSourcesLinkField") and request.dataSourcesLinkField:
                from_field = request.dataSourcesLinkField.fromField
                from_table = request.dataSourcesLinkField.fromTable

                for table in tables:
                    if (
                        table.table_name == from_table
                        and from_field not in table.selected_field_names
                        and len(table.selected_field_names) > 0
                    ):
                        table.selected_field_names.append(from_field)

            # 处理条件
            condition_str = None
            if condition:
                if isinstance(condition, str):
                    # 字符串格式的条件
                    condition_str = self._validate_condition(condition, tables)
                elif isinstance(condition, ConditionField):
                    # ConditionField对象格式的条件
                    condition_str = self._process_condition_field(condition, tables)
                elif isinstance(condition, list[ConditionField]):
                    # 列表格式的条件
                    condition_str = self._process_condition_list(condition, tables)
                else:
                    raise ValueError(f"不支持的条件格式: {type(condition)}")

            # 处理数据权限条件
            permission_condition = self._build_data_permission_condition(request)

            # 处理时间范围条件
            time_range_condition = self._build_time_range_condition(request)

            # 合并所有条件
            all_conditions = []
            if condition_str:
                all_conditions.append(condition_str)
            if permission_condition:
                all_conditions.append(permission_condition)
            if time_range_condition:
                all_conditions.append(time_range_condition)

            # 组合条件
            combined_condition = None
            if all_conditions:
                combined_condition = " AND ".join([f"({cond})" for cond in all_conditions])

            # 如果只有一个表，生成简单查询
            if len(tables) == 1:
                sql = self._generate_single_table_query(
                    database_name, tables[0], combined_condition, order_by, order_direction
                )
                description = f"查询 {database_name}.{tables[0].table_name} 表数据"
            else:
                # 多表查询需要关联字段
                sql = self._generate_multi_table_query(
                    database_name, tables, combined_condition, order_by, order_direction
                )
                table_names = ", ".join([t.table_name for t in tables])
                description = f"关联查询 {database_name} 中的 {table_names} 表数据"

            return SqlGenerateResponse(sql=sql, description=description)
        except Exception:
            return SqlGenerateResponse(sql="", description="生成SQL请求失败")

    def _build_data_permission_condition(self, request: SqlGenerateRequest) -> Optional[str]:
        """
        构建数据权限条件

        根据数据权限类型和值构建SQL条件

        Args:
            request: SQL生成请求

        Returns:
            SQL条件字符串，如果没有数据权限则返回None
        """
        if not hasattr(request, "data_permission") or not request.data_permission:
            return None

        if not hasattr(request, "data_permission_values") or not request.data_permission_values:
            return None

        # 将data_permission_values转换为字符串列表
        user_ids = [str(user_id) for user_id in request.data_permission_values]
        if not user_ids:
            return None

        # 根据不同的权限类型构建条件
        if (
            request.data_permission == RiskType.ALL_EMPLOYEE
            or request.data_permission == RiskType.AGENT_USER
            or request.data_permission == RiskType.CRM_USER
        ):
            # 找到主表（第一个表）
            if not request.tables:
                return None

            # 假设主表中有user_id或member_id字段
            table = request.tables[0]
            table_alias = "t1" if len(request.tables) > 1 else table.table_name

            # 检查表中是否有user_id或member_id字段
            user_id_field = None
            for field in ["user_id", "member_id", "id"]:
                if field in table.selected_field_names:
                    user_id_field = field
                    break

            if not user_id_field:
                return None

            # 构建IN条件
            return f"`{table_alias}`.`{user_id_field}` IN ({','.join(user_ids)})"

        return None

    def _build_time_range_condition(self, request: SqlGenerateRequest) -> Optional[str]:
        """
        构建时间范围条件

        根据时间范围类型和值构建SQL条件

        Args:
            request: SQL生成请求

        Returns:
            SQL条件字符串，如果没有时间范围则返回None
        """
        if not hasattr(request, "data_time_range_type") or not request.data_time_range_type:
            return None

        if not hasattr(request, "data_time_value") or not request.data_time_value:
            return None

        # 找到主表（第一个表）
        if not request.tables:
            return None

        table = request.tables[0]
        table_alias = "t1" if len(request.tables) > 1 else table.table_name

        # 检查表中是否有create_time或create_at字段
        time_field = None
        for field in ["create_time", "create_at", "created_at", "created_time"]:
            if field in table.selected_field_names:
                time_field = field
                break

        if not time_field:
            return None

        # 根据时间范围类型构建条件
        time_value = int(request.data_time_value)
        if request.data_time_range_type == "day":
            return f"`{table_alias}`.`{time_field}` >= DATE_SUB(NOW(), INTERVAL {time_value} DAY)"
        elif request.data_time_range_type == "month":
            return f"`{table_alias}`.`{time_field}` >= DATE_SUB(NOW(), INTERVAL {time_value} MONTH)"
        elif request.data_time_range_type == "quarter":
            return f"`{table_alias}`.`{time_field}` >= DATE_SUB(NOW(), INTERVAL {time_value * 3} MONTH)"
        elif request.data_time_range_type == "year":
            return f"`{table_alias}`.`{time_field}` >= DATE_SUB(NOW(), INTERVAL {time_value} YEAR)"

        return None

    def ensure_data_source_link_fields(self, request: DataSourceLinkRequest) -> None:
        """
        确保数据源链接字段在selected_field_names中

        Args:
            request: 数据源链接请求
        """
        if not request.dataSourcesLinkField or not request.selectedTables:
            return

        from_field = request.dataSourcesLinkField.fromField
        from_table = request.dataSourcesLinkField.fromTable

        # 查找匹配的表并确保fromField在selected_field_names中
        for table in request.selectedTables:
            if table.table_name == from_table and from_field not in table.selected_field_names:
                table.selected_field_names.append(from_field)

    def _get_all_valid_field_names(self, tables: List[TableDataSource]) -> Set[str]:
        """获取所有表中的有效字段名"""
        valid_fields = set()
        for table in tables:
            valid_fields.update(table.selected_field_names)
        return valid_fields

    def _validate_condition(self, condition: str, tables: List[TableDataSource]) -> str:
        """
        验证WHERE条件，防止SQL注入

        Args:
            condition: WHERE条件
            tables: 表数据源列表

        Returns:
            安全的WHERE条件
        """
        if not condition or condition.strip() == "":
            return ""

        # 获取所有有效字段名
        valid_fields = self._get_all_valid_field_names(tables)

        # 分割条件为词法单元
        tokens = re.findall(r"[\w.]+|\S", condition)

        # 处理每个词法单元
        for i, token in enumerate(tokens):
            # 检查是否是字段名
            if (
                token.lower() not in [op.lower() for op in self.VALID_OPERATORS]
                and not token.startswith("'")
                and not token.endswith("'")
                and not token.startswith('"')
                and not token.endswith('"')
                and not token.isdigit()
                and not re.match(r"^-?\d+(\.\d+)?$", token)
            ):
                # 如果不在有效字段列表中，可能是不安全的
                if token not in valid_fields and "." not in token:
                    # 将可疑字段替换为安全占位符
                    tokens[i] = "1=0"  # 使条件永远为假

        # 重建条件
        return " ".join(tokens)

    def _process_condition_field(self, condition: ConditionField, tables: List[TableDataSource]) -> str:
        """
        处理ConditionField对象格式的条件

        Args:
            condition: 条件字段对象
            tables: 表数据源列表

        Returns:
            处理后的SQL条件字符串
        """
        # 确保条件字段在selected_field_names中
        from_field = condition.fromField
        from_table = condition.fromTable

        # 查找表别名（用于多表查询）
        table_alias = None
        for i, table in enumerate(tables, 1):
            if table.table_name == from_table:
                if len(tables) > 1:
                    table_alias = f"t{i}"
                if from_field not in table.selected_field_names and len(table.selected_field_names) > 0:
                    table.selected_field_names.append(from_field)
                break

        # 构建条件字符串
        field_ref = f"`{from_table}`.`{from_field}`" if table_alias is None else f"`{table_alias}`.`{from_field}`"

        # 根据值类型和操作符生成条件
        value = condition.value
        operator = condition.operator.upper()

        if operator in ("IS NULL", "IS NOT NULL"):
            return f"{field_ref} {operator}"

        if isinstance(value, str):
            # 字符串值需要加引号
            value_str = f"'{value}'"
        elif isinstance(value, (list, tuple)):
            # 列表值用于IN操作符
            if operator not in ("IN", "NOT IN"):
                operator = "IN"
            value_items = []
            for item in value:
                if isinstance(item, str):
                    value_items.append(f"'{item}'")
                else:
                    value_items.append(str(item))
            value_str = f"({', '.join(value_items)})"
        else:
            # 数字或其他类型
            value_str = str(value)

        return f"{field_ref} {operator} {value_str}"

    def _process_condition_list(self, condition: List[ConditionField], tables: List[TableDataSource]) -> str:
        """
        处理列表格式的条件

        Args:
            condition: 条件列表
            tables: 表数据源列表

        Returns:
            处理后的SQL条件字符串
        """
        if not condition:
            return ""

        # 处理每个条件并用 AND 连接
        condition_parts = []
        for cond in condition:
            condition_part = self._process_condition_field(cond, tables)
            if condition_part:
                condition_parts.append(condition_part)

        if not condition_parts:
            return ""

        # 用括号包裹条件组
        return "(" + " AND ".join(condition_parts) + ")"

    def _generate_single_table_query(
        self,
        database_name: str,
        table: TableDataSource,
        condition: Optional[str],
        order_by: Optional[str],
        order_direction: str,
    ) -> str:
        """生成单表查询SQL"""
        # 使用选定的字段而不是 SELECT *
        if table.selected_field_names and len(table.selected_field_names) > 0:
            fields = ", ".join([f"`{field}`" for field in table.selected_field_names])
            sql = f"SELECT {fields} FROM `{database_name}`.`{table.table_name}`"
        else:
            # 如果没有选定字段，则使用 SELECT *
            sql = f"SELECT * FROM `{database_name}`.`{table.table_name}`"

        # 添加条件
        if condition:
            sql += f" WHERE {condition}"

        # 添加排序
        if order_by:
            sql += f" ORDER BY {order_by} {order_direction}"

        return sql

    def _detect_table_relationships(self, tables: List[TableDataSource]) -> List[Tuple[str, str, str, str]]:
        """
        检测表之间的关系

        返回形式为 (table1, field1, table2, field2) 的列表，表示 table1.field1 = table2.field2
        """
        relationships = []

        # 主表
        main_table = tables[0]
        main_relation_field = main_table.relation_field or "id"

        for table in tables[1:]:
            # 如果表指定了关联字段，优先使用
            if table.relation_field:
                relationships.append(
                    (
                        main_table.table_name,
                        main_relation_field,
                        table.table_name,
                        table.relation_field,
                    )
                )
                continue

            # 1. 检查是否有 main_table_id 形式的字段
            relation_field = f"{main_table.table_name}_id"
            if relation_field in table.selected_field_names:
                relationships.append((main_table.table_name, main_relation_field, table.table_name, relation_field))
                continue

            # 2. 检查是否有 id 字段和 main_table 中有 table_id 字段
            relation_field = f"{table.table_name}_id"
            if relation_field in main_table.selected_field_names:
                relationships.append((main_table.table_name, relation_field, table.table_name, "id"))
                continue

            # 3. 如果表名是单数形式，尝试复数形式
            if main_table.table_name.endswith("s"):
                # 去掉s的表名
                singular_name = main_table.table_name[:-1]
                relation_field = f"{singular_name}_id"
                if relation_field in table.selected_field_names:
                    relationships.append((main_table.table_name, main_relation_field, table.table_name, relation_field))
                    continue

            # 4. 默认关系: 主表id与其他表的member_id
            if "member_id" in table.selected_field_names:
                relationships.append((main_table.table_name, main_relation_field, table.table_name, "member_id"))
            else:
                # 无法确定关系，使用id字段
                relationships.append((main_table.table_name, main_relation_field, table.table_name, "id"))

        return relationships

    def _generate_multi_table_query(
        self,
        database_name: str,
        tables: List[TableDataSource],
        condition: Optional[str],
        order_by: Optional[str],
        order_direction: str,
    ) -> str:
        """生成多表关联查询SQL"""
        # 主表
        main_table = tables[0]

        # 构建字段列表，使用表别名前缀
        select_fields = []
        for i, table in enumerate(tables, 1):
            table_alias = f"t{i}"
            for field in table.selected_field_names:
                select_fields.append(f"`{table_alias}`.`{field}`")

        # 构建基本查询
        sql = f"SELECT {', '.join(select_fields)} FROM `{database_name}`.`{main_table.table_name}` AS t1"

        # 添加JOIN语句
        for i, table in enumerate(tables[1:], 2):
            # 获取关联字段
            main_relation_field = main_table.relation_field or "id"
            relation_field = table.relation_field or "id"

            # 添加JOIN
            sql += (
                f" LEFT JOIN `{database_name}`.`{table.table_name}` AS t{i} "
                f"ON `t1`.`{main_relation_field}` = `t{i}`.`{relation_field}`"
            )

        # 添加条件
        if condition:
            sql += f" WHERE {condition}"

        # 添加排序
        if order_by:
            sql += f" ORDER BY {order_by} {order_direction}"

        return sql


sql_generator_service = SQLGeneratorService()
