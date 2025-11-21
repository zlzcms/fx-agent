import type { VbenFormSchema } from '#/adapter/form';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';
import { getTaskRegisteredApi } from '#/api';

export const schema: VbenFormSchema[] = [
  {
    component: 'RadioGroup',
    componentProps: {
      buttonStyle: 'solid',
      options: [
        { label: `${$t('@scheduler.interval')}（${$t('@scheduler.period')}）`, value: 0 },
        { label: `${$t('@scheduler.crontab')}（${$t('@scheduler.schedule')}）`, value: 1 },
      ],
      optionType: 'button',
    },
    defaultValue: 0,
    fieldName: 'type',
    formItemClass: 'col-span-2 md:col-span-2',
    label: $t('@scheduler.strategyType'),
  },
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('@scheduler.taskName'),
    rules: 'required',
  },
  {
    component: 'ApiSelect',
    componentProps: {
      allowClear: true,
      api: getTaskRegisteredApi,
      class: 'w-full',
      labelField: 'name',
      valueField: 'task',
      placeholder: $t('@scheduler.taskModuleName'),
    },
    fieldName: 'task',
    label: $t('@scheduler.celeryTask'),
    rules: 'required',
  },
  {
    component: 'Textarea',
    fieldName: 'args',
    label: $t('@scheduler.positionArgs'),
    help: $t('@scheduler.jsonListString'),
  },
  {
    component: 'Textarea',
    fieldName: 'kwargs',
    label: $t('@scheduler.keywordArgs'),
    help: $t('@scheduler.jsonDictString'),
    rules: z
      .string()
      .optional()
      .transform((val, ctx) => {
        if (!val) return null;

        try {
          const parsed = JSON.parse(val);
          return z.record(z.string(), z.unknown()).parse(parsed);
        } catch {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: $t('@scheduler.invalidJsonString'),
          });
          return z.NEVER;
        }
      }),
  },
  {
    component: 'Input',
    fieldName: 'queue',
    label: $t('@scheduler.queue'),
    help: $t('@scheduler.downToQueue'),
  },
  {
    component: 'Input',
    fieldName: 'exchange',
    label: $t('@scheduler.messageExchange'),
    help: $t('@scheduler.exchangeReference'),
  },
  {
    component: 'Input',
    fieldName: 'routing_key',
    label: $t('@scheduler.routingKey'),
    help: $t('@scheduler.routingKeyReference'),
  },
  {
    component: 'DatePicker',
    componentProps: {
      class: 'w-full',
      showTime: true,
    },
    fieldName: 'start_time',
    label: $t('@scheduler.startTime'),
  },
  {
    component: 'DatePicker',
    componentProps: {
      class: 'w-full',
      showTime: true,
    },
    dependencies: {
      disabled: (values) => {
        return !!values.expire_seconds;
      },
      triggerFields: ['expire_seconds'],
    },
    fieldName: 'expire_time',
    label: $t('@scheduler.endTime'),
    help: $t('@scheduler.onlySetOne'),
  },
  {
    component: 'InputNumber',
    componentProps: {
      class: 'w-full',
    },
    dependencies: {
      disabled: (values) => {
        return !!values.expire_time;
      },
      triggerFields: ['expire_time'],
    },
    fieldName: 'expire_seconds',
    label: $t('@scheduler.expireSeconds'),
    help: $t('@scheduler.onlySetOne'),
  },
  {
    component: 'InputNumber',
    componentProps: {
      class: 'w-full',
      min: 1,
    },
    dependencies: {
      show: (values) => {
        return values.type === 0;
      },
      required: (values) => {
        return values.type === 0;
      },
      triggerFields: ['type'],
    },
    fieldName: 'interval_every',
    label: $t('@scheduler.intervalPeriod'),
  },
  {
    component: 'Select',
    componentProps: {
      class: 'w-full',
      options: [
        {
          label: $t('@scheduler.days'),
          value: 'days',
        },
        {
          label: $t('@scheduler.hours'),
          value: 'hours',
        },
        {
          label: $t('@scheduler.minutes'),
          value: 'minutes',
        },
        {
          label: $t('@scheduler.seconds'),
          value: 'seconds',
        },
        // {
        //   label: '微秒',
        //   value: 'microseconds',
        // },
      ],
    },
    dependencies: {
      show: (values) => {
        return values.type === 0;
      },
      triggerFields: ['type'],
    },
    defaultValue: 'seconds',
    fieldName: 'interval_period',
    label: $t('@scheduler.periodType'),
  },
  {
    component: 'Input',
    dependencies: {
      show: (values) => {
        return values.type === 1;
      },
      required: (values) => {
        return values.type === 1;
      },
      triggerFields: ['type'],
    },
    fieldName: 'crontab',
    label: $t('@scheduler.schedule'),
    help: $t('@scheduler.crontabExpression'),
  },
  {
    component: 'RadioGroup',
    componentProps: {
      buttonStyle: 'solid',
      options: [
        { label: $t('common.enabled'), value: true },
        { label: $t('common.disabled'), value: false },
      ],
      optionType: 'button',
    },
    defaultValue: false,
    fieldName: 'one_off',
    label: $t('@scheduler.executeOnce'),
  },
  {
    component: 'Textarea',
    fieldName: 'remark',
    label: $t('@scheduler.remark'),
  },
];
