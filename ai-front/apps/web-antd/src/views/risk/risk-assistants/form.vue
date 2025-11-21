<script setup lang="ts">
import type { ReportConfigItem, VariableConfigItem } from './data';

import type { CreateRiskAssistantParams, UpdateRiskAssistantParams } from '#/api';
import type { DocumentConfigItem } from '#/components/markdown-it-vue';

import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { Switch as ASwitch, message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import {
  createRiskAssistantApi,
  getAllDataSourcesApi,
  getRiskAssistantApi,
  polishContentApi,
  updateRiskAssistantApi,
} from '#/api';
import FormHeader from '#/components/form-header/FormHeader.vue';
import { MarkdownEditor } from '#/components/markdown-it-vue';
import { TableFieldConfig } from '#/components/table-field-config';
import TextInputWithPolish from '#/components/text-input-with-polish/TextInputWithPolish.vue';
import TrainingDetailModal from '#/components/training-records/TrainingDetailModal.vue';
import TrainingRecordsList from '#/components/training-records/TrainingRecordsList.vue';
import { useTrainingLogs } from '#/composables/useTrainingLogs';

import {
  defaultReportConfig,
  defaultVariableConfig,
  loadAIModelOptions,
  useBasicInfoSchema,
  useDataSourceSchema,
  useReportConfigSchema,
  useVariableConfigSchema,
} from './data';
import MockTraining from './mock-training.vue';

function normalizeStatusValue(status: any): boolean {
  if (typeof status === 'boolean') {
    return status;
  }
  if (typeof status === 'number') {
    return status === 1;
  }
  if (typeof status === 'string') {
    return status === 'true' || status === '1';
  }
  return Boolean(status);
}

function getFieldType(fieldType: string): 'boolean' | 'date' | 'number' | 'string' {
  if (fieldType === 'number') {
    return 'number';
  }
  if (fieldType === 'boolean') {
    return 'boolean';
  }
  if (fieldType === 'date') {
    return 'date';
  }
  return 'string';
}

const router = useRouter();
const route = useRoute();

const isEditMode = computed(() => !!route.params.id);
const assistantId = computed(() => route.params.id as string);

const tabItems = [
  { key: 'basic', label: $t('@risk.risk-assistants.basicInfo') },
  { key: 'mock', label: $t('@risk.risk-assistants.mockRecords') },
];
const activeTab = ref('basic');

const handleTabChange = (tab: string) => {
  activeTab.value = tab;
};

const loading = ref(false); // 页面加载状态
const submitLoading = ref(false); // 提交加载状态
const aiModelOptions = ref<Array<{ label: string; value: string }>>([]);
const aiPolishLoading = ref(false);
const taskPromptValue = ref('');
const assistantStatus = ref(true);
const variableConfig = ref<VariableConfigItem[]>([...defaultVariableConfig]);
const reportConfig = ref<ReportConfigItem>({ ...defaultReportConfig });
const riskType = ref<string>('');

const {
  trainingLogs,
  trainingDetailVisible,
  selectedTraining,
  loadTrainingLogs,
  refreshTrainingLogs,
  handleTrainingLogPageChange,
  viewTrainingDetail,
} = useTrainingLogs(assistantId, 'risk_control_assistant', '@risk.risk-assistants');

const [BasicInfoForm, basicInfoFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useBasicInfoSchema(),
});

const [DataSourceForm, dataSourceFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useDataSourceSchema(),
});

const [VariableConfigForm, variableConfigFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: useVariableConfigSchema(),
});

const [ReportConfigForm, reportConfigFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: useReportConfigSchema(),
});

async function handleAIPolish() {
  if (!taskPromptValue.value?.trim()) {
    message.warning($t('@risk.risk-assistants.pleaseEnterTaskPrompt'));
    return;
  }

  aiPolishLoading.value = true;
  try {
    // 获取助手角色和背景信息，用于提供更好的上下文
    const basicInfo = await basicInfoFormApi.getValues();

    const response = await polishContentApi({
      content: taskPromptValue.value.trim(),
      role: basicInfo.role || '风控助手',
      task: '对任务提示词进行润色，使其更加清晰、准确和专业，确保能够指导风控助手准确执行风险评估任务',
    });

    if (response && response.polished_content) {
      taskPromptValue.value = response.polished_content;
      message.success($t('@risk.risk-assistants.aiPolishComplete'));
    } else {
      message.error($t('@risk.risk-assistants.aiPolishFailed'));
    }
  } catch (error: any) {
    console.error($t('@risk.risk-assistants.aiPolishFailed'), error);
    message.error(
      error?.message
        ? `${$t('@risk.risk-assistants.aiPolishFailed')}：${error.message}`
        : $t('@risk.risk-assistants.aiPolishFailedRetry') ||
            $t('@risk.risk-assistants.aiPolishFailed'),
    );
  } finally {
    aiPolishLoading.value = false;
  }
}

