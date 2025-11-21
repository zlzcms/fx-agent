/**
 * @Author: zhujinlong
 * @Date:   2025-01-03 15:30:00
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-25 10:53:52
 */
import type { VbenFormSchema } from '#/adapter/form';
import type {
  OnActionClickFn,
  OnActionClickParams,
  VxeGridProps,
} from '#/adapter/vxe-table';

import { $t } from '@vben/locales';
import { z } from '#/adapter/form';

import type { AIAssistantTemplate } from '#/api';
import { toggleAIAssistantTemplateStatusApi } from '#/api';

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('views.ai.templates.assistantName'),
    componentProps: {
      placeholder: $t('views.ai.templates.enterAssistantName'),
    },
  },
  {
    component: 'Input',
    fieldName: 'type',
    label: $t('views.ai.templates.assistantType'),
    componentProps: {
      placeholder: $t('views.ai.templates.enterAssistantType'),
    },
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('views.ai.templates.enabled'),
          value: true,
        },
        {
          label: $t('views.ai.templates.disabled'),
          value: false,
        },
      ],
      placeholder: $t('views.ai.templates.selectTemplateStatus'),
    },
    fieldName: 'template_is_open',
    label: $t('views.ai.templates.templateStatus'),
  },
];

// AI助手类型颜色映射
const ASSISTANT_TYPE_COLOR_MAP: Record<string, string> = {
  'data_analyst': 'blue',
  'report_generator': 'green',
  'dashboard_creator': 'purple',
  'alert_monitor': 'orange',
  'custom': 'default',
};

// 表格列配置
export function useColumns(
  onActionClick?: OnActionClickFn<AIAssistantTemplate>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('page.table.id'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'avatar',
      title: $t('views.ai.templates.avatar'),
      width: 80,
      cellRender: {
        name: 'CellImage',
        props: {
          height: 40,
          width: 40,
          round: true,
          preview: false,
          fallback: '/default-avatar.png',
        },
      },
    },
    {
      field: 'name',
      title: $t('views.ai.templates.assistantName'),
      maxWidth: 100,
      showOverflow: 'ellipsis',
    },
    {
      field: 'type',
      title: $t('views.ai.templates.assistantType'),
      width: 140,
      formatter({ cellValue }) {
        const typeMap: Record<string, string> = {
          'data_analyst': $t('views.ai.templates.dataAnalyst'),
          'report_generator': $t('views.ai.templates.reportGenerator'),
          'dashboard_creator': $t('views.ai.templates.dashboardCreator'),
          'alert_monitor': $t('views.ai.templates.alertMonitor'),
          'custom': $t('views.ai.templates.custom')
        };
        return typeMap[cellValue] || cellValue || '-';
      },
    },

    {
      field: 'description',
      title: $t('views.ai.templates.description'),
      maxWidth: 150,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    {
      field: 'template_is_open',
      title: $t('views.ai.templates.templateStatus'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          beforeChange: async (newStatus: boolean, row: AIAssistantTemplate) => {
            try {
              await toggleAIAssistantTemplateStatusApi(row.id, newStatus);
              // 显示成功消息
              const { message } = await import('ant-design-vue');
              const successMessage = newStatus
                ? $t('views.ai.templates.templateEnabledSuccess')
                : $t('views.ai.templates.templateDisabledSuccess');
              message.success(successMessage);
              return true; // 允许状态更新
            } catch (error) {
              // 显示错误消息
              const { message } = await import('ant-design-vue');
              const errorMessage = newStatus
                ? $t('views.ai.templates.templateEnabledFailed')
                : $t('views.ai.templates.templateDisabledFailed');
              message.error(errorMessage);
              return false; // 阻止状态更新
            }
          },
        },
        props: {
          checkedValue: true,
          unCheckedValue: false,
        },
      },
    },

    {
      field: 'created_time',
      title: $t('views.ai.templates.createdTime'),
      width: 160,
      formatter({ cellValue }) {
        return cellValue ? new Date(cellValue).toLocaleString() : '-';
      },
    },
    {
      field: 'updated_time',
      title: $t('views.ai.templates.updatedTime'),
      width: 160,
      formatter({ cellValue }) {
        return cellValue ? new Date(cellValue).toLocaleString() : '-';
      },
    },
  ];
}

// 获取助手类型颜色
export function getAssistantTypeColor(type: string): string {
  return ASSISTANT_TYPE_COLOR_MAP[type] || 'default';
}
