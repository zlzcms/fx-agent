<script setup lang="ts">
import { Page } from '@vben/common-ui';
import { IconifyIcon } from '@vben/icons';
import { useRouter } from 'vue-router';

const router = useRouter();

</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full items-center justify-center">
      <div class="text-center px-6 py-10">
        <IconifyIcon
          icon="mdi:tools"
          class="mx-auto mb-4"
          style="font-size: 64px; color: #9ca3af;"
        />
        <h2 class="text-xl mb-2">友情提示</h2>
        <p class="text-gray-500 mb-6">该功能正在开发中，敬请期待～</p>
      </div>
    </div>
  </Page>

</template>


