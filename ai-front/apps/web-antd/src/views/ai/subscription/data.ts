import type { Ref } from 'vue';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeGridProps } from '#/adapter/vxe-table';

import { $t } from '@vben/locales';

// 使用统一的接口定义，从 API 模块导入
// 不再在此文件中重复定义接口
import { SubscriptionType, subscriptionTypeOptions } from '#/types/subscription';

// Options
export const executionFrequencyOptions = [
  { label: $t('@subscription.executionFrequency.hours'), value: 'hours' },
  { label: $t('@subscription.executionFrequency.daily'), value: 'daily' },
  { label: $t('@subscription.executionFrequency.weekly'), value: 'weekly' },
  { label: $t('@subscription.executionFrequency.monthly'), value: 'monthly' },
];

export const weekdayOptions = [
  { label: $t('@subscription.weekdays.monday'), value: '1' },
  { label: $t('@subscription.weekdays.tuesday'), value: '2' },
  { label: $t('@subscription.weekdays.wednesday'), value: '3' },
  { label: $t('@subscription.weekdays.thursday'), value: '4' },
  { label: $t('@subscription.weekdays.friday'), value: '5' },
  { label: $t('@subscription.weekdays.saturday'), value: '6' },
  { label: $t('@subscription.weekdays.sunday'), value: '0' },
];

export const dayOptions = Array.from({ length: 31 }, (_, i) => ({
  label: $t('@subscription.dayNumber', { day: i + 1 }),
  value: i + 1,
}));

// Utility function
export function generatePlanCycleDescription(frequency: string, values: any) {
  const timeMap = {
    hours: () => $t('@subscription.everyNHours', { n: values.execution_hours }),
    daily: () => $t('@subscription.everyDayAt', { time: values.execution_time }),
    weekly: () => {
      const weekday = weekdayOptions.find((item) => item.value === values.execution_weekday);
      return $t('@subscription.everyWeekAt', {
        weekday: weekday?.label,
        time: values.execution_time,
      });
    },
    monthly: () => {
      const day = dayOptions.find((item) => item.value === values.execution_day);
      return $t('@subscription.everyMonthAt', { day: day?.label, time: values.execution_time });
    },
  };
  return timeMap[frequency as keyof typeof timeMap]?.() || '';
}

// Query Schema
export function useQuerySchema(): VbenFormSchema[] {
  return [
    {
      fieldName: 'name',
      label: $t('@subscription.subscriptionName'),
      component: 'Input',
      componentProps: {
        placeholder: $t('@subscription.pleaseEnterSubscriptionName'),
        allowClear: true,
      },
    },
    {
      fieldName: 'assistant_name',
      label: $t('@subscription.assistantName'),
      component: 'Input',
      componentProps: {
        placeholder: $t('@subscription.pleaseEnterAssistantName'),
        allowClear: true,
      },
    },
    {
      fieldName: 'status',
      label: $t('@subscription.status'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectStatus'),
        allowClear: true,
        options: [
          { label: $t('@subscription.enabled'), value: true },
          { label: $t('@subscription.disabled'), value: false },
        ],
      },
    },
  ];
}

// Props for schema functions
interface SchemaProps {
  assistantTypeOptions: Ref<any[]>;
  assistantOptionsByType: Ref<Record<string, any[]>>;
  responsibleOptions: Ref<any[]>;
  notificationMethodOptions: Ref<any[]>;
  customerOptions: Ref<any[]>;
  userOptions: Ref<any[]>;
  agentOptions: Ref<any[]>;
  countryOptions: Ref<any[]>;
  customerSearchLoading?: Ref<boolean>;
  userSearchLoading?: Ref<boolean>;
  agentSearchLoading?: Ref<boolean>;
  searchCustomers?: (keyword: string) => void;
  searchUsers?: (keyword: string) => void;
  searchAgents?: (keyword: string) => void;
}

