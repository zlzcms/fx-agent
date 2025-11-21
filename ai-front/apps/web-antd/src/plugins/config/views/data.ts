import type { VbenFormSchema } from '#/adapter/form';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

export const emailSchema: VbenFormSchema[] = [
  {
    component: 'Select',
    componentProps: {
      options: [
        {
          label: 'SMTP',
          value: '0',
        },
      ],
    },
    defaultValue: '0',
    fieldName: 'EMAIL_PROTOCOL',
    label: $t('@sys-config.emailProtocol'),
    rules: 'required',
  },
  {
    component: 'Input',
    fieldName: 'EMAIL_HOST',
    label: $t('@sys-config.serverAddress'),
    rules: 'required',
  },
  {
    component: 'InputNumber',
    fieldName: 'EMAIL_PORT',
    label: $t('@sys-config.serverPort'),
    rules: 'required',
  },
  {
    component: 'Input',
    fieldName: 'EMAIL_USERNAME',
    label: $t('@sys-config.emailAccount'),
    rules: z.string().email({ message: $t('@sys-config.invalidEmail') }),
  },
  {
    component: 'Input',
    fieldName: 'EMAIL_PASSWORD',
    label: $t('@sys-config.emailPassword'),
    help: $t('@sys-config.emailPasswordHelp'),
    rules: 'required',
  },
  {
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: $t('common.enabled'), value: '1' },
        { label: $t('common.disabled'), value: '0' },
      ],
      optionType: 'button',
    },
    defaultValue: '1',
    fieldName: 'EMAIL_SSL',
    label: $t('@sys-config.sslEncryption'),
    labelClass: 'float-left',
    rules: 'required',
  },
  {
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: $t('common.enabled'), value: '1' },
        { label: $t('common.disabled'), value: '0' },
      ],
      optionType: 'button',
    },
    defaultValue: '0',
    fieldName: 'EMAIL_STATUS',
    label: $t('@sys-config.status'),
    help: $t('@sys-config.statusHelp'),
    rules: 'required',
  },
];

export const hookSchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'HOOK_ADDR',
    label: $t('@sys-config.hookAddress'),
    rules: 'required',
  },

  {
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: $t('common.enabled'), value: '1' },
        { label: $t('common.disabled'), value: '0' },
      ],
      optionType: 'button',
    },
    defaultValue: '0',
    fieldName: 'HOOK_STATUS',
    label: $t('@sys-config.status'),
    help: $t('@sys-config.statusHelp'),
    rules: 'required',
  },
];

export const aiModelSchema: VbenFormSchema[] = [
  {
    component: 'Select',
    fieldName: 'ai_default_model_id',
    label: $t('@sys-config.defaultAIModel'),
    help: $t('@sys-config.defaultAIModelHelp'),
    componentProps: {
      options: [],
      placeholder: $t('@sys-config.selectDefaultAIModel'),
      showSearch: true,
      allowClear: true,
      filterOption: (input: string, option: any) => {
        return option.label.toLowerCase().includes(input.toLowerCase());
      },
    },
  },
];
