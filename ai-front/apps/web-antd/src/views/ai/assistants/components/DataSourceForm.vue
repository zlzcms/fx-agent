<script setup lang="ts">
// import { watch } from 'vue'; // 暂时未使用
import { useVbenForm } from '#/adapter/form';
import { RiskType } from '#/api/risk';

import { useDataSourceSchema } from '../data';

// Props
const props = defineProps({
  dataSourceOptions: {
    type: Array,
    default: () => [],
  },
  selectedDataSources: {
    type: Array,
    default: () => [],
  },
  dataSourceDetails: {
    type: Object,
    default: () => ({}),
  },
  defaultLimit: {
    type: Number,
    default: 200,
  },
});

// Emits
// const _emit = defineEmits([
//   'update:selectedDataSources',
//   'dataSourceSelect',
//   'dataSourceDeselect',
//   'dataSourceChange',
//   'dataPermissionTypeChange',
//   'openSelectionModal',
// ]);

/**
 * 数据源表单
 */
const [DataSourceForm, dataSourceFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useDataSourceSchema(),
});

// 安全获取数据源表单值的专用函数
async function getDataSourceFormValuesSafely() {
  // 策略1: 直接尝试从表单API获取
  try {
    const values = await Promise.race([
      dataSourceFormApi.getValues(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('表单API获取超时')), 500),
      ),
    ]);

    // 确保关键字段有值
    values.data_permission = values.data_permission || RiskType.ALL_EMPLOYEE;
    values.data_permission_values = values.data_permission_values || [];
    values.data_time_range_type = values.data_time_range_type || 'month';
    values.data_time_value = values.data_time_value || 1;

    return values;
  } catch {
    // 预期会失败，由策略2处理
  }

  // 确保从表单中直接获取值
  let directFormValues = {};
  try {
    directFormValues = (await dataSourceFormApi.getValues()) || {};
  } catch (error) {
    console.error('获取表单值失败:', error);
  }

  // 策略2: 使用响应式状态和默认值
  const baseValues = {
    data_sources: props.selectedDataSources || [],
    data_limit: props.defaultLimit,

    // 获取数据权限 - 使用表单值或默认值
    data_permission: (directFormValues as any).data_permission || RiskType.ALL_EMPLOYEE, // 默认值为全体员工

    // 获取数据权限值列表
    data_permission_values: (directFormValues as any).data_permission_values || [],

    // 获取时间范围类型
    data_time_range_type: (directFormValues as any).data_time_range_type || 'month',

    // 获取时间值
    data_time_value: (directFormValues as any).data_time_value || 1,
  };

  return baseValues;
}

// 暴露给父组件的方法
defineExpose({
  dataSourceFormApi,
  getDataSourceFormValuesSafely,
});
</script>

<template>
  <div>
    <DataSourceForm />
  </div>
</template>

<style scoped>
/* 在这里添加样式 */
</style>
