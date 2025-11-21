<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import Email from '#/plugins/config/views/email.vue';
import ComingSoon from '#/views/_core/fallback/coming-soon.vue';

import AiModel from './ai-model.vue';
import ApiKey from './api-key.vue';
import Hook from './hook.vue';

const activeKey = ref('0');

const emailRef = ref();
const hookRef = ref();
const aiModelRef = ref();
const apiKeyRef = ref();
watch(
  activeKey,
  async (newValue) => {
    switch (newValue) {
      case '3': {
        await nextTick();
        if (emailRef.value) {
          await emailRef.value.fetchConfigList();
        }

        break;
      }
      case '4': {
        await nextTick();
        if (hookRef.value) {
          await hookRef.value.fetchConfigList();
        }

        break;
      }
      case '5': {
        await nextTick();
        if (aiModelRef.value) {
          await aiModelRef.value.fetchConfigList();
        }

        break;
      }
      case '6': {
        await nextTick();
        if (apiKeyRef.value) {
          await apiKeyRef.value.fetchConfigList();
        }

        break;
      }
      // No default
    }
  },
  { immediate: true },
);
</script>

<template>
  <Page auto-content-height>
    <a-card class="h-full overflow-y-auto rounded-[var(--radius)]" :bordered="false">
      <a-tabs
        class="h-full"
        v-model:active-key="activeKey"
        tab-position="left"
        animated
        :tab-bar-style="{ width: '16%' }"
      >
        <a-tab-pane key="0">
          <template #tab>
            <span class="icon-[mdi--web] -mb-1 size-5"></span>
            {{ $t('@sys-config.websiteConfig') }}
          </template>
          <ComingSoon />
        </a-tab-pane>
        <a-tab-pane key="1">
          <template #tab>
            <span class="icon-[carbon--security] -mb-1 size-5"></span>
            {{ $t('@sys-config.securityConfig') }}
          </template>
          <ComingSoon />
        </a-tab-pane>
        <a-tab-pane key="2">
          <template #tab>
            <span class="icon-[majesticons--lock-line] -mb-1 size-5"></span>
            {{ $t('@sys-config.loginConfig') }}
          </template>
          <ComingSoon />
        </a-tab-pane>
        <a-tab-pane key="3">
          <template #tab>
            <span class="icon-[ic--outline-email] -mb-1 size-5"></span>
            {{ $t('@sys-config.emailConfig') }}
          </template>
          <Email ref="emailRef" />
        </a-tab-pane>
        <a-tab-pane key="4">
          <template #tab>
            <span class="icon-[ic--outline-email] -mb-1 size-5"></span>
            {{ $t('@sys-config.larkWebhook') }}
          </template>
          <Hook ref="hookRef" />
        </a-tab-pane>
        <a-tab-pane key="5">
          <template #tab>
            <span class="icon-[mdi--robot] -mb-1 size-5"></span>
            {{ $t('@sys-config.aiModelConfig') }}
          </template>
          <AiModel ref="aiModelRef" />
        </a-tab-pane>
        <a-tab-pane key="6">
          <template #tab>
            <span class="icon-[mdi--key] -mb-1 size-5"></span>
            {{ $t('@sys-config.apiKeyManagement') }}
          </template>
          <ApiKey ref="apiKeyRef" />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </Page>
</template>

<style lang="scss" scoped>
:deep(.ant-card-body) {
  height: 100%;
  min-height: 100%;
}
</style>