// Add/Edit Schema
export function useSubscriptionSchema(props: SchemaProps): VbenFormSchema[] {
  return [
    {
      fieldName: 'name',
      label: $t('@subscription.subscriptionName'),
      component: 'Input',
      componentProps: {
        placeholder: $t('@subscription.pleaseEnterSubscriptionName'),
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'assistant_id',
      label: $t('@subscription.assistant'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectAssistant'),
        options: props.assistantOptionsByType.value.all || [], // Default to all
        showSearch: true,
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
        class: 'w-full',
      },
      rules: 'selectRequired',
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'execution_frequency',
      label: $t('@subscription.planCycle'),
      component: 'Select',
      defaultValue: 'hours',
      componentProps: { options: executionFrequencyOptions, class: 'w-full' },
      rules: 'selectRequired',
      formItemClass: 'col-span-2',
    },
    {
      fieldName: 'execution_hours',
      hideLabel: true,
      component: 'InputNumber',
      defaultValue: 1,
      componentProps: {
        placeholder: $t('@subscription.hourInterval'),
        min: 1,
        max: 23,
        addonAfter: $t('@subscription.hour'),
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-1',
      dependencies: {
        show: (v) => v.execution_frequency === 'hours',
        triggerFields: ['execution_frequency'],
      },
    },
    {
      fieldName: 'execution_weekday',
      hideLabel: true,
      component: 'Select',
      defaultValue: '1',
      componentProps: {
        placeholder: $t('@subscription.executionWeekday'),
        options: weekdayOptions,
        class: 'w-full',
      },
      rules: 'selectRequired',
      formItemClass: 'col-span-1',
      dependencies: {
        show: (v) => v.execution_frequency === 'weekly',
        triggerFields: ['execution_frequency'],
      },
    },
    {
      fieldName: 'execution_day',
      hideLabel: true,
      component: 'Select',
      defaultValue: 1,
      componentProps: {
        placeholder: $t('@subscription.executionDate'),
        options: dayOptions.map((i) => ({ ...i, value: String(i.value) })),
        class: 'w-full',
      },
      rules: 'selectRequired',
      formItemClass: 'col-span-1',
      dependencies: {
        show: (v) => v.execution_frequency === 'monthly',
        triggerFields: ['execution_frequency'],
      },
    },
    {
      fieldName: 'execution_time',
      hideLabel: true,
      component: 'TimePicker',
      defaultValue: '06:00',
      componentProps: {
        placeholder: $t('@subscription.executionTime'),
        format: 'HH:mm',
        valueFormat: 'HH:mm',
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-1',
      dependencies: {
        show: (v) => ['daily', 'monthly', 'weekly'].includes(v.execution_frequency),
        triggerFields: ['execution_frequency'],
      },
    },
    {
      fieldName: 'notification_recipients',
      label: $t('@subscription.notificationRecipients'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectNotificationRecipients'),
        mode: 'multiple',
        options: props.responsibleOptions.value || [],
        showSearch: true,
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'notification_methods',
      label: $t('@subscription.notificationMethods'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectNotificationMethods'),
        mode: 'multiple',
        options: props.notificationMethodOptions.value || [],
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'limit_types',
      label: $t('@subscription.dataRangeLimit'),
      component: 'Select',
      componentProps: {
        mode: 'multiple',
        placeholder: $t('@subscription.pleaseSelectDataRange'),
        options: [
          { label: $t('@subscription.registerTime'), value: 'register_time' },
          { label: $t('@subscription.customer'), value: 'customer' },
          { label: $t('@subscription.employee'), value: 'user' },
          { label: $t('@subscription.agent'), value: 'agent' },
          { label: $t('@subscription.country'), value: 'country' },
          { label: $t('@subscription.tag'), value: 'user_tag' },
          { label: $t('@subscription.kyc'), value: 'kyc' },
        ],
        class: 'w-full',
      },
      rules: 'required',
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'register_time',
      label: $t('@subscription.registerTime'),
      component: 'InputNumber',
      defaultValue: 1,
      componentProps: {
        placeholder: $t('@subscription.pleaseEnterDays'),
        min: 1,
        max: 365,
        addonAfter: $t('@subscription.days'),
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('register_time'),
        required: (v) => v.limit_types?.includes('register_time'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'customer',
      label: $t('@subscription.customer'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectCustomerOrSearch'),
        mode: 'multiple',
        options: props.customerOptions.value || [],
        showSearch: true,
        filterOption: false,
        loading: props.customerSearchLoading?.value || false,
        notFoundContent: $t('@subscription.noDataTrySearch'),
        onSearch: props.searchCustomers,
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('customer'),
        required: (v) => v.limit_types?.includes('customer'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'user',
      label: $t('@subscription.employee'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectEmployeeOrSearch'),
        mode: 'multiple',
        options: props.userOptions.value || [],
        showSearch: true,
        filterOption: false,
        loading: props.userSearchLoading?.value || false,
        notFoundContent: $t('@subscription.noDataTrySearch'),
        onSearch: props.searchUsers,
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('user'),
        required: (v) => v.limit_types?.includes('user'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'agent',
      label: $t('@subscription.agent'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectAgentOrSearch'),
        mode: 'multiple',
        options: props.agentOptions.value || [],
        showSearch: true,
        filterOption: false,
        loading: props.agentSearchLoading?.value || false,
        notFoundContent: $t('@subscription.noDataTrySearch'),
        onSearch: props.searchAgents,
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('agent'),
        required: (v) => v.limit_types?.includes('agent'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'country',
      label: $t('@subscription.country'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectCountry'),
        mode: 'multiple',
        options: props.countryOptions.value || [],
        showSearch: true,
        filterOption: (input: string, option: any) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()),
        maxTagCount: 3,
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('country'),
        required: (v) => v.limit_types?.includes('country'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'user_tag',
      label: $t('@subscription.tag'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectTag'),
        options: [
          { label: $t('@subscription.userTags.standard'), value: '0' },
          { label: $t('@subscription.userTags.whitelist'), value: '1' },
          { label: $t('@subscription.userTags.blacklist'), value: '2' },
        ],
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('user_tag'),
        required: (v) => v.limit_types?.includes('user_tag'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'kyc_status',
      label: $t('@subscription.kyc'),
      component: 'Select',
      componentProps: {
        placeholder: $t('@subscription.pleaseSelectKycStatus'),
        options: [
          { label: $t('@subscription.kycStatus.notKyc'), value: '0' },
          { label: $t('@subscription.kycStatus.questionnaire'), value: '1' },
          { label: $t('@subscription.kycStatus.basicInfo'), value: '2' },
          { label: $t('@subscription.kycStatus.uploadId'), value: '3' },
          { label: $t('@subscription.kycStatus.signContract'), value: '4' },
          { label: $t('@subscription.kycStatus.uploadAddress'), value: '5' },
          { label: $t('@subscription.kycStatus.kycSuccess'), value: '9' },
          { label: $t('@subscription.kycStatus.kycFailed'), value: '-1' },
        ],
        class: 'w-full',
      },
      dependencies: {
        show: (v) => v.limit_types?.includes('kyc'),
        required: (v) => v.limit_types?.includes('kyc'),
        triggerFields: ['limit_types'],
      },
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'status',
      label: $t('@subscription.status'),
      component: 'Switch',
      componentProps: {
        checkedChildren: $t('@subscription.enabled'),
        unCheckedChildren: $t('@subscription.disabled'),
      },
      defaultValue: true,
      formItemClass: 'col-span-4',
    },
    {
      fieldName: 'subscription_type',
      label: $t('@subscription.subscriptionType'),
      component: 'Input',
      componentProps: { style: { display: 'none' } },
      defaultValue: SubscriptionType.SERVER,
      formItemClass: 'hidden',
    },
  ];
}

// Columns
export function useColumns(
  onActionClick: OnActionClickFn,
  getAssistantName: (id: string) => string,
): VxeGridProps['columns'] {
  return [
    { field: 'name', title: $t('@subscription.subscriptionName'), minWidth: 160, fixed: 'left' },
    {
      field: 'subscription_type',
      title: $t('@subscription.subscriptionType'),
      minWidth: 100,
      formatter: ({ cellValue }) =>
        subscriptionTypeOptions.find((i) => i.value === cellValue)?.label || cellValue,
    },
    {
      field: 'assistant_name',
      title: $t('@subscription.assistantName'),
      minWidth: 120,
      formatter: ({ cellValue }) => getAssistantName(cellValue),
    },
    {
      field: 'notification_methods',
      title: $t('@subscription.notificationMethods'),
      minWidth: 120,
      formatter: ({ cellValue }) =>
        Array.isArray(cellValue) ? cellValue.map((m) => m.name).join(', ') : '-',
    },
    {
      field: 'plan_cycle',
      title: $t('@subscription.executionPlan'),
      minWidth: 120,
      slots: { default: 'plan_cycle' },
    },
    {
      field: 'responsible_persons',
      title: $t('@subscription.notificationRecipients'),
      minWidth: 140,
      formatter: ({ cellValue }) => {
        if (!Array.isArray(cellValue) || cellValue.length === 0) return '-';
        const names = cellValue
          .map((p) => {
            if (typeof p === 'string') return p;
            return p.username || p.name || p.email || `人员${p.personnel_id || p.id || ''}`;
          })
          .filter(Boolean);
        return names.length > 3
          ? $t('@subscription.peopleCount', { count: names.length })
          : names.join(', ');
      },
    },
    {
      field: 'status',
      title: $t('@subscription.status'),
      minWidth: 80,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('@subscription.enabled'), value: true },
          { color: 'error', label: $t('@subscription.disabled'), value: false },
        ],
      },
    },
    {
      field: 'created_time',
      title: $t('@subscription.createdTime'),
      minWidth: 160,
      formatter: ({ cellValue }) => (cellValue ? new Date(cellValue).toLocaleString() : '-'),
    },
    {
      field: 'operation',
      title: $t('@subscription.operation'),
      align: 'center',
      fixed: 'right',
      width: 120,
      cellRender: {
        name: 'CellOperation',
        attrs: { nameField: 'name', onClick: onActionClick },
        options: ['edit', 'delete'],
      },
    },
  ];
}
