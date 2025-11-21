/**
 * @Author: zhujinlong
 * @Date:   2025-06-17 10:17:17
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-23 17:31:10
 */
/**
 * 表格字段配置组件相关类型定义
 */

// 字段配置项接口
export interface TableFieldConfigItem {
  fieldName: string;
  fieldType: 'string' | 'number' | 'date' | 'boolean';
  fieldDesc: string;
}

// 内部字段项接口（包含ID）
export interface TableFieldItem extends TableFieldConfigItem {
  id?: string;
}

// 组件属性接口
export interface TableFieldConfigProps {
  modelValue?: TableFieldConfigItem[];
}

// 组件事件接口
export interface TableFieldConfigEmits {
  (e: 'update:modelValue', value: TableFieldConfigItem[]): void;
  (e: 'change', value: TableFieldConfigItem[]): void;
}

// 字段类型选项 - 使用函数来动态生成，避免模块级别的$t调用
export function getFieldTypeOptions($t: any) {
  return [
    { label: $t('page.components.tableFieldConfig.fieldTypes.string'), value: 'string' as const },
    { label: $t('page.components.tableFieldConfig.fieldTypes.number'), value: 'number' as const },
    { label: $t('page.components.tableFieldConfig.fieldTypes.date'), value: 'date' as const },
    { label: $t('page.components.tableFieldConfig.fieldTypes.boolean'), value: 'boolean' as const },
] as const;
}

// 字段类型映射 - 使用函数来动态生成
export function getFieldTypeMap($t: any) {
  return {
    string: $t('page.components.tableFieldConfig.fieldTypes.string'),
    number: $t('page.components.tableFieldConfig.fieldTypes.number'),
    date: $t('page.components.tableFieldConfig.fieldTypes.date'),
} as const;
}
