/**
 * @Author: zhujinlong
 * @Date:   2025-06-23 15:45:00
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-07-05 11:57:14
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { z } from '#/adapter/form';
// 导入API
import { updateRiskAssistantStatusApi } from '#/api';

// 风控助手接口类型
interface RiskAssistant {
  id: string;
  name: string;
  ai_model_id: string;
  ai_model_name?: string;
  role: string;
  risk_type?: string;
  background?: string;
  task_prompt: string;
  variable_config?: string;
  report_config?: string;
  status: boolean | number; // 支持布尔值和数字类型
  created_time: string;
  updated_time: string;
}

// AI模型映射 - 移除缓存机制，改为实时获取
const aiModelMap = new Map<string, string>();

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@risk.risk-assistants.name'),
    componentProps: {
      placeholder: $t('@risk.risk-assistants.inputName'),
    },
  },
  {
    component: 'Select',
    fieldName: 'ai_model_id',
    label: $t('@risk.risk-assistants.aiModel'),
    componentProps: {
      allowClear: true,
      placeholder: $t('@risk.risk-assistants.selectAIModel'),
      showSearch: true,
      options: [], // 动态加载
    },
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        { label: $t('@risk.risk-assistants.enabled'), value: true },
        { label: $t('@risk.risk-assistants.disabled'), value: false },
      ],
      placeholder: $t('@risk.risk-assistants.selectStatus'),
    },
    fieldName: 'status',
    label: $t('@risk.risk-assistants.status'),
  },
];

// 状态切换API函数
const updateRiskAssistantStatusApiHandler = async (id: string, status: boolean) => {
  try {
    const result = await updateRiskAssistantStatusApi(id, status);
    message.success(
      `${status ? $t('@risk.risk-assistants.enabled') : $t('@risk.risk-assistants.disabled')}${$t('@risk.risk-assistants.riskAssistant')} ${$t('@risk.risk-assistants.success')}`,
    );
    return result;
  } catch (error: any) {
    console.error($t('@risk.risk-assistants.switchStatusFailed'), error);
    message.error(
      $t('@risk.risk-assistants.switchStatusError', {
        msg: error?.response?.data?.msg || error?.message || $t('@risk.risk-assistants.retry'),
      }),
    );
    throw error; // 重新抛出错误，让组件回滚状态
  }
};

// 状态值标准化函数
export function normalizeStatusValue(status: any): boolean {
  if (typeof status === 'boolean') {
    return status;
  }
  if (typeof status === 'number') {
    return status === 1;
  }
  if (typeof status === 'string') {
    return status === 'true' || status === '1';
  }
  return Boolean(status);
}

// 表格列配置
export function useColumns(
  onActionClick?: OnActionClickFn<RiskAssistant>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('@risk.risk-assistants.seq'),
      type: 'seq',
      width: 60,
    },
    {
      field: 'name',
      title: $t('@risk.risk-assistants.name'),
      minWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'ai_model_id',
      title: $t('@risk.risk-assistants.aiModel'),
      width: 120,
      showOverflow: 'ellipsis',
      formatter({ row }) {
        return getAIModelNameById(row.ai_model_id);
      },
    },
    {
      field: 'role',
      title: $t('@risk.risk-assistants.role'),
      width: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'risk_type',
      title: $t('@risk.risk-assistants.riskType'),
      width: 120,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    {
      field: 'background',
      title: $t('@risk.risk-assistants.background'),
      minWidth: 200,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    {
      field: 'task_prompt',
      title: $t('@risk.risk-assistants.taskPrompt'),
      minWidth: 200,
      showOverflow: 'ellipsis',
    },
    {
      field: 'status',
      title: $t('@risk.risk-assistants.status'),
      width: 100,
      align: 'center',
      cellRender: {
        name: 'CellSwitch',
        props: {
          checkedValue: true,
          unCheckedValue: false,
        },
        attrs: {
          onChange: async ({ row }: { row: RiskAssistant }) => {
            // 标准化原始状态值
            const originalStatus = normalizeStatusValue(row.status);
            // 开关组件会直接改变row.status的值，这里我们使用改变后的值
            const newStatus = row.status as boolean;

            try {
              const result = await updateRiskAssistantStatusApiHandler(row.id, newStatus);

              // 确保返回的状态值也被标准化并更新到行数据
              if (result && result.status !== undefined) {
                row.status = normalizeStatusValue(result.status);
              }
            } catch (error) {
              console.error($t('@risk.risk-assistants.switchStatusRollback'), error);
              // API调用失败，回滚到原状态
              row.status = originalStatus;
            }
          },
        },
      },
    },
    {
      field: 'created_time',
      title: $t('@risk.risk-assistants.createdTime'),
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
      title: $t('@risk.risk-assistants.updatedTime'),
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
      title: $t('@risk.risk-assistants.operation'),
      align: 'center',
      fixed: 'right',
      width: 120,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit'],
      },
    },
  ];
}

// 基本信息表单配置
export function useBasicInfoSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('@risk.risk-assistants.name'),
      rules: z.string().min(1, { message: $t('@risk.risk-assistants.inputName') }),
      formItemClass: 'col-span-2',
      componentProps: {
        placeholder: $t('@risk.risk-assistants.inputRiskAssistantName'),
        maxlength: 50,
        showCount: true,
        style: { width: '100%' },
      },
    },
    {
      component: 'Select',
      fieldName: 'ai_model_id',
      label: $t('@risk.risk-assistants.aiModel'),
      rules: z.string().min(1, { message: $t('@risk.risk-assistants.selectAIModel') }),
      formItemClass: 'col-span-2',
      componentProps: {
        placeholder: $t('@risk.risk-assistants.selectAIModel'),
        showSearch: true,
        options: [], // 动态加载
        style: { width: '100%' },
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
      },
    },
    {
      component: 'Input',
      fieldName: 'role',
      label: $t('@risk.risk-assistants.role'),
      rules: z.string().min(1, { message: $t('@risk.risk-assistants.inputRole') }),
      formItemClass: 'col-span-2',
      componentProps: {
        placeholder: $t('@risk.risk-assistants.inputRolePlaceholder'),
        maxlength: 100,
        showCount: true,
        style: { width: '100%' },
      },
    },
    {
      component: 'Textarea',
      fieldName: 'background',
      label: $t('@risk.risk-assistants.backgroundDesc'),
      rules: z.string().min(1, { message: $t('@risk.risk-assistants.inputBackgroundDesc') }),
      formItemClass: 'col-span-2',
      componentProps: {
        placeholder: $t('@risk.risk-assistants.inputBackgroundDescPlaceholder'),
        rows: 3,
        maxlength: 2000,
        showCount: true,
        style: { width: '100%' },
      },
    },
    {
      component: 'Input',
      fieldName: 'task_prompt',
      label: $t('@risk.risk-assistants.taskPrompt'),
      formItemClass: 'col-span-2 hidden', // 隐藏这个字段，因为会用自定义组件替代
      componentProps: {
        style: { display: 'none' },
      },
    },
  ];
}

// 变量配置表单配置 - 使用类似AI助手的表格配置
export function useVariableConfigSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'variable_config',
      label: $t('@risk.risk-assistants.variableConfig'),
      formItemClass: 'col-span-2 hidden', // 隐藏这个字段，使用自定义组件
      componentProps: {
        style: { display: 'none' },
      },
    },
  ];
}

// 报告配置表单配置 - 使用类似AI助手的文档配置
export function useReportConfigSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'report_config',
      label: $t('@risk.risk-assistants.reportConfig'),
      formItemClass: 'col-span-2 hidden', // 隐藏这个字段，使用自定义组件
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
      label: $t('views.ai.assistants.analysisDataSource'), // 分析数据源
      rules: z
        .array(z.string())
        .min(1, { message: $t('views.ai.assistants.pleaseSelectAnalysisDataSource') }),
      formItemClass: 'col-span-2', // 占满整行
      componentProps: {
        mode: 'multiple',
        placeholder: $t('views.ai.assistants.pleaseSelectAnalysisDataSource'),
        options: [], // 需要动态加载数据源列表
        showSearch: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().includes(input.toLowerCase());
        },
        maxTagCount: 3,
        maxTagPlaceholder: (omittedValues: any[]) =>
          `+${omittedValues.length}${$t('views.ai.assistants.dataSources')}`,
        style: { width: '100%' },
      },
      // help: $t('views.ai.assistants.selectDataSourcesForAIAssistant'),
    },

    {
      component: 'Select',
      fieldName: 'data_time_range_type',
      // rules: z.array(z.string()).min(1, { message: $t('views.ai.assistants.dataTimeRange') }),
      label: $t('views.ai.assistants.dataTimeRange'), // 数据时间范围
      formItemClass: 'col-span-1', // 占半行
      defaultValue: 'month',
      componentProps: {
        placeholder: $t('views.ai.assistants.pleaseSelectRange'),
        options: [
          { label: $t('views.ai.assistants.byDay'), value: 'day' },
          { label: $t('views.ai.assistants.byMonth'), value: 'month' },
          { label: $t('views.ai.assistants.byQuarter'), value: 'quarter' },
          { label: $t('views.ai.assistants.byYear'), value: 'year' },
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
        .min(1, { message: $t('views.ai.assistants.pleaseEnterValue') })
        .nullable()
        .refine((val) => val !== null && val !== undefined, {
          message: $t('views.ai.assistants.pleaseEnterValue'),
        }),
      componentProps: {
        placeholder: $t('views.ai.assistants.pleaseEnterValue'),
        min: 1,
        max: 100,
        style: { width: '100%' },
      },
      dependencies: {
        triggerFields: ['data_time_range_type'],
        componentProps: (values: Record<string, any>) => {
          const unitLabels: Record<string, string> = {
            day: $t('views.ai.assistants.days'),
            month: $t('views.ai.assistants.months'),
            quarter: $t('views.ai.assistants.quarters'),
            year: $t('views.ai.assistants.years'),
          };
          return {
            addonAfter:
              unitLabels[values.data_time_range_type as string] || $t('views.ai.assistants.months'),
          };
        },
      },
    },
  ];
}

// 添加表单配置
export function useAddSchema(): VbenFormSchema[] {
  return [...useBasicInfoSchema()];
}

// 编辑表单配置
export function useEditSchema(): VbenFormSchema[] {
  return [...useBasicInfoSchema()];
}

// 变量配置项类型
export interface VariableConfigItem {
  fieldName: string;
  fieldType: 'boolean' | 'date' | 'number' | 'string';
  fieldDesc?: string;
  required?: boolean;
}

// 报告配置项类型
export interface ReportConfigItem {
  template: 'custom' | 'detailed' | 'standard' | 'summary';
  content: string;
  sections?: Array<{
    enabled: boolean;
    name: string;
    order?: number;
    title: string;
  }>;
}

// 默认变量配置模板
export const defaultVariableConfig: VariableConfigItem[] = [
  {
    fieldName: $t('@risk.risk-assistants.loginAnalysis'),
    fieldType: 'string',
    fieldDesc: $t('@risk.risk-assistants.loginAbnormalDetection'),
    required: true,
  },
  {
    fieldName: $t('@risk.risk-assistants.fundAnalysis'),
    fieldType: 'string',
    fieldDesc: $t('@risk.risk-assistants.fundAbnormalDetection'),
    required: true,
  },
  {
    fieldName: $t('@risk.risk-assistants.transferAnalysis'),
    fieldType: 'string',
    fieldDesc: $t('@risk.risk-assistants.transferAbnormalDetection'),
    required: true,
  },
];

// 默认报告配置模板
export const defaultReportConfig: ReportConfigItem = {
  template: 'standard',
  content: '',
  sections: [
    {
      name: 'executive_summary',
      title: $t('@risk.risk-assistants.executiveSummary'),
      enabled: true,
      order: 1,
    },
    {
      name: 'risk_analysis',
      title: $t('@risk.risk-assistants.riskAnalysis'),
      enabled: true,
      order: 2,
    },
    {
      name: 'data_insights',
      title: $t('@risk.risk-assistants.dataInsights'),
      enabled: true,
      order: 3,
    },
    {
      name: 'recommendations',
      title: $t('@risk.risk-assistants.recommendations'),
      enabled: true,
      order: 4,
    },
  ],
};

// 加载AI模型选项 - 不使用缓存，每次都从API获取最新数据
export async function loadAIModelOptions() {
  try {
    // 导入AI模型API
    const { getAllAIModelsApi } = await import('#/api');
    const models = await getAllAIModelsApi();

    // 清空并重建映射
    aiModelMap.clear();
    models.forEach((model) => {
      aiModelMap.set(model.id, model.name);
    });

    const aiModelOptions = models.map((model) => ({
      label: model.name,
      value: model.id,
    }));

    return aiModelOptions;
  } catch (error) {
    console.error('加载AI模型选项失败:', error);
    // 清理映射，避免使用过期数据
    clearAIModelMap();
    return [];
  }
}

// 根据AI模型ID获取模型名称
export function getAIModelNameById(modelId: string): string {
  if (!modelId) {
    console.warn('getAIModelNameById: modelId为空');
    return '-';
  }

  const modelName = aiModelMap.get(modelId);
  if (modelName) {
    return modelName;
  }

  // 返回ID作为fallback，而不是直接返回'-'
  return modelId;
}

// 清理AI模型映射
export function clearAIModelMap() {
  aiModelMap.clear();
  console.warn('AI模型映射已清理');
}
