<script setup lang="ts">
import type { CreateAIAssistantParams, PersonnelData, UpdateAIAssistantParams } from '#/api';
import type { DocumentConfigItem } from '#/components/markdown-it-vue';
import type { TableFieldConfigItem } from '#/components/table-field-config';

import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import {
  createAIAssistantApi,
  getAIAssistantApi,
  getAllAIModelsApi,
  getAllAssistantTypesApi,
  getAllDataSourcesApi,
  getAllPersonnelApi,
  getDataPermissionsApi,
  getDataSourceApi,
  getNotificationMethodsApi,
  getTableFieldsApi,
  polishContentApi,
  quickCreateAssistantApi,
  updateAIAssistantApi,
} from '#/api';
import { RiskType } from '#/api/risk';
import FormHeader from '#/components/form-header/FormHeader.vue';
import TrainingDetailModal from '#/components/training-records/TrainingDetailModal.vue';
import TrainingRecordsList from '#/components/training-records/TrainingRecordsList.vue';
import { useTrainingLogs } from '#/composables/useTrainingLogs';

import BasicInfoContent from './components/BasicInfoContent.vue';
import { useOutputSchema } from './data';
import MockTraining from './mock-training.vue';

import 'highlight.js/styles/github.css';

const tabItems = [
  { key: 'assistant', label: $t('@ai-assistants.basicInfo') },
  { key: 'test', label: $t('@ai-assistants.mockTraining') },
];
const activeTab = ref('assistant');
const handleTabChange = (tab: string) => {
  activeTab.value = tab;
};

const handleCancel = () => {
  router.go(-1);
};
const router = useRouter();
const route = useRoute();

const isEditMode = computed(() => !!route.params.id);
const assistantId = computed(() => route.params.id as string);

const loading = ref(false); // 页面加载状态
const submitLoading = ref(false); // 提交加载状态（与loading合并使用）

const modelOptions = ref<Array<{ label: string; value: string }>>([]);
const dataSourceOptions = ref<Array<{ label: string; value: string }>>([]);
const personnelOptions = ref<Array<{ label: string; value: string }>>([]);
const notificationMethodOptions = ref<Array<{ label: string; value: string }>>([]);
const assistantTypeOptions = ref<Array<{ label: string; value: string }>>([]);
const dataPermissionOptions = ref<Array<any>>([]);
const responsibleOptions = ref<Array<{ label: string; value: string }>>([]);
const responsibleSearchLoading = ref(false);

const manualTableFieldsConfig = ref<any[]>([]);
const manualDocumentConfig = ref<any>({
  template: 'standard',
  content: '',
});
const manualResponsiblePersons = ref<PersonnelData[]>([]);
const manualNotificationMethods = ref<string[]>([]);

const dataSourceDetails = ref<Record<string, any>>({});
const selectedDataSources = ref<string[]>([]);
const primaryDataSourceId = ref<string | undefined>('');
const tableFieldsConfig = ref<TableFieldConfigItem[]>([]);
const tableFieldsCache = ref<Record<string, any[]>>({});
const fieldSelectionStates = ref<Record<string, Record<string, boolean>>>({});
const outputFormat = ref<'both' | 'document' | 'table'>('both');
const dataSourcesLinkField = ref<
  Record<string, { fromField: null | string; fromTable: null | string }>
>({});

const documentConfig = ref<DocumentConfigItem>({
  template: 'standard',
  content: '',
});

const outputData = ref<{
  auto_export: boolean;
  export_formats: string[];
  include_charts: boolean;
}>({
  include_charts: false,
  auto_export: false,
  export_formats: [],
});

const aiPolishLoading = ref(false);
const modelDefinitionValue = ref('');

const mockTrainingVisible = ref(false);

const basicInfoContentRef = ref();

const [, outputFormApi] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useOutputSchema(),
});

const {
  trainingLogs,
  trainingDetailVisible,
  selectedTraining,
  loadTrainingLogs,
  refreshTrainingLogs,
  handleTrainingLogPageChange,
  viewTrainingDetail,
} = useTrainingLogs(assistantId, 'ai_assistant', '@ai-assistants');

