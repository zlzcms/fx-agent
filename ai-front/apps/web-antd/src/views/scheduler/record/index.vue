<script lang="ts" setup>
import type { VbenFormProps } from '@vben/common-ui';

import type { VxeGridListeners, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { TaskResult } from '#/api';

import { onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { confirm, Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsDelete } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { deleteTaskResultApi, getTaskResultApi, getTaskResultListApi } from '#/api';

import { getTaskStatusConfig } from '../../../types/celery';
import { columns, querySchema } from './data';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<TaskResult> = {
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
  columns,
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        return await getTaskResultListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        });
      },
    },
  },
};

const gridEvents: VxeGridListeners<TaskResult> = {
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

const checkedRows = ref<number[]>([]);
const deleteDisable = ref<boolean>(true);
const deleteLoading = ref<boolean>(false);

const deleteTaskResult = async () => {
  confirm({
    icon: 'warning',
    content: $t('@scheduler.confirmDeleteSelectedRecords'),
  }).then(async () => {
    deleteLoading.value = true;
    try {
      await deleteTaskResultApi(checkedRows.value);
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

// 详情弹窗相关
const [DetailModal, detailModalApi] = useVbenModal({
  title: '任务详情',
  fullscreenButton: true,
  draggable: true,
});

const currentTaskDetail = ref<null | TaskResult>(null);

// 查看详情
const viewDetail = async (row: TaskResult) => {
  try {
    const result = await getTaskResultApi(row.id);
    currentTaskDetail.value = result;
    detailModalApi.open();
  } catch (error) {
    console.error(`${$t('@scheduler.getTaskDetailsFailed')}:`, error);
    message.error($t('@scheduler.getTaskDetailsFailed'));
  }
};

// 安全解析 JSON
const safeParseJSON = (jsonString: null | string | undefined) => {
  if (!jsonString) return '-';
  try {
    return JSON.stringify(JSON.parse(jsonString), null, 2);
  } catch {
    return jsonString;
  }
};

const route = useRoute();
onMounted(() => {
  // 如果 URL 中有 name 参数，设置到查询表单中
  if (route.query.name) {
    gridApi.formApi.setValues({ name: route.query.name });
    // 自动执行查询
    gridApi.query();
  }
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
          @click="deleteTaskResult"
        >
          <MaterialSymbolsDelete class="size-5" />
          {{ $t('@scheduler.deleteRecords') }}
        </VbenButton>
      </template>

      <template #status_slot="{ row }">
        <span
          :class="`${getTaskStatusConfig(row.status).color} font-semibold`"
          :title="getTaskStatusConfig(row.status).label"
        >
          {{ row.status }}
        </span>
      </template>

      <template #action_slot="{ row }">
        <div class="flex justify-center">
          <a-button type="link" class="text-blue-500" @click="viewDetail(row)">
            {{ $t('@scheduler.details') }}
          </a-button>
        </div>
      </template>
    </Grid>

    <!-- 详情弹窗 -->
    <DetailModal :title="$t('@scheduler.taskDetails')" class="w-[1200px]" :footer="false">
      <div v-if="currentTaskDetail" class="space-y-6 p-1">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground">
              {{ $t('@scheduler.recordTaskId') }}:
            </label>
            <div class="p-3 bg-muted rounded-md border text-sm font-mono">
              {{ currentTaskDetail.task_id }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordTaskName') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm">
              {{ currentTaskDetail.name || '-' }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordStatus') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm">
              <span
                :class="`${getTaskStatusConfig(currentTaskDetail.status).color} font-semibold`"
                :title="getTaskStatusConfig(currentTaskDetail.status).label"
              >
                {{ currentTaskDetail.status }}
              </span>
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.retryCount') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm">
              {{ currentTaskDetail.retries || 0 }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordWorker') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm font-mono">
              {{ currentTaskDetail.worker || '-' }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordQueue') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm">
              {{ currentTaskDetail.queue || '-' }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordEndTime') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm">
              {{ currentTaskDetail.date_done || '-' }}
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground"
              >{{ $t('@scheduler.recordPositionalArgs') }}:</label
            >
            <div class="p-3 bg-muted rounded-md border text-sm font-mono max-h-48 overflow-y-auto">
              <pre class="whitespace-pre-wrap break-words text-xs leading-relaxed">{{
                safeParseJSON(currentTaskDetail.args)
              }}</pre>
            </div>
          </div>
        </div>

        <div class="space-y-2">
          <label class="text-sm font-semibold text-foreground"
            >{{ $t('@scheduler.recordKeywordArgs') }}:</label
          >
          <div class="p-3 bg-muted rounded-md border text-sm font-mono max-h-60 overflow-y-auto">
            <pre class="whitespace-pre-wrap break-words text-xs leading-relaxed">{{
              safeParseJSON(currentTaskDetail.kwargs)
            }}</pre>
          </div>
        </div>

        <div class="space-y-2">
          <label class="text-sm font-semibold text-foreground"
            >{{ $t('@scheduler.executionResult') }}:</label
          >
          <div class="p-3 bg-muted rounded-md border text-sm font-mono max-h-64 overflow-y-auto">
            <pre class="whitespace-pre-wrap break-words text-xs leading-relaxed">{{
              currentTaskDetail.result || '-'
            }}</pre>
          </div>
        </div>

        <div v-if="currentTaskDetail.traceback" class="space-y-2">
          <label class="text-sm font-semibold text-destructive"
            >{{ $t('@scheduler.errorTraceback') }}:</label
          >
          <div
            class="p-3 bg-destructive/10 rounded-md border border-destructive/20 text-sm font-mono max-h-40 overflow-y-auto"
          >
            <pre class="text-destructive whitespace-pre-wrap break-words">{{
              currentTaskDetail.traceback
            }}</pre>
          </div>
        </div>
      </div>
    </DetailModal>
  </Page>
</template>