function handleTaskPromptChange(value: string) {
  taskPromptValue.value = value;
  basicInfoFormApi.setFieldValue('task_prompt', value);
}

function handleVariableConfigChange(config: any[]) {
  const convertedConfig: VariableConfigItem[] = config.map((item, index) => ({
    fieldName: item.fieldName || item.field || `${$t('@risk.risk-assistants.name')}${index + 1}`,
    fieldDesc:
      item.fieldDesc || item.title || `${$t('@risk.risk-assistants.description')}${index + 1}`,
    fieldType: getFieldType(item.fieldType),
    required: item.required || false,
  }));
  variableConfig.value = convertedConfig;

  variableConfigFormApi.setFieldValue('variable_config', JSON.stringify(convertedConfig));
}

function handleReportConfigChange(config: DocumentConfigItem) {
  const convertedConfig: ReportConfigItem = {
    template: (config.template as any) || 'standard',
    content: config.content || '',
    sections: reportConfig.value.sections, // 保持现有的sections配置
  };

  reportConfig.value = convertedConfig;

  reportConfigFormApi.setFieldValue('report_config', JSON.stringify(convertedConfig));
}

async function loadDynamicData() {
  try {
    const aiModels = await loadAIModelOptions();
    aiModelOptions.value = aiModels;

    basicInfoFormApi.updateSchema([
      {
        fieldName: 'ai_model_id',
        componentProps: {
          options: aiModelOptions.value,
        },
      },
    ]);

    const dataSources = await getAllDataSourcesApi({ status: true });

    const dataSourceOptions = dataSources.map((ds) => ({
      label: ds.collection_name,
      value: ds.query_name,
      description: ds.collection_description,
    }));

    dataSourceFormApi.updateSchema([
      {
        fieldName: 'data_sources',
        componentProps: {
          options: dataSourceOptions,
        },
      },
    ]);

    dataSourceFormApi.setValues({
      data_time_range_type: 'month',
      data_time_value: 1,
    });
  } catch (error) {
    console.error($t('@risk.risk-assistants.loadDynamicDataFailed'), error);
    message.error($t('@risk.risk-assistants.loadDynamicDataFailed'));
  }
}

async function loadAssistantData() {
  if (!isEditMode.value || !assistantId.value) {
    return;
  }

  loading.value = true;
  try {
    const data = await getRiskAssistantApi(assistantId.value);
    riskType.value = data.risk_type || '';
    basicInfoFormApi.setValues({
      name: data.name,
      ai_model_id: data.ai_model_id,
      role: data.role,
      background: data.background,
      risk_type: data.risk_type,
    });
    taskPromptValue.value = data.task_prompt || '';

    assistantStatus.value = normalizeStatusValue(data.status);

    if (data.variable_config) {
      try {
        const parsedConfig = JSON.parse(data.variable_config);
        if (Array.isArray(parsedConfig)) {
          variableConfig.value = parsedConfig;
        }
      } catch (error) {
        console.error($t('@risk.risk-assistants.parseVariableConfigFailed'), error);
      }
    }

    if (data.report_config) {
      try {
        const parsedConfig = JSON.parse(data.report_config);
        reportConfig.value = { ...defaultReportConfig, ...parsedConfig };
      } catch (error) {
        console.error($t('@risk.risk-assistants.parseReportConfigFailed'), error);
      }
    }

    if ((data as any).setting) {
      try {
        const parsedDataSource = (data as any).setting;
        if (parsedDataSource && Array.isArray(parsedDataSource.data_sources)) {
          dataSourceFormApi.setValues({
            data_sources: parsedDataSource.data_sources,
            data_time_range_type: parsedDataSource.data_time_range_type || 'month',
            data_time_value: parsedDataSource.data_time_value || 1,
          });
        }
      } catch (error) {
        console.error($t('@risk.risk-assistants.parseDataSourceConfigFailed'), error);
      }
    }
  } catch (error: any) {
    console.error($t('@risk.risk-assistants.loadAssistantDataFailed'), error);
    message.error($t('@risk.risk-assistants.loadAssistantDataFailed'));
    goBack();
  } finally {
    loading.value = false;
  }
}

const mockTrainingVisible = ref(false);
const assistantName = ref('');

async function updateAssistantName() {
  try {
    if (basicInfoFormApi) {
      const values = await basicInfoFormApi.getValues();
      assistantName.value = values?.name || '';
    }
  } catch (error) {
    console.warn($t('@risk.risk-assistants.getAssistantNameFailed'), error);
    assistantName.value = '';
  }
}

