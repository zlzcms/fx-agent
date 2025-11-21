import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, OnActionClickParams, VxeGridProps } from '#/adapter/vxe-table';
import type { SysRoleResult, SysUserResult } from '#/api';

import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { z } from '#/adapter/form';
import { getSysDeptTreeApi, updateSysUserPermissionApi } from '#/api';

export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'username',
    label: $t('@sys-user.username'),
  },
  {
    component: 'Input',
    fieldName: 'phone',
    label: $t('@sys-user.phone'),
  },
  {
    component: 'Select',
    componentProps: {
      allowClear: true,
      options: [
        {
          label: $t('@sys-user.normal'),
          value: 1,
        },
        {
          label: $t('@sys-user.disabled'),
          value: 0,
        },
      ],
      placeholder: $t('common.form.select'),
    },
    fieldName: 'status',
    label: $t('common.form.status'),
  },
];

export function useColumns(
  onActionClick?: OnActionClickFn<SysUserResult>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      fixed: 'left',
      width: 50,
    },
    { field: 'username', title: $t('@sys-user.username'), fixed: 'left', width: 100 },
    { field: 'nickname', title: $t('@sys-user.nickname'), width: 100 },
    {
      field: 'avatar',
      title: $t('@sys-user.avatar'),
      width: 80,
      slots: { default: 'avatar' },
    },
    {
      field: 'dept',
      title: $t('@sys-user.department'),
      width: 120,
      slots: { default: 'dept' },
    },
    {
      field: 'roles',
      title: $t('@sys-user.role'),
      width: 200,
      showOverflow: 'ellipsis',
      slots: { default: 'roles' },
    },
    {
      field: 'phone',
      title: $t('@sys-user.phone'),
      width: 150,
      formatter({ cellValue }) {
        return cellValue || $t('@sys-user.none');
      },
    },
    {
      field: 'email',
      title: $t('@sys-user.email'),
      width: 150,
      formatter({ cellValue }) {
        return cellValue || $t('@sys-user.none');
      },
    },
    {
      field: 'crm_user_id',
      title: $t('@sys-user.crmUserId'),
      width: 150,
      formatter({ cellValue }) {
        return cellValue || $t('@sys-user.notBound');
      },
    },
    {
      field: 'status',
      title: $t('@sys-user.status'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          onChange: ({ row }: OnActionClickParams<SysUserResult>) => {
            updateSysUserPermissionApi(row.id, 'status').then(
              message.success($t('ui.actionMessage.operationSuccess')),
            );
          },
        },
      },
    },
    {
      field: 'is_superuser',
      title: $t('@sys-user.superAdmin'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          onChange: ({ row }: OnActionClickParams<SysUserResult>) => {
            updateSysUserPermissionApi(row.id, 'superuser').then(
              message.success($t('ui.actionMessage.operationSuccess')),
            );
          },
        },
        props: {
          checkedValue: true,
          unCheckedValue: false,
        },
      },
    },
    {
      field: 'is_staff',
      title: $t('@sys-user.backendLogin'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          onChange: ({ row }: OnActionClickParams<SysUserResult>) => {
            updateSysUserPermissionApi(row.id, 'staff').then(
              message.success($t('ui.actionMessage.operationSuccess')),
            );
          },
        },
        props: {
          checkedValue: true,
          unCheckedValue: false,
        },
      },
    },
    {
      field: 'is_multi_login',
      title: $t('@sys-user.multiLogin'),
      width: 100,
      cellRender: {
        name: 'CellSwitch',
        attrs: {
          onChange: ({ row }: OnActionClickParams<SysUserResult>) => {
            updateSysUserPermissionApi(row.id, 'multi_login').then(
              message.success($t('ui.actionMessage.operationSuccess')),
            );
          },
        },
        props: {
          checkedValue: true,
          unCheckedValue: false,
        },
      },
    },
    {
      field: 'join_time',
      title: $t('@sys-user.registerTime'),
      width: 168,
    },
    {
      field: 'last_login_time',
      title: $t('@sys-user.lastLoginTime'),
      width: 168,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 150,
      cellRender: {
        attrs: {
          nameField: 'username',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          'edit',
          {
            code: 'delete',
            disabled: (row: SysUserResult) => {
              return row.username === 'admin';
            },
          },
          {
            code: 'more',
            items: [{ code: 'reset_password', text: $t('@sys-user.resetPassword') }],
          },
        ],
      },
    },
  ];
}

