import type { Ref } from 'vue';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
import type { RecommendedQuestion, SysRoleResult } from '#/api';

import { $t } from '@vben/locales';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'title',
    label: $t('@recommended-questions.questionTitle'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        { label: $t('@recommended-questions.normal'), value: 1 },
        { label: $t('@recommended-questions.disabled'), value: 0 },
      ],
    },
    fieldName: 'status',
    label: $t('common.form.status'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        { label: $t('@recommended-questions.yes'), value: true },
        { label: $t('@recommended-questions.no'), value: false },
      ],
    },
    fieldName: 'is_default',
    label: $t('@recommended-questions.isDefault'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<RecommendedQuestion>,
  roleSelectOptions?: Ref<SysRoleResult[]>,
): VxeGridProps['columns'] {
  return [
    // {
    //   field: 'seq',
    //   title: $t('common.table.id'),
    //   type: 'seq',
    //   width: 50,
    // },
    { field: 'title', title: $t('@recommended-questions.questionTitle'), minWidth: 160 },
    {
      field: 'content',
      title: $t('@recommended-questions.content'),
      minWidth: 240,
      showOverflow: 'ellipsis',
    },
    {
      field: 'role_ids',
      title: $t('@recommended-questions.roles'),
      minWidth: 160,
      formatter({ cellValue }) {
        if (!cellValue || !Array.isArray(cellValue) || cellValue.length === 0)
          return $t('@recommended-questions.notSet');
        const opts = roleSelectOptions?.value ?? [];
        return cellValue
          .map((id: number) => opts.find((r) => r.id === id)?.name ?? String(id))
          .join(', ');
      },
    },
    { field: 'sort_order', title: $t('@recommended-questions.sortOrder'), width: 100 },
    {
      field: 'is_default',
      title: $t('@recommended-questions.isDefault'),
      width: 100,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('@recommended-questions.yes'), value: true },
          { color: 'default', label: $t('@recommended-questions.no'), value: false },
        ],
      },
    },
    {
      field: 'status',
      title: $t('common.form.status'),
      width: 100,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('@recommended-questions.normal'), value: 1 },
          { color: 'error', label: $t('@recommended-questions.disabled'), value: 0 },
        ],
      },
    },
    { field: 'created_time', title: $t('common.table.created_time'), width: 168 },
    { field: 'updated_time', title: $t('common.table.updated_time'), width: 168 },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 200,
      cellRender: {
        attrs: {
          nameField: 'title',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
    },
  ];
}

export function useFormSchema(roleSelectOptions: any): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'title',
      label: $t('@recommended-questions.questionTitle'),
      componentProps: {
        class: 'w-full',
      },
      rules: 'required',
    },
    {
      component: 'Textarea',
      fieldName: 'content',
      label: $t('@recommended-questions.content'),
      componentProps: {
        class: 'w-full',
        rows: 4,
        maxLength: 500,
        showCount: true,
        placeholder: $t('@recommended-questions.contentPlaceholder'),
      },
      rules: 'required',
    },
    {
      component: 'Select',
      fieldName: 'role_ids',
      label: $t('@recommended-questions.associatedRoles'),
      componentProps: {
        class: 'w-full',
        mode: 'multiple',
        options: roleSelectOptions,
        fieldNames: { label: 'name', value: 'id' },
        filterOption: (input: string, option: SysRoleResult) => {
          return option.name?.toLowerCase()?.includes(input.toLowerCase()) ?? false;
        },
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'sort_order',
      label: $t('@recommended-questions.sortOrder'),
      componentProps: {
        class: 'w-full',
        min: 0,
        max: 9999,
        step: 1,
      },
    },
    {
      component: 'RadioGroup',
      fieldName: 'is_default',
      label: $t('@recommended-questions.isDefaultQuestion'),
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('@recommended-questions.yes'), value: true },
          { label: $t('@recommended-questions.no'), value: false },
        ],
        optionType: 'button',
      },
      defaultValue: false,
    },
    {
      component: 'RadioGroup',
      fieldName: 'status',
      label: $t('common.form.status'),
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('@recommended-questions.normal'), value: 1 },
          { label: $t('@recommended-questions.disabled'), value: 0 },
        ],
        optionType: 'button',
      },
      defaultValue: 1,
    },
  ];
}
