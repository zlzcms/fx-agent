/**
 * @Author: zhujinlong
 * @Date:   2025-01-03 15:00:00
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-25 16:17:12
 */
import type { VbenFormSchema } from '#/adapter/form';
import type {
  // OnActionClickFn,
  VxeGridProps,
} from '#/adapter/vxe-table';

import { ref } from 'vue';

import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { z } from '#/adapter/form';
// import type { DataSource } from '#/api';
import {
  getDatabaseListApi,
  getDatabaseTablesWithFieldsApi,
  // toggleDataSourceStatusApi,
  getTableFieldsApi,
} from '#/api';

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'collection_name',
    label: $t('views.ai.datasources.collectionName'),
    componentProps: {
      placeholder: $t('views.ai.datasources.enterCollectionName'),
    },
  },
];

// 表格列配置
export function useColumns(): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 80,
      minWidth: 80,
    },
    {
      field: 'collection_name',
      title: $t('views.ai.datasources.collectionName'),
      width: 180,
      minWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'collection_description',
      title: $t('views.ai.datasources.collectionDescription'),
      minWidth: 200,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || $t('views.ai.datasources.noDescription');
      },
    },
    // {
    //   field: 'data_sources_count',
    //   title: $t('views.ai.datasources.dataSourceCount'),
    //   width: 120,
    //   minWidth: 120,
    //   formatter({ cellValue }) {
    //     return cellValue ? `${cellValue} ${$t('views.ai.datasources.total')}` : `0 ${$t('views.ai.datasources.total')}`;
    //   },
    // },
    // {
    //   field: 'status',
    //   title: $t('views.ai.datasources.status'),
    //   width: 100,
    //   minWidth: 100,
    //   cellRender: {
    //     name: 'CellSwitch',
    //     attrs: {
    //       beforeChange: async (newVal: boolean, row: DataSource) => {
    //         try {
    //           await toggleDataSourceStatusApi(row.id, newVal);
    //           const successMessage = newVal
    //             ? $t('views.ai.datasources.toggleStatusSuccess')
    //             : $t('views.ai.datasources.toggleStatusSuccess');
    //           message.success(successMessage);
    //           return true; // 允许状态更新
    //         } catch (error) {
    //           console.error($t('views.ai.datasources.toggleStatusFailed'), error);
    //           message.error($t('views.ai.datasources.toggleStatusFailed'));
    //           return false; // 阻止状态更新
    //         }
    //       },
    //     },
    //     props: {
    //       checkedValue: true,
    //       unCheckedValue: false,
    //     },
    //   },
    // },
    {
      field: 'created_time',
      title: $t('views.ai.datasources.createdTime'),
      width: 180,
      minWidth: 160,
    },
    {
      field: 'updated_time',
      title: $t('views.ai.datasources.updatedTime'),
      width: 180,
      minWidth: 160,
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    // {
    //   field: 'operation',
    //   title: $t('page.table.operation'),
    //   align: 'center',
    //   fixed: 'right',
    //   width: 160,
    //   minWidth: 160,
    //   cellRender: {
    //     attrs: {
    //       nameField: 'collection_name',
    //       onClick: onActionClick,
    //     },
    //     name: 'CellOperation',
    //     options: ['view', 'edit', 'delete'],
    //   },
    // },
  ];
}

// 数据库选项
export const databaseOptions = ref<{ description?: string; label: string; value: string }[]>([]);
// 数据表选项
export const tableOptions = ref<{ description?: string; label: string; value: string }[]>([]);
// 选中的数据源列表
export const selectedDataSources = ref<
  Array<{
    database_name: string;
    description: string;
    fields?: Array<{
      description?: string;
      field_name: string;
      field_type: string;
    }>;
    selected_field?: string;
    status: boolean;
    table_name: string;
  }>
>([]);

// 字段选择相关的状态
export const fieldSelections = ref<Map<string, string>>(new Map());
export const loadingFields = ref<Map<string, boolean>>(new Map());

// 加载数据库列表
export async function loadDatabaseOptions() {
  try {
    const response = await getDatabaseListApi();
    databaseOptions.value = response.map((db) => ({
      label: db.name,
      value: db.name,
      description: db.description,
    }));
  } catch (error) {
    console.error($t('views.ai.datasources.loadDatabaseFailed'), error);
    databaseOptions.value = [];
  }
}

// 加载数据表列表
export async function loadTableOptions(databaseName: string) {
  if (!databaseName) {
    tableOptions.value = [];
    return;
  }

  try {
    const response = await getDatabaseTablesWithFieldsApi(databaseName);
    // 从树形结构中提取表名
    const tables = response.filter((node) => node.type === 'table');
    tableOptions.value = tables.map((table) => ({
      label: table.name,
      value: table.name,
      description: table.description || '',
    }));
  } catch (error) {
    console.error($t('views.ai.datasources.loadTableFailed'), error);
    tableOptions.value = [];
  }
}