export function useEditSchema(roleSelectOptions: any): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('@sys-user.username'),
      rules: 'required',
    },
    {
      component: 'Input',
      fieldName: 'nickname',
      label: $t('@sys-user.nickname'),
      rules: 'required',
    },
    {
      component: 'Input',
      fieldName: 'avatar',
      label: $t('@sys-user.avatarUrl'),
    },
    {
      component: 'Input',
      fieldName: 'phone',
      label: $t('@sys-user.phoneNumber'),
      rules: z
        .string()
        .regex(/^1[3-9]\d{9}$/, $t('@sys-user.enterCorrectPhone'))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'email',
      label: $t('@sys-user.email'),
      rules: z
        .string({ message: $t('@sys-user.enterEmail') })
        .email($t('@sys-user.enterCorrectEmail')),
    },
    {
      component: 'Input',
      fieldName: 'crm_user_id',
      label: $t('@sys-user.crmUserId'),
      componentProps: {
        placeholder: $t('@sys-user.crmUserIdPlaceholder'),
      },
    },
    {
      component: 'ApiTreeSelect',
      componentProps: {
        allowClear: true,
        api: getSysDeptTreeApi,
        class: 'w-full',
        labelField: 'name',
        valueField: 'id',
        childrenField: 'children',
      },
      fieldName: 'dept_id',
      label: $t('@sys-user.belongDepartment'),
    },
    {
      component: 'Select',
      componentProps: {
        class: 'w-full',
        mode: 'multiple',
        options: roleSelectOptions,
        fieldNames: { label: 'name', value: 'id' },
        filterOption: (input: string, option: SysRoleResult) => {
          return option.name?.toLowerCase()?.includes(input.toLowerCase()) ?? false;
        },
      },
      fieldName: 'roles',
      label: $t('@sys-user.role'),
      rules: 'selectRequired',
    },
  ];
}

export function useAddSchema(roleSelectOptions: any): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('@sys-user.username'),
      rules: 'required',
    },
    {
      component: 'Input',
      fieldName: 'nickname',
      label: $t('@sys-user.nickname'),
    },
    {
      component: 'InputPassword',
      fieldName: 'password',
      label: $t('@sys-user.password'),
      rules: z
        .string({ message: $t('@sys-user.enterPassword') })
        .min(6, $t('@sys-user.passwordMinLength'))
        .max(20, $t('@sys-user.passwordMaxLength')),
    },
    {
      component: 'Input',
      fieldName: 'phone',
      label: $t('@sys-user.phoneNumber'),
      rules: z
        .string()
        .regex(/^1[3-9]\d{9}$/, $t('@sys-user.enterCorrectPhone'))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'email',
      label: $t('@sys-user.email'),
      rules: z
        .string({ message: $t('@sys-user.enterEmail') })
        .email($t('@sys-user.enterCorrectEmail')),
    },
    {
      component: 'Input',
      fieldName: 'crm_user_id',
      label: $t('@sys-user.crmUserId'),
      componentProps: {
        placeholder: $t('@sys-user.crmUserIdPlaceholder'),
      },
    },
    {
      component: 'ApiTreeSelect',
      componentProps: {
        allowClear: true,
        api: getSysDeptTreeApi,
        class: 'w-full',
        labelField: 'name',
        valueField: 'id',
        childrenField: 'children',
      },
      fieldName: 'dept_id',
      label: $t('@sys-user.belongDepartment'),
      rules: 'required',
    },
    {
      component: 'Select',
      componentProps: {
        class: 'w-full',
        mode: 'multiple',
        options: roleSelectOptions,
        fieldNames: { label: 'name', value: 'id' },
        filterOption: (input: string, option: SysRoleResult) => {
          return option.name?.toLowerCase()?.includes(input.toLowerCase()) ?? false;
        },
      },
      fieldName: 'roles',
      label: $t('@sys-user.role'),
      rules: 'selectRequired',
    },
  ];
}

export const resetPwdSchema: VbenFormSchema[] = [
  {
    component: 'InputPassword',
    fieldName: 'password',
    label: $t('@sys-user.password'),
    rules: z
      .string({ message: $t('@sys-user.enterNewPassword') })
      .min(6, $t('@sys-user.passwordMinLengthAlt'))
      .max(20, $t('@sys-user.passwordMaxLength')),
  },
];
