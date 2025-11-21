# -*- coding: utf-8 -*-
# @Author: claude-4-sonnet
# @Date:   2025-06-27 10:00:00
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL生成器和验证器API

这个模块提供了根据数据源模型生成SQL查询语句和验证SQL语句的API。支持以下功能：

SQL生成功能：
1. 单表查询：从单个表中查询数据
2. 多表关联查询：自动检测表之间的关系并生成JOIN查询
3. 查询条件和排序：支持自定义的查询条件和排序
4. 测试执行：生成SQL并执行查询，返回结果
5. 链接数据查询：通过主数据源的链接字段关联查询非主数据源

SQL验证功能：
1. SQL语法分析：解析SQL语句，提取表和字段信息
2. 元数据验证：验证SQL中引用的表和字段是否存在
3. 测试执行：执行SQL查询并返回有限的结果集

生成器用法示例:
```json
{
  "database_name": "devapi1_mtarde_c",
  "tables": [
    {
      "table_name": "t_member",
      "table_description": "用户基本表结构",
      "data_limit": 200,
      "relation_field": "id",
      "selected_field_names": [
        "id",
        "amount"
      ]
    },
    {
      "table_name": "t_member_login_log",
      "table_description": "登录日志",
      "data_limit": 200,
      "relation_field": "member_id",
      "selected_field_names": [
        "id",
        "member_id",
        "create_time"
      ]
    }
  ],
  "condition": "t1.amount > 100",
  "order_by": "t1.amount",
  "order_direction": "DESC"
}
```

链接数据查询用法示例:
```json
{
  "primaryDataSourceResult": {
    "columns": [{...}, {...}],
    "dataSourceId": "...",
    "dataSourcesLinkField": "id",
    "rows": [{...}, {...}]
  },
  "noPrimaryDataSource": [
    {
      "dataSourcesLinkField": {"fromTable": "t_member", "fromField": "id"},
      "database_name": "devapi1_mtarde_c",
      "tables": [...]
    }
  ]
}
```

验证器用法示例：
```json
{
  "sql": "SELECT t1.`id` AS `t1_id`, t1.`username` AS `t1_username`, t2.`login_time` AS `t2_login_time` "
         "FROM `devapi1_mtarde_c`.`t_member` AS t1 "
         "LEFT JOIN `devapi1_mtarde_c`.`t_member_login_log` AS t2 ON t1.`id` = t2.`member_id` LIMIT 200"
}
```

数据源链接用法示例：
```json
{
  "dataSourcesLinkField": {"fromField":"id","fromTable":"t_member"},
  "sqlExecutionResult": {
    "dataSourceId": "ds_001",
    "dataSourceName": "会员数据源",
    "rows": [{"id": 1, "username": "user1"}, {"id": 2, "username": "user2"}]
  },
  "selectedTables": [
    {
      "database_name": "devapi1_mtarde_c",
      "table_name": "t_member",
      "selected_field_names": ["username"]
    }
  ]
}
```

在多表查询中，可以通过`relation_field`参数指定表之间的关联字段。默认情况下：
- 第一个表是主表，其他表通过JOIN关联到主表
- 如果没有指定`relation_field`，系统会尝试自动检测关联字段

