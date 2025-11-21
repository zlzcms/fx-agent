<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type {
  VxeTableGridOptions,
} from '#/adapter/vxe-table';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  querySchema,
  useColumns,
} from './data';

// 导入API
import type {
  AIAssistantTemplate,
  AIAssistantTemplateParams,
} from '#/api';

import {
  getAIAssistantTemplateListApi,
} from '#/api';

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
};

const gridOptions: VxeTableGridOptions<AIAssistantTemplate> = {
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
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  columns: useColumns(),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        return await getAIAssistantTemplateListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as AIAssistantTemplateParams);
      },
    },
  },
};

const [Grid] = useVbenVxeGrid({ formOptions, gridOptions });
</script>

<template>
  <Page auto-content-height>
    <Grid />
  </Page>
</template> 