# 数据库管理API规范

本文档描述了数据库管理功能需要的后端API接口。

## 数据结构

### DatabaseTreeNode
```typescript
interface DatabaseTreeNode {
  id: string;                    // 唯一标识
  name: string;                  // 名称（数据库名、表名、字段名）
  type: 'database' | 'table' | 'field';  // 类型
  description?: string;          // 描述信息
  parent_id?: string;           // 父节点ID
  
  // 字段特有属性
  field_type?: string;          // 字段类型（VARCHAR, INT等）
  is_nullable?: boolean;        // 是否可为空
  default_value?: string;       // 默认值
  
  // 表特有属性
  table_rows?: number;          // 表数据行数
  table_size?: string;          // 表大小（如："1.2MB"）
}
```

## API接口

### 1. 获取数据库树形结构
```
GET /api/v1/ai/databases/tree
```

**查询参数：**
- `database_name?`: string - 可选，指定数据库名称
- `include_tables?`: boolean - 是否包含表信息，默认true
- `include_fields?`: boolean - 是否包含字段信息，默认true

**响应示例：**
```json
[
  {
    "id": "db_1",
    "name": "user_center",
    "type": "database",
    "description": "用户中心数据库",
    "parent_id": null
  },
  {
    "id": "table_1",
    "name": "users",
    "type": "table",
    "description": "用户表",
    "parent_id": "db_1",
    "table_rows": 10000,
    "table_size": "2.1MB"
  },
  {
    "id": "field_1",
    "name": "id",
    "type": "field",
    "description": "用户ID",
    "parent_id": "table_1",
    "field_type": "INT",
    "is_nullable": false,
    "default_value": null
  },
  {
    "id": "field_2",
    "name": "username",
    "type": "field",
    "description": "用户名",
    "parent_id": "table_1",
    "field_type": "VARCHAR(50)",
    "is_nullable": false,
    "default_value": null
  }
]
```

### 2. 获取数据库列表
```
GET /api/v1/ai/databases
```

**响应示例：**
```json
["user_center", "order_system", "product_catalog"]
```

### 3. 获取指定数据库的表列表（带字段信息）
```
GET /api/v1/ai/databases/{database_name}/tables-with-fields
```

**响应：** 与树形结构相同，但只返回指定数据库的表和字段信息。

### 4. 批量更新描述信息
```
PUT /api/v1/ai/databases/descriptions
```

**请求体：**
```json
{
  "updates": [
    {
      "id": "db_1",
      "type": "database",
      "description": "更新后的数据库描述"
    },
    {
      "id": "table_1",
      "type": "table",
      "description": "更新后的表描述"
    },
    {
      "id": "field_1",
      "type": "field",
      "description": "更新后的字段描述"
    }
  ]
}
```

**响应：**
```json
{
  "success": true,
  "updated_count": 3,
  "message": "成功更新3项描述信息"
}
```

### 5. 刷新数据库结构（重新扫描）
```
POST /api/v1/ai/databases/refresh
```

**请求体：**
```json
{
  "database_name": "user_center"  // 可选，不指定则刷新所有数据库
}
```

**响应：**
```json
{
  "success": true,
  "message": "数据库结构刷新成功",
  "scanned_databases": ["user_center"],
  "scanned_tables": 5,
  "scanned_fields": 50
}
```

## 实现建议

### 1. 数据存储设计

建议在数据库中创建以下表来存储元数据：

```sql
-- 数据库元数据表
CREATE TABLE database_metadata (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('database', 'table', 'field') NOT NULL,
    description TEXT,
    parent_id VARCHAR(50),
    
    -- 字段特有属性
    field_type VARCHAR(100),
    is_nullable BOOLEAN,
    default_value TEXT,
    
    -- 表特有属性
    table_rows BIGINT,
    table_size VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_parent_id (parent_id),
    INDEX idx_type (type)
);
```

### 2. ID生成规则

- 数据库：`db_{database_name}`
- 表：`table_{database_name}_{table_name}`  
- 字段：`field_{database_name}_{table_name}_{field_name}`

### 3. 性能优化

1. **缓存机制**：由于数据库结构变化不频繁，建议使用Redis缓存树形结构数据
2. **异步刷新**：数据库结构扫描可能耗时较长，建议异步处理
3. **增量更新**：只刷新有变化的数据库/表结构

### 4. 错误处理

```json
{
  "success": false,
  "error_code": "DB_CONNECTION_FAILED",
  "message": "无法连接到数据库 user_center",
  "details": "Connection timeout after 30 seconds"
}
```

## 前端集成

前端已实现以下功能：

1. ✅ 树形表格显示数据库结构
2. ✅ 类型标签和图标显示
3. ✅ 行内编辑描述信息
4. ✅ 批量保存更改
5. ✅ 数据库选择过滤
6. ✅ 统计信息显示
7. ✅ 刷新数据库结构

请确保后端API返回的数据格式与前端预期的 `DatabaseTreeNode` 接口一致。 