async function handleMockTraining() {
  await updateAssistantName();
  mockTrainingVisible.value = true;
}

function goBack() {
  router.go(-1);
}

function handleCancel() {
  router.go(-1);
}

async function handleSubmit() {
  try {
    submitLoading.value = true;

    const { valid: basicValid } = await basicInfoFormApi.validate();
    if (!basicValid) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseCompleteBasicInfo'));
      return;
    }

    const basicInfo = await basicInfoFormApi.getValues();
    if (!basicInfo.name?.trim()) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseEnterAssistantName'));
      return;
    }

    if (!basicInfo.background?.trim()) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseEnterBackgroundDescription'));
      return;
    }

    if (!taskPromptValue.value?.trim()) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseEnterTaskPrompt'));
      return;
    }

    if (!variableConfig.value || variableConfig.value.length === 0) {
      activeTab.value = 'variable';
      message.error($t('@risk.risk-assistants.pleaseConfigureAtLeastOneVariable'));
      return;
    }

    if (!reportConfig.value?.content?.trim()) {
      activeTab.value = 'report';
      message.error($t('@risk.risk-assistants.pleaseConfigureReportTemplate'));
      return;
    }

    const { valid: dataSourceValid } = await dataSourceFormApi.validate();

    if (!dataSourceValid) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseCompleteDataSourceConfig'));
      return;
    }

    const dataSource = await dataSourceFormApi.getValues();

    if (!dataSource.data_sources || dataSource.data_sources.length === 0) {
      activeTab.value = 'basic';
      message.error($t('@risk.risk-assistants.pleaseSelectAnalysisDataSource'));
      return;
    }

    const submitData = {
      name: basicInfo.name,
      ai_model_id: basicInfo.ai_model_id,
      role: basicInfo.role,
      background: basicInfo.background,
      task_prompt: taskPromptValue.value,
      variable_config: JSON.stringify(variableConfig.value),
      report_config: JSON.stringify(reportConfig.value),
      status: assistantStatus.value,
      setting: dataSource,
    };

    if (isEditMode.value) {
      await updateRiskAssistantApi(assistantId.value, submitData as UpdateRiskAssistantParams);
      message.success($t('@risk.risk-assistants.updateSuccess'));
    } else {
      await createRiskAssistantApi(submitData as CreateRiskAssistantParams);
      message.success($t('@risk.risk-assistants.addSuccess'));
    }

    goBack();
  } catch (error: any) {
    console.error($t('@risk.risk-assistants.submitFailed'), error);
    message.error(error?.response?.data?.msg || $t('@risk.risk-assistants.submitFailedRetry'));
  } finally {
    submitLoading.value = false;
  }
}

onMounted(async () => {
  await loadDynamicData();

  if (isEditMode.value) {
    await loadAssistantData();
  } else {
    taskPromptValue.value = $t('@risk.risk-assistants.defaultTaskPrompt');
  }
});

watch(activeTab, (newTab) => {
  if (newTab === 'mock') {
    loadTrainingLogs();
  }
});

watch(assistantId, (newId) => {
  if (newId && activeTab.value === 'mock') {
    loadTrainingLogs();
  }
});
</script>

