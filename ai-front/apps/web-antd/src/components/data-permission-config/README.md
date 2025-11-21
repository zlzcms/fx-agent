# 数据权限配置组件 (DataPermissionConfig)

这是一个专门用于配置数据访问权限的交互式组件，替代了原有的简单 Select 多选框，提供了更友好和灵活的配置体验。

## 功能特点

### 🎯 主要功能
- **可视化权限选择**: 使用卡片式界面展示权限选项，直观易懂
- **权限配置预览**: 每个权限卡片显示配置概览，一目了然
- **搜索和筛选**: 支持按名称/描述搜索，按权限类型筛选
- **详细配置查看**: 点击查看完整的权限配置 JSON
- **已选权限管理**: 显示已选权限列表，支持快速移除

### 📋 支持的权限类型
- **时间范围权限** (`time_range`): 限制访问时间段
- **用户范围权限** (`user_scope`): 限制特定用户/部门访问
- **IP范围权限** (`ip_range`): 限制IP地址访问
- **数据范围权限** (`data_scope`): 限制数据库和数据量
- **字段级权限** (`field_level`): 控制字段级别访问
- **自定义权限** (`custom`): 自定义业务规则

## 组件属性

```typescript
interface Props {
  modelValue?: string[];    // v-model 绑定的权限ID数组
  options?: PermissionItem[]; // 权限选项数据
}

interface PermissionItem {
  id: string;
  name: string;
  permission_type: string;
  permission_config: any;
  description: string;
  status: boolean;
  created_time: string;
  updated_time?: string;
}
```

## 使用方法

### 1. 在表单 Schema 中使用

```typescript
// data.ts
{
  component: 'DataPermissionConfig',
  fieldName: 'data_permissions',
  label: '数据权限范围',
  formItemClass: 'col-span-2',
  componentProps: {
    options: [], // 权限选项数据
    style: { width: '100%' },
  },
  help: '设置AI助手对所选数据源的访问权限',
}
```

### 2. 动态更新权限选项

```typescript
// 在组件中更新权限选项
dataSourceFormApi.updateSchema([
  {
    fieldName: 'data_permissions',
    componentProps: {
      options: dataPermissionOptions.value,
    },
  },
]);
```

### 3. API 数据格式

权限 API 应返回如下格式的数据：

```json
{
  "name": "时间范围权限",
  "permission_type": "time_range",
  "permission_config": {
    "start_time": "09:00",
    "end_time": "18:00",
    "weekdays": [1, 2, 3, 4, 5],
    "timezone": "Asia/Shanghai"
  },
  "description": "限制在工作时间内访问数据",
  "status": true,
  "id": "ai_permission_001",
  "created_time": "2025-06-18T09:31:08.207998Z"
}
```

## UI 界面说明

### 主界面
- **空状态**: 显示权限锁图标和提示文字
- **已选状态**: 显示权限标签卡片，包含权限名称、类型和移除按钮
- **配置按钮**: 点击打开权限选择模态框

### 权限选择模态框
- **搜索栏**: 支持按权限名称或描述搜索
- **类型筛选**: 下拉选择特定权限类型
- **权限卡片网格**: 展示所有可选权限
- **权限卡片内容**:
  - 权限图标和基本信息
  - 权限类型标签
  - 配置概览（如时间范围、用户数量等）
  - "查看详细配置"按钮
  - 选中状态指示器

### 权限详情模态框
- **权限基本信息**: 名称、描述、类型
- **详细配置**: 完整的 JSON 配置
- **元数据信息**: 权限ID、创建时间、状态

## 样式特点

- **现代化设计**: 使用卡片布局和渐变效果
- **交互反馈**: 悬停动画和选中状态
- **响应式布局**: 适配不同屏幕尺寸  
- **一致性**: 与整体UI风格保持一致

## 扩展性

组件设计具有良好的扩展性：
- 权限类型可以轻松扩展
- 配置预览逻辑可以定制
- 图标映射可以自定义
- 样式主题可以调整

## 最佳实践

1. **数据预加载**: 在页面初始化时加载权限数据
2. **错误处理**: 妥善处理 API 请求失败的情况
3. **性能优化**: 对大量权限数据进行分页或虚拟滚动
4. **用户体验**: 提供清晰的加载状态和操作反馈

这个组件大大提升了数据权限配置的用户体验，让复杂的权限管理变得直观和高效。 