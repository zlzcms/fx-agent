<script setup lang="ts">
import { ref } from 'vue';
import { useVbenForm } from '#/adapter/form';
import { useOutputSchema } from '../data';
import { TableFieldConfig } from '#/components/table-field-config';
import type { TableFieldConfigItem } from '#/components/table-field-config';
import { MarkdownEditor } from '#/components/markdown-it-vue';
import type { DocumentConfigItem } from '#/components/markdown-it-vue';

// Props
const props = defineProps({
  tableFieldsConfig: {
    type: Array,
    default: () => [],
  },
  documentConfig: {
    type: Object,
    default: () => ({ template: 'standard', content: '' }),
  },
  outputFormat: {
    type: String,
    default: 'both',
  },
  outputData: {
    type: Object,
    default: () => ({
      include_charts: false,
      auto_export: false,
      export_formats: [],
    }),
  },
});

// Emits
const emit = defineEmits([
  'update:tableFieldsConfig',
  'update:documentConfig',
  'update:outputFormat',
  'update:outputData',
  'tableFieldConfigChange',
  'documentConfigChange',
]);

// 手动跟踪状态
const manualTableFieldsConfig = ref<TableFieldConfigItem[]>(props.tableFieldsConfig as TableFieldConfigItem[]);
const manualDocumentConfig = ref<DocumentConfigItem>(props.documentConfig as DocumentConfigItem);

/**
 * 输出配置表单
 */
const [OutputForm, outputFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useOutputSchema(),
});

// 安全获取输出配置表单值的专用函数
async function getOutputFormValuesSafely() {
  // 对于输出配置，最可靠的数据源是响应式状态 `outputFormat` 和 `outputData`
  const values = {
    output_format: props.outputFormat,
    value: {
      include_charts: props.outputData.include_charts,
      auto_export: props.outputData.auto_export,
      export_formats: props.outputData.export_formats,
    }
  };

  return Promise.resolve(values);
}

// 表格字段配置变化处理
function handleTableFieldConfigChange(config: any[]) {
  manualTableFieldsConfig.value = config || [];
  emit('tableFieldConfigChange', config);
  emit('update:tableFieldsConfig', config);
}

// 文档配置变化处理
function handleDocumentConfigChange(config: any) {
  manualDocumentConfig.value = config || manualDocumentConfig.value;
  emit('documentConfigChange', config);
  emit('update:documentConfig', config);
}

// 暴露给父组件的方法
defineExpose({
  outputFormApi,
  getOutputFormValuesSafely,
});
</script>

<template>
  <div>
    <OutputForm />
    <div class="mt-4">
      <h3 class="text-lg font-medium text-gray-900 mb-2">表格字段配置</h3>
      <TableFieldConfig
        :modelValue="manualTableFieldsConfig"
        @change="handleTableFieldConfigChange"
        style="width: 100%"
      />

      <h3 class="text-lg font-medium text-gray-900 mb-2 mt-4">文档内容配置</h3>
      <MarkdownEditor
        :modelValue="manualDocumentConfig"
        @change="handleDocumentConfigChange"
        :height="400"
        style="width: 100%"
      />
    </div>
  </div>
</template>

<style scoped>
/* 在这里添加样式 */
</style>
