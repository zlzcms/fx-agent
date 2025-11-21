import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { OperaLogResult } from '#/api';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'username',
    label: $t('@log-opera.username'),
  },
  {
    component: 'Input',
    fieldName: 'ip',
    label: $t('@log-opera.ipAddress'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@log-opera.normal'),
          value: 1,
        },
        {
          label: $t('@log-opera.abnormal'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('@log-opera.status'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<OperaLogResult>,
): VxeGridProps['columns'] {
  return [
    { field: 'checkbox', type: 'checkbox', align: 'left', width: 50 },
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      width: 50,
    },
    { field: 'username', title: $t('@log-opera.username') },
    {
      field: 'method',
      title: $t('@log-opera.requestMethod'),
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'processing', label: 'GET', value: 'GET' },
          { color: 'success', label: 'POST', value: 'POST' },
          { color: 'cyan', label: 'PUT', value: 'PUT' },
          { color: 'error', label: 'PUT', value: 'DELETE' },
        ],
      },
    },
    { field: 'title', title: $t('@log-opera.operationTitle'), align: 'left', width: 200 },
    { field: 'path', title: $t('@log-opera.requestPath'), align: 'left', width: 300 },
    { field: 'browser', title: $t('@log-opera.browser') },
    {
      field: 'status',
      title: $t('@log-opera.status'),
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('@log-opera.success'), value: 1 },
          { color: 'error', label: $t('@log-opera.failed'), value: 0 },
        ],
      },
    },
    { field: 'code', title: $t('@log-opera.statusCode') },
    { field: 'cost_time', title: $t('@log-opera.costTime') },
    { field: 'opera_time', title: $t('@log-opera.operationTime') },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 100,
      cellRender: {
        attrs: {
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'details',
            text: $t('@log-opera.details'),
          },
        ],
      },
    },
  ];
}