async function loadAssistantDetail() {
  if (!isEditMode.value || !assistantId.value) {
    return;
  }

  loading.value = true;
  try {
    const detail = await getAIAssistantApi(assistantId.value);

    const responsiblePersons = detail.responsible_persons
      ? detail.responsible_persons.map((person: any) => {
          return person.personnel_id;
        })
      : [];
    updateBasicFormSchema([
      {
        fieldName: 'responsible_persons',
        componentProps: {
          options: detail.responsible_persons
            ? detail.responsible_persons.map((person: any) => {
                return {
                  label: person.username,
                  value: person.personnel_id,
                  email: person.email,
                };
              })
            : [],
        },
      },
    ]);
    const notificationMethods = detail.notification_methods
      ? detail.notification_methods.map((method: any) =>
          typeof method === 'string' ? method : method.id,
        )
      : [];

    const dataTimeRangeType = detail.data_time_range_type || 'month';
    const dataTimeValue = detail.data_time_value || 1;

    const basicFormValues = {
      id: detail.id,
      name: detail.name,
      type: detail.type,
      assistant_type_id: detail.assistant_type_id,
      ai_model_id: detail.ai_model_id,
      avatar: detail.avatar ? [{ url: detail.avatar, thumbUrl: detail.avatar }] : [],
      description: detail.description,
      model_definition: detail.model_definition,
      execution_frequency: detail.execution_frequency || 'daily',
      execution_time: detail.execution_time || '09:00',
      execution_minutes: detail.execution_minutes || 30,
      execution_hours: detail.execution_hours || 2,
      execution_weekday: detail.execution_weekday || '1',
      execution_weekly_time: detail.execution_weekly_time || '19:00',
      execution_day: detail.execution_day || '30',
      execution_monthly_time: detail.execution_monthly_time || '19:00',
      responsible_persons: responsiblePersons,
      notification_methods: notificationMethods,
      status: detail.status === undefined ? true : detail.status,
      is_template: detail.is_template || false,
      is_view_myself: detail.is_view_myself || false,
    };

    setBasicFormValues(basicFormValues);

    modelDefinitionValue.value = detail.model_definition || '';

    const dataSourceIds = detail.data_sources?.map((ds) => ds.collection_id) || [];
    selectedDataSources.value = [...new Set(dataSourceIds)];

    primaryDataSourceId.value =
      detail.settings?.primaryDataSourceId ||
      (selectedDataSources.value.length > 0 ? selectedDataSources.value[0] : '');

    if (basicInfoContentRef.value?.dataSourceFormApi) {
      basicInfoContentRef.value.dataSourceFormApi.setValues({
        data_sources: selectedDataSources.value,
        data_time_range_type: dataTimeRangeType,
        data_time_value: dataTimeValue,
      });
    }

    manualResponsiblePersons.value = detail.responsible_persons
      ? (detail.responsible_persons as PersonnelData[])
      : [];
    manualNotificationMethods.value = notificationMethods;

    outputFormat.value = 'both';
    outputFormApi.setFieldValue('output_format', 'both');

    if (detail.settings) {
      if (detail.settings.tableFieldsConfig) {
        tableFieldsConfig.value = detail.settings.tableFieldsConfig;
        manualTableFieldsConfig.value = detail.settings.tableFieldsConfig;
      }
      if (detail.settings.documentConfig) {
        documentConfig.value = detail.settings.documentConfig;
        manualDocumentConfig.value = detail.settings.documentConfig;
      }
      if (detail.settings.fieldSelectionStates) {
        fieldSelectionStates.value = detail.settings.fieldSelectionStates;
      }
    }

    if (detail.output_data) {
      try {
        const parsedOutputData =
          typeof detail.output_data === 'string'
            ? JSON.parse(detail.output_data)
            : detail.output_data;

        if (parsedOutputData.table) {
          try {
            const parsedTableData = safeParseJSON(parsedOutputData.table);
            tableFieldsConfig.value = parsedTableData;
            manualTableFieldsConfig.value = parsedTableData;
          } catch {
            tableFieldsConfig.value = parsedOutputData.table;
            manualTableFieldsConfig.value = parsedOutputData.table;
          }
        }

        if (parsedOutputData.document) {
          documentConfig.value.content = parsedOutputData.document;
          manualDocumentConfig.value = {
            ...manualDocumentConfig.value,
            content: parsedOutputData.document,
          };
        }

        if (parsedOutputData.include_charts !== undefined) {
          outputData.value.include_charts = parsedOutputData.include_charts;
        }
        if (parsedOutputData.auto_export !== undefined) {
          outputData.value.auto_export = parsedOutputData.auto_export;
        }
        if (parsedOutputData.export_formats !== undefined) {
          outputData.value.export_formats = parsedOutputData.export_formats;
        }
      } catch (error) {
        console.error($t('@ai-assistants.parseOutputDataFailed'), error);
        throw error;
      }
    } else {
      console.warn($t('@ai-assistants.usingOldFormat'));
    }

    for (const dataSourceId of selectedDataSources.value) {
      if (!dataSourceDetails.value[dataSourceId]) {
        try {
          const detail = await getDataSourceApi(dataSourceId);
          dataSourceDetails.value[dataSourceId] = detail;
          setDataSourcesLinkField(detail.datasources, dataSourceId);
        } catch (error) {
          console.error($t('@ai-assistants.loadDataSourceDetailFailed', { dataSourceId }), error);
          throw error;
        }
      }
    }

    if (
      documentConfig.value?.content &&
      (!manualDocumentConfig.value?.content || manualDocumentConfig.value.content === '')
    ) {
      manualDocumentConfig.value = {
        ...manualDocumentConfig.value,
        content: documentConfig.value.content,
        template: documentConfig.value.template || 'standard',
      };
    }
  } catch (error: any) {
    console.error($t('@ai-assistants.loadAssistantDetailFailed'), error);
    message.error(
      `${$t('@ai-assistants.loadAssistantDetailFailed')}：${error?.message || $t('@ai-assistants.pleaseRefreshPageAndRetry')}`,
    );
    goBack();
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.go(-1);
}

const assistantName = ref('');

async function updateAssistantName() {
  try {
    if (basicInfoContentRef.value?.basicFormPart1Api) {
      const values = await basicInfoContentRef.value.basicFormPart1Api.getValues();
      assistantName.value = values?.name || '';
    }
  } catch (error) {
    console.warn($t('@ai-assistants.getAssistantNameFailed'), error);
    assistantName.value = '';
  }
}

watch(
  () => basicInfoContentRef.value?.basicFormPart1Api,
  async (api) => {
    if (api) {
      await updateAssistantName();
    }
  },
  { immediate: true },
);

async function handleMockTraining() {
  try {
    await updateAssistantName();
    mockTrainingVisible.value = true;
  } catch (error) {
    console.error($t('@ai-assistants.startMockTestFailed'), error);
    message.error($t('@ai-assistants.startMockTrainingFailed'));
    mockTrainingVisible.value = false;
  }
}

async function fetchLatestFieldInfo() {
  const fieldsInfoMap: Record<string, any[]> = {};
  const fieldInfoPromises: Promise<void>[] = [];

  for (const dataSourceId of selectedDataSources.value) {
    const detail = dataSourceDetails.value[dataSourceId];
    if (!detail || !detail.datasources) continue;

    for (const ds of detail.datasources) {
      if (!ds.database_name || !ds.table_name) {
        console.warn($t('@ai-assistants.dataSourceFieldMissing'), ds);
        continue;
      }

      const tableKey = `${dataSourceId}.${ds.database_name}.${ds.table_name}`;

      const promise = getTableFieldsApi(ds.database_name, ds.table_name)
        .then((fields) => {
          fieldsInfoMap[tableKey] = fields;
        })
        .catch((error) => {
          console.error($t('@ai-assistants.getFieldInfoFailed', { tableKey }), error);
          fieldsInfoMap[tableKey] = tableFieldsCache.value[tableKey] || [];
        });

      fieldInfoPromises.push(promise);
    }
  }

  await Promise.allSettled(fieldInfoPromises);
  return fieldsInfoMap;
}

async function buildDataSourcesConfig() {
  const fieldsInfoMap = await fetchLatestFieldInfo();

  return selectedDataSources.value
    .map((dataSourceId) => {
      const detail = dataSourceDetails.value[dataSourceId];
      if (!detail) {
        console.warn($t('@ai-assistants.dataSourceDetailMissing', { dataSourceId }));
        return null;
      }

      return {
        collection_id: dataSourceId,
        collection_name: detail.collection_name,
        collection_description: detail.collection_description,
        query_name: detail.query_name,
        tables:
          detail.datasources
            ?.map((ds: any) => {
              if (!ds.database_name || !ds.table_name) {
                console.warn($t('@ai-assistants.dataSourceFieldMissing'), ds);
                return null;
              }
              const tableKey = `${dataSourceId}.${ds.database_name}.${ds.table_name}`;
              const fields = fieldsInfoMap[tableKey] || [];
              const selectedFieldIds = fields.map((field) => field.id);
              const selectedFieldNames = fields.map((field) => field.name);

              return {
                database_name: ds.database_name,
                table_name: ds.table_name,
                table_description: ds.description || '',
                data_limit: ds.data_count || 200,
                relation_field: ds.relation_field,
                selected_fields: selectedFieldIds,
                selected_field_names: selectedFieldNames,
              };
            })
            .filter((table: any): table is NonNullable<typeof table> => table !== null) || [],
      };
    })
    .filter((config): config is NonNullable<typeof config> => config !== null);
}

async function handleSave() {
  if (isEditMode.value && !assistantId.value) {
    console.error($t('@ai-assistants.assistantIdEmpty'));
    message.error($t('@ai-assistants.assistantIdCannotBeEmpty'));
    return;
  }

  if (!basicInfoContentRef.value) {
    console.error($t('@ai-assistants.componentNotInitialized'));
    message.error($t('@ai-assistants.pageNotFullyLoaded'));
    return;
  }

  submitLoading.value = true;

  try {
    const basicValid = await validateBasicForms();
    const dataSourceValid = await validateFormSafely(
      basicInfoContentRef.value?.dataSourceFormApi,
      $t('@ai-assistants.dataSource'),
    );
    const outputValid = await validateFormSafely(outputFormApi, $t('@ai-assistants.outputConfig'));

    if (basicValid.valid && dataSourceValid.valid && outputValid.valid) {
      const basicData = await getBasicFormValuesSafely();
      const rawDataSourceValues = await getDataSourceFormValuesSafely();
      const dataSourceData = {
        data_sources: rawDataSourceValues.data_sources || selectedDataSources.value,
        data_time_range_type: rawDataSourceValues.data_time_range_type || 'month',
        data_time_value: rawDataSourceValues.data_time_value || 1,
      };

      let outputFormValues;
      try {
        outputFormValues = await getOutputFormValuesSafely();
      } catch (error) {
        console.warn($t('@ai-assistants.setDataRangeLimitFailed'), error);
        outputFormValues = { value: {} };
      }

      let avatarValue = '';
      if (basicData.avatar && Array.isArray(basicData.avatar) && basicData.avatar.length > 0) {
        const file = basicData.avatar[0];
        avatarValue = file.thumbUrl || file.url || '';
      } else if (typeof basicData.avatar === 'string') {
        avatarValue = basicData.avatar;
      }

      const dataSourcesConfig = await buildDataSourcesConfig();
      const responsiblePersons = manualResponsiblePersons.value || [];
      const notificationMethods = (manualNotificationMethods.value || []).map((method: any) =>
        typeof method === 'string' ? method : method.id,
      );
      const tableOutputData = JSON.stringify(manualTableFieldsConfig.value);
      const documentOutputData = manualDocumentConfig.value.content || '';

      const data: CreateAIAssistantParams | UpdateAIAssistantParams = {
        name: basicData.name || '',
        type: basicData.type || 'data_analysis',
        assistant_type_id: basicData.assistant_type_id || null,
        ai_model_id: basicData.ai_model_id || '',
        avatar: avatarValue,
        description: basicData.description || '',
        model_definition: modelDefinitionValue.value || '',
        execution_frequency: basicData.execution_frequency || 'daily',
        execution_time: basicData.execution_time || '09:00',
        execution_minutes: basicData.execution_minutes,
        execution_hours: basicData.execution_hours,
        execution_weekday: basicData.execution_weekday,
        execution_weekly_time: basicData.execution_weekly_time,
        execution_day: basicData.execution_day,
        execution_monthly_time: basicData.execution_monthly_time,
        responsible_persons: responsiblePersons,
        notification_methods: notificationMethods,
        status: basicData.status === undefined ? true : basicData.status,
        is_template: basicData.is_template || false,
        is_view_myself: basicData.is_view_myself || false,
        data_sources: dataSourcesConfig,
        data_time_range_type: dataSourceData.data_time_range_type || 'month', // 新增字段
        data_time_value: dataSourceData.data_time_value || 1, // 新增字段
        data_permission: rawDataSourceValues.data_permission || RiskType.ALL_EMPLOYEE,
        data_permission_values: rawDataSourceValues.data_permission_values || [],
        output_format: 'both', // 修改为同时支持两种格式
        output_data: JSON.stringify({
          table: tableOutputData, // tableOutputData 已经是字符串格式
          document: documentOutputData, // documentOutputData 是文档内容字符串
          include_charts: outputFormValues?.value?.include_charts || false,
          auto_export: outputFormValues?.value?.auto_export || false,
          export_formats: outputFormValues?.value?.export_formats || [],
        }),
        document_template: documentConfig.value?.template || 'default',
        custom_template:
          documentConfig.value?.template === 'custom'
            ? documentConfig.value?.content || ''
            : undefined,

        settings: {},
      };
      if (isEditMode.value) {
        await updateAIAssistantApi(assistantId.value, data as UpdateAIAssistantParams);
        message.success($t('@ai-assistants.updateAssistantSuccess'));
      } else {
        await createAIAssistantApi(data as CreateAIAssistantParams);
        message.success($t('@ai-assistants.createAssistantSuccess'));
      }

      submitLoading.value = false;
      goBack();
    } else {
      submitLoading.value = false;
      console.warn($t('@ai-assistants.formValidationFailed'));

      if (!basicValid.valid && basicValid.errors && basicValid.errors.length > 0) {
        message.error(`基本信息验证失败: ${basicValid.errors.join(', ')}`);
      }
      if (!dataSourceValid.valid) {
        message.error($t('@ai-assistants.dataSourceValidationFailed'));
      }
      if (!outputValid.valid) {
        message.error($t('@ai-assistants.outputConfigValidationFailed'));
      }
    }
  } catch (error: any) {
    submitLoading.value = false;
    console.error($t('@ai-assistants.saveError'), error);
    message.error(
      `${$t('@ai-assistants.saveFailed')}：${error?.message || $t('@ai-assistants.pleaseRetryAgain')}`,
    );
  }
}

async function loadDynamicData() {
  try {
    const models = await getAllAIModelsApi();
    modelOptions.value = models.map((model) => ({
      label: model.name,
      value: model.id,
    }));

    const assistantTypes = await getAllAssistantTypesApi();
    assistantTypeOptions.value = assistantTypes.map((type) => ({
      label: type.name,
      value: type.id,
    }));

    const dataSources = await getAllDataSourcesApi({ status: true });
    dataSourceOptions.value = dataSources.map((ds) => ({
      label: ds.collection_name,
      value: ds.id,
      description: ds.collection_description,
    }));

    const personnel = await getAllPersonnelApi({ status: true });
    personnelOptions.value = personnel.map((person) => ({
      label: person.name,
      value: person.id,
    }));

    const notificationMethods = await getNotificationMethodsApi();
    notificationMethodOptions.value = notificationMethods
      .filter((method) => method.status)
      .map((method) => ({
        label: method.name,
        value: method.id,
      }));

    const dataPermissions = await getDataPermissionsApi();
    dataPermissionOptions.value = dataPermissions.filter((permission) => permission.status);

    await updateFormOptions();

    if (route.query.from === 'template' && route.query.templateId) {
      await loadTemplateData();
    }

    if (route.query.from === 'quickCreate' && route.query.question) {
      await loadQuickCreateData();
    }
  } catch (error: any) {
    console.error($t('@ai-assistants.loadDynamicDataFailed'), error);
    message.error(
      `${$t('@ai-assistants.loadDataFailed')}：${error?.message || $t('@ai-assistants.pleaseRefreshPageAndRetry')}`,
    );
  }
}

async function loadTemplateData() {
  try {
    const templateId = route.query.templateId as string;
    if (!templateId) return;

    const detail = await getAIAssistantApi(templateId);

    if (!detail) {
      message.warning($t('@ai-assistants.templateDataNotExist'));
      return;
    }

    const responsiblePersons = detail.responsible_persons
      ? detail.responsible_persons.map((person: any) => {
          return person.personnel_id;
        })
      : [];
    updateBasicFormSchema([
      {
        fieldName: 'responsible_persons',
        componentProps: {
          options: detail.responsible_persons
            ? detail.responsible_persons.map((person: any) => {
                return {
                  label: person.username,
                  value: person.personnel_id,
                  email: person.email,
                };
              })
            : [],
        },
      },
    ]);
    const notificationMethods = detail.notification_methods
      ? detail.notification_methods.map((method: any) =>
          typeof method === 'string' ? method : method.id,
        )
      : [];

    const dataTimeRangeType = detail.data_time_range_type || 'month';
    const dataTimeValue = detail.data_time_value || 1;

    const basicFormValues = {
      type: detail.type,
      assistant_type_id: detail.assistant_type_id,
      ai_model_id: detail.ai_model_id,
      avatar: detail.avatar ? [{ url: detail.avatar, thumbUrl: detail.avatar }] : [],
      description: detail.description,
      model_definition: detail.model_definition,
      execution_frequency: detail.execution_frequency || 'daily',
      execution_time: detail.execution_time || '09:00',
      execution_minutes: detail.execution_minutes || 30,
      execution_hours: detail.execution_hours || 2,
      execution_weekday: detail.execution_weekday || '1',
      execution_weekly_time: detail.execution_weekly_time || '19:00',
      execution_day: detail.execution_day || '30',
      execution_monthly_time: detail.execution_monthly_time || '19:00',
      responsible_persons: responsiblePersons,
      notification_methods: notificationMethods,
      status: detail.status === undefined ? true : detail.status,
      is_template: false, // 新创建的助手默认不是模板
      is_view_myself: detail.is_view_myself || false,
    };

    setBasicFormValues(basicFormValues);

    modelDefinitionValue.value = detail.model_definition || '';
    const dataSourceIds = detail.data_sources?.map((ds) => ds.collection_id) || [];
    selectedDataSources.value = [...new Set(dataSourceIds)];

    primaryDataSourceId.value =
      detail.settings?.primaryDataSourceId ||
      (selectedDataSources.value.length > 0 ? selectedDataSources.value[0] : '');

    if (basicInfoContentRef.value?.dataSourceFormApi) {
      basicInfoContentRef.value.dataSourceFormApi.setValues({
        data_sources: selectedDataSources.value,
        data_time_range_type: dataTimeRangeType,
        data_time_value: dataTimeValue,
      });
    }

    if (
      basicInfoContentRef.value?.dataSourceLimitFormPartRef?.dataSourceLimitFormApi &&
      detail.settings?.dataRangeLimitConfig
    ) {
      const limitConfig = detail.settings.dataRangeLimitConfig;
      const formValues: Record<string, any> = {};

      if (limitConfig.limit_types) {
        formValues.limit_types = limitConfig.limit_types;
      }

      if (limitConfig.register_time) {
        formValues.register_time = limitConfig.register_time;
      }

      if (limitConfig.customer) {
        formValues.customer = limitConfig.customer;
        formValues.customer_display = limitConfig.customer_display || [];
      }

      if (limitConfig.agent) {
        formValues.agent = limitConfig.agent;
        formValues.agent_display = limitConfig.agent_display || [];
      }

      if (limitConfig.country) {
        formValues.country = limitConfig.country;
      }

      if (limitConfig.user_tag) {
        formValues.user_tag = limitConfig.user_tag;
      }

      if (limitConfig.kyc_status) {
        formValues.kyc_status = limitConfig.kyc_status;
      }

      try {
        const dataSourceLimitFormPartRef = basicInfoContentRef.value?.dataSourceLimitFormPartRef;
        const dataSourceLimitFormApi = dataSourceLimitFormPartRef?.dataSourceLimitFormApi;

        if (dataSourceLimitFormApi) {
          await dataSourceLimitFormApi.setValues(formValues);
        }
      } catch (error) {
        console.warn($t('@ai-assistants.setDataRangeLimitFailed'), error);
      }
    }

    manualResponsiblePersons.value = detail.responsible_persons
      ? (detail.responsible_persons as PersonnelData[])
      : [];
    manualNotificationMethods.value = notificationMethods;

    if (detail.settings) {
      if (detail.settings.tableFieldsConfig) {
        manualTableFieldsConfig.value = detail.settings.tableFieldsConfig;
      }
      if (detail.settings.documentConfig) {
        manualDocumentConfig.value = detail.settings.documentConfig;
      }
      if (detail.settings.fieldSelectionStates) {
        fieldSelectionStates.value = detail.settings.fieldSelectionStates;
      }
    }

    outputFormat.value = 'both';
    outputFormApi.setFieldValue('output_format', 'both');

    if (detail.settings) {
      if (detail.settings.tableFieldsConfig) {
        tableFieldsConfig.value = detail.settings.tableFieldsConfig;
      }
      if (detail.settings.documentConfig) {
        documentConfig.value = detail.settings.documentConfig;
      }
      if (detail.settings.fieldSelectionStates) {
        fieldSelectionStates.value = detail.settings.fieldSelectionStates;
      }
    }

    if (detail.output_data) {
      try {
        const parsedOutputData =
          typeof detail.output_data === 'string'
            ? JSON.parse(detail.output_data)
            : detail.output_data;

        if (parsedOutputData.table) {
          try {
            const parsedTableData = safeParseJSON(parsedOutputData.table);
            tableFieldsConfig.value = parsedTableData;
            manualTableFieldsConfig.value = parsedTableData;
          } catch {
            tableFieldsConfig.value = parsedOutputData.table;
            manualTableFieldsConfig.value = parsedOutputData.table;
          }
        }

        if (parsedOutputData.document) {
          documentConfig.value.content = parsedOutputData.document;
          manualDocumentConfig.value = {
            ...manualDocumentConfig.value,
            content: parsedOutputData.document,
          };
        }

        if (parsedOutputData.include_charts !== undefined) {
          outputData.value.include_charts = parsedOutputData.include_charts;
        }
        if (parsedOutputData.auto_export !== undefined) {
          outputData.value.auto_export = parsedOutputData.auto_export;
        }
        if (parsedOutputData.export_formats !== undefined) {
          outputData.value.export_formats = parsedOutputData.export_formats;
        }
      } catch (error) {
        console.error($t('@ai-assistants.parseOutputDataFailed'), error);
        throw error;
      }
    }

    for (const dataSourceId of selectedDataSources.value) {
      if (!dataSourceDetails.value[dataSourceId]) {
        try {
          const dataSourceDetail = await getDataSourceApi(dataSourceId);
          dataSourceDetails.value[dataSourceId] = dataSourceDetail;
          setDataSourcesLinkField(dataSourceDetail.datasources, dataSourceId);
        } catch (error) {
          console.error($t('@ai-assistants.loadDataSourceDetailFailed', { dataSourceId }), error);
          throw error;
        }
      }
    }

    if (
      documentConfig.value?.content &&
      (!manualDocumentConfig.value?.content || manualDocumentConfig.value.content === '')
    ) {
      manualDocumentConfig.value = {
        ...manualDocumentConfig.value,
        content: documentConfig.value.content,
        template: documentConfig.value.template || 'standard',
      };
    }

    message.success($t('@ai-assistants.templateDataLoadSuccess'));
  } catch (error: any) {
    console.error($t('@ai-assistants.templateDataLoadFailed', { msg: '' }), error);
    message.error(
      $t('@ai-assistants.templateDataLoadFailed', {
        msg: error?.message || $t('@ai-assistants.retryPlease'),
      }),
    );
  }
}

async function loadQuickCreateData() {
  try {
    const question = route.query.question as string;
    if (!question) return;

    const response = await quickCreateAssistantApi({ question });

    if (!response) {
      message.warning($t('@ai-assistants.quickCreateDataNotAvailable'));
      return;
    }

    const quickCreateData = response;
    const basicFormValues = {
      name: quickCreateData.name || '',
      description: quickCreateData.description || '',
      type: 'data_analysis',
      assistant_type_id: '',
      ai_model_id: '',
      avatar: [],
      model_definition: quickCreateData.model_definition || '',
      execution_frequency: 'daily',
      execution_time: '09:00',
      execution_minutes: 30,
      execution_hours: 2,
      execution_weekday: '1',
      execution_weekly_time: '19:00',
      execution_day: '30',
      execution_monthly_time: '19:00',
      responsible_persons: [],
      notification_methods: [],
      status: true,
      is_template: false,
      is_view_myself: false,
    };

    setBasicFormValues(basicFormValues);
    modelDefinitionValue.value = quickCreateData.model_definition || '';

    if (quickCreateData.table_output && Array.isArray(quickCreateData.table_output)) {
      const tableFields = quickCreateData.table_output;
      manualTableFieldsConfig.value = tableFields;
      tableFieldsConfig.value = tableFields;
    }

    if (quickCreateData.document_output) {
      documentConfig.value.content = quickCreateData.document_output;
      manualDocumentConfig.value = {
        ...manualDocumentConfig.value,
        content: quickCreateData.document_output,
      };
    }

    outputFormat.value = 'both';
    outputFormApi.setFieldValue('output_format', 'both');
    message.success($t('@ai-assistants.quickCreateDataLoadSuccess'));
  } catch (error: any) {
    console.error($t('@ai-assistants.quickCreateDataLoadFailed', { msg: '' }), error);
    message.error(
      $t('@ai-assistants.quickCreateDataLoadFailed', {
        msg: error?.message || $t('@ai-assistants.retryPlease'),
      }),
    );
  }
}

async function updateFormOptions() {
  updateBasicFormSchema([
    {
      fieldName: 'assistant_type_id',
      componentProps: {
        options: assistantTypeOptions.value,
      },
    },
    {
      fieldName: 'ai_model_id',
      componentProps: {
        options: modelOptions.value,
      },
    },
    {
      fieldName: 'responsible_persons',
      componentProps: {
        options:
          responsibleOptions.value.length > 0 ? responsibleOptions.value : personnelOptions.value,
        onSearch: searchResponsible,
        showSearch: true,
        filterOption: false,
        loading: responsibleSearchLoading.value,
        disabled: false, // 始终不禁用输入框
        placeholder: $t('@ai-assistants.pleaseSelectResponsiblePersons'),
      },
    },
    {
      fieldName: 'notification_methods',
      componentProps: {
        options: notificationMethodOptions.value,
        onChange: handleNotificationMethodsChange,
      },
    },
  ]);

  if (assistantTypeOptions.value.length > 0 && assistantTypeOptions.value[0]) {
    try {
      const formValues = await getBasicFormValues();
      if (!formValues.assistant_type_id) {
        setBasicFormValues({ assistant_type_id: assistantTypeOptions.value[0].value });
      }
    } catch {
      setBasicFormValues({ assistant_type_id: assistantTypeOptions.value[0].value });
    }
  }

  if (basicInfoContentRef.value?.dataSourceFormApi) {
    basicInfoContentRef.value.dataSourceFormApi.updateSchema([
      {
        fieldName: 'data_sources',
        componentProps: {
          options: dataSourceOptions.value,
          onSelect: handleDataSourceSelect,
          onDeselect: handleDataSourceDeselect,
          onChange: handleDataSourceChange,
        },
      },
    ]);
  }
}

async function handleDataSourceSelect(value: string, option: any) {
  if (selectedDataSources.value.includes(value)) {
    return;
  }

  try {
    if (!dataSourceDetails.value[value]) {
      try {
        const detail = await getDataSourceApi(value);
        dataSourceDetails.value[value] = detail;
        setDataSourcesLinkField(detail.datasources, value);
      } catch (error) {
        console.error($t('@ai-assistants.getDataSourceDetailFailed', { value }), error);
      }
    }
    if (!primaryDataSourceId.value && selectedDataSources.value.length === 1) {
      primaryDataSourceId.value = value;
    }

    message.success(`已选择数据源: ${option.label}`);
  } catch (error) {
    console.error($t('@ai-assistants.getDataSourceDetailFailed'), error);
    message.error($t('@ai-assistants.getDataSourceDetailFailed'));
  }
}

function handleDataSourceDeselect(value: string, _option: any) {
  selectedDataSources.value = selectedDataSources.value.filter((id) => id !== value);
}

function setDataSourcesLinkField(datasources: any, value: string) {
  if (!dataSourcesLinkField.value[value]) {
    dataSourcesLinkField.value[value] = { fromTable: null, fromField: null };
  }
  if (datasources && datasources.length > 0) {
    const firstTable = datasources[0];
    if (firstTable && dataSourcesLinkField.value[value]) {
      const defaultTable = firstTable.table_name;
      if (defaultTable) {
        dataSourcesLinkField.value[value].fromTable = defaultTable;
      }
    }
    const isMemberTable = ref(false);
    for (const ds of datasources) {
      if (ds.table_name === 't_member' && !isMemberTable.value) {
        isMemberTable.value = true;
      }
    }

    dataSourcesLinkField.value[value].fromField = isMemberTable.value ? 'id' : 'member_id';
  }
}

async function handleDataSourceChange(values: string[]) {
  const uniqueValues = [...new Set(values || [])];
  selectedDataSources.value = uniqueValues;

  if (uniqueValues.length > 0) {
    const primaryExists =
      primaryDataSourceId.value && uniqueValues.includes(primaryDataSourceId.value);
    if (!primaryExists) {
      primaryDataSourceId.value = uniqueValues[0];
    }
  } else {
    primaryDataSourceId.value = '';
  }

  const loadPromises = [];

  for (const value of uniqueValues) {
    if (!dataSourceDetails.value[value]) {
      const loadPromise = (async () => {
        try {
          const detail = await getDataSourceApi(value);
          dataSourceDetails.value[value] = detail;
          setDataSourcesLinkField(detail.datasources, value);
        } catch (error) {
          console.error($t('@ai-assistants.getDataSourceDetailFailed', { value }), error);
        }
      })();

      loadPromises.push(loadPromise);
    }
  }

  if (loadPromises.length > 0) {
    await Promise.all(loadPromises);
  }
}

function handleTableFieldConfigChange(config: any[]) {
  manualTableFieldsConfig.value = config || [];
  tableFieldsConfig.value = config || [];
}

function safeParseJSON(jsonString: any) {
  if (typeof jsonString === 'object' && jsonString !== null) {
    return jsonString;
  }

  if (typeof jsonString === 'string') {
    try {
      return JSON.parse(jsonString);
    } catch (error) {
      console.error($t('@ai-assistants.jsonParseFailed'), error);
      return jsonString; // 解析失败时返回原始字符串
    }
  }

  return {};
}

function handleDocumentConfigChange(config: any) {
  manualDocumentConfig.value = config || manualDocumentConfig.value;
}

function handleResponsiblePersonsChange(values: PersonnelData[]) {
  manualResponsiblePersons.value = values || [];
}

function handleNotificationMethodsChange(values: string[]) {
  manualNotificationMethods.value = values || [];
}

async function validateFormSafely(formApi: any, formName: string) {
  try {
    if (formName === $t('@ai-assistants.dataSource')) {
      const hasSelectedSources = selectedDataSources.value && selectedDataSources.value.length > 0;
      if (!hasSelectedSources) {
        message.error($t('@ai-assistants.pleaseSelectAtLeastOneDataSource'));
        return { valid: false };
      }
      return { valid: true };
    }

    if (formName === $t('@ai-assistants.outputConfig')) {
      const hasValidOutputFormat =
        outputFormat.value && ['both', 'document', 'table'].includes(outputFormat.value);
      if (!hasValidOutputFormat) {
        message.error($t('@ai-assistants.pleaseSelectValidOutputFormat'));
        return { valid: false };
      }
      return { valid: true };
    }

    try {
      const result = await formApi.validate();
      return result;
    } catch (validationError) {
      console.error($t('@ai-assistants.formValidationError', { formName }), validationError);
      return { valid: true };
    }
  } catch (error: any) {
    console.error($t('@ai-assistants.formValidationUnknownError', { formName }), error?.message);
    if (formName === $t('@ai-assistants.dataSource')) {
      return { valid: selectedDataSources.value && selectedDataSources.value.length > 0 };
    }
    if (formName === $t('@ai-assistants.outputConfig')) {
      return { valid: !!outputFormat.value };
    }
    return { valid: false };
  }
}

async function getBasicFormValuesSafely() {
  try {
    const getValuesPromise = getBasicFormValues(); // 调用原始的组合函数

    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error($t('@ai-assistants.basicInfoFormTimeout'))), 1000);
    });

    const values = await Promise.race([getValuesPromise, timeoutPromise]);
    return values;
  } catch {
    return {
      id: undefined,
      name: undefined,
      type: undefined,
      assistant_type_id: undefined,
      ai_model_id: undefined,
      avatar: [],
      description: undefined,
      model_definition: modelDefinitionValue.value || '', // 这个是独立的响应式状态，可以安全获取
      execution_frequency: 'daily',
      execution_time: '09:00',
      execution_minutes: 30,
      execution_hours: 2,
      responsible_persons: manualResponsiblePersons.value,
      notification_methods: manualNotificationMethods.value,
      status: true,
      is_template: false,
      is_view_myself: false,
    };
  }
}

