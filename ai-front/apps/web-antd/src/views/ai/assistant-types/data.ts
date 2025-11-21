/**
 * @Author: zhujinlong
 * @Date:   2025-06-11 13:52:43
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-21 17:55:19
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

// 助手类型接口类型
interface AssistantType {
  id: string;
  name: string;
  created_time: string;
  updated_time: string;
}

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@ai-assistantTypes.typeName'),
    componentProps: {
      placeholder: $t('@ai-assistantTypes.enterTypeName'),
    },
  },
];

// 表格列配置
export function useColumns(
  onActionClick?: OnActionClickFn<AssistantType>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'name',
      title: $t('@ai-assistantTypes.typeName'),
      minWidth: 150,
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
      component: 'Input',
      fieldName: 'name',
      label: $t('@ai-assistantTypes.typeName'),
      rules: z.string().min(1, { message: $t('@ai-assistantTypes.enterTypeNameRequired') }),
      componentProps: {
        placeholder: $t('@ai-assistantTypes.enterTypeNameExample'),
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
      label: $t('@ai-assistantTypes.typeName'),
      rules: z.string().min(1, { message: $t('@ai-assistantTypes.enterTypeNameRequired') }),
      componentProps: {
        placeholder: $t('@ai-assistantTypes.enterTypeNameExample'),
      },
    },
  ];
}
