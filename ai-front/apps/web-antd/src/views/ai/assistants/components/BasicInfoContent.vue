<script setup lang="ts">
import type { DocumentConfigItem } from '#/components/markdown-it-vue';
import type { TableFieldConfigItem } from '#/components/table-field-config';

import { computed } from 'vue';

import { $t } from '@vben/locales';

import { useVbenForm } from '#/adapter/form';
import { MarkdownEditor } from '#/components/markdown-it-vue';
import { TableFieldConfig } from '#/components/table-field-config';
import TextInputWithPolish from '#/components/text-input-with-polish/TextInputWithPolish.vue';

import { useBasicInfoPart1Schema, useDataSourceSchema } from '../data';

interface Props {
  modelDefinitionValue: string;
  manualTableFieldsConfig: TableFieldConfigItem[];
  manualDocumentConfig: DocumentConfigItem;
  aiPolishLoading: boolean;
}

interface Emits {
  (e: 'update:modelDefinitionValue', value: string): void;
  (e: 'update:manualTableFieldsConfig', value: TableFieldConfigItem[]): void;
  (e: 'update:manualDocumentConfig', value: DocumentConfigItem): void;
  (e: 'aiPolish'): void;
  (e: 'tableFieldConfigChange', config: TableFieldConfigItem[]): void;
  (e: 'documentConfigChange', config: DocumentConfigItem): void;
  (e: 'dataRangeLimitChange', value: Record<string, any>): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const [BasicFormPart1, basicFormPart1Api] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'w-full',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useBasicInfoPart1Schema(),
});

const [DataSourceForm, dataSourceFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'w-full',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useDataSourceSchema(),
});

const modelDefinitionValue = computed({
  get: () => props.modelDefinitionValue,
  set: (value: string) => emit('update:modelDefinitionValue', value),
});

const manualTableFieldsConfig = computed({
  get: () => props.manualTableFieldsConfig,
  set: (value: TableFieldConfigItem[]) => emit('update:manualTableFieldsConfig', value),
});

const manualDocumentConfig = computed({
  get: () => props.manualDocumentConfig,
  set: (value: DocumentConfigItem) => emit('update:manualDocumentConfig', value),
});

const handleModelDefinitionChange = (value: string) => {
  emit('update:modelDefinitionValue', value);
};

const handleAIPolish = () => {
  emit('aiPolish');
};

const handleTableFieldConfigChange = (config: TableFieldConfigItem[]) => {
  emit('tableFieldConfigChange', config);
};

const handleDocumentConfigChange = (config: DocumentConfigItem) => {
  emit('documentConfigChange', config);
};

defineExpose({
  basicFormPart1Api,
  dataSourceFormApi,
});
</script>

<template>
  <div class="basic-info-content w-full">
    <div class="flex w-full" style="display: flex; width: 100%">
      <div class="left-panel">
        <BasicFormPart1 />

        <div class="pl-10 mb-6">
          <TextInputWithPolish
            v-model="modelDefinitionValue"
            :label="$t('@ai-assistants.modelDefinition')"
            :description="$t('@ai-assistants.modelDefinitionDescription')"
            :placeholder="$t('@ai-assistants.pleaseInputModelDetailedDefinition')"
            :hint="
              $t('@ai-assistants.supportDetailedDescriptionOfModelFeaturesAndApplicationScenarios')
            "
            :max-length="1000"
            :rows="4"
            :polish-loading="aiPolishLoading"
            i18n-prefix="@ai-assistants"
            @polish="handleAIPolish"
            @update:model-value="handleModelDefinitionChange"
          />
        </div>

        <DataSourceForm />
      </div>

      <div class="right-panel">
        <div class="text-base text-gray-900 mb-2">
          {{ $t('@ai-assistants.tableFieldConfig') }}
        </div>
        <TableFieldConfig
          v-model="manualTableFieldsConfig"
          @change="handleTableFieldConfigChange"
          style="width: 100%"
        />
        <h3 class="text-base text-gray-900 mb-2 mt-4">
          {{ $t('@ai-assistants.documentContentConfig') }}
        </h3>
        <MarkdownEditor
          v-model="manualDocumentConfig"
          @change="handleDocumentConfigChange"
          :height="600"
          style="width: 100%"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.basic-info-content {
  width: 100%;
  max-width: 100%;
}

.left-panel,
.right-panel {
  flex: 1;
  width: 50%;
  min-width: 0; /* 防止flex项目溢出 */
  padding: 20px;
  background-color: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.left-panel {
  margin-right: 8px;
}

.right-panel {
  margin-left: 8px;
}

.flex {
  display: flex;
  width: 100%;
  max-width: 100%;
}

:deep(.vben-form) {
  width: 100%;
}

:deep(.vben-form .ant-form) {
  width: 100%;
}

:deep(.vben-form label) {
  font-weight: normal !important;
  color: #666 !important;
}

:deep(.vben-form .ant-form-item-label > label) {
  font-weight: normal !important;
  color: #666 !important;
}

:deep(.vben-form .ant-form-item-label > label.ant-form-item-required::before) {
  color: #666 !important;
}
</style>
