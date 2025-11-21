import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { ApiKeyResult } from '#/api';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'key_name',
    label: $t('@sys-config.apiKeyName'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('common.enabled'),
          value: 1,
        },
        {
          label: $t('common.disabled'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('common.form.status'),
  },
];

export function useColumns(onActionClick?: OnActionClickFn<ApiKeyResult>): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      width: 50,
    },
    { field: 'key_name', title: $t('@sys-config.apiKeyName'), width: 150 },
    {
      field: 'api_key_prefix',
      title: $t('@sys-config.apiKey'),
      width: 450,
      showOverflow: 'tooltip',
    },
    {
      field: 'description',
      title: $t('@sys-config.description'),
      width: 200,
    },
    {
      field: 'status',
      title: $t('@sys-config.status'),
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('common.enabled'), value: 1 },
          { color: 'error', label: $t('common.disabled'), value: 0 },
        ],
      },
      width: 100,
    },
    {
      field: 'expires_at',
      title: $t('@sys-config.expiresAt'),
      width: 180,
    },
    {
      field: 'usage_count',
      title: $t('@sys-config.usageCount'),
      width: 100,
    },
    {
      field: 'last_used_at',
      title: $t('@sys-config.lastUsedAt'),
      width: 180,
    },
    {
      field: 'created_time',
      title: $t('common.table.created_time'),
      width: 168,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 200,
      cellRender: {
        attrs: {
          nameField: 'key_name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
    },
  ];
}

export const schema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'key_name',
    label: $t('@sys-config.apiKeyName'),
    rules: 'required',
    componentProps: {
      placeholder: $t('@sys-config.enterApiKeyName'),
    },
  },
  {
    component: 'Textarea',
    fieldName: 'description',
    label: $t('@sys-config.description'),
    componentProps: {
      rows: 3,
      placeholder: $t('@sys-config.enterDescription'),
    },
  },
  {
    component: 'DatePicker',
    fieldName: 'expires_at',
    label: $t('@sys-config.expiresAt'),
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      placeholder: $t('@sys-config.selectExpiresAt'),
      style: { width: '100%' },
    },
  },
  {
    component: 'Textarea',
    fieldName: 'ip_whitelist',
    label: $t('@sys-config.ipWhitelist'),
    componentProps: {
      rows: 3,
      placeholder: $t('@sys-config.enterIpWhitelist'),
    },
  },
  {
    component: 'RadioGroup',
    componentProps: {
      buttonStyle: 'solid',
      options: [
        { label: $t('common.enabled'), value: 1 },
        { label: $t('common.disabled'), value: 0 },
      ],
      optionType: 'button',
    },
    defaultValue: 1,
    fieldName: 'status',
    label: $t('@sys-config.status'),
    rules: 'required',
  },
];