async function getBasicFormValues() {
  if (!basicInfoContentRef.value) {
    throw new Error('BasicInfoContent component not found');
  }

  const part1Values = await basicInfoContentRef.value.basicFormPart1Api.getValues();
  return part1Values;
}

function updateBasicFormSchema(updates: any[]) {
  if (!basicInfoContentRef.value) {
    console.warn('BasicInfoContent component not found');
    return;
  }

  const part1Fields = new Set([
    'ai_model_id',
    'assistant_type_id',
    'avatar',
    'description',
    'model_definition',
    'name',
  ]);

  const part1Updates = updates.filter((update) => part1Fields.has(update.fieldName));

  if (part1Updates.length > 0) {
    basicInfoContentRef.value.basicFormPart1Api.updateSchema(part1Updates);
  }
}

function setBasicFormValues(values: any) {
  if (!basicInfoContentRef.value) {
    console.warn('BasicInfoContent component not found');
    return;
  }

  const part1Fields = new Set([
    'ai_model_id',
    'assistant_type_id',
    'avatar',
    'description',
    'model_definition',
    'name',
  ]);

  const part1Values: any = {};

  Object.keys(values).forEach((key) => {
    if (part1Fields.has(key)) {
      part1Values[key] = values[key];
    }
  });

  basicInfoContentRef.value.basicFormPart1Api.setValues(part1Values);
}

