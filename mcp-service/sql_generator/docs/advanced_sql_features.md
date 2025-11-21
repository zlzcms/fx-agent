# SQLGenerator高级功能整合指南

本文档介绍如何在SQLGenerator中整合SQLBuilder的高级功能，以实现更灵活、强大的SQL生成能力。

## 架构选择

SQLGenerator目前采用了"sql_builder + 模板 + 配置"的混合架构。这种架构有以下优缺点：

**优点**：
- 模板提供了灵活性，特别是处理复杂查询
- 可以针对不同数据库方言定制模板
- 对于常见查询模式可以预定义模板

**缺点**：
- 维护两套系统（Builder和模板）增加复杂性
- 学习成本较高（需要了解模板语法和Builder API）

随着SQLBuilder功能的扩展，我们可以考虑更多地依赖Builder API，减少对模板的依赖，同时保留模板系统用于特殊场景。

## 整合方案

### 1. 在SQLGenerator中直接使用SQLBuilder

修改SQLGenerator类，使其能够直接使用SQLBuilder的高级功能：

```python
def generate_with_builder(self, config: Dict[str, Any]) -> str:
    """
    使用SQLBuilder生成SQL语句

    Args:
        config: 包含SQL配置的字典

    Returns:
        生成的SQL语句
    """
    builder = SQLBuilder(dialect=self.dialect)

    # 根据配置构建SQL
    sql_type = config.get("type", "").lower()

    if sql_type == "select":
        self._build_select(builder, config)
    elif sql_type == "insert":
        self._build_insert(builder, config)
    # ... 其他类型

    # 构建SQL
    sql, params = builder.build()

    # 处理参数（如果需要）
    # ...

    return sql
```

### 2. 添加辅助方法处理高级功能

为每种高级功能添加专门的辅助方法：

```python
def _build_window_function(self, builder: SQLBuilder, config: Dict[str, Any]) -> None:
    """构建窗口函数"""
    window_funcs = config.get("window_functions", [])
    for wf in window_funcs:
        function = wf.get("function")
        column = wf.get("column", "")
        partition_by = wf.get("partition_by")
        order_by = wf.get("order_by")
        frame_clause = wf.get("frame")
        alias = wf.get("alias")

        builder.window(function, column, partition_by, order_by, frame_clause, alias)
```

### 3. 扩展配置格式

扩展配置格式以支持新的高级功能：

```json
{
  "type": "select",
  "table": "employees",
  "columns": ["name", "department", "salary"],
  "window_functions": [
    {
      "function": "ROW_NUMBER",
      "column": "",
      "partition_by": ["department"],
      "order_by": [{"column": "salary", "direction": "DESC"}],
      "alias": "salary_rank"
    }
  ],
  "json_extracts": [
    {
      "column": "data",
      "path": "address.city",
      "alias": "city"
    }
  ]
}
```

## 具体功能整合

### 窗口函数

在SQLGenerator中添加对窗口函数的支持：

```python
def generate_window_function(self, table: str, base_columns: List[str],
                           window_functions: List[Dict[str, Any]], where: Optional[str] = None,
                           order_by: Optional[List[Dict[str, str]]] = None) -> str:
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
    builder = SQLBuilder(dialect=self.dialect)

    # 添加基础列
    for col in base_columns:
        builder.select(col)

    # 添加窗口函数
    for wf in window_functions:
        function = wf["function"]
        column = wf["column"]
        partition_by = wf.get("partition_by")
        order_by_clause = wf.get("order_by")
        frame_clause = wf.get("frame")
        alias = wf.get("alias")

        builder.window(function, column, partition_by, order_by_clause, frame_clause, alias)

    # 添加表
    builder.from_table(table)

    # 添加WHERE条件
    if where:
        builder.where(where)

    # 添加ORDER BY
    if order_by:
        for order in order_by:
            builder.order_by(order["column"], order.get("direction", "ASC"))

    # 构建SQL
    sql, _ = builder.build()
    return sql
```

### JSON操作

