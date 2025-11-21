<script lang="ts" setup>
import type { VbenFormProps } from '@vben/common-ui';

import type {
  OnActionClickParams,
  VxeGridListeners,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { LoginLogResult, OperaLogResult } from '#/api';

import { ref, watch } from 'vue';

import { confirm, JsonViewer, Page, useVbenDrawer, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsDelete } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { deleteOperaLogApi, getOperaLogListApi } from '#/api';

import { querySchema, useColumns } from './data';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<OperaLogResult> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        return await getOperaLogListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        });
      },
    },
  },
};

const gridEvents: VxeGridListeners<LoginLogResult> = {
  checkboxChange: () => {
    const data = gridApi.grid.getCheckboxRecords(true);
    checkedRows.value = data.map((item: any) => item.id);
  },
  checkboxAll: () => {
    const data = gridApi.grid.getCheckboxRecords(true);
    checkedRows.value = data.map((item: any) => item.id);
  },
};

const [Grid, gridApi] = useVbenVxeGrid({
  formOptions,
  gridOptions,
  gridEvents,
});

function onRefresh() {
  gridApi.query();
}

function onActionClick({ code, row }: OnActionClickParams<OperaLogResult>) {
  switch (code) {
    case 'details': {
      operaLogDetails.value = row;
      drawerApi.open();
    }
  }
}

const [Drawer, drawerApi] = useVbenDrawer({
  destroyOnClose: true,
  footer: false,
  class: 'w-2/5',
});

const operaLogDetails = ref<OperaLogResult>();

const checkedRows = ref<number[]>([]);
const deleteDisable = ref<boolean>(true);
const deleteLoading = ref<boolean>(false);

const deleteLoginLog = async () => {
  confirm({
    icon: 'warning',
    content: $t('@log-opera.confirmDelete'),
  }).then(async () => {
    deleteLoading.value = true;
    try {
      await deleteOperaLogApi(checkedRows.value);
      message.success($t('ui.actionMessage.deleteSuccess'));
      onRefresh();
      deleteDisable.value = true;
    } catch (error) {
      console.error(error);
    } finally {
      deleteLoading.value = false;
    }
  });
};

watch(checkedRows, () => {
  deleteDisable.value = checkedRows.value.length === 0;
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton
          variant="destructive"
          :disabled="deleteDisable"
          :loading="deleteLoading"
          @click="deleteLoginLog"
        >
          <MaterialSymbolsDelete class="size-5" />
          {{ $t('@log-opera.deleteLog') }}
        </VbenButton>
      </template>
    </Grid>
    <Drawer :title="$t('@log-opera.operationLogDetails')">
      <a-descriptions class="ml-1" :label-style="{ color: '#6b7280' }" :column="2">
        <a-descriptions-item :label="$t('@log-opera.traceId')">
          {{ operaLogDetails?.trace_id }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.username')">
          {{ operaLogDetails?.username }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.requestMethod')">
          {{ operaLogDetails?.method }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.requestPath')">
          {{ operaLogDetails?.path }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.operationTitle')">
          {{ operaLogDetails?.title }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.operatingSystem')">
          {{ operaLogDetails?.os }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.device')">
          {{ operaLogDetails?.device }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.browser')">
          {{ operaLogDetails?.browser }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.requestIp')">
          {{ operaLogDetails?.ip }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.country')">
          {{
            operaLogDetails?.country === 'None' || !operaLogDetails?.country
              ? 'N/A'
              : operaLogDetails?.country
          }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.region')">
          {{
            operaLogDetails?.region === 'None' || !operaLogDetails?.region
              ? 'N/A'
              : operaLogDetails?.region
          }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.city')">
          {{ operaLogDetails?.city }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.statusCodeLabel')">
          {{ operaLogDetails?.code }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.statusLabel')">
          <a-tag v-if="operaLogDetails?.status === 1" color="success">
            {{ $t('@log-opera.success') }}
          </a-tag>
          <a-tag v-else color="error"> {{ $t('@log-opera.failed') }} </a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.operationTimeLabel')">
          {{ operaLogDetails?.opera_time }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.costTimeLabel')">
          <a-tag v-if="(operaLogDetails?.cost_time || 0) < 200" color="success">
            {{ operaLogDetails?.cost_time }} ms
          </a-tag>
          <a-tag v-else color="warning"> {{ operaLogDetails?.cost_time }} ms </a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.userAgent')" :span="2">
          {{ operaLogDetails?.user_agent }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.requestParams')" :span="2">
          <JsonViewer
            class="mr-8 w-full"
            :value="operaLogDetails?.args"
            :copyable="!!operaLogDetails?.args"
            boxed
            expanded
            :expand-depth="3"
            :show-array-index="false"
            @copied="message.success($t('@log-opera.copiedRequestParams'))"
          />
        </a-descriptions-item>
        <a-descriptions-item :label="$t('@log-opera.responseMessage')">
          {{ operaLogDetails?.msg }}
        </a-descriptions-item>
      </a-descriptions>
    </Drawer>
  </Page>
</template>