async function validateBasicForms() {
  if (!basicInfoContentRef.value) {
    throw new Error('BasicInfoContent component not found');
  }

  const part1Valid = await basicInfoContentRef.value.basicFormPart1Api.validate();

  const allErrors: string[] = [];
  if (part1Valid.errors) {
    if (Array.isArray(part1Valid.errors)) {
      allErrors.push(...part1Valid.errors);
    } else {
      Object.values(part1Valid.errors).forEach((error) => {
        if (typeof error === 'string') {
          allErrors.push(error);
        }
      });
    }
  }

  return {
    valid: part1Valid.valid,
    errors: allErrors,
  };
}

async function handleAIPolish() {
  if (!modelDefinitionValue.value?.trim()) {
    message.warning($t('@ai-assistants.pleaseInputModelDefinitionContent'));
    return;
  }

  aiPolishLoading.value = true;
  try {
    // 获取助手名称和描述，用于提供更好的上下文
    const basicData = await getBasicFormValuesSafely();

    const response = await polishContentApi({
      content: modelDefinitionValue.value.trim(),
      role: basicData.name || 'AI助手',
      task: '对模型定义进行润色，使其更加专业、清晰和完整，准确描述模型的功能、应用场景和所需能力',
    });

    if (response && response.polished_content) {
      modelDefinitionValue.value = response.polished_content;
      message.success($t('@ai-assistants.aiPolishComplete'));
    } else {
      message.error($t('@ai-assistants.polishFailed'));
    }
  } catch (error: any) {
    console.error($t('@ai-assistants.aiPolishFailed'), error);
    message.error(
      $t('@ai-assistants.aiPolishFailed', {
        msg: error?.message || $t('@ai-assistants.retryPlease'),
      }),
    );
  } finally {
    aiPolishLoading.value = false;
  }
}