添加JSON操作支持：

```python
def generate_json_query(self, table: str, base_columns: List[str],
                       json_extracts: List[Dict[str, Any]],
                       json_conditions: List[Dict[str, Any]] = None,
                       where: Optional[str] = None) -> str:
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
    builder = SQLBuilder(dialect=self.dialect)

    # 添加基础列
    for col in base_columns:
        builder.select(col)

    # 添加JSON提取
    for je in json_extracts:
        builder.json_extract(je["column"], je["path"], je.get("alias"))

    # 添加表
    builder.from_table(table)

    # 添加JSON条件
    if json_conditions:
        for jc in json_conditions:
            builder.json_contains(jc["column"], jc["value"], jc.get("path"))

    # 添加WHERE条件
    if where:
        builder.where(where)

    # 构建SQL
    sql, _ = builder.build()
    return sql
```

### 子查询和CTE

添加子查询和CTE支持：

```python
def generate_with_subquery(self, main_config: Dict[str, Any],
                          subqueries: Dict[str, Dict[str, Any]]) -> str:
    """
    生成带有子查询的SQL

    Args:
        main_config: 主查询配置
        subqueries: 子查询配置字典，键为子查询别名

    Returns:
        带有子查询的SQL语句
    """
    # 创建子查询构建器
    subquery_builders = {}
    for alias, config in subqueries.items():
        sub_builder = SQLBuilder(dialect=self.dialect)
        self._build_query(sub_builder, config)
        subquery_builders[alias] = sub_builder

    # 创建主查询构建器
    main_builder = SQLBuilder(dialect=self.dialect)

    # 处理CTE
    ctes = main_config.get("ctes", {})
    for name, cte_config in ctes.items():
        if isinstance(cte_config, str):
            # 原始SQL CTE
            main_builder.with_cte(name, cte_config)
        elif cte_config.get("recursive", False):
            # 递归CTE
            main_builder.with_recursive(name, cte_config["query"])
        else:
            # 使用已构建的子查询作为CTE
            sub_alias = cte_config.get("subquery_ref")
            if sub_alias and sub_alias in subquery_builders:
                sql, _ = subquery_builders[sub_alias].build()
                main_builder.with_cte(name, sql)

    # 构建主查询
    self._build_query(main_builder, main_config)

    # 添加子查询到FROM子句
    for alias, config in main_config.get("subqueries", {}).items():
        sub_alias = config.get("subquery_ref")
        if sub_alias and sub_alias in subquery_builders:
            main_builder.subquery(subquery_builders[sub_alias], alias)

    # 构建SQL
    sql, _ = main_builder.build()
    return sql
```

## 配置文件示例

以下是一个使用高级功能的配置文件示例：

```json
{
  "type": "select",
  "ctes": {
    "dept_avg": {
      "query": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department"
    }
  },
  "columns": ["e.name", "e.salary", "d.avg_salary"],
  "table": "employees",
  "alias": "e",
  "joins": [
    {
      "table": "dept_avg",
      "alias": "d",
      "condition": "e.department = d.department",
      "type": "INNER"
    }
  ],
  "window_functions": [
    {
      "function": "ROW_NUMBER",
      "column": "",
      "partition_by": ["e.department"],
      "order_by": [{"column": "e.salary", "direction": "DESC"}],
      "alias": "salary_rank"
    }
  ],
  "where": "e.salary > d.avg_salary",
  "order_by": [
    {"column": "e.department", "direction": "ASC"},
    {"column": "salary_rank", "direction": "ASC"}
  ]
}
```

## 结论

通过整合SQLBuilder的高级功能，SQLGenerator可以支持更复杂的SQL生成需求，同时保持API的一致性和易用性。这种整合方案既保留了模板系统的灵活性，又充分利用了SQLBuilder的强大功能。

对于简单的查询，可以使用SQLBuilder直接生成SQL；对于复杂的、需要特定格式的查询，可以继续使用模板系统。这种混合架构能够满足各种SQL生成需求。
