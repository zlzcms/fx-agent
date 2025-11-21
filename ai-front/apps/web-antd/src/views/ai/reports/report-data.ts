import type { VbenFormProps } from '#/adapter/form';
import type { VxeTableGridOptions } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';
import { formatDate } from '@vben/utils';

// 报告项数据类型（兼容API返回的数据结构）
export interface ReportItem {
  id: number;
  assistant_id: string;
  member_id: number;
  report_status: boolean;
  report_score: number;
  report_result?: string;
  report_table?: string;
  report_document?: string;
  created_time: string;
  updated_time: string;
  model_name?: string; // 模型名称
  ai_response?: {
    [key: string]: any;
    analytical_report: string;
    response_metadata: Record<string, any>;
    user_count: number;
  };
  assistant: {
    [key: string]: any;
    assistant_type_display: string;
    id: number;
    name: string;
  };
  summary?: string; // 处理后添加的摘要字段
}

// 报告配置类型
export interface ReportConfig {
  title: string;
  i18nPrefix: string;
  reportType: string;
}

// 获取评分标签颜色
export function getScoreColor(score: number): string {
  if (score >= 0.9) return 'success';
  if (score >= 0.7) return 'warning';
  return 'error';
}

// 创建查询表单配置
export function createQuerySchema(i18nPrefix: string) {
  return [
    {
      fieldName: 'assistant_name',
      label: $t(`${i18nPrefix}.assistantName`),
      component: 'Input',
      componentProps: {
        placeholder: $t(`${i18nPrefix}.assistantNamePlaceholder`),
      },
    },
    {
      fieldName: 'dateRange',
      label: $t(`${i18nPrefix}.dateRange`),
      component: 'RangePicker',
      componentProps: {
        placeholder: [$t(`${i18nPrefix}.startDate`), $t(`${i18nPrefix}.endDate`)],
        showTime: true,
        format: 'YYYY-MM-DD HH:mm:ss',
      },
    },
  ];
}

// 创建表格列配置
export function createColumns(i18nPrefix: string) {
  return [
    {
      field: 'id',
      title: $t(`${i18nPrefix}.recordId`),
      width: 100,
    },
    {
      field: 'assistant.name',
      title: $t(`${i18nPrefix}.assistantName`),
      width: 150,
    },
    {
      field: 'user_count',
      title: $t(`${i18nPrefix}.analysisUserCount`),
      width: 120,
      formatter: ({ cellValue }: { cellValue: number }) =>
        `${cellValue}${$t(`${i18nPrefix}.peopleUnit`)}`,
    },
    {
      field: 'created_time',
      title: $t(`${i18nPrefix}.generationTime`),
      width: 180,
      formatter: ({ cellValue }: { cellValue: string }) =>
        formatDate(cellValue, 'YYYY-MM-DD HH:mm:ss'),
    },
    {
      field: 'report_score',
      title: $t(`${i18nPrefix}.reportScore`),
      width: 100,
      slots: { default: 'reportScore' },
      formatter: ({ cellValue }: { cellValue: number }) => `${(cellValue * 100).toFixed(1)}%`,
    },
    {
      field: 'model_name',
      title: $t(`${i18nPrefix}.modelName`),
      width: 150,
    },
    {
      field: 'summary',
      title: $t(`${i18nPrefix}.summary`),
      minWidth: 200,
    },
    {
      field: 'action',
      title: $t(`${i18nPrefix}.operation`),
      width: 100,
      fixed: 'right' as const,
      slots: { default: 'action' },
    },
  ];
}

// 创建表格配置
export function createGridOptions(i18nPrefix: string): VxeTableGridOptions {
  return {
    rowConfig: {
      keyField: 'id',
      isHover: true,
      resizable: true,
    },
    virtualYConfig: {
      enabled: false,
    },
    autoResize: true,
    exportConfig: {},
    height: 'auto',
    printConfig: {},
    toolbarConfig: {
      search: true,
      export: true,
      print: true,
      refresh: { code: 'query' },
      custom: true,
      zoom: true,
    },
    pagerConfig: {},
    columns: createColumns(i18nPrefix),
  };
}

// 创建表单配置
export function createFormOptions(i18nPrefix: string): VbenFormProps {
  return {
    collapsed: false,
    showCollapseButton: true,
    submitButtonOptions: {
      content: $t('page.form.query'),
    },
    schema: createQuerySchema(i18nPrefix),
    submitOnChange: true,
    submitOnEnter: true,
  };
}
