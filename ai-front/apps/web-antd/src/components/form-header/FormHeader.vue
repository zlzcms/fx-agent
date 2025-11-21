<script setup lang="ts">
import { $t } from '@vben/locales';

import CustomTabs from '#/components/CustomTabs.vue';

interface Tab {
  key: string;
  label: string;
}

defineProps({
  tabs: {
    type: Array as () => Tab[],
    required: true,
  },
  activeTab: {
    type: String,
    required: true,
  },
  submitLoading: {
    type: Boolean,
    default: false,
  },
  submitLabel: {
    type: String,
    required: true,
  },
});

defineEmits<{
  cancel: [];
  submit: [];
  tabChange: [tab: string];
}>();
</script>

<template>
  <div class="top-section">
    <div class="tabs-section">
      <CustomTabs :tabs="tabs" :active-tab="activeTab" @tab-change="$emit('tabChange', $event)" />
    </div>

    <div class="action-buttons">
      <a-button type="primary" @click="$emit('submit')" :loading="submitLoading">
        {{ submitLabel }}
      </a-button>
      <a-button @click="$emit('cancel')" :disabled="submitLoading">
        {{ $t('views.common.cancel') }}
      </a-button>
    </div>
  </div>
</template>

<style scoped>
.top-section {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 24px;
}

.tabs-section {
  flex: 1;
  min-width: 0;
}

.action-buttons {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  justify-content: flex-end;
}
</style>