<template>
  <Page>
    <a-spin
      size="large"
      class="page-loading-spin"
      :spinning="loading"
      :tip="$t('@risk.risk-assistants.loadingAssistantInfo')"
    >
      <div class="form-container">
        <div class="rounded-lg bg-background p-6 w-full">
          <FormHeader
            :tabs="tabItems"
            :active-tab="activeTab"
            :submit-loading="submitLoading"
            :submit-label="$t('@risk.risk-assistants.confirmPublish')"
            @tab-change="handleTabChange"
            @submit="handleSubmit"
            @cancel="handleCancel"
          />

          <div v-show="activeTab === 'basic'">
            <div class="grid grid-cols-12 gap-4">
              <div class="col-span-6">
                <BasicInfoForm />

                <div class="pl-8" style="margin-top: 0">
                  <TextInputWithPolish
                    v-model="taskPromptValue"
                    :label="$t('@risk.risk-assistants.taskPrompt')"
                    :description="$t('@risk.risk-assistants.taskPromptDescription')"
                    :placeholder="$t('@risk.risk-assistants.taskPromptPlaceholder')"
                    :hint="$t('@risk.risk-assistants.taskPromptHint')"
                    :max-length="5000"
                    :rows="6"
                    :polish-loading="aiPolishLoading"
                    :required="true"
                    i18n-prefix="@risk.risk-assistants"
                    @polish="handleAIPolish"
                    @update:model-value="handleTaskPromptChange"
                  />
                </div>

                <div class="status-config-area pl-6 mt-6">
                  <div class="flex items-center space-x-4">
                    <label class="text-sm font-medium text-gray-900">
                      {{ $t('@risk.risk-assistants.status') }}：
                    </label>
                    <ASwitch
                      v-model:checked="assistantStatus"
                      :checked-children="$t('@risk.risk-assistants.enabled')"
                      :un-checked-children="$t('@risk.risk-assistants.disabled')"
                    />
                    <span class="text-sm text-gray-500">
                      {{
                        assistantStatus
                          ? $t('@risk.risk-assistants.assistantEnabledHint')
                          : $t('@risk.risk-assistants.assistantDisabledHint')
                      }}
                    </span>
                  </div>
                </div>
                <div class="mt-6">
                  <DataSourceForm />
                </div>
              </div>
              <div class="col-span-6">
                <div class="mb-6">
                  <h3 class="text-lg font-medium mb-2">
                    {{ $t('@risk.risk-assistants.tableFieldConfig') }}
                    <span class="text-red-500">*</span>
                  </h3>
                  <p class="text-gray-600 text-sm">
                    {{ $t('@risk.risk-assistants.tableFieldConfigDescription') }}
                  </p>
                </div>

                <div class="variable-config-wrapper">
                  <TableFieldConfig
                    :model-value="
                      variableConfig.map((item) => ({
                        fieldName: item.fieldName,
                        fieldDesc: item.fieldDesc || '', // 确保fieldDesc不会是undefined
                        fieldType: item.fieldType === 'number' ? 'number' : 'string',
                      }))
                    "
                    @change="handleVariableConfigChange"
                  />
                </div>
                <div class="mt-6">
                  <h3 class="text-lg font-medium mb-2">
                    {{ $t('@risk.risk-assistants.reportConfig') }}
                    <span class="text-red-500">*</span>
                  </h3>
                  <p class="text-gray-600 text-sm">
                    {{ $t('@risk.risk-assistants.reportConfigDescription') }}
                  </p>
                </div>

                <div class="report-config-wrapper">
                  <MarkdownEditor
                    :model-value="{
                      template: reportConfig.template,
                      content: reportConfig.content,
                    }"
                    @change="handleReportConfigChange"
                    :templates="[
                      {
                        value: 'standard',
                        label: $t('@risk.risk-assistants.standardReport'),
                        description: $t('@risk.risk-assistants.standardReportDesc'),
                      },
                      {
                        value: 'detailed',
                        label: $t('@risk.risk-assistants.detailedReport'),
                        description: $t('@risk.risk-assistants.detailedReportDesc'),
                      },
                      {
                        value: 'summary',
                        label: $t('@risk.risk-assistants.summaryReport'),
                        description: $t('@risk.risk-assistants.summaryReportDesc'),
                      },
                      {
                        value: 'custom',
                        label: $t('@risk.risk-assistants.customTemplate'),
                        description: $t('@risk.risk-assistants.customTemplateDesc'),
                      },
                    ]"
                    :placeholder="$t('@risk.risk-assistants.reportTemplatePlaceholder')"
                  />
                </div>
              </div>
            </div>
          </div>

          <div v-show="activeTab === 'mock'">
            <TrainingRecordsList
              :loading="trainingLogs.loading"
              :records="trainingLogs.data.items"
              :pagination="trainingLogs.pagination"
              :total="trainingLogs.data.total"
              :show-mock-button="isEditMode"
              i18n-prefix="@risk.risk-assistants"
              @refresh="refreshTrainingLogs"
              @mock-training="handleMockTraining"
              @view-detail="viewTrainingDetail"
              @page-change="handleTrainingLogPageChange"
            />

            <TrainingDetailModal
              v-model:visible="trainingDetailVisible"
              :training="selectedTraining"
              i18n-prefix="@risk.risk-assistants"
            />
          </div>

          <div style="display: none">
            <VariableConfigForm />
            <ReportConfigForm />
          </div>
        </div>

        <MockTraining
          v-model:open="mockTrainingVisible"
          :assistant-name="assistantName"
          :assistant-id="assistantId"
          :risk-type="riskType"
        />
      </div>
    </a-spin>
  </Page>
</template>
<style scoped src="./form.style.css"></style>

<style scoped>
.page-loading-spin {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.page-loading-spin :deep(.ant-spin-container) {
  width: 100%;
  height: 100%;
}

.form-container {
  width: 100%;
  max-width: 100%;
  padding: 0;
  margin: 0;
}

.rounded-lg.bg-background {
  width: 100%;
  max-width: 100%;
}
</style>
