import type { ComputedRef } from 'vue';

import type { AISubscription, CreateAISubscriptionParams, UpdateAISubscriptionParams } from '#/api';

import { nextTick, ref } from 'vue';

import { $t } from '@vben/locales';

import { message, Modal } from 'ant-design-vue';

import { createAISubscriptionApi, deleteAISubscriptionApi, updateAISubscriptionApi } from '#/api';
import { SubscriptionType } from '#/types/subscription';

import { generatePlanCycleDescription } from '../data';

interface CrudProps {
  options: {
    assistantOptionsByType: ComputedRef<Record<string, any[]>>;
    loadAgentByIds?: (ids: string[]) => Promise<void>;
    loadCustomerByIds?: (ids: string[]) => Promise<void>;
    loadUserByIds?: (ids: string[]) => Promise<void>;
    notificationMethodOptions?: ComputedRef<any[]>;
    responsibleOptions: ComputedRef<any[]>;
  };
  gridApi: any;
}

// 扩展AISubscription接口以包含设置字段
interface ExtendedAISubscription extends AISubscription {
  setting?: Record<string, any>;
}

export function useSubscriptionCrud(props: CrudProps) {
  const { options, gridApi } = props;

  // Modal and Form APIs
  const addModalApi = ref<any>();
  const editModalApi = ref<any>();
  const addFormApi = ref<any>();
  const editFormApi = ref<any>();

  // State
  const editSubscriptionId = ref('');
  const editLoading = ref(false);

  function registerModal(type: 'add' | 'edit', modalApi: any, formApi: any) {
    if (type === 'add') {
      addModalApi.value = modalApi;
      addFormApi.value = formApi;
    } else {
      editModalApi.value = modalApi;
      editFormApi.value = formApi;
    }
  }

  function setupFormListeners(formApi: any) {
    formApi.updateSchema?.([
      {
        fieldName: 'limit_types',
        componentProps: {
          onChange: (selected: string[]) => {
            const fieldsToClear = {
              register_time: 'register_time',
              customer: 'customer',
              agent: 'agent',
              country: 'country',
              user_tag: 'user_tag',
              kyc: 'kyc_status',
            };
            Object.entries(fieldsToClear).forEach(([type, field]) => {
              if (!selected?.includes(type)) {
                formApi.setFieldValue?.(field, undefined);
              }
            });
          },
        },
      },
    ]);
  }

  // Data transformation
  function mapRowToFormData(row: ExtendedAISubscription) {
    const dataSourceLimit = row.setting?.dataSourceLimit || {};
    const limitTypes = dataSourceLimit.limit_types || [];

    const formData: any = {
      ...row,
      notification_recipients:
        row.responsible_persons?.map((p) => (typeof p === 'string' ? p : p.personnel_id)) || [],
      notification_methods: Array.isArray(row.notification_methods)
        ? row.notification_methods.map((m) => (typeof m === 'string' ? m : String(m.id || m)))
        : [],
      limit_types: limitTypes,
    };

    // Only include fields for selected limit types
    if (limitTypes.includes('register_time')) {
      formData.register_time = dataSourceLimit.register_time;
    }
    if (limitTypes.includes('customer')) {
      formData.customer = dataSourceLimit.customer || [];
    }
    if (limitTypes.includes('user')) {
      formData.user = dataSourceLimit.user || [];
    }
    if (limitTypes.includes('agent')) {
      formData.agent = dataSourceLimit.agent || [];
    }
    if (limitTypes.includes('country')) {
      formData.country = dataSourceLimit.country || [];
    }
    if (limitTypes.includes('user_tag')) {
      formData.user_tag = dataSourceLimit.user_tag;
    }
    if (limitTypes.includes('kyc')) {
      formData.kyc_status = dataSourceLimit.kyc_status;
    }

    return formData;
  }

  function transformFormDataToSubmit(values: any) {
    const submitData = {
      ...values,
      execution_day: values.execution_day === undefined ? undefined : String(values.execution_day),
      plan_cycle: generatePlanCycleDescription(values.execution_frequency, values),
      responsible_persons:
        values.notification_recipients?.map((id: string) => {
          const person = options.responsibleOptions.value.find((p) => p.value === id);
          return {
            personnel_id: id,
            username: person?.label || id,
            email: person?.email || '',
          };
        }) || [],
      setting: {
        ...values.setting,
        dataSourceLimit: buildDataSourceLimit(values),
      },
    };

    // Delete frontend-only fields
    // Remove unwanted fields using object destructuring
    const {
      id: _id,
      created_at: _created_at,
      updated_at: _updated_at,
      register_time: _register_time,
      customer: _customer,
      agent: _agent,
      country: _country,
      user_tag: _user_tag,
      kyc_status: _kyc_status,
      ...cleanedData
    } = submitData;

    return cleanedData;
  }

  // Build dataSourceLimit object based on selected limit types
  function buildDataSourceLimit(values: any) {
    const limitTypes = values.limit_types || [];
    const dataSourceLimit: any = {
      limit_types: limitTypes,
    };

    // Only include fields for selected limit types
    if (limitTypes.includes('register_time')) {
      dataSourceLimit.register_time = values.register_time;
    }
    if (limitTypes.includes('customer')) {
      dataSourceLimit.customer = values.customer || [];
    }
    if (limitTypes.includes('user')) {
      dataSourceLimit.user = values.user || [];
    }
    if (limitTypes.includes('agent')) {
      dataSourceLimit.agent = values.agent || [];
    }
    if (limitTypes.includes('country')) {
      dataSourceLimit.country = values.country || [];
    }
    if (limitTypes.includes('user_tag')) {
      dataSourceLimit.user_tag = values.user_tag;
    }
    if (limitTypes.includes('kyc')) {
      dataSourceLimit.kyc_status = values.kyc_status;
    }

    return dataSourceLimit;
  }

  // Modal handlers
  async function showCreateModal() {
    addModalApi.value?.open();
    await nextTick();
    const formApi = addFormApi.value;
    if (!formApi) return;
    await formApi.resetForm?.();
    formApi.setValues?.({
      subscription_type: SubscriptionType.SERVER,
      status: true,
    });
    setupFormListeners(formApi);
  }

  async function showEditModal(row: ExtendedAISubscription) {
    editSubscriptionId.value = row.id;
    editModalApi.value?.open();

    await nextTick();
    const formApi = editFormApi.value;
    if (!formApi) {
      console.error('Edit form API not available');
      return;
    }

    try {
      await formApi.resetForm?.();
      const formData = mapRowToFormData(row);

      // 加载已选中但不在选项列表中的用户/代理/CRM用户信息
      if (formData.customer && Array.isArray(formData.customer) && formData.customer.length > 0) {
        await options.loadCustomerByIds?.(formData.customer);
      }
      if (formData.user && Array.isArray(formData.user) && formData.user.length > 0) {
        await options.loadUserByIds?.(formData.user);
      }
      if (formData.agent && Array.isArray(formData.agent) && formData.agent.length > 0) {
        await options.loadAgentByIds?.(formData.agent);
      }

      // console.log('Setting form data:', formData);
      await formApi.setValues?.(formData);
      setupFormListeners(formApi);
      // console.log('Edit form loaded successfully');
    } catch (error) {
      console.error('Failed to load edit form data:', error);
      message.error($t('@subscription.loadEditDataFailed'));
    }
  }

  // CRUD operations
  async function handleDelete(row: ExtendedAISubscription) {
    Modal.confirm({
      title: $t('@subscription.confirmDelete'),
      content: $t('@subscription.confirmDeleteContent', { name: row.name }),
      okText: $t('@subscription.confirm'),
      cancelText: $t('@subscription.cancel'),
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteAISubscriptionApi([row.id]);
          message.success($t('ui.actionMessage.deleteSuccess', [row.name]));
          gridApi.query();
        } catch (error: any) {
          console.error('删除失败:', error);
          message.error(
            $t('@subscription.deleteFailed', {
              msg: error.message || $t('@subscription.pleaseRetry'),
            }),
          );
        }
      },
    });
  }

  async function handleSubmit(isEdit: boolean) {
    const formApi = isEdit ? editFormApi.value : addFormApi.value;
    if (!formApi) return;

    try {
      const { valid } = await formApi.validate();
      if (!valid) return;

      const values = await formApi.getValues?.();

      // 验证数据范围限制类型必须至少选择一个
      if (!values.limit_types || values.limit_types.length === 0) {
        message.error($t('@subscription.pleaseSelectAtLeastOneDataRangeLimit'));
        return;
      }

      const submitData = transformFormDataToSubmit(values);

      if (isEdit) {
        await updateAISubscriptionApi(
          editSubscriptionId.value,
          submitData as UpdateAISubscriptionParams,
        );
        message.success($t('@subscription.updateSuccess'));
        editModalApi.value?.close();
      } else {
        await createAISubscriptionApi(submitData as CreateAISubscriptionParams);
        message.success($t('@subscription.createSuccess'));
        addModalApi.value?.close();
      }
      gridApi.query();
    } catch (error) {
      console.error(`${isEdit ? '更新' : '创建'}失败:`, error);
      message.error(isEdit ? $t('@subscription.updateFailed') : $t('@subscription.createFailed'));
    }
  }

  function handleCancel(isEdit: boolean) {
    const modalApi = isEdit ? editModalApi.value : addModalApi.value;
    const formApi = isEdit ? editFormApi.value : addFormApi.value;

    modalApi?.close();
    formApi?.resetForm?.();
  }

  return {
    // State
    editLoading,

    // Methods
    registerModal,
    showCreateModal,
    showEditModal,
    handleDelete,
    handleSubmit,
    handleCancel,
  };
}