async function getDataSourceFormValuesSafely() {
  try {
    if (!basicInfoContentRef.value?.dataSourceFormApi) {
      throw new Error('DataSourceFormApi not available');
    }

    const values = await Promise.race([
      basicInfoContentRef.value.dataSourceFormApi.getValues(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error($t('@ai-assistants.formApiTimeout'))), 500),
      ),
    ]);

    values.data_permission = values.data_permission || RiskType.ALL_EMPLOYEE;
    values.data_permission_values = values.data_permission_values || [];
    values.data_time_range_type = values.data_time_range_type || 'month';
    values.data_time_value = values.data_time_value || 1;

    return values;
  } catch {}

  const formEl = basicInfoContentRef.value?.dataSourceFormApi?.formRef?.value;
  let directFormValues = {};
  if (formEl) {
    try {
      directFormValues = formEl.getFieldsValue(true) || {};
    } catch (error) {
      console.error($t('@ai-assistants.getFormValueFailed'), error);
    }
  }

  const baseValues = {
    data_sources: selectedDataSources.value || [],

    data_permission:
      (directFormValues as any).data_permission ||
      basicInfoContentRef.value?.dataSourceFormApi?.getFieldValue?.('data_permission') ||
      RiskType.ALL_EMPLOYEE,

    data_permission_values:
      (directFormValues as any).data_permission_values ||
      basicInfoContentRef.value?.dataSourceFormApi?.getFieldValue?.('data_permission_values') ||
      [],

    data_time_range_type:
      (directFormValues as any).data_time_range_type ||
      basicInfoContentRef.value?.dataSourceFormApi?.getFieldValue?.('data_time_range_type') ||
      'month',

    data_time_value:
      (directFormValues as any).data_time_value ||
      basicInfoContentRef.value?.dataSourceFormApi?.getFieldValue?.('data_time_value') ||
      1,
  };

  return baseValues;
}

