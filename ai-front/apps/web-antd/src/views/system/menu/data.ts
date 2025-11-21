import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { SysMenuTreeResult } from '#/api';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';
import { getSysMenuTreeApi } from '#/api';
import { componentKeys } from '#/router/routes';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'title',
    label: $t('@sys-menu.menuTitle'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@sys-menu.normal'),
          value: 1,
        },
        {
          label: $t('@sys-menu.stopped'),
          value: 0,
        },
      ],
    },
    fieldName: 'status',
    label: $t('views.common.status'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<SysMenuTreeResult>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'title',
      title: $t('@sys-menu.title'),
      align: 'left',
      fixed: 'left',
      slots: { default: 'title_default' },
      treeNode: true,
      width: 160,
    },
    {
      field: 'type',
      title: $t('@sys-menu.type'),
      width: 80,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'orange', label: $t('@sys-menu.directory'), value: 0 },
          { color: 'default', label: $t('@sys-menu.menu'), value: 1 },
          { color: 'blue', label: $t('@sys-menu.button'), value: 2 },
          { color: 'warning', label: $t('@sys-menu.embedded'), value: 3 },
          { color: 'success', label: $t('@sys-menu.externalLink'), value: 4 },
        ],
      },
    },
    { field: 'sort', title: $t('@sys-menu.sort'), width: 50 },
    { field: 'perms', title: $t('@sys-menu.permissionIdentifier'), align: 'left', width: 160 },
    { field: 'name', title: $t('@sys-menu.menuName'), align: 'left', width: 180 },
    { field: 'path', title: $t('@sys-menu.routePath'), align: 'left', width: 180 },
    { field: 'component', title: $t('@sys-menu.pageComponent'), align: 'left', width: 300 },
    {
      field: 'status',
      title: $t('@sys-menu.status'),
      width: 80,
      cellRender: {
        name: 'CellTag',
      },
    },
    { field: 'remark', title: $t('@sys-menu.remark') },
    {
      field: 'operation',
      title: $t('page.table.operation'),
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
            text: $t('@sys-menu.addSubMenu'),
            disabled: (row: SysMenuTreeResult) => {
              return [2, 3, 4].includes(row.type);
            },
          },
          'edit',
          {
            code: 'delete',
            disabled: (row: SysMenuTreeResult) => {
              return row.name === 'System' || row.name === 'Log';
            },
          },
        ],
      },
    },
  ];
}

export const schema: VbenFormSchema[] = [
  {
    component: 'RadioGroup',
    componentProps: {
      buttonStyle: 'solid',
      options: [
        { label: $t('@sys-menu.directory'), value: 0 },
        { label: $t('@sys-menu.menu'), value: 1 },
        { label: $t('@sys-menu.button'), value: 2 },
        { label: $t('@sys-menu.embedded'), value: 3 },
        { label: $t('@sys-menu.externalLink'), value: 4 },
      ],
      optionType: 'button',
    },
    defaultValue: 1,
    fieldName: 'type',
    formItemClass: 'col-span-2 md:col-span-2',
    label: $t('@sys-menu.menuType'),
  },
  {
    component: 'Input',
    fieldName: 'title',
    label: $t('@sys-menu.menuTitle'),
    rules: 'required',
  },
  {
    component: 'ApiTreeSelect',
    componentProps: {
      allowClear: true,
      api: getSysMenuTreeApi,
      class: 'w-full',
      labelField: 'title',
      valueField: 'id',
      childrenField: 'children',
    },
    fieldName: 'parent_id',
    label: $t('@sys-menu.parentDept'),
  },
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@sys-menu.menuName'),
    rules: 'required',
  },
  {
    component: 'Input',
    dependencies: {
      show: (values) => {
        return [0, 1, 3, 4].includes(values.type);
      },
      triggerFields: ['type'],
    },
    fieldName: 'path',
    label: $t('@sys-menu.routePath'),
    rules: 'required',
  },
  {
    component: 'InputNumber',
    componentProps: {
      defaultValue: 0,
      min: 0,
      style: { width: '100%' },
    },
    fieldName: 'sort',
    label: $t('@sys-menu.sort'),
  },
  {
    component: 'IconPicker',
    dependencies: {
      show: (values) => {
        return [0, 1, 3, 4].includes(values.type);
      },
      triggerFields: ['type'],
    },
    fieldName: 'icon',
    label: $t('@sys-menu.icon'),
  },
  {
    component: 'AutoComplete',
    componentProps: {
      allowClear: true,
      class: 'w-full',
      filterOption(input: string, option: { value: string }) {
        return option.value.toLowerCase().includes(input.toLowerCase());
      },
      options: componentKeys.map((v: any) => ({ value: v })),
    },
    dependencies: {
      rules: (values) => {
        return values.type === 1 ? 'required' : null;
      },
      show: (values) => {
        return values.type === 1;
      },
      triggerFields: ['type'],
    },
    fieldName: 'component',
    label: $t('@sys-menu.componentPath'),
  },
  {
    component: 'Input',
    dependencies: {
      rules: (values) => {
        return values.type === 2 ? 'required' : null;
      },
      show: (values) => {
        return [1, 2, 3].includes(values.type);
      },
      triggerFields: ['type'],
    },
    fieldName: 'perms',
    label: $t('@sys-menu.permissionIdentifier'),
  },
  {
    component: 'Input',
    dependencies: {
      show: (values) => {
        return [3, 4].includes(values.type);
      },
      triggerFields: ['type'],
    },
    fieldName: 'link',
    label: $t('@sys-menu.linkAddress'),
    rules: z.string().url($t('ui.formRules.invalidURL')),
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
    label: $t('@sys-menu.status'),
    rules: 'required',
  },
  {
    component: 'Switch',
    componentProps: {
      checkedValue: 1,
      unCheckedValue: 0,
    },
    defaultValue: 1,
    dependencies: {
      show: (values) => {
        return values.type !== 2;
      },
      triggerFields: ['type'],
    },
    fieldName: 'display',
    label: $t('@sys-menu.isDisplay'),
  },
  {
    component: 'Switch',
    componentProps: {
      checkedValue: 1,
      unCheckedValue: 0,
    },
    defaultValue: 1,
    dependencies: {
      show: (values) => {
        return values.type === 1;
      },
      triggerFields: ['type'],
    },
    fieldName: 'cache',
    label: $t('@sys-menu.isCache'),
  },
  {
    component: 'Textarea',
    fieldName: 'remark',
    label: $t('@sys-menu.remark'),
  },
];
