import type { VbenFormSchema } from '#/adapter/form';
import type { VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'username',
    label: $t('@log-login.username'),
  },
  {
    component: 'Input',
    fieldName: 'ip',
    label: $t('@log-login.ipAddress'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@log-login.success'),
          value: 1,
        },
        {
          label: $t('@log-login.failed'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('@log-login.status'),
  },
];

export const columns: VxeGridProps['columns'] = [
  { field: 'checkbox', type: 'checkbox', align: 'left', width: 50 },
  {
    field: 'seq',
    title: $t('common.table.id'),
    type: 'seq',
    width: 50,
  },
  { field: 'username', title: $t('@log-login.username') },
  {
    field: 'status',
    title: $t('@log-login.status'),
    cellRender: {
      name: 'CellTag',
      options: [
        { color: 'success', label: $t('@log-login.success'), value: 1 },
        { color: 'error', label: $t('@log-login.failed'), value: 0 },
      ],
    },
  },
  { field: 'ip', title: $t('@log-login.ipAddress') },
  { field: 'country', title: $t('@log-login.country') },
  { field: 'region', title: $t('@log-login.region') },
  { field: 'os', title: $t('@log-login.operatingSystem') },
  { field: 'browser', title: $t('@log-login.browser') },
  { field: 'device', title: $t('@log-login.device') },
  { field: 'msg', title: $t('@log-login.message') },
  { field: 'login_time', title: $t('@log-login.loginTime'), width: 168 },
  {
    field: 'created_time',
    title: $t('common.table.created_time'),
    width: 168,
  },
];
