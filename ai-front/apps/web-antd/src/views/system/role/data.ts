import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { SysRoleResult } from '#/api';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@sys-role.roleName'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@sys-role.enabled'),
          value: 1,
        },
        {
          label: $t('@sys-role.stopped'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('common.form.status'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<SysRoleResult>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      width: 50,
    },
    { field: 'name', title: $t('@sys-role.roleName') },
    {
      field: 'is_filter_scopes',
      title: $t('@sys-role.filterDataPermission'),
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('common.enabled'), value: true },
          { color: 'error', label: $t('common.disabled'), value: false },
        ],
      },
    },
    {
      field: 'status',
      title: $t('@sys-role.status'),
      cellRender: {
        name: 'CellTag',
      },
      width: 100,
    },
    { field: 'remark', title: $t('common.table.mark') },
    {
      field: 'created_time',
      title: $t('common.table.created_time'),
      width: 168,
    },
    {
      field: 'updated_time',
      title: $t('common.table.updated_time'),
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
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'perm',
            text: $t('@sys-role.permissionSettings'),
          },
          'edit',
          {
            code: 'delete',
            disabled: (row: SysRoleResult) => {
              return row.id === 1;
            },
          },
        ],
      },
    },
  ];
}

export const schema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@sys-role.roleName'),
    rules: 'required',
  },
  {
    component: 'RadioGroup',
    componentProps: {
      buttonStyle: 'solid',
      options: [
        { label: $t('common.enabled'), value: true },
        { label: $t('common.disabled'), value: false },
      ],
      optionType: 'button',
    },
    defaultValue: true,
    fieldName: 'is_filter_scopes',
    label: $t('@sys-role.filterDataPermission'),
    rules: 'required',
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
    label: $t('@sys-role.status'),
    rules: 'required',
  },
  {
    component: 'Textarea',
    fieldName: 'remark',
    label: $t('@sys-role.remark'),
  },
];

export const drawerQuerySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'title',
    label: $t('@sys-role.menuTitle'),
  },
];

export const drawerColumns: VxeGridProps['columns'] = [
  {
    type: 'checkbox',
    title: $t('@sys-role.menuTitle'),
    align: 'left',
    fixed: 'left',
    treeNode: true,
  },
  {
    field: 'type',
    title: $t('@sys-role.type'),
    cellRender: {
      name: 'CellTag',
      options: [
        { color: 'orange', label: $t('@sys-role.directory'), value: 0 },
        { color: 'default', label: $t('@sys-role.menu'), value: 1 },
        { color: 'blue', label: $t('@sys-role.button'), value: 2 },
        { color: 'warning', label: $t('@sys-role.embedded'), value: 3 },
        { color: 'success', label: $t('@sys-role.externalLink'), value: 4 },
      ],
    },
  },
  { field: 'perms', title: $t('@sys-role.permissionIdentifier') },
  { field: 'remark', title: $t('@sys-role.remark') },
];

export function drawerDataScopeColumns(
  onActionClick?: OnActionClickFn<SysRoleResult>,
): VxeGridProps['columns'] {
  return [
    {
      type: 'checkbox',
      title: $t('@sys-role.scopeName'),
      align: 'left',
      fixed: 'left',
      minWidth: 150,
    },
    {
      field: 'status',
      title: $t('@sys-role.status'),
      cellRender: {
        name: 'CellTag',
      },
      width: 100,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 200,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'details',
            text: $t('@sys-role.ruleDetails'),
          },
        ],
      },
    },
  ];
}

export const drawerDataRuleColumns: VxeGridProps['columns'] = [
  {
    field: 'seq',
    title: $t('common.table.id'),
    type: 'seq',
    width: 50,
  },
  { field: 'name', title: $t('@sys-role.ruleName') },
];
