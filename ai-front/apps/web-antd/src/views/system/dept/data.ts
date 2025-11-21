import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { SysDeptTreeResult } from '#/api';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';
import { getSysDeptTreeApi } from '#/api';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@sys-dept.deptName'),
  },
  {
    component: 'Input',
    fieldName: 'leader',
    label: $t('@sys-dept.leader'),
  },
  {
    component: 'Input',
    fieldName: 'phone',
    label: $t('@sys-dept.phoneNumber'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@sys-dept.normal'),
          value: 1,
        },
        {
          label: $t('@sys-dept.stopped'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('common.form.status'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<SysDeptTreeResult>,
): VxeGridProps['columns'] {
  return [
    { field: 'name', title: $t('@sys-dept.name'), align: 'left', treeNode: true },
    { field: 'leader', title: $t('@sys-dept.leader') },
    { field: 'phone', title: $t('@sys-dept.phoneNumber') },
    { field: 'email', title: $t('@sys-dept.email') },
    { field: 'sort', title: $t('@sys-dept.sort') },
    {
      field: 'status',
      title: $t('@sys-dept.status'),
      cellRender: {
        name: 'CellTag',
      },
    },
    {
      field: 'created_time',
      title: $t('common.table.created_time'),
      width: 168,
      formatter: 'formatDateTime',
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
            code: 'add',
            text: $t('@sys-dept.addSubDept'),
          },
          'edit',
          {
            code: 'delete',
            disabled: (row: SysDeptTreeResult) => {
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
    label: $t('@sys-dept.deptName'),
    rules: 'required',
  },
  {
    component: 'ApiTreeSelect',
    componentProps: {
      allowClear: true,
      api: getSysDeptTreeApi,
      class: 'w-full',
      labelField: 'name',
      valueField: 'id',
      childrenField: 'children',
    },
    fieldName: 'parent_id',
    label: $t('@sys-dept.parentDept'),
  },
  {
    component: 'Input',
    fieldName: 'leader',
    label: $t('@sys-dept.leader'),
  },
  {
    component: 'Input',
    componentProps: {
      allowClear: true,
    },
    fieldName: 'phone',
    label: $t('@sys-dept.phoneNumber'),
  },
  {
    component: 'Input',
    componentProps: {
      allowClear: true,
    },
    fieldName: 'email',
    label: $t('@sys-dept.emailAddress'),
    rules: z
      .string()
      .email({ message: $t('@sys-dept.invalidEmail') })
      .optional(),
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
    label: $t('@sys-dept.status'),
    rules: 'required',
  },
];
