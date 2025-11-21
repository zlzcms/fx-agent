<script setup lang="ts">
import type { SysResetPasswordParams } from '#/api';

import { ref } from 'vue';

import { VbenButton } from '@vben/common-ui';

import { Modal } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { resetSysUserPasswordApi } from '#/api';
import { useAuthStore } from '#/store';

import { passwordSchema } from './data';

const props = defineProps<{ userId: number }>();

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  showDefaultActions: false,
  schema: passwordSchema,
});

const authStore = useAuthStore();
const buttonDisabled = ref<boolean>(false);
const buttonLoading = ref<boolean>(false);

const resetPassword = async () => {
  const { valid } = await formApi.validate();
  if (valid) {
    Modal.confirm({
      title: '提示',
      content: '确定修改密码吗？',
      onOk: async () => {
        buttonLoading.value = true;
        const data = await formApi.getValues<SysResetPasswordParams>();
        try {
          await resetSysUserPasswordApi(props.userId, data);
          await authStore.logout(false);
        } catch (error) {
          console.error(error);
        } finally {
          buttonLoading.value = false;
        }
      },
    });
  }
};
</script>

<template>
  <Form />
  <VbenButton
    :disabled="buttonDisabled"
    :loading="buttonLoading"
    @click="async () => await resetPassword()"
  >
    修改密码
  </VbenButton>
</template>
