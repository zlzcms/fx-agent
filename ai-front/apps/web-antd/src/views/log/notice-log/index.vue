<script lang="ts" setup>
import type { VbenFormProps } from '@vben/common-ui';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { NoticeLogResult } from '#/api';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getNoticeLogListApi } from '#/api';
import { pagerPresets } from '#/configs/pager';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: [
    {
      component: 'Input',
      fieldName: 'description',
      label: $t('@log-notice.notificationDescription'),
      componentProps: {
        placeholder: $t('@log-notice.notificationDescriptionPlaceholder'),
      },
    },
    {
      component: 'Select',
      fieldName: 'notification_type',
      label: $t('@log-notice.notificationMethod'),
      componentProps: {
        placeholder: $t('@log-notice.notificationMethodPlaceholder'),
        options: [
          { label: $t('@log-notice.email'), value: 'email' },
          { label: $t('@log-notice.larkWebhook'), value: 'lark_webhook' },
        ],
      },
    },
    {
      component: 'Select',
      fieldName: 'is_success',
      label: $t('@log-notice.successStatus'),
      componentProps: {
        placeholder: $t('@log-notice.successStatusPlaceholder'),
        options: [
          { label: $t('@log-notice.success'), value: true },
          { label: $t('@log-notice.failed'), value: false },
        ],
      },
    },
    {
      component: 'DatePicker',
      fieldName: 'start_time',
      label: $t('@log-notice.startTime'),
      componentProps: {
        showTime: true,
        format: 'YYYY-MM-DD HH:mm:ss',
        valueFormat: 'YYYY-MM-DD HH:mm:ss',
        placeholder: $t('@log-notice.startTimePlaceholder'),
      },
    },
    {
      component: 'DatePicker',
      fieldName: 'end_time',
      label: $t('@log-notice.endTime'),
      componentProps: {
        showTime: true,
        format: 'YYYY-MM-DD HH:mm:ss',
        valueFormat: 'YYYY-MM-DD HH:mm:ss',
        placeholder: $t('@log-notice.endTimePlaceholder'),
      },
    },
  ],
};

const gridOptions: VxeTableGridOptions<NoticeLogResult> = {
  rowConfig: { keyField: 'id' },
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
  pagerConfig: pagerPresets.standard,
  columns: [
    { field: 'id', title: $t('@log-notice.id'), width: 80 },
    { field: 'description', title: $t('@log-notice.notificationDescription'), minWidth: 200 },
    {
      field: 'notification_type',
      title: $t('@log-notice.notificationMethod'),
      width: 120,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'blue', label: $t('@log-notice.email'), value: 'email' },
          { color: 'green', label: $t('@log-notice.larkWebhook'), value: 'lark_webhook' },
        ],
      },
    },
    { field: 'content', title: $t('@log-notice.notificationContent'), minWidth: 300 },
    { field: 'address', title: $t('@log-notice.notificationAddress'), minWidth: 200 },
    {
      field: 'is_success',
      title: $t('@log-notice.status'),
      width: 80,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('@log-notice.success'), value: true },
          { color: 'error', label: $t('@log-notice.failed'), value: false },
        ],
      },
    },
    { field: 'failure_reason', title: $t('@log-notice.failureReason'), minWidth: 200 },
    { field: 'created_time', title: $t('@log-notice.createdTime'), width: 180 },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const res = await getNoticeLogListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        });

        return res;
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