async function getOutputFormValuesSafely() {
  const values = {
    output_format: outputFormat.value,
    value: {
      include_charts: outputData.value.include_charts,
      auto_export: outputData.value.auto_export,
      export_formats: outputData.value.export_formats,
    },
  };

  return values;
}

onMounted(async () => {
  try {
    loading.value = true; // 开始页面加载
    await loadDynamicData();
    await loadAssistantDetail();
    await loadResponsibleOptions();

    if (isEditMode.value && assistantId.value && activeTab.value === 'test') {
      await loadTrainingLogs();
    }
  } catch (error) {
    console.error($t('@ai-assistants.pageInitFailed'), error);
    message.error($t('@ai-assistants.pageLoadFailed'));
  } finally {
    loading.value = false; // 结束页面加载
  }
});

watch(activeTab, (newTab) => {
  if (
    newTab === 'datasource' &&
    selectedDataSources.value.length > 0 && // Ensure the form is synchronized with the current selected data sources
    basicInfoContentRef.value?.dataSourceFormApi
  ) {
    basicInfoContentRef.value.dataSourceFormApi.setValues({
      data_sources: selectedDataSources.value,
      data_limit: 200,
    });
  }

  if (newTab === 'test') {
    loadTrainingLogs();
  }
});

async function loadResponsibleOptions() {
  try {
    responsibleSearchLoading.value = true;
    const res = await getAllPersonnelApi({ status: true });
    const items = res || [];
    responsibleOptions.value = items.map((u: any) => ({
      label: u.name || u.email || `用户${u.id}`,
      value: u.id,
      email: u.email,
    }));
  } catch {
    responsibleOptions.value = [];
  } finally {
    responsibleSearchLoading.value = false;
    updateBasicFormSchema([
      {
        fieldName: 'responsible_persons',
        componentProps: {
          options: responsibleOptions.value,
          loading: false,
          disabled: false, // 加载完成后不禁用输入框
          onChange: (value: any) => {
            const newValues: PersonnelData[] = value.map((v: any) => {
              return {
                personnel_id: `${v.value}`,
                username: v.label,
                email: v.option.email,
              };
            });
            handleResponsiblePersonsChange(newValues);
          },
        },
      },
    ]);
  }
}

