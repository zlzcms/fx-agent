import type { VbenFormSchema } from '#/adapter/form';

import { h } from 'vue';

import { $t } from '@vben/locales';

import { Button } from 'ant-design-vue';

export function userSchema(fileList: any): VbenFormSchema[] {
  return [
    {
      component: 'RadioGroup',
      defaultValue: 0,
      componentProps: {
        options: [
          {
            label: $t('@sys-plugin.zipPackage'),
            value: 0,
          },
          {
            label: $t('@sys-plugin.git'),
            value: 1,
          },
        ],
      },
      fieldName: 'installType',
      label: $t('@sys-plugin.installMethod'),
    },
    {
      component: 'Upload',
      dependencies: {
        show: (values) => values && values.installType === 0,
        triggerFields: ['installType'],
      },
      componentProps: {
        name: 'file',
        accept: '.zip',
        maxCount: 1,
        multiple: false,
        directory: false,
        fileList: fileList.value,
        beforeUpload: (file: any) => {
          fileList.value = [file];
          return false;
        },
        onRemove: () => {
          fileList.value = [];
        },
      },
      renderComponentContent: () => ({
        default: () => {
          return h(Button, {}, { default: () => $t('@sys-plugin.upload') });
        },
      }),
      fieldName: 'uploadField',
      label: $t('@sys-plugin.zipFile'),
      rules: 'required',
      help: $t('@sys-plugin.zipFileHelp'),
    },
    {
      component: 'Input',
      dependencies: {
        show: (values) => values && values.installType === 1,
        triggerFields: ['installType'],
      },
      fieldName: 'repo_url',
      label: $t('@sys-plugin.gitAddress'),
      rules: 'required',
      help: $t('@sys-plugin.gitAddressHelp'),
    },
  ];
}
