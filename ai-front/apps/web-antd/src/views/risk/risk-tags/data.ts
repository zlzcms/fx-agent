/**
 * @Author: zhujinlong
 * @Date:   2025-06-23 14:17:33
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-23 15:00:23
 */

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
// 导入API类型
import type { RiskTag } from '#/api';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';
import { getAllRiskTypesApi } from '#/api';

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@risk.risk-tags.tagName'),
    componentProps: {
      placeholder: $t('@risk.risk-tags.enterTagName'),
    },
  },
  {
    component: 'ApiSelect',
    fieldName: 'risk_type',
    label: $t('@risk.risk-tags.riskType'),
    componentProps: {
      placeholder: $t('@risk.risk-tags.selectRiskType'),
      class: 'w-full',
      api: async () => {
        const data = await getAllRiskTypesApi();
        return data;
      },
      allowClear: true,
    },
  },
];

// 表格列配置
export function useColumns(onActionClick?: OnActionClickFn<RiskTag>): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'name',
      title: $t('@risk.risk-tags.tagName'),
      minWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'risk_type_name',
      title: $t('@risk.risk-tags.riskType'),
      minWidth: 120,
      showOverflow: 'ellipsis',
    },
    {
      field: 'description',
      title: $t('@risk.risk-tags.tagDescription'),
      minWidth: 200,
      showOverflow: 'ellipsis',
    },
    {
      field: 'created_time',
      title: $t('common.createdTime'),
      width: 180,
      formatter({ cellValue }) {
        if (!cellValue) return '';
        return new Date(cellValue).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
      },
    },
    {
      field: 'updated_time',
      title: $t('common.updatedTime'),
      width: 180,
      formatter({ cellValue }) {
        if (!cellValue) return '';
        return new Date(cellValue).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
      },
    },
    {
      field: 'operation',
      title: $t('page.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 120,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
    },
  ];
}

// 添加表单配置
export function useAddSchema(): VbenFormSchema[] {
  return [
    {
      component: 'ApiSelect',
      fieldName: 'risk_type',
      label: $t('@risk.risk-tags.riskType'),
      rules: z.string().min(1, { message: $t('@risk.risk-tags.selectRiskTypeRequired') }),
      componentProps: {
        placeholder: $t('@risk.risk-tags.selectRiskType'),
        class: 'w-full',
        api: async () => {
          const data = await getAllRiskTypesApi();
          return data;
        },
        autoSelect: 'first',
      },
    },
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@risk.risk-tags.tagName'),
      rules: z
        .string()
        .min(1, { message: $t('@risk.risk-tags.enterTagNameRequired') })
        .max(100, { message: $t('@risk.risk-tags.tagNameMaxLength') }),
      componentProps: {
        placeholder: $t('@risk.risk-tags.enterTagNameExample'),
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: $t('@risk.risk-tags.tagDescription'),
      rules: z
        .string()
        .max(500, { message: $t('@risk.risk-tags.tagDescriptionMaxLength') })
        .optional(),
      componentProps: {
        placeholder: $t('@risk.risk-tags.enterTagDescription'),
        rows: 3,
      },
    },
  ];
}

// 编辑表单配置
export function useEditSchema(): VbenFormSchema[] {
  return [
    {
      component: 'ApiSelect',
      fieldName: 'risk_type',
      label: $t('@risk.risk-tags.riskType'),
      rules: z.string().min(1, { message: $t('@risk.risk-tags.selectRiskTypeRequired') }),
      componentProps: {
        placeholder: $t('@risk.risk-tags.selectRiskType'),
        class: 'w-full',
        api: async () => {
          const data = await getAllRiskTypesApi();
          return data;
        },
      },
    },
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@risk.risk-tags.tagName'),
      rules: z
        .string()
        .min(1, { message: $t('@risk.risk-tags.enterTagNameRequired') })
        .max(100, { message: $t('@risk.risk-tags.tagNameMaxLength') }),
      componentProps: {
        placeholder: $t('@risk.risk-tags.enterTagNameExample'),
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: $t('@risk.risk-tags.tagDescription'),
      rules: z
        .string()
        .max(500, { message: $t('@risk.risk-tags.tagDescriptionMaxLength') })
        .optional(),
      componentProps: {
        placeholder: $t('@risk.risk-tags.enterTagDescription'),
        rows: 3,
      },
    },
  ];
}
