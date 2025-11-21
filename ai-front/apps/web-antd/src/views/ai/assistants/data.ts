/**
 * @Author: zhujinlong
 * @Date:   2025-06-11 13:55:05
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-07-07 18:02:58
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';
// 导入新的接口类型
import type { PersonnelData } from '#/api';

// 导入表格字段配置相关类型
import { h } from 'vue';

import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { z } from '#/adapter/form';
// 导入正确的API函数
import { getAllAssistantTypesApi, updateAIAssistantApi } from '#/api';

// AI助手接口类型 - 更新字段定义
interface AIAssistant {
  id: string;
  name: string;
  type: string;
  assistant_type_id: string;
  assistant_type_display?: string;
  ai_model_id: string;
  ai_model_name?: string;
  avatar?: string;
  description: string;
  model_definition: string; // 模型定义
  execution_frequency: string; // 执行频率：每天、每周、每月
  execution_time: string; // 执行时间：具体时间点
  // 新增的执行时间配置字段
  execution_minutes?: number; // 分钟间隔
  execution_hours?: number; // 小时间隔
  execution_weekday?: string; // 执行星期
  execution_weekly_time?: string; // 每周执行时间
  execution_day?: string; // 执行日期
  execution_monthly_time?: string; // 每月执行时间
  // 修改 responsible_persons 类型
  responsible_persons: PersonnelData[];
  notification_methods: string[]; // 通知方式（多选）
  status: boolean;
  is_template: boolean; // 设为模板
  is_view_myself: boolean; // 本人查看
  // 数据源相关
  data_sources: Array<{
    collection_id: string;
    tables: any[];
  }>; // 分析数据源（多选）
  data_permissions: string[]; // 数据权限范围（多选）
  data_permission: string;
  data_limit?: number; // 数据限制条数
  // 输出相关
  output_format: 'both' | 'document' | 'table'; // 输出方式：表格、文档、两者都有
  output_data?: Record<string, any>; // 合并后的输出数据JSON
  created_time: string;
  updated_time: string;
}

// 执行频率选项
export const executionFrequencyOptions = [
  { label: $t('@ai-assistants.minutes'), value: 'minutes' },
  { label: $t('@ai-assistants.hours'), value: 'hours' },
  { label: $t('@ai-assistants.daily'), value: 'daily' },
  { label: $t('@ai-assistants.weekly'), value: 'weekly' },
  { label: $t('@ai-assistants.monthly'), value: 'monthly' },
];
// 执行星期选项
export const executionWeekdayOptions = [
  { label: $t('@ai-assistants.monday'), value: '1' },
  { label: $t('@ai-assistants.tuesday'), value: '2' },
  { label: $t('@ai-assistants.wednesday'), value: '3' },
  { label: $t('@ai-assistants.thursday'), value: '4' },
  { label: $t('@ai-assistants.friday'), value: '5' },
  { label: $t('@ai-assistants.saturday'), value: '6' },
  { label: $t('@ai-assistants.sunday'), value: '0' },
];

// 数据范围限制类型选项
// 数据范围限制选项已移除

// 创建动态查询表单配置的函数
export function createQuerySchema(
  assistantTypeOptions: Array<{ label: string; value: string }> = [],
): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@ai-assistants.assistantName'),
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseEnterAssistantName'),
      },
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: assistantTypeOptions,
        placeholder: $t('@ai-assistants.pleaseSelectAssistantType'),
        showSearch: true,
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
      },
      fieldName: 'assistant_type_id',
      label: $t('@ai-assistants.assistantType'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('@ai-assistants.enabled'), value: true },
          { label: $t('@ai-assistants.disabled'), value: false },
        ],
        placeholder: $t('@ai-assistants.pleaseSelectStatus'),
      },
      fieldName: 'status',
      label: $t('@ai-assistants.status'),
    },
  ];
}

// 查询表单配置 - 保持原有的静态配置作为默认
export const querySchema: VbenFormSchema[] = createQuerySchema();

// 状态切换API函数 - 修复为调用正确的API
const updateAIAssistantStatusApi = async (id: string, status: boolean) => {
  try {
    // 调用真正的更新API，只更新状态字段，但需要包含必填字段data_permission
    await updateAIAssistantApi(id, { status, data_permission: '' });
    message.success(
      `${status ? $t('@ai-assistants.enabled') : $t('@ai-assistants.disabled')}AI助手成功`,
    );
  } catch (error: any) {
    console.error('切换AI助手状态失败:', error);
    message.error(`切换状态失败：${error?.message || $t('@ai-assistants.pleaseRetry')}`);
    throw error; // 重新抛出错误，让组件回滚状态
  }
};

// 表格列配置
export function useColumns(onActionClick?: OnActionClickFn<AIAssistant>): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('@ai-assistants.sequenceNumber'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'avatar',
      title: $t('@ai-assistants.avatar'),
      width: 80,
      slots: { default: 'avatar' },
    },
    {
      field: 'name',
      title: $t('@ai-assistants.assistantName'),
      maxWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'assistant_type_display',
      title: $t('@ai-assistants.assistantType'),
      width: 120,
      slots: { default: 'assistant_type_id' },
    },
    {
      field: 'ai_model_id',
      title: $t('@ai-assistants.aiModel'),
      width: 150,
      slots: { default: 'ai_model_id' },
    },
    {
      field: 'description',
      title: $t('@ai-assistants.description'),
      maxWidth: 200,
      slots: { default: 'description' },
    },
    {
      field: 'execution_time',
      title: $t('@ai-assistants.executionPlan'),
      width: 180,
      formatter: ({ row }: { row: AIAssistant }) => {
        const {
          execution_frequency,
          execution_minutes,
          execution_hours,
          execution_time,
          execution_weekday,
          execution_weekly_time,
          execution_day,
          execution_monthly_time,
        } = row;

        if (!execution_frequency) {
          return '-';
        }

        switch (execution_frequency) {
          case 'daily': {
            return `每天 ${execution_time || ''}`;
          }
          case 'hours': {
            return `每 ${execution_hours || ''} ${$t('@ai-assistants.hours')}`;
          }
          case 'minutes': {
            return `每 ${execution_minutes || ''} ${$t('@ai-assistants.minutes')}`;
          }
          case 'monthly': {
            return `${$t('@ai-assistants.monthly')}${execution_day || ''}日 ${execution_monthly_time || ''}`;
          }
          case 'weekly': {
            const weekdayLabel =
              executionWeekdayOptions.find((opt) => opt.value === execution_weekday)?.label || '';
            return `${$t('@ai-assistants.weekly')}${weekdayLabel} ${execution_weekly_time || ''}`;
          }
          default: {
            return execution_frequency || '-';
          }
        }
      },
    },
    {
      field: 'output_format',
      title: $t('@ai-assistants.outputFormat'),
      width: 100,
      formatter: ({ cellValue }) => {
        const formatMap: Record<string, string> = {
          table: $t('@ai-assistants.table'),
          document: $t('@ai-assistants.document'),
          both: $t('@ai-assistants.tableAndDocument'),
        };
        return formatMap[cellValue] || cellValue || '-';
      },
    },
    {
      field: 'status',
      title: $t('@ai-assistants.status'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          beforeChange: async (newStatus: boolean, row: AIAssistant) => {
            try {
              await updateAIAssistantStatusApi(row.id, newStatus);
              return true; // 允许状态更新
            } catch {
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
      title: $t('@ai-assistants.createdTime'),
      width: 160,
    },
    {
      field: 'operation',
      title: $t('@ai-assistants.operation'),
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

// 基本信息表单配置 - 第一部分（基础信息）
export function useBasicInfoPart1Schema(): VbenFormSchema[] {
  return [
    {
      component: 'Upload',
      fieldName: 'avatar',
      label: $t('@ai-assistants.assistantImage'),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        accept: 'image/*',
        listType: 'picture-card',
        maxCount: 1,
        showUploadList: {
          showPreviewIcon: true,
          showRemoveIcon: true,
          showDownloadIcon: false,
        },
        beforeUpload: (file: File) => {
          // 检查文件类型
          const isImage = file.type.startsWith('image/');
          if (!isImage) {
            message.error($t('@ai-assistants.onlyImageFilesAllowed'));
            return false;
          }

          // 检查文件大小（限制为2MB）
          const isLt2M = file.size / 1024 / 1024 < 2;
          if (!isLt2M) {
            message.error($t('@ai-assistants.imageSizeCannotExceed2MB'));
            return false;
          }

          return false; // 阻止自动上传，由表单统一处理
        },
      },
      renderComponentContent: () => ({
        default: () =>
          h(
            'div',
            {
              style: {
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#666',
              },
            },
            [
              h('div', { style: { fontSize: '24px', marginBottom: '8px' } }, '+'),
              h('div', { style: { fontSize: '14px' } }, $t('@ai-assistants.uploadImage')),
            ],
          ),
      }),
      // help: $t('@ai-assistants.supportedFormatsAndSize'),
    },
    {
      component: 'Select',
      fieldName: 'assistant_type_id',
      label: $t('@ai-assistants.assistantType'),
      rules: z.string().min(1, { message: $t('@ai-assistants.pleaseSelectAssistantType') }),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseSelectAssistantType'),
        options: [],
        style: { width: '100%' },
        showSearch: true,
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
      },
      // help: $t('@ai-assistants.selectAssistantFunctionType'),
    },
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@ai-assistants.assistantName'), // 助手名称
      rules: z.string().min(1, { message: $t('@ai-assistants.pleaseEnterAssistantName') }),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseEnterAssistantName'),
        maxlength: 50,
        showCount: true,
        style: { width: '100%' },
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: $t('@ai-assistants.assistantDescription'), // 助手描述
      rules: z.string().min(1, { message: $t('@ai-assistants.pleaseEnterAssistantDescription') }),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseEnterAssistantFunctionDescription'),
        rows: 3,
        maxlength: 500,
        showCount: true,
        style: { width: '100%' },
      },
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        placeholder: $t('@ai-assistants.pleaseSelectAIModel'),
        showSearch: true,
        options: [], // 动态加载
        style: { width: '100%' },
      },
      formItemClass: 'col-span-2', // 占满整行
      fieldName: 'ai_model_id',
      label: $t('@ai-assistants.aiModel'), // AI模型
      rules: z.string().min(1, { message: $t('@ai-assistants.pleaseSelectAIModel') }),
    },
    {
      component: 'Input',
      fieldName: 'model_definition',
      label: $t('@ai-assistants.modelDefinition'), // 模型定义
      formItemClass: 'col-span-2 hidden', // 隐藏这个字段，因为会用自定义组件替代
      componentProps: {
        style: { display: 'none' },
      },
    },
  ];
}

// 数据源表单配置
export function useDataSourceSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Select',
      fieldName: 'data_sources',
      label: $t('@ai-assistants.analysisDataSource'), // 分析数据源
      rules: z
        .array(z.string())
        .min(1, { message: $t('@ai-assistants.pleaseSelectAnalysisDataSource') }),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        mode: 'multiple',
        placeholder: $t('@ai-assistants.pleaseSelectAnalysisDataSource'),
        options: [], // 需要动态加载数据源列表
        showSearch: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().includes(input.toLowerCase());
        },
        maxTagCount: 3,
        maxTagPlaceholder: (omittedValues: any[]) =>
          `+${omittedValues.length}${$t('@ai-assistants.dataSources')}`,
        style: { width: '100%' },
      },
      // help: $t('@ai-assistants.selectDataSourcesForAIAssistant'),
    },

    // {
    //   component: 'Select',
    //   fieldName: 'data_permission',
    //   label: $t('@ai-assistants.dataPermissionScope'),//数据权限范围
    //   formItemClass: 'col-span-1', // 占半行
    //   rules: z.string().min(1, { message: $t('@ai-assistants.pleaseSelectDataPermissionScope') }),
    //   componentProps: {
    //     placeholder: $t('@ai-assistants.pleaseSelectDataPermissionScope'),
    //     options: [
    //       { label: $t('@ai-assistants.allEmployees'), value: 'all_employee' },
    //       { label: $t('@ai-assistants.crmUsers'), value: 'crm_user' },
    //       { label: $t('@ai-assistants.agents'), value: 'agent_user' },
    //     ],
    //     style: { width: '100%' },
    //   },
    // },
    // {
    //   component: 'Select',
    //   fieldName: 'data_permission_values',
    //   formItemClass: 'col-span-1 fixed-label-width-10', // 占半行
    //   componentProps: {
    //     mode: 'multiple',
    //     placeholder: $t('@ai-assistants.pleaseSelectRange'),
    //     options: [], // 需要根据权限范围动态加载
    //     showSearch: true,
    //     filterOption: (input: string, option: any) => {
    //       console.log('option', option);
    //       return option.label.toLowerCase().includes(input.toLowerCase());
    //     },
    //     maxTagCount: 3,
    //     maxTagPlaceholder: (omittedValues: any[]) => `+${omittedValues.length}${$t('@ai-assistants.items')}`,
    //     style: { width: '100%' },
    //   }
    // },

    {
      component: 'Select',
      fieldName: 'data_time_range_type',
      // rules: z.array(z.string()).min(1, { message: $t('@ai-assistants.dataTimeRange') }),
      label: $t('@ai-assistants.dataTimeRange'), // 数据时间范围
      formItemClass: 'col-span-1', // 占半行
      defaultValue: 'month',
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseSelectRange'),
        options: [
          { label: $t('@ai-assistants.byDay'), value: 'day' },
          { label: $t('@ai-assistants.byMonth'), value: 'month' },
          { label: $t('@ai-assistants.byQuarter'), value: 'quarter' },
          { label: $t('@ai-assistants.byYear'), value: 'year' },
        ],
        style: { width: '100%' },
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'data_time_value',
      formItemClass: 'col-span-1 fixed-label-width-10', // 占半行
      label: '',
      defaultValue: 1,
      rules: z
        .number()
        .min(1, { message: $t('@ai-assistants.pleaseEnterValue') })
        .nullable()
        .refine((val) => val !== null && val !== undefined, {
          message: $t('@ai-assistants.pleaseEnterValue'),
        }),
      componentProps: {
        placeholder: $t('@ai-assistants.pleaseEnterValue'),
        min: 1,
        max: 100,
        style: { width: '100%' },
      },
      dependencies: {
        triggerFields: ['data_time_range_type'],
        componentProps: (values: Record<string, any>) => {
          const unitLabels: Record<string, string> = {
            day: $t('@ai-assistants.days'),
            month: $t('@ai-assistants.months'),
            quarter: $t('@ai-assistants.quarters'),
            year: $t('@ai-assistants.years'),
          };
          return {
            addonAfter:
              unitLabels[values.data_time_range_type as string] || $t('@ai-assistants.months'),
          };
        },
      },
    },

    // DataPermissionConfig 已移到模板中直接使用
    // {
    //   component: 'InputNumber',
    //   fieldName: 'data_limit',
    //   label: $t('@ai-assistants.dataAnalysisPerTime'),
    //   defaultValue: 100,
    //   formItemClass: 'col-span-2', // 占满整行
    //   componentProps: {
    //     placeholder: $t('@ai-assistants.pleaseEnterDataAnalysisLimit'),
    //     min: 1,
    //     max: 200,
    //     style: { width: '100%' },
    //     addonAfter: $t('@ai-assistants.data'),
    //   },
    // }
  ];
}

// 输出配置表单 - 包含输出方式和输出数据字段
export function useOutputSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'output_format',
      label: '',
      defaultValue: 'table',
      rules: z.string().min(1, { message: $t('@ai-assistants.pleaseSelectOutputFormat') }),
      formItemClass: 'col-span-2 output-format-field hidden-field',
      componentProps: {
        type: 'hidden',
      },
    },
    {
      component: 'Input',
      fieldName: 'output_data',
      label: $t('@ai-assistants.outputData'),
      formItemClass: 'col-span-2 hidden-field',
      componentProps: {
        type: 'hidden',
      },
    },
  ];
}

// 数据范围限制表单配置
// 数据范围限制表单配置已移除

// 添加表单配置 - 使用新的分组结构
export function useAddSchema(): VbenFormSchema[] {
  return [...useDataSourceSchema(), ...useOutputSchema()];
}

// 编辑表单配置 - 使用新的分组结构
export function useEditSchema(): VbenFormSchema[] {
  return [...useDataSourceSchema(), ...useOutputSchema()];
}

// 导出相关的类型和函数
export type { AIAssistant };

// 动态加载助手类型选项
export async function loadAssistantTypeOptions() {
  try {
    const response = await getAllAssistantTypesApi();
    return response.map((type: any) => ({
      label: type.name,
      value: type.id,
    }));
  } catch (error) {
    console.error('加载助手类型失败:', error);
    return [];
  }
}

export { type TableFieldConfigItem } from '#/components/table-field-config';
