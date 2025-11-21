# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-12 15:50:43
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-01 20:52:47
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

from typing import Dict, List, Optional

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.app.admin.crud.crud_database_metadata import crud_database_metadata
from backend.app.admin.schema.database_metadata import (
    BatchUpdateDescriptionsRequest,
    BatchUpdateDescriptionsResponse,
    DatabaseTreeNode,
    DatabaseTreeNodeCreate,
    FieldMetadata,
    RefreshDatabaseRequest,
    RefreshDatabaseResponse,
    SqlAnalysisResponse,
    TableMetadata,
)
from backend.app.admin.schema.sql_generator import (
    DataSourceLinkRequest,
    DataSourceLinkResponse,
)
from backend.core.conf import settings


class DatabaseMetadataService:
    """数据库元数据服务"""

    @staticmethod
    def _generate_id(type_name: str, name: str, parent_name: Optional[str] = None) -> str:
        """生成元数据ID"""
        if type_name == "database":
            return f"db_{name}"
        elif type_name == "table":
            return f"table_{parent_name}_{name}"
        elif type_name == "field":
            # parent_name 格式为 table_database_tablename
            return f"field_{parent_name}_{name}"
        else:
            return f"{type_name}_{name}"

    @staticmethod
    def _format_table_size(size_bytes: Optional[int]) -> Optional[str]:
        """格式化表大小"""
        if size_bytes is None:
            return None

        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"

    @staticmethod
    def _clean_string_value(value: str) -> str:
        """清理字符串值，移除无效的UTF-8字符和空字节"""
        if value is None:
            return None

        # 移除空字节和其他控制字符
        cleaned = value.replace("\x00", "").replace("\r", "").replace("\n", " ")

        # 尝试编码/解码以确保UTF-8兼容性
        try:
            cleaned = cleaned.encode("utf-8", errors="ignore").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            cleaned = ""

        # 限制长度以避免数据库字段溢出
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000] + "..."

        return cleaned if cleaned.strip() else None

    def _create_mysql_url(self, database_name: Optional[str] = None) -> URL:
        """创建MySQL连接URL"""
        return URL.create(
            drivername="mysql+asyncmy",
            username=settings.DATABASE_WAREHOUSE_USER,
            password=settings.DATABASE_WAREHOUSE_PASSWORD,
            host=settings.DATABASE_WAREHOUSE_HOST,
            port=settings.DATABASE_WAREHOUSE_PORT,
            database=database_name,
            query={"charset": settings.DATABASE_WAREHOUSE_CHARSET},
        )

    async def get_database_tree(
        self,
        db: AsyncSession,
        *,
        database_name: Optional[str] = None,
        include_tables: bool = True,
        include_fields: bool = True,
    ) -> List[DatabaseTreeNode]:
        """获取数据库树形结构"""
        records = await crud_database_metadata.get_tree_structure(
            db, database_name=database_name, include_tables=include_tables, include_fields=include_fields
        )

        return [
            DatabaseTreeNode(
                id=record.metadata_id,
                name=record.name,
                type=record.type,
                description=record.description,
                parent_id=record.parent_id,
                field_type=record.field_type,
                is_nullable=record.is_nullable,
                default_value=record.default_value,
                table_rows=record.table_rows,
                table_size=record.table_size,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    async def get_databases(self, db: AsyncSession) -> List[str]:
        """获取数据库列表"""
        records = await crud_database_metadata.get_databases(db)
        return [
            {"id": record.metadata_id, "name": record.name, "description": record.description} for record in records
        ]

    async def get_tables_with_fields(self, db: AsyncSession, *, database_name: str) -> List[DatabaseTreeNode]:
        """获取指定数据库的表和字段信息"""
        records = await crud_database_metadata.get_tables_with_fields(db, database_name=database_name)

        return [
            DatabaseTreeNode(
                id=record.metadata_id,
                name=record.name,
                type=record.type,
                description=record.description,
                parent_id=record.parent_id,
                field_type=record.field_type,
                is_nullable=record.is_nullable,
                default_value=record.default_value,
                table_rows=record.table_rows,
                table_size=record.table_size,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    async def get_table_fields(
        self, db: AsyncSession, *, database_name: str, table_name: str
    ) -> List[DatabaseTreeNode]:
        """获取指定表的字段信息"""
        records = await crud_database_metadata.get_table_fields(db, database_name=database_name, table_name=table_name)

        return [
            DatabaseTreeNode(
                id=record.metadata_id,
                name=record.name,
                type=record.type,
                description=record.description,
                parent_id=record.parent_id,
                field_type=record.field_type,
                is_nullable=record.is_nullable,
                default_value=record.default_value,
                table_rows=record.table_rows,
                table_size=record.table_size,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    async def batch_update_descriptions(
        self, db: AsyncSession, *, request: BatchUpdateDescriptionsRequest
    ) -> BatchUpdateDescriptionsResponse:
        """批量更新描述信息"""
        updates = [update.model_dump() for update in request.updates]
        updated_count = await crud_database_metadata.batch_update_descriptions(db, updates=updates)

        return BatchUpdateDescriptionsResponse(
            success=True, updated_count=updated_count, message=f"成功更新{updated_count}项描述信息"
        )

    async def _get_all_databases(self) -> List[str]:
        """获取MySQL服务器上的所有数据库"""
        try:
            # 连接到MySQL服务器（不指定数据库）
            url = self._create_mysql_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                result = await conn.execute(text("SHOW DATABASES"))
                databases = [row[0] for row in result.fetchall()]

                # 过滤掉系统数据库
                system_databases = {"information_schema", "performance_schema", "mysql", "sys"}
                user_databases = [db for db in databases if db not in system_databases]

            await engine.dispose()
            return user_databases

        except Exception as e:
            raise Exception(f"获取数据库列表失败: {str(e)}")

    async def _scan_database_structure(self, database_name: str) -> Dict:
        """扫描单个数据库的结构"""
        try:
            # 创建指定数据库的连接
            url = self._create_mysql_url(database_name)
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                # SelectDB不支持SCHEMA_COMMENT，跳过数据库注释查询
                db_comment = None

                # 获取所有表的信息 - 简化查询以兼容SelectDB
                tables_result = await conn.execute(
                    text("""
                    SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = :db_name AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """),
                    {"db_name": database_name},
                )

                database_info = {"name": database_name, "comment": self._clean_string_value(db_comment), "tables": []}

                for table_row in tables_result.fetchall():
                    table_name, table_comment, table_rows = table_row

                    # 获取表的字段信息 - 简化查询以兼容SelectDB
                    columns_result = await conn.execute(
                        text("""
                        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
                        ORDER BY ORDINAL_POSITION
                    """),
                        {"db_name": database_name, "table_name": table_name},
                    )

                    table_info = {
                        "name": table_name,
                        "comment": self._clean_string_value(table_comment),
                        "rows": table_rows or 0,
                        "size_mb": None,  # SelectDB可能不支持准确的表大小查询
                        "fields": [],
                    }

                    for column_row in columns_result.fetchall():
                        column_name, column_type, is_nullable, column_default, column_comment = column_row

                        field_info = {
                            "name": column_name,
                            "type": self._clean_string_value(column_type),
                            "nullable": is_nullable == "YES",
                            "default": self._clean_string_value(str(column_default))
                            if column_default is not None
                            else None,
                            "comment": self._clean_string_value(column_comment),
                        }
                        table_info["fields"].append(field_info)

                    database_info["tables"].append(table_info)

            await engine.dispose()
            return database_info

        except Exception as e:
            raise Exception(f"扫描数据库 {database_name} 失败: {str(e)}")

    async def _save_database_metadata(self, db: AsyncSession, database_info: Dict) -> int:
        """保存数据库元数据到数据库，实现创建或更新逻辑"""
        saved_count = 0
        database_name = database_info["name"]

        # 保存数据库信息
        db_id = self._generate_id("database", database_name)
        existing_db = await crud_database_metadata.get_by_metadata_id(db, metadata_id=db_id)

        if existing_db:
            # 更新现有数据库记录（保留description）
            existing_db.name = database_name
            # description 不更新，保留用户设置的值
        else:
            # 创建新的数据库记录
            db_node = DatabaseTreeNodeCreate(
                id=db_id,
                name=database_name,
                type="database",
                description=database_info["comment"],  # 使用数据库注释
                parent_id=None,
            )
            await crud_database_metadata.create_or_update(db, obj_in=db_node)
        saved_count += 1

        # 保存表和字段信息
        for table_info in database_info["tables"]:
            table_name = table_info["name"]
            table_id = self._generate_id("table", table_name, database_name)

            existing_table = await crud_database_metadata.get_by_metadata_id(db, metadata_id=table_id)

            if existing_table:
                # 更新现有表记录（保留description）
                existing_table.name = table_name
                existing_table.table_rows = table_info["rows"]
                existing_table.table_size = self._format_table_size(
                    int(table_info["size_mb"] * 1024 * 1024) if table_info["size_mb"] else None
                )
                # description 不更新，保留用户设置的值
            else:
                # 创建新的表记录
                table_node = DatabaseTreeNodeCreate(
                    id=table_id,
                    name=table_name,
                    type="table",
                    description=table_info["comment"],  # 使用表注释
                    parent_id=db_id,
                    table_rows=table_info["rows"],
                    table_size=self._format_table_size(
                        int(table_info["size_mb"] * 1024 * 1024) if table_info["size_mb"] else None
                    ),
                )
                await crud_database_metadata.create_or_update(db, obj_in=table_node)
            saved_count += 1

            # 保存字段信息
            for field_info in table_info["fields"]:
                field_name = field_info["name"]
                field_id = self._generate_id("field", field_name, table_id)

                existing_field = await crud_database_metadata.get_by_metadata_id(db, metadata_id=field_id)

                if existing_field:
                    # 更新现有字段记录（保留description）
                    existing_field.name = field_name
                    existing_field.field_type = field_info["type"]
                    existing_field.is_nullable = field_info["nullable"]
                    existing_field.default_value = field_info["default"]
                    # description 不更新，保留用户设置的值
                else:
                    # 创建新的字段记录
                    field_node = DatabaseTreeNodeCreate(
                        id=field_id,
                        name=field_name,
                        type="field",
                        description=field_info["comment"],  # 使用字段注释
                        parent_id=table_id,
                        field_type=field_info["type"],
                        is_nullable=field_info["nullable"],
                        default_value=field_info["default"],
                    )
                    await crud_database_metadata.create_or_update(db, obj_in=field_node)
                saved_count += 1

        return saved_count

    async def refresh_database_structure(
        self, db: AsyncSession, *, request: RefreshDatabaseRequest
    ) -> RefreshDatabaseResponse:
        """刷新数据库结构"""
        try:
            scanned_databases = []
            total_tables = 0
            total_fields = 0

            if request.database_name:
                # 刷新指定数据库
                database_info = await self._scan_database_structure(request.database_name)
                await self._save_database_metadata(db, database_info)

                scanned_databases.append(request.database_name)
                total_tables = len(database_info["tables"])
                total_fields = sum(len(table["fields"]) for table in database_info["tables"])

            else:
                # 刷新所有数据库
                all_databases = await self._get_all_databases()

                for db_name in all_databases:
                    try:
                        database_info = await self._scan_database_structure(db_name)
                        await self._save_database_metadata(db, database_info)

                        scanned_databases.append(db_name)
                        total_tables += len(database_info["tables"])
                        total_fields += sum(len(table["fields"]) for table in database_info["tables"])

                    except Exception as e:
                        # 记录错误但继续处理其他数据库
                        print(f"刷新数据库 {db_name} 失败: {str(e)}")

            return RefreshDatabaseResponse(
                success=True,
                message="数据库结构刷新成功",
                scanned_databases=scanned_databases,
                scanned_tables=total_tables,
                scanned_fields=total_fields,
            )

        except Exception as e:
            return RefreshDatabaseResponse(
                success=False,
                message=f"数据库结构刷新失败: {str(e)}",
                scanned_databases=[],
                scanned_tables=0,
                scanned_fields=0,
            )

    async def analyze_sql(self, db: AsyncSession, *, sql: str) -> SqlAnalysisResponse:
        """
        分析SQL语句，提取表和字段信息并进行验证

        参数:
        - sql: 要分析的SQL语句

        返回:
        - database_name: 数据库名称
        - tables: 表信息列表
        - valid: SQL是否有效
        - error_message: 错误信息（如果有）
        """
        try:
            # 1. 提取数据库名称
            db_match = re.search(r"FROM\s+`?([a-zA-Z0-9_-]+)`?\.", sql, re.IGNORECASE)
            if not db_match:
                return SqlAnalysisResponse(
                    valid=False, database_name=None, tables=[], error_message="无法从SQL中解析数据库名称"
                )

            database_name = db_match.group(1)

            # 2. 提取表名和别名
            tables_info = []
            table_pattern = re.compile(
                r"FROM\s+`?([a-zA-Z0-9_-]+)`?\.`?([a-zA-Z0-9_-]+)`?\s+AS\s+([a-zA-Z0-9_]+)|JOIN\s+`?([a-zA-Z0-9_-]+)`?\.`?([a-zA-Z0-9_-]+)`?\s+AS\s+([a-zA-Z0-9_]+)",
                re.IGNORECASE,
            )

            tables_matches = table_pattern.finditer(sql)
            table_aliases = {}  # 表别名映射

            for match in tables_matches:
                if match.group(1):  # FROM 子句匹配
                    db_name, table_name, alias = match.group(1), match.group(2), match.group(3)
                else:  # JOIN 子句匹配
                    db_name, table_name, alias = match.group(4), match.group(5), match.group(6)

                table_aliases[alias] = (db_name, table_name)

            # 3. 提取字段
            fields_pattern = re.compile(r"t\d+\.`([a-zA-Z0-9_-]+)`\s+AS\s+`t\d+_[a-zA-Z0-9_-]+`", re.IGNORECASE)
            fields_matches = fields_pattern.finditer(sql)

            field_counts = {}  # 每个表的字段计数

            for match in fields_matches:
                field_name = match.group(1)
                # 尝试从字段名中确定所属的表
                table_ref = re.search(r"t(\d+)", match.group(0))
                if table_ref:
                    table_alias = f"t{table_ref.group(1)}"
                    if table_alias in table_aliases:
                        db_name, table_name = table_aliases[table_alias]
                        field_counts.setdefault((db_name, table_name), set()).add(field_name)

            # 4. 验证表和字段是否存在于元数据中
            for (db_name, table_name), fields in field_counts.items():
                if db_name != database_name:
                    continue  # 跳过不属于当前数据库的表

                # 检查表是否存在
                table_id = self._generate_id("table", table_name, database_name)
                table_metadata = await crud_database_metadata.get_by_metadata_id(db, metadata_id=table_id)

                if not table_metadata:
                    tables_info.append(
                        TableMetadata(table_name=table_name, exists=False, field_count=len(fields), fields=[])
                    )
                    continue

                # 获取表的所有字段
                table_fields = await self.get_table_fields(db, database_name=database_name, table_name=table_name)
                field_names = {field.name: field for field in table_fields}

                fields_info = []
                for field_name in fields:
                    field_exists = field_name in field_names
                    field_info = FieldMetadata(
                        field_name=field_name,
                        exists=field_exists,
                        description=field_names[field_name].description if field_exists else None,
                        field_type=field_names[field_name].field_type if field_exists else None,
                    )
                    fields_info.append(field_info)

                tables_info.append(
                    TableMetadata(table_name=table_name, exists=True, field_count=len(fields), fields=fields_info)
                )

            return SqlAnalysisResponse(valid=True, database_name=database_name, tables=tables_info, error_message=None)

        except Exception as e:
            return SqlAnalysisResponse(
                valid=False, database_name=None, tables=[], error_message=f"SQL分析失败: {str(e)}"
            )

    async def validate_sql(self, db: AsyncSession, *, sql: str) -> dict:
        """
        验证SQL语句的有效性并检测其访问的表和字段

        参数:
        - sql: 要验证的SQL语句

        返回:
        - valid: SQL是否有效
        - analysis: SQL分析结果
        - message: 提示信息
        """
        # 简单的SQL注入检测
        dangerous_patterns = [
            r";\s*DROP",
            r";\s*DELETE",
            r";\s*UPDATE",
            r";\s*INSERT",
            r"INFORMATION_SCHEMA",
            r"--",
            r"/\*",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return {"valid": False, "analysis": None, "message": "SQL语句包含可能的安全风险"}

        # 执行SQL分析
        analysis = await self.analyze_sql(db, sql=sql)

        # 如果SQL分析失败，返回错误信息
        if not analysis.valid:
            return {"valid": False, "analysis": analysis, "message": analysis.error_message or "SQL分析失败"}

        # 检查表和字段是否都存在
        all_tables_exist = all(table.exists for table in analysis.tables)
        all_fields_exist = all(field.exists for table in analysis.tables for field in table.fields)

        if not all_tables_exist:
            missing_tables = [table.table_name for table in analysis.tables if not table.exists]
            return {"valid": False, "analysis": analysis, "message": f"表不存在: {', '.join(missing_tables)}"}

        if not all_fields_exist:
            missing_fields = [
                f"{table.table_name}.{field.field_name}"
                for table in analysis.tables
                for field in table.fields
                if not field.exists
            ]
            return {"valid": False, "analysis": analysis, "message": f"字段不存在: {', '.join(missing_fields)}"}

        return {"valid": True, "analysis": analysis, "message": "SQL验证通过"}

    async def execute_query(self, db: AsyncSession, *, sql: str, limit: int = 1000) -> dict:
        """
        执行测试查询，返回有限的结果集

        参数:
        - sql: 要执行的SQL语句
        - limit: 最大返回行数，默认为10

        返回:
        - success: 是否成功执行
        - rows: 查询结果行
        - columns: 结果列信息
        - message: 提示信息
        """
        try:
            # 从SQL中提取数据库名称
            db_match = re.search(r"FROM\s+`?([a-zA-Z0-9_-]+)`?\.", sql, re.IGNORECASE)
            if not db_match:
                return {"success": False, "rows": [], "columns": [], "message": "无法从SQL中解析数据库名称"}

            database_name = db_match.group(1)

            # 限制结果集大小
            if "LIMIT" in sql.upper():
                # 替换已有的LIMIT子句
                sql = re.sub(r"LIMIT\s+\d+", f"LIMIT {limit}", sql, flags=re.IGNORECASE)
            else:
                # 添加LIMIT子句
                sql = f"{sql} LIMIT {limit}"

            # 创建数据库连接
            url = self._create_mysql_url(database_name)
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                result = await conn.execute(text(sql))
                rows = result.fetchall()

                # 获取列信息
                column_names = result.keys()

                # 转换结果为字典列表
                data = []
                for row in rows:
                    data.append({k: v for k, v in row._mapping.items()})

                # 构建详细的列信息（包含列名和描述）
                columns = []

                # 尝试从SQL中提取表名，用于获取列描述
                table_matches = re.findall(r"FROM\s+`?([a-zA-Z0-9_-]+)`?\.`?([a-zA-Z0-9_-]+)`?", sql, re.IGNORECASE)

                # 创建字段描述映射表
                field_descriptions = {}

                # 如果找到表名，尝试获取字段描述
                if table_matches:
                    for db_name, table_name in table_matches:
                        # 获取表的字段信息
                        try:
                            table_fields = await self.get_table_fields(db, database_name=db_name, table_name=table_name)

                            # 构建字段名到描述的映射
                            for field in table_fields:
                                field_descriptions[field.name] = field.description
                        except Exception:
                            # 如果获取失败，继续处理
                            pass

                # 为每个列添加描述信息
                for column_name in column_names:
                    # 尝试提取原始字段名（去掉别名）
                    original_name = column_name.split("_")[-1] if "_" in column_name else column_name

                    columns.append(
                        {
                            "column_name": column_name,
                            "column_description": field_descriptions.get(original_name, ""),
                            "children_columns": [],
                        }
                    )

            await engine.dispose()

            return {"success": True, "rows": data, "columns": columns, "message": f"查询成功，返回 {len(data)} 行数据"}

        except Exception as e:
            return {"success": False, "rows": [], "columns": [], "message": f"查询执行失败: {str(e)}"}

    async def process_data_source_link(
        self, db: AsyncSession, *, request: DataSourceLinkRequest
    ) -> DataSourceLinkResponse:
        """
        处理数据源链接请求

        参数:
        - request: 包含数据源链接字段、SQL执行结果和选定表的请求

        返回:
        - fields_info: 字段信息列表
        - data_rows: 数据行列表
        """
        # 1. 定义返回数据结构
        fields_info = []
        data_rows = []

        # 2. 获取链接字段信息
        from_field = request.dataSourcesLinkField.fromField
        from_table = request.dataSourcesLinkField.fromTable

        # 3. 遍历选定的表
        for table in request.selectedTables:
            database_name = table.database_name if hasattr(table, "database_name") else None
            table_name = table.table_name

            if not database_name:
                continue

            # 获取表的字段信息
            table_fields = await self.get_table_fields(db, database_name=database_name, table_name=table_name)

            # 将表字段转换为更易于处理的格式
            table_fields_dict = {
                field.name: {"name": field.name, "description": field.description, "type": field.field_type}
                for field in table_fields
            }

            # 如果表名与fromTable相等且fromField不在selected_field_names中，则添加
            if table_name == from_table and from_field not in table.selected_field_names:
                table.selected_field_names.append(from_field)

            # 根据selected_field_names过滤字段信息
            for field_name in table.selected_field_names:
                if field_name in table_fields_dict:
                    field_info = table_fields_dict[field_name]
                    fields_info.append(
                        {
                            "field_name": field_name,
                            "field_description": field_info["description"],
                            "field_type": field_info["type"],
                        }
                    )

        # 4. 处理数据行
        # 从SQL执行结果中获取行数据
        source_rows = request.sqlExecutionResult.rows

        # 根据字段信息过滤行数据
        field_names = [info["field_name"] for info in fields_info]

        for row in source_rows:
            filtered_row = {}
            for field_name in field_names:
                if field_name in row:
                    filtered_row[field_name] = row[field_name]

            if filtered_row:  # 只添加非空行
                data_rows.append(filtered_row)

        return DataSourceLinkResponse(
            link_field=from_field or "",
            dataSourceId=request.sqlExecutionResult.dataSourceId,
            fields_info=fields_info,
            data_rows=data_rows,
        )

    async def process_linked_data_query(
        self, db: AsyncSession, *, primary_result: dict, no_primary_sources: List[dict]
    ) -> dict:
        """
        处理链接数据查询

        参数:
        - primary_result: 主数据源查询结果
        - no_primary_sources: 非主数据源列表

        返回:
        - rows: 合并后的数据行
        - columns: 合并后的列信息
        - message: 处理消息
        """
        try:
            # 获取主数据源的列和行
            primary_columns = primary_result.get("columns", [])
            primary_rows = primary_result.get("rows", [])
            data_source_link_field = primary_result.get("dataSourcesLinkField", "")

            # 初始化压缩数据格式
            compress_data = {"columns": [], "rows": []}

            # 压缩数据 - 提取列名
            for col in primary_columns:
                compress_data["columns"].append(col.get("column_description"))

            # 压缩数据 - 转换行数据{key:value}为数组格式
            for row in primary_rows:
                row_value = []
                for k, v in row.items():
                    row_value.append(v)
                compress_data["rows"].append(row_value)

            # 合并后的列信息
            merged_columns = primary_columns.copy()

            if data_source_link_field == "":
                return {
                    "rows": primary_rows,
                    "columns": primary_columns,
                    "compress_data": compress_data,
                    "message": "链接数据查询成功",
                }
            #  print('no_primary_sources',no_primary_sources)
            # 遍历主数据源的每一行
            for row_item in primary_rows:
                # 获取链接字段的值
                data_source_link_field_value = row_item.get(data_source_link_field)

                # 遍历每个非主数据源
                for source_item in no_primary_sources:
                    # 获取数据源链接字段信息
                    link_field_info = source_item.get("dataSourcesLinkField", {})
                    database_name = source_item.get("database_name", "")
                    tables = source_item.get("tables", [])
                    collection_name = source_item.get("collection_name", "")
                    source_item.get("collection_description", "")
                    compress_data["columns"].append(f"相关联{collection_name}信息")

                    if not link_field_info or not database_name or not tables:
                        continue

                    # 构建查询条件
                    condition = {
                        "fromField": link_field_info.get("fromField", ""),
                        "fromTable": link_field_info.get("fromTable", ""),
                        "value": data_source_link_field_value,
                        "operator": "=",  # 默认使用等于操作符
                    }
                    #  print(condition)
                    if condition.get("fromField") == "" or condition.get("fromTable") == "":
                        continue

                    # 构建SQL生成请求

                    from backend.app.admin.schema.sql_generator import SqlGenerateRequest

                    # 确保tables格式正确
                    sql_request = SqlGenerateRequest(database_name=database_name, tables=tables, condition=condition)

                    # 生成SQL语句
                    from backend.app.admin.service.sql_generator_service import sql_generator_service

                    sql_response = await sql_generator_service.generate_sql(db, request=sql_request)
                    # 执行SQL查询
                    query_result = await self.execute_query(db, sql=sql_response.sql, limit=100)

                    if query_result["success"]:
                        # if len(query_result["rows"])  == 1:

                        #     # 将列信息添加到合并列中
                        #     for col in query_result["columns"]:
                        #         col_with_db = {
                        #             "column_name": f"{database_name}.{col['column_name']}",
                        #             "column_description": col.get("column_description", "")
                        #         }
                        #         # 检查是否已存在相同的列名
                        #         if not any(
                        #             existing_col.get("column_name") == col_with_db["column_name"]
                        #             for existing_col in merged_columns
                        #         ):
                        #             merged_columns.append(col_with_db)
                        #         row_item[f"{database_name}.{col['column_name']}"] = query_result["rows"][0][
                        #             col['column_name']
                        #         ]
                        # else:
                        #     print('sql_response',sql_response.sql)
                        #     print('query_result',query_result.get("message",""),'\n')
                        if len(query_result["rows"]) > 0:
                            row_item[database_name] = query_result["rows"]

                            # Create children_columns list
                            children_data = "{columns:["
                            for col in query_result["columns"]:
                                children_data += f"{col.get('column_description', '')},"
                            # 去掉最后一个逗号
                            children_data = children_data[:-1]
                            children_data += "]"

                            rows_data = "rows:["
                            for row in query_result["rows"]:
                                item_data = "["
                                for k, v in row.items():
                                    item_data += f"{v},"
                                item_data = item_data[:-1]
                                item_data += "]"
                                rows_data += f"{item_data},"
                            rows_data = rows_data[:-1]
                            rows_data += "]"
                            children_data += f"{rows_data}" + "}"
                            compress_data["rows"].append(f"这一行相关{collection_name}的数据如下:{children_data}")

            return {
                "rows": primary_rows,
                "columns": merged_columns,
                "compress_data": compress_data,
                "message": "链接数据查询成功",
            }

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            print(f"链接数据查询失败: {error_detail}")
            return {"rows": [], "columns": [], "compress_data": compress_data, "message": f"链接数据查询失败: {str(e)}"}


database_metadata_service = DatabaseMetadataService()