async function searchResponsible(keyword: string) {
  if (!keyword || !keyword.trim()) {
    await loadResponsibleOptions();
    return;
  }
  try {
    responsibleSearchLoading.value = true;
    updateBasicFormSchema([
      {
        fieldName: 'responsible_persons',
        componentProps: {
          loading: true,
          disabled: false, // 搜索过程中不禁用输入框
        },
      },
    ]);
    const res = await getAllPersonnelApi({ status: true });
    const items = res || [];
    const filteredItems = items.filter(
      (u: any) =>
        (u.name && u.name.toLowerCase().includes(keyword.toLowerCase())) ||
        (u.email && u.email.toLowerCase().includes(keyword.toLowerCase())),
    );
    responsibleOptions.value = filteredItems.map((u: any) => ({
      label: u.name || u.email || `用户${u.id}`,
      value: u.id,
      email: u.email,
    }));
  } catch {
    responsibleOptions.value = [];
  } finally {
    responsibleSearchLoading.value = false;
    updateBasicFormSchema([
      {
        fieldName: 'responsible_persons',
        componentProps: {
          options: responsibleOptions.value,
          loading: false,
          disabled: false,
          notFoundContent: $t('@ai-assistants.noData'),
        },
      },
    ]);
  }
}
</script>

<template>
  <Page>
    <a-spin
      :spinning="loading"
      :tip="$t('@ai-assistants.pageLoadingTip')"
      size="large"
      class="page-loading-spin"
    >
      <div class="form-container">
        <div class="rounded-lg bg-background p-6 w-full">
          <FormHeader
            :tabs="tabItems"
            :active-tab="activeTab"
            :submit-loading="submitLoading"
            :submit-label="$t('@ai-assistants.confirmPublish')"
            @tab-change="handleTabChange"
            @submit="handleSave"
            @cancel="handleCancel"
          />

          <div v-show="activeTab === 'assistant'">
            <BasicInfoContent
              ref="basicInfoContentRef"
              v-model:model-definition-value="modelDefinitionValue"
              v-model:manual-table-fields-config="manualTableFieldsConfig"
              v-model:manual-document-config="manualDocumentConfig"
              :ai-polish-loading="aiPolishLoading"
              @ai-polish="handleAIPolish"
              @table-field-config-change="handleTableFieldConfigChange"
              @document-config-change="handleDocumentConfigChange"
            />
          </div>
          <div v-show="activeTab === 'test'">
            <TrainingRecordsList
              :loading="trainingLogs.loading"
              :records="trainingLogs.data.items"
              :pagination="trainingLogs.pagination"
              :total="trainingLogs.data.total"
              :show-mock-button="true"
              i18n-prefix="@ai-assistants"
              @refresh="refreshTrainingLogs"
              @mock-training="handleMockTraining"
              @view-detail="viewTrainingDetail"
              @page-change="handleTrainingLogPageChange"
            />

            <TrainingDetailModal
              v-model:visible="trainingDetailVisible"
              :training="selectedTraining"
              i18n-prefix="@ai-assistants"
            />
          </div>
        </div>

        <MockTraining
          v-model:open="mockTrainingVisible"
          :assistant-name="assistantName"
          :assistant-id="assistantId"
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
