/**
 * @Author: zhujinlong
 * @Date:   2025-06-23 11:01:06
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-23 13:39:51
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

// 风控等级接口类型
interface RiskLevel {
  id: string;
  name: string;
  start_score: number;
  end_score: number;
  description?: string;
  created_time: string;
  updated_time: string;
}

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@risk.risk-levels.levelName'),
    componentProps: {
      placeholder: $t('@risk.risk-levels.enterLevelName'),
    },
  },
  {
    component: 'InputNumber',
    fieldName: 'min_score',
    label: $t('@risk.risk-levels.minScore'),
    componentProps: {
      placeholder: $t('@risk.risk-levels.enterMinScore'),
      min: 0,
      max: 1000,
    },
  },
  {
    component: 'InputNumber',
    fieldName: 'max_score',
    label: $t('@risk.risk-levels.maxScore'),
    componentProps: {
      placeholder: $t('@risk.risk-levels.enterMaxScore'),
      min: 0,
      max: 1000,
    },
  },
];

// 表格列配置
export function useColumns(onActionClick?: OnActionClickFn<RiskLevel>): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'name',
      title: $t('@risk.risk-levels.levelName'),
      minWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'start_score',
      title: $t('@risk.risk-levels.startScore'),
      width: 100,
      align: 'center',
    },
    {
      field: 'end_score',
      title: $t('@risk.risk-levels.endScore'),
      width: 100,
      align: 'center',
    },
    {
      field: 'score_range',
      title: $t('@risk.risk-levels.scoreRange'),
      width: 150,
      align: 'center',
      formatter({ row }) {
        return `${row.start_score} - ${row.end_score}`;
      },
    },
    {
      field: 'description',
      title: $t('@risk.risk-levels.description'),
      minWidth: 200,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
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
      component: 'Input',
      fieldName: 'name',
      label: $t('@risk.risk-levels.levelName'),
      rules: z.string().min(1, { message: $t('@risk.risk-levels.enterLevelNameRequired') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterLevelNameExample'),
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'start_score',
      label: $t('@risk.risk-levels.startScore'),
      rules: z
        .number()
        .min(0, { message: $t('@risk.risk-levels.startScoreMin') })
        .max(1000, { message: $t('@risk.risk-levels.startScoreMax') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterStartScore'),
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'end_score',
      label: $t('@risk.risk-levels.endScore'),
      rules: z
        .number()
        .min(0, { message: $t('@risk.risk-levels.endScoreMin') })
        .max(1000, { message: $t('@risk.risk-levels.endScoreMax') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterEndScore'),
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: $t('@risk.risk-levels.description'),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterDescriptionOptional'),
        rows: 3,
        maxlength: 500,
        showCount: true,
      },
    },
  ];
}

// 编辑表单配置
export function useEditSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@risk.risk-levels.levelName'),
      rules: z.string().min(1, { message: $t('@risk.risk-levels.enterLevelNameRequired') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterLevelNameExample'),
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'start_score',
      label: $t('@risk.risk-levels.startScore'),
      rules: z
        .number()
        .min(0, { message: $t('@risk.risk-levels.startScoreMin') })
        .max(1000, { message: $t('@risk.risk-levels.startScoreMax') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterStartScore'),
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'end_score',
      label: $t('@risk.risk-levels.endScore'),
      rules: z
        .number()
        .min(0, { message: $t('@risk.risk-levels.endScoreMin') })
        .max(1000, { message: $t('@risk.risk-levels.endScoreMax') }),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterEndScore'),
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: $t('@risk.risk-levels.description'),
      componentProps: {
        placeholder: $t('@risk.risk-levels.enterDescriptionOptional'),
        rows: 3,
        maxlength: 500,
        showCount: true,
      },
    },
  ];
}