安全说明：
- 所有SQL语句都会经过安全验证，防止SQL注入攻击
- 测试执行功能限制返回最多10条记录
- 禁止执行修改数据的语句（如UPDATE、DELETE、INSERT等）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.database_metadata import SqlAnalysisResponse, SqlExecuteRequest, SqlValidationRequest
from backend.app.admin.schema.sql_generator import (
    DataSourceLinkRequest,
    DataSourceLinkResponse,
    LinkedDataQueryRequest,
    LinkedDataQueryResponse,
    SqlGenerateRequest,
    SqlGenerateResponse,
)
from backend.app.admin.service.database_metadata_service import database_metadata_service
from backend.app.admin.service.sql_generator_service import sql_generator_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.post("/generate", summary="生成SQL查询语句", dependencies=[DependsJwtAuth])
async def generate_sql(
    request: SqlGenerateRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[SqlGenerateResponse]:
    """
    生成SQL查询语句

    根据指定的数据库、表和字段生成SQL查询语句。支持单表查询和多表关联查询。

    参数:
    - database_name: 数据库名称
    - tables: 表信息列表，每个表包含:
        - table_name: 表名
        - table_description: 表描述
        - data_limit: 数据限制
        - relation_field: 关联字段名，用于多表关联
        - selected_field_names: 选定的字段名列表
    - condition: 可选的查询条件，支持两种格式:
        - 字符串格式: 直接的SQL条件表达式，如 "t1.amount > 100"
        - 对象格式: 包含以下字段的对象:
            - fromField: 条件字段名
            - fromTable: 条件表名
            - value: 条件值
            - operator: 条件操作符，默认为"="
    - order_by: 可选的排序字段
    - order_direction: 可选的排序方向，默认为DESC
    - dataSourcesLinkField: 可选的数据源链接字段信息，包含:
        - fromField: 来源字段
        - fromTable: 来源表
    - data_permission: 数据权限类型（all_employee, agent_user, crm_user）
    - data_permission_values: 数据权限值（用户ID列表）
    - data_time_range_type: 时间范围类型（day, month, quarter, year）
    - data_time_value: 时间范围值

    多表关联说明:
    - 如果tables列表包含多个表，系统将自动生成JOIN语句
    - 第一个表作为主表，其他表通过LEFT JOIN关联到主表
    - 可以通过relation_field指定关联字段，主表默认使用"id"字段
    - 如果没有指定relation_field，系统会尝试自动检测关联字段
    - 如果指定了relation_field但未包含在selected_field_names中，系统会自动添加该字段
    - 如果指定了dataSourcesLinkField，系统会确保fromField字段包含在对应表的selected_field_names中

    返回:
    - sql: 生成的SQL查询语句
    - description: SQL查询描述

    示例:
    ```json
    {
      "database_name": "devapi1_mtarde_c",
      "tables": [
        {
          "table_name": "t_member",
          "table_description": "用户基本表结构",
          "data_limit": 200,
          "relation_field": "id",
          "selected_field_names": [
            "id",
            "amount"
          ]
        },
        {
          "table_name": "t_member_login_log",
          "relation_field": "member_id",
          "selected_field_names": [
            "id",
            "member_id",
            "create_time"
          ]
        }
      ],
      "condition": {
        "fromField": "amount",
        "fromTable": "t_member",
        "value": 100,
        "operator": ">"
      },
      "dataSourcesLinkField": {
        "fromField": "id",
        "fromTable": "t_member"
      },
      "data_permission": "all_employee",
      "data_permission_values": [1, 2, 3],
      "data_time_range_type": "month",
      "data_time_value": 3
    }
    ```
    """
    # 处理数据权限和时间范围
    if (
        hasattr(request, "data_permission")
        and hasattr(request, "data_permission_values")
        and request.data_permission
        and request.data_permission_values
    ):
        # 如果是代理商权限，需要获取代理商下的所有用户
        if request.data_permission == "agent_user" and request.data_permission_values:
            from backend.app.admin.service.warehouse_user_service import warehouse_user_service

            agent_ids = request.data_permission_values
            user_ids = await warehouse_user_service.get_users_under_agent(db, agent_ids=agent_ids)
            if user_ids:
                request.data_permission_values = user_ids

    # 服务层会处理确保数据源链接字段在selected_field_names中
    result = await sql_generator_service.generate_sql(db, request=request)
    return response_base.success(data=result)


@router.post("/test-execute", summary="测试执行SQL查询", dependencies=[DependsJwtAuth])
async def test_execute_sql(
    request: SqlGenerateRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """
    测试执行SQL查询（限制返回前10条数据）

    根据指定的数据库、表和字段生成SQL查询语句，并执行查询返回结果。
    为了安全考虑，结果限制为最多10条记录。

    参数:
    - database_name: 数据库名称
    - tables: 表信息列表，每个表包含表名、描述、选定的字段等信息
      - 每个表可以包含relation_field字段，用于指定与主表的关联字段
      - 如果relation_field未包含在selected_field_names中，系统会自动添加该字段
    - condition: 可选的查询条件，支持字符串格式和对象格式:
      - 字符串格式: 如 "t1.amount > 100"
      - 对象格式: 包含fromField、fromTable、value和operator字段
    - order_by: 可选的排序字段
    - order_direction: 可选的排序方向，默认为DESC

    返回:
    - sql: 执行的SQL查询语句
    - rows: 查询结果行
    - total: 结果总数

    注意:
    - 该接口始终限制返回最多10条记录，无论请求中的data_limit如何设置
    - 条件参数(condition)会经过安全验证，防止SQL注入
    """
    # 首先生成SQL
    sql_response = await sql_generator_service.generate_sql(db, request=request)
    sql = sql_response.sql

    # 添加LIMIT 10强制限制结果
    if "LIMIT" in sql:
        # 如果已有LIMIT，将其替换为LIMIT 10
        sql = sql.split("LIMIT")[0] + "LIMIT 10"
    else:
        # 如果没有LIMIT，添加LIMIT 10
        sql += " LIMIT 10"

    # 执行SQL（安全考虑，这里可以添加更多的验证）
    result = await db.execute(sql)
    rows = result.fetchall()

    # 将结果转换为字典列表
    data = []
    for row in rows:
        # 这里假设row是一个带有键值的对象，如果是元组需要根据字段名映射
        data.append({k: v for k, v in row._mapping.items()})

    return response_base.success(data={"sql": sql, "rows": data, "total": len(data)})


@router.post("/analyze", summary="分析SQL查询语句", dependencies=[DependsJwtAuth])
async def analyze_sql(
    request: SqlValidationRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[SqlAnalysisResponse]:
    """
    分析SQL查询语句

    解析SQL语句，提取表和字段信息，并验证元数据。

    参数:
    - sql: 要分析的SQL语句

    返回:
    - valid: SQL是否有效
    - database_name: 数据库名称
    - dataSourcesLinkField: 数据源链接字段信息，包含:
        - fromField: 来源字段
        - fromTable: 来源表
    - tables: 表信息列表，每个表包含:
        - table_name: 表名
        - exists: 表是否存在
        - field_count: 字段数量
        - fields: 字段信息列表，每个字段包含:
            - field_name: 字段名
            - exists: 字段是否存在
            - description: 字段描述
            - field_type: 字段类型
    - error_message: 错误信息（如果有）

    示例:
    ```json
    {
      "sql": "SELECT t1.`id` AS `t1_id`, t1.`username` AS `t1_username` "
             "FROM `devapi1_mtarde_c`.`t_member` AS t1 LIMIT 10"
    }
    ```
    """
    result = await database_metadata_service.analyze_sql(db, sql=request.sql)
    return response_base.success(data=result)


@router.post("/validate", summary="验证SQL查询语句", dependencies=[DependsJwtAuth])
async def validate_sql(request: SqlValidationRequest, db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[dict]:
    """
    验证SQL查询语句

    验证SQL语句的有效性，检查语法和引用的表和字段是否存在。

    参数:
    - sql: 要验证的SQL语句

    返回:
    - valid: SQL是否有效
    - analysis: SQL分析结果
    - message: 提示信息

    示例:
    ```json
    {
      "sql": "SELECT t1.`id` AS `t1_id`, t1.`username` AS `t1_username` "
             "FROM `devapi1_mtarde_c`.`t_member` AS t1 LIMIT 10"
    }
    ```
    """
    result = await database_metadata_service.validate_sql(db, sql=request.sql)
    return response_base.success(data=result)


@router.post("/execute", summary="执行SQL查询", dependencies=[DependsJwtAuth])
async def execute_sql(request: SqlExecuteRequest, db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[dict]:
    """
    执行自定义SQL查询（限制返回前10条数据）

    执行SQL查询并返回有限的结果集。为了安全考虑，结果限制为最多10条记录。

    参数:
    - sql: 要执行的SQL语句
    - limit: 最大返回行数，默认为10

    返回:
    - success: 是否成功执行
    - rows: 查询结果行
    - columns: 结果列信息
    - message: 提示信息

    注意:
    - 该接口始终限制返回最多10条记录，以保护数据库性能
    - SQL语句会经过安全验证，禁止执行修改数据的语句

    示例:
    ```json
    {
      "sql": "SELECT t1.`id`, t1.`username` FROM `devapi1_mtarde_c`.`t_member` AS t1 LIMIT 5"
    }
    ```
    """
    # 首先验证SQL
    validation = await database_metadata_service.validate_sql(db, sql=request.sql)
    if not validation["valid"]:
        # 返回验证失败信息，但使用success响应
        return response_base.success(
            data={"success": False, "message": validation["message"], "validation": validation}
        )

    # 执行SQL查询
    result = await database_metadata_service.execute_query(
        db,
        sql=request.sql,
        limit=min(request.limit, 5),  # 确保最多返回5条
    )

    # 无论执行成功或失败，都使用success响应，前端通过data.success判断
    return response_base.success(data=result)


@router.post("/data-source-link", summary="处理数据源链接", dependencies=[DependsJwtAuth])
async def process_data_source_link(
    request: DataSourceLinkRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DataSourceLinkResponse]:
    """
    处理数据源链接请求

    根据提供的数据源链接字段、SQL执行结果和选定表，处理数据源链接。

    参数:
    - dataSourcesLinkField: 数据源链接字段信息，包含:
        - fromField: 来源字段
        - fromTable: 来源表
    - sqlExecutionResult: SQL执行结果，包含:
        - dataSourceId: 数据源ID
        - dataSourceName: 数据源名称
        - rows: 查询结果行列表
    - selectedTables: 选定的表列表，每个表包含:
        - database_name: 数据库名称
        - table_name: 表名
        - selected_field_names: 选定的字段名列表

    处理逻辑:
    1. 确保fromField字段在对应表的selected_field_names中
    2. 遍历选定的表，获取每个表的字段信息
    3. 如果表名与fromTable相等且fromField不在selected_field_names中，则添加
    4. 根据selected_field_names过滤字段信息和行数据

    返回:
    - fields_info: 字段信息列表
    - data_rows: 数据行列表

    示例:
    ```json
    {
      "dataSourcesLinkField": {"fromField":"id","fromTable":"t_member"},
      "sqlExecutionResult": {
        "dataSourceId": "ds_001",
        "dataSourceName": "会员数据源",
        "rows": [{"id": 1, "username": "user1"}, {"id": 2, "username": "user2"}]
      },
      "selectedTables": [
        {
          "database_name": "devapi1_mtarde_c",
          "table_name": "t_member",
          "selected_field_names": ["username"]
        }
      ]
    }
    ```
    """
    # 确保数据源链接字段在selected_field_names中
    sql_generator_service.ensure_data_source_link_fields(request)

    result = await database_metadata_service.process_data_source_link(db, request=request)
    return response_base.success(data=result)


# 检测数据条件
@router.post("/check-data-condition", summary="检测数据条件", dependencies=[DependsJwtAuth])
async def check_data_condition(
    request: LinkedDataQueryRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[LinkedDataQueryResponse]:
    """
    检测数据条件

    根据主数据源的查询结果和链接字段，关联查询非主数据源的数据，并将结果合并返回。

    参数:
    - primaryDataSourceResult: 主数据源查询结果，包含:
        - columns: 列信息列表
        - dataSourceId: 数据源ID
        - dataSourcesLinkField: 数据源链接字段
        - rows: 查询结果行列表
    - noPrimaryDataSource: 非主数据源列表，每个非主数据源包含:
        - dataSourcesLinkField: 数据源链接字段信息，包含fromTable和fromField
        - database_name: 数据库名称
        - tables: 表信息列表

    处理逻辑:
    1. 遍历主数据源的每一行数据
    2. 获取链接字段的值
    3. 遍历每个非主数据源
    4. 构建查询条件，使用链接字段值作为条件值
    5. 生成SQL语句并执行查询
    6. 将查询结果添加到主行中
    7. 更新合并后的列信息

    返回:
    - rows: 合并后的数据行列表
    - columns: 合并后的列信息列表
    - message: 处理消息

    示例:
    ```json
    {
      "primaryDataSourceResult": {
        "columns": [
          {"column_name": "id", "column_description": "用户ID"},
          {"column_name": "username", "column_description": "用户名"}
        ],
        "dataSourceId": "ds_001",
        "dataSourcesLinkField": "id",
        "rows": [{"id": 1, "username": "user1"}, {"id": 2, "username": "user2"}]
      },
      "noPrimaryDataSource": [
        {
          "dataSourcesLinkField": {"fromTable": "t_member_login_log", "fromField": "member_id"},
          "database_name": "devapi1_mtarde_c",
          "tables": [
            {
              "table_name": "t_member_login_log",
              "selected_field_names": ["login_time", "login_ip"]
            }
          ]
        }
      ]
    }
    ```
    """
    result = await database_metadata_service.process_linked_data_query(
        db, primary_result=request.primaryDataSourceResult, no_primary_sources=request.noPrimaryDataSource
    )

    return response_base.success(data=result)
