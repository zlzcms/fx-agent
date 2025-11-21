<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { AISubscriptionParams } from '#/api';

import { computed, nextTick, onMounted, watch } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getAISubscriptionListApi } from '#/api';
import { pagerPresets } from '#/configs/pager';

import { useSubscriptionCrud } from './composables/useSubscriptionCrud';
import { useSubscriptionOptions } from './composables/useSubscriptionOptions';
import {
  generatePlanCycleDescription,
  useColumns,
  useQuerySchema,
  useSubscriptionSchema,
} from './data';

// Constants
const MODAL_CONFIG = {
  class: 'w-[600px] max-w-[95vw]',
  contentClass: 'p-4',
} as const;

const FORM_CONFIG = {
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-4',
  commonConfig: { labelWidth: 100 },
} as const;

// Options
const options = useSubscriptionOptions();
const { getAssistantName } = options;

// Query form configuration
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: { content: $t('page.form.query') },
  schema: useQuerySchema(),
  submitOnChange: true,
  submitOnEnter: true,
  wrapperClass: 'grid-cols-1 md:grid-cols-3',
};

// Action handler
const onActionClick = ({ code, row }: any) => {
  switch (code) {
    case 'delete': {
      crud.handleDelete(row as any);
      break;
    }
    case 'edit': {
      crud.showEditModal(row as any);
      break;
    }
  }
};

// Initialize Grid with columns
const [Grid, gridApi] = useVbenVxeGrid({
  formOptions,
  gridOptions: {
    rowConfig: { keyField: 'id' },
    height: '100%',
    pagerConfig: pagerPresets.standard,
    toolbarConfig: {
      export: true,
      print: true,
      refresh: { code: 'query' },
      custom: true,
      zoom: true,
    },
    proxyConfig: {
      ajax: {
        query: async ({ page }: any, formValues: any) => {
          const result = await getAISubscriptionListApi({
            page: page.currentPage,
            size: page.pageSize,
            ...formValues,
          } as AISubscriptionParams);
          return { items: result.items || [], total: result.total || 0 };
        },
      },
    },
    columns: useColumns(onActionClick, getAssistantName),
  },
});

// Initialize CRUD
const crud = useSubscriptionCrud({
  options: {
    responsibleOptions: computed(() => options.responsibleOptions.value),
    assistantOptionsByType: options.assistantOptionsByType,
    notificationMethodOptions: computed(() => options.notificationMethodOptions.value),
    loadCustomerByIds: options.loadCustomerByIds,
    loadUserByIds: options.loadUserByIds,
    loadAgentByIds: options.loadAgentByIds,
  },
  gridApi,
});

// Modals
const [addModal, addModalApi] = useVbenModal({
  title: $t('@subscription.newSubscription'),
  ...MODAL_CONFIG,
});

const [editModal, editModalApi] = useVbenModal({
  title: $t('@subscription.editSubscription'),
  ...MODAL_CONFIG,
});

// Forms with shared configuration
const subscriptionSchema = computed(() =>
  useSubscriptionSchema({
    assistantTypeOptions: options.assistantTypeOptions,
    assistantOptionsByType: options.assistantOptionsByType,
    responsibleOptions: options.responsibleOptions,
    notificationMethodOptions: options.notificationMethodOptions,
    customerOptions: options.customerOptions,
    userOptions: options.userOptions,
    agentOptions: options.agentOptions,
    countryOptions: options.countryOptions,
    customerSearchLoading: options.customerSearchLoading,
    userSearchLoading: options.userSearchLoading,
    agentSearchLoading: options.agentSearchLoading,
    searchCustomers: options.searchCustomers,
    searchUsers: options.searchUsers,
    searchAgents: options.searchAgents,
  }),
);

const [AddForm, addFormApi] = useVbenForm({
  ...FORM_CONFIG,
  schema: [],
});

const [EditForm, editFormApi] = useVbenForm({
  ...FORM_CONFIG,
  schema: [],
});

// Register modals
crud.registerModal('add', addModalApi, addFormApi);
crud.registerModal('edit', editModalApi, editFormApi);

// Watch for options changes and update forms
watch(
  () => [
    options.assistantTypeOptions.value,
    options.responsibleOptions.value,
    options.notificationMethodOptions.value,
    options.customerOptions.value,
    options.agentOptions.value,
    options.countryOptions.value,
  ],
  async () => {
    try {
      const schema = subscriptionSchema.value;
      if (schema.length > 0) {
        await nextTick();
        await addFormApi.setState({ schema });
        await editFormApi.setState({ schema });
      } else {
        console.warn('Schema is empty during options update');
      }
    } catch (error) {
      console.error('Failed to update form schemas:', error);
    }
  },
  { deep: true },
);

// Lifecycle
onMounted(async () => {
  try {
    await options.loadOptions();

    // Manually update schemas after options are loaded
    await nextTick();
    const schema = subscriptionSchema.value;
    if (schema.length > 0) {
      await addFormApi.setState({ schema });
      await editFormApi.setState({ schema });
    } else {
      console.warn('Schema is empty, forms may not work properly');
    }
  } catch (error) {
    console.error('Failed to initialize component:', error);
  }
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton type="primary" :icon="MaterialSymbolsAdd" @click="crud.showCreateModal">
          {{ $t('@subscription.newSubscription') }}
        </VbenButton>
      </template>

      <!-- 执行计划插槽 -->
      <template #plan_cycle="{ row }">
        {{ row.plan_cycle || generatePlanCycleDescription(row.execution_frequency, row) }}
      </template>
    </Grid>

    <!-- Add Modal -->
    <addModal>
      <div :class="MODAL_CONFIG.contentClass">
        <AddForm />
      </div>
      <template #footer>
        <div class="flex justify-end gap-2 p-3">
          <a-button @click="crud.handleCancel(false)">{{ $t('@subscription.cancel') }}</a-button>
          <a-button type="primary" @click="crud.handleSubmit(false)">
            {{ $t('@subscription.confirm') }}
          </a-button>
        </div>
      </template>
    </addModal>

    <!-- Edit Modal -->
    <editModal>
      <div :class="MODAL_CONFIG.contentClass">
        <EditForm />
      </div>
      <template #footer>
        <div class="flex justify-end gap-2 p-3">
          <a-button @click="crud.handleCancel(true)">{{ $t('@subscription.cancel') }}</a-button>
          <a-button type="primary" @click="crud.handleSubmit(true)">
            {{ $t('@subscription.confirm') }}
          </a-button>
        </div>
      </template>
    </editModal>
  </Page>
</template>

<style scoped>
/* Modal content spacing */
:deep(.ant-modal-body) {
  padding: 0;
}
</style>
