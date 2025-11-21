/**
 * @Author: zhujinlong
 * @Date:   2025-06-11 13:52:43
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-24 15:51:33
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, OnActionClickParams, VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

// AI模型接口类型
interface AIModel {
  id: string;
  name: string;
  api_key: string;
  base_url: string;
  model_type: string;
  model: string;
  temperature: number;
  status: boolean;
  created_time: string;
  updated_time: string;
}

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@ai-models.modelName'),
    componentProps: {
      placeholder: $t('@ai-models.enterModelNameExample'),
    },
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@ai-models.openAI'),
          value: 'OpenAI',
        },
        {
          label: $t('@ai-models.anthropic'),
          value: 'Anthropic',
        },
        {
          label: $t('@ai-models.google'),
          value: 'Google',
        },
        {
          label: $t('@ai-models.baidu'),
          value: 'Baidu',
        },
        {
          label: $t('@ai-models.alibaba'),
          value: 'Alibaba',
        },
        {
          label: $t('@ai-models.other'),
          value: 'Other',
        },
      ],
      placeholder: $t('@ai-models.selectModelType'),
    },
    fieldName: 'model_type',
    label: $t('@ai-models.modelType'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@ai-models.enable'),
          value: true,
        },
        {
          label: $t('@ai-models.disable'),
          value: false,
        },
      ],
      placeholder: $t('@ai-models.selectStatus'),
    },
    fieldName: 'status',
    label: $t('@ai-models.status'),
  },
];

// 表格列配置
export function useColumns(
  onActionClick?: OnActionClickFn<AIModel>,
  onRefresh?: () => void,
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
      title: $t('@ai-models.modelName'),
      maxWidth: 120,
      showOverflow: 'ellipsis',
    },
    {
      field: 'model_type',
      title: $t('@ai-models.modelType'),
      width: 120,
      slots: { default: 'model_type' },
    },
    {
      field: 'model',
      title: $t('@ai-models.modelIdentifier'),
      width: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'temperature',
      title: $t('@ai-models.temperature'),
      width: 100,
      formatter({ cellValue }) {
        return cellValue.toFixed(2);
      },
    },
    {
      field: 'api_key',
      title: $t('@ai-models.apiKey'),
      width: 200,
      slots: { default: 'api_key' },
    },
    {
      field: 'base_url',
      title: $t('@ai-models.baseUrl'),
      maxWidth: 150,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || $t('@ai-models.useDefaultAddress');
      },
    },
    {
      field: 'status',
      title: $t('@ai-models.status'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          onChange: async ({ row }: OnActionClickParams<AIModel>) => {
            try {
              // 导入API需要在函数内部进行动态导入
              const { toggleAIModelStatusApi } = await import('#/api');
              const { message } = await import('ant-design-vue');

              // 开关组件点击后，row.status已经是新的状态值
              await toggleAIModelStatusApi(row.id, row.status);
              const successMessage = row.status
                ? $t('@ai-models.toggleStatusSuccess')
                : $t('@ai-models.toggleStatusSuccess');
              message.success(successMessage);

              // 刷新表格数据
              if (onRefresh) {
                onRefresh();
              }
            } catch (error) {
              console.error($t('@ai-models.toggleStatusFailed'), error);
              const { message } = await import('ant-design-vue');
              message.error($t('@ai-models.toggleStatusFailed'));
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
      title: $t('page.table.created_time'),
      width: 160,
      formatter({ cellValue }) {
        return cellValue ? new Date(cellValue).toLocaleString() : '-';
      },
    },
    {
      field: 'updated_time',
      title: $t('page.table.updated_time'),
      width: 160,
      formatter({ cellValue }) {
        return cellValue ? new Date(cellValue).toLocaleString() : '-';
      },
    },
    {
      field: 'operation',
      title: $t('page.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 130,
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
      label: $t('@ai-models.modelName'),
      rules: z.string().min(1, { message: $t('@ai-models.enterModelName') }),
      componentProps: {
        placeholder: $t('@ai-models.enterModelNameExample'),
      },
    },
    {
      component: 'Select',
      fieldName: 'model_type',
      label: $t('@ai-models.modelType'),
      rules: z.string().min(1, { message: $t('@ai-models.pleaseSelectModelType') }),
      defaultValue: 'DeepSeek',
      componentProps: {
        options: [
          { label: 'DeepSeek', value: 'DeepSeek' },
          { label: 'OpenAI', value: 'OpenAI' },
          { label: 'Google', value: 'Google' },
          { label: 'Baidu', value: 'Baidu' },
          { label: 'Alibaba', value: 'Alibaba' },
          { label: 'HuoShan', value: 'HuoShan' },
          { label: 'Anthropic', value: 'Anthropic' },
          { label: $t('@ai-models.other'), value: 'Other' },
        ],
        placeholder: $t('@ai-models.selectModelType'),
      },
      dependencies: {
        triggerFields: ['model_type'],
        trigger: (values, formApi) => {
          const modelTypeUrlMap: Record<string, string> = {
            DeepSeek: 'https://api.deepseek.com/v1',
            OpenAI: 'https://api.openai.com/v1',
            Google: 'https://generativelanguage.googleapis.com/v1beta',
            Baidu: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1',
            Alibaba: 'https://dashscope.aliyuncs.com/api/v1',
            HuoShan: 'https://ark.cn-beijing.volces.com/api/v3',
            Anthropic: 'https://api.anthropic.com/v1',
            Other: '',
          };
          const baseUrl = modelTypeUrlMap[values.model_type] || '';
          formApi?.setFieldValue('base_url', baseUrl);
        },
      },
    },
    {
      component: 'Input',
      fieldName: 'model',
      label: $t('@ai-models.modelIdentifier'),
      rules: z.string().min(1, { message: $t('@ai-models.enterModelIdentifier') }),
      componentProps: {
        placeholder: $t('@ai-models.enterModelIdentifierExample'),
      },
      help: $t('@ai-models.modelIdentifierHelp'),
    },
    {
      component: 'InputNumber',
      fieldName: 'temperature',
      label: $t('@ai-models.temperature'),
      defaultValue: 0.75,
      componentProps: {
        min: 0,
        max: 1,
        step: 0.01,
        precision: 2,
        placeholder: $t('@ai-models.enterTemperature'),
      },
      help: $t('@ai-models.temperatureHelp'),
    },
    {
      component: 'InputPassword',
      fieldName: 'api_key',
      label: $t('@ai-models.apiKey'),
      rules: z.string().min(1, { message: $t('@ai-models.enterApiKey') }),
      componentProps: {
        placeholder: $t('@ai-models.enterApiKey'),
        autocomplete: 'off',
      },
      help: $t('@ai-models.apiKeyHelp'),
    },
    {
      component: 'Input',
      fieldName: 'base_url',
      label: $t('@ai-models.baseUrl'),
      componentProps: {
        placeholder: $t('@ai-models.enterBaseUrl'),
      },
      help: $t('@ai-models.baseUrlHelp'),
    },
    {
      component: 'Switch',
      fieldName: 'status',
      label: $t('@ai-models.enableStatus'),
      defaultValue: true,
      componentProps: {
        checkedChildren: $t('@ai-models.enable'),
        unCheckedChildren: $t('@ai-models.disable'),
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
      label: $t('@ai-models.modelName'),
      rules: z.string().min(1, { message: $t('@ai-models.enterModelName') }),
      componentProps: {
        placeholder: $t('@ai-models.enterModelName'),
      },
    },
    {
      component: 'Select',
      fieldName: 'model_type',
      label: $t('@ai-models.modelType'),
      rules: z.string().min(1, { message: $t('@ai-models.pleaseSelectModelType') }),
      componentProps: {
        options: [
          { label: 'DeepSeek', value: 'DeepSeek' },
          { label: 'OpenAI', value: 'OpenAI' },
          { label: 'Google', value: 'Google' },
          { label: 'Baidu', value: 'Baidu' },
          { label: 'Alibaba', value: 'Alibaba' },
          { label: 'HuoShan', value: 'HuoShan' },
          { label: 'Anthropic', value: 'Anthropic' },
          { label: $t('@ai-models.other'), value: 'Other' },
        ],
        placeholder: $t('@ai-models.selectModelType'),
      },
    },
    {
      component: 'Input',
      fieldName: 'model',
      label: $t('@ai-models.modelIdentifier'),
      rules: z.string().min(1, { message: $t('@ai-models.enterModelIdentifier') }),
      componentProps: {
        placeholder: $t('@ai-models.enterModelIdentifierExample'),
      },
      help: $t('@ai-models.modelIdentifierHelp'),
    },
    {
      component: 'InputNumber',
      fieldName: 'temperature',
      label: $t('@ai-models.temperature'),
      componentProps: {
        min: 0,
        max: 1,
        step: 0.01,
        precision: 2,
        placeholder: $t('@ai-models.enterTemperature'),
      },
      help: $t('@ai-models.temperatureHelp'),
    },
    {
      component: 'InputPassword',
      fieldName: 'api_key',
      label: $t('@ai-models.apiKey'),
      rules: z.string().min(1, { message: $t('@ai-models.enterApiKey') }),
      componentProps: {
        placeholder: $t('@ai-models.enterApiKey'),
        autocomplete: 'off',
      },
      help: $t('@ai-models.apiKeyHelp'),
    },
    {
      component: 'Input',
      fieldName: 'base_url',
      label: $t('@ai-models.baseUrl'),
      componentProps: {
        placeholder: $t('@ai-models.enterBaseUrl'),
      },
      help: $t('@ai-models.baseUrlHelp'),
    },
    {
      component: 'Switch',
      fieldName: 'status',
      label: $t('@ai-models.enableStatus'),
      componentProps: {
        checkedChildren: $t('@ai-models.enable'),
        unCheckedChildren: $t('@ai-models.disable'),
      },
    },
  ];
}
