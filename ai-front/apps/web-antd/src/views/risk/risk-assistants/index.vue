<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { RiskAssistantParams } from '#/api';

import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { VbenButton, Page } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';
import { message } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getRiskAssistantListApi } from '#/api';

import { querySchema, useColumns, loadAIModelOptions } from './data';
import { pagerPresets } from '#/configs/pager';

const router = useRouter();

// 加载状态
const loading = ref(false);
const aiModelOptionsLoaded = ref(false);

/**
 * 处理表格操作按钮点击事件
 */
function onActionClick(params: any) {
  const { code, row } = params;
  switch (code) {
    case 'edit': {
      // 跳转到编辑页面
      router.push(`/risk/risk-assistant/edit/${row.id}`);
      break;
    }
    // 预留删除功能
    // case 'delete': {
    //   handleDelete(row);
    //   break;
    // }
  }
}

/**
 * 跳转到添加页面
 */
function handleAdd() {
  router.push('/risk/risk-assistant/add');
}

/**
 * 预留删除功能
 */
// function handleDelete(row: any) {
//   // 实现删除逻辑
// }

/**
 * 表格配置
 */
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('page.form.query'),
  },
  schema: querySchema,
  submitOnChange: true,
  submitOnEnter: true,
};

const gridOptions: VxeTableGridOptions = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  virtualYConfig: {
    enabled: true,
    gt: 0,
  },
  height: 'auto',
  exportConfig: {
    filename: `风控助手列表_${new Date().toLocaleDateString()}`,
  },
  printConfig: {
    columns: [
      { field: 'name' },
      { field: 'ai_model_id' },
      { field: 'role' },
      { field: 'status' },
      { field: 'created_time' },
    ],
  },
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  pagerConfig: pagerPresets.standard,
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        try {
          loading.value = true;

          // 确保AI模型映射已初始化
          if (!aiModelOptionsLoaded.value) {
            await loadAIModelOptions();
            aiModelOptionsLoaded.value = true;
          }

          const response = await getRiskAssistantListApi({
            page: page.currentPage,
            size: page.pageSize,
            ...formValues,
          } as RiskAssistantParams);

          return {
            items: response.items || [],
            total: response.total || 0,
          };
        } catch (error: any) {
          console.error('获取风控助手列表失败:', error);
          const errorMsg =
            error?.response?.data?.message || error?.message || '获取风控助手列表失败';
          message.error(errorMsg);
          return {
            items: [],
            total: 0,
          };
        } finally {
          loading.value = false;
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

/**
 * 刷新表格数据
 */
function onRefresh() {
  gridApi.query();
}

/**
 * 初始化AI模型选项
 */
async function initAIModelOptions() {
  try {
    const aiModelOptions = await loadAIModelOptions();

    // 更新查询表单中的AI模型选项
    const modelField = querySchema.find((field) => field.fieldName === 'ai_model_id');
    if (modelField?.componentProps) {
      const props = modelField.componentProps as any;
      if (props && typeof props === 'object') {
        props.options = aiModelOptions;
      }
    }

    aiModelOptionsLoaded.value = true;
    return aiModelOptions;
  } catch (error: any) {
    console.error('加载AI模型选项失败:', error);
    const errorMsg = error?.response?.data?.message || error?.message || '加载AI模型选项失败';
    message.error(errorMsg);
    return [];
  }
}

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  // 预加载AI模型选项
  await initAIModelOptions();
});
</script>

<template>
  <Page auto-content-height>
    <Grid :loading="loading">
      <template #toolbar-actions>
        <VbenButton v-if="false" type="primary" @click="handleAdd" :disabled="loading">
          <MaterialSymbolsAdd class="size-5" />
          {{ $t('views.ai.assistants.addAssistant') }}
        </VbenButton>
      </template>
    </Grid>
  </Page>
</template>

<style scoped>
/* 响应式优化 */
@media (max-width: 768px) {
  :deep(.vxe-table .vxe-body--column) {
    padding: 6px 8px;
  }

  :deep(.ant-tag) {
    padding: 1px 6px;
    font-size: 11px;
  }
}

:deep(.vxe-table--body .vxe-body--row:hover) {
  background-color: #f5f5f5;
}

/* 标签样式优化 */
:deep(.ant-tag) {
  margin: 2px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
}

/* 工具栏按钮样式 */
:deep(.vxe-table--toolbar .vben-button) {
  margin-right: 8px;
}

/* 表格紧凑模式优化 */
:deep(.vxe-table .vxe-body--column) {
  padding: 8px 12px;
}

/* 开关组件样式优化 */
:deep(.vxe-table .ant-switch) {
  min-width: 44px;
}

/* 操作按钮样式优化 */
:deep(.vxe-table .vxe-cell--actions) {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* 数据为空时的样式 */
:deep(.vxe-table--empty-content) {
  padding: 40px 20px;
  color: #999;
}

/* 表格行样式优化 */
</style>
