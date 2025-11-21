import type { VbenFormSchema } from '#/adapter/form';
import type { VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@scheduler.recordTaskName'),
  },
  {
    component: 'Input',
    fieldName: 'task_id',
    label: $t('@scheduler.recordTaskId'),
  },
];

export const columns: VxeGridProps['columns'] = [
  { field: 'checkbox', type: 'checkbox', align: 'left', width: 50 },
  { field: 'task_id', title: $t('@scheduler.recordTaskId') },
  { field: 'name', title: $t('@scheduler.recordTaskName') },
  {
    field: 'args',
    title: $t('@scheduler.recordPositionalArgs'),
    formatter: ({ cellValue }) =>
      JSON.stringify(cellValue, (_, value) => {
        return value === null ? undefined : value;
      }),
  },
  {
    field: 'kwargs',
    title: $t('@scheduler.recordKeywordArgs'),
    formatter: ({ cellValue }) =>
      JSON.stringify(cellValue, (_, value) => {
        return value === null ? undefined : value;
      }),
  },
  {
    field: 'status',
    title: $t('@scheduler.recordStatus'),
    slots: { default: 'status_slot' },
  },
  {
    field: 'result',
    title: $t('@scheduler.executionResult'),
    formatter: ({ cellValue }) => {
      if (cellValue === null || cellValue === undefined) {
        return '';
      }
      if (typeof cellValue === 'object') {
        return JSON.stringify(cellValue, null, 2);
      }
      return String(cellValue);
    },
  },
  { field: 'retries', title: $t('@scheduler.retryCount') },
  { field: 'traceback', title: $t('@scheduler.errorTraceback') },
  { field: 'worker', title: $t('@scheduler.recordWorker') },
  { field: 'queue', title: $t('@scheduler.recordQueue') },
  { field: 'date_done', title: $t('@scheduler.recordEndTime') },
  {
    field: 'action',
    title: $t('common.table.operation'),
    width: 120,
    fixed: 'right',
    slots: { default: 'action_slot' },
  },
];