// 添加数据源到已选择列表
export async function addDataSource(databaseName: string, tableName: string) {
  // 检查是否已存在
  const exists = selectedDataSources.value.some(
    (ds) => ds.database_name === databaseName && ds.table_name === tableName,
  );

  if (exists) {
    message.warning($t('views.ai.datasources.dataSourceExists'));
    return false;
  }

  // 获取表信息
  const tableInfo = tableOptions.value.find((t) => t.value === tableName);

  // 添加到选择列表
  const newDataSource = {
    database_name: databaseName,
    table_name: tableName,
    description: tableInfo?.description || '',
    status: true,
    selected_field: '',
    fields: [],
  };

  selectedDataSources.value.push(newDataSource);

  // 自动加载该表的字段信息
  const fields = await loadTableFields(databaseName, tableName);
  const dataSourceIndex = selectedDataSources.value.findIndex(
    (ds) => ds.database_name === databaseName && ds.table_name === tableName,
  );

  if (dataSourceIndex !== -1) {
    const ds = selectedDataSources.value[dataSourceIndex];
    if (ds) {
      ds.fields = fields;
      if (fields.length > 0 && fields[0]) {
        ds.selected_field = fields[0].field_name;
        const key = `${databaseName}.${tableName}`;
        fieldSelections.value.set(key, fields[0].field_name);
      }
    }
  }
}

// 新增：加载表字段信息
export async function loadTableFields(databaseName: string, tableName: string) {
  const key = `${databaseName}.${tableName}`;
  loadingFields.value.set(key, true);

  try {
    const fields = await getTableFieldsApi(databaseName, tableName);
    return (fields || []).map((field) => ({
      field_name: field.name || '',
      field_type: field.field_type || 'unknown',
      description: field.description || '',
    }));
  } catch (error) {
    console.error('加载表字段失败:', error);
    return [];
  } finally {
    loadingFields.value.set(key, false);
  }
}

// 新增：更新字段选择
export function updateFieldSelection(databaseName: string, tableName: string, fieldName: string) {
  const key = `${databaseName}.${tableName}`;
  fieldSelections.value.set(key, fieldName);

  // 同时更新selectedDataSources中的选择
  const dataSourceIndex = selectedDataSources.value.findIndex(
    (ds) => ds.database_name === databaseName && ds.table_name === tableName,
  );

  if (dataSourceIndex !== -1 && selectedDataSources.value[dataSourceIndex]) {
    selectedDataSources.value[dataSourceIndex].selected_field = fieldName;
  }
}

// 新增：获取字段选择
export function getFieldSelection(databaseName: string, tableName: string): string {
  const key = `${databaseName}.${tableName}`;
  return fieldSelections.value.get(key) || '';
}

// 新增：获取字段加载状态
export function isLoadingFields(databaseName: string, tableName: string): boolean {
  const key = `${databaseName}.${tableName}`;
  return loadingFields.value.get(key) || false;
}

// 从选中列表中移除数据源
export function removeDataSource(index: number) {
  const removedDataSource = selectedDataSources.value[index];
  if (removedDataSource) {
    const key = `${removedDataSource.database_name}.${removedDataSource.table_name}`;
    // 清理相关的字段选择状态
    fieldSelections.value.delete(key);
    loadingFields.value.delete(key);
  }
  selectedDataSources.value.splice(index, 1);
}

// 更新数据源描述
export function updateDataSourceDescription(index: number, description: string) {
  if (selectedDataSources.value[index]) {
    selectedDataSources.value[index].description = description;
  }
}

// 更新数据源状态
export function updateDataSourceStatus(index: number, status: boolean) {
  if (selectedDataSources.value[index]) {
    selectedDataSources.value[index].status = status;
  }
}

// 清空选中的数据源
export function clearSelectedDataSources() {
  selectedDataSources.value = [];
  // 清空所有字段选择状态
  fieldSelections.value.clear();
  loadingFields.value.clear();
}

// 添加表单配置 - 集合创建表单
export function useAddSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'collection_name',
      label: '集合名称',
      rules: z.string().min(1, { message: '请输入集合名称' }),
      componentProps: {
        placeholder: '请输入集合名称',
      },
    },
    {
      component: 'Textarea',
      fieldName: 'collection_description',
      label: '集合描述',
      componentProps: {
        placeholder: '请输入集合描述',
        rows: 3,
      },
    },
    {
      component: 'Switch',
      fieldName: 'status',
      label: '启用状态',
      defaultValue: true,
    },
  ];
}
