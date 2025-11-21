<script setup lang="ts">
import { computed } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Settings } from '@vben/icons';
import { $t } from '@vben/locales';

interface Props {
  modelValue: string;
  label: string;
  description?: string;
  placeholder?: string;
  hint?: string;
  maxLength?: number;
  rows?: number;
  polishLoading?: boolean;
  required?: boolean;
  i18nPrefix?: string; // 国际化前缀，用于错误提示等
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  placeholder: '',
  hint: '',
  maxLength: 5000,
  rows: 6,
  polishLoading: false,
  required: false,
  i18nPrefix: '',
});

const emit = defineEmits<{
  polish: [];
  'update:modelValue': [value: string];
}>();

const currentValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const characterCount = computed(() => props.modelValue?.length || 0);
</script>

<template>
  <div class="task-prompt-area">
    <div class="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
      <div class="flex items-center justify-between">
        <div>
          <label class="block text-sm font-medium text-gray-900 mb-2">
            {{ label }}
            <span v-if="required" class="text-red-500">*</span>
          </label>
          <p v-if="description" class="text-sm text-gray-500">
            {{ description }}
          </p>
        </div>
        <VbenButton
          variant="outline"
          :loading="polishLoading"
          @click="$emit('polish')"
          class="ai-polish-btn flex items-center"
        >
          <Settings class="mr-1 size-4" />
          {{ $t(i18nPrefix ? `${i18nPrefix}.aiPolish` : 'views.common.aiPolish') }}
        </VbenButton>
      </div>

      <textarea
        v-model="currentValue"
        :placeholder="placeholder"
        class="task-prompt-textarea w-full p-3 border border-gray-300 rounded-md resize-vertical focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        :rows="rows"
        :maxlength="maxLength"
        :style="{ minHeight: `${rows * 25}px` }"
      ></textarea>
      <div class="mt-2 flex justify-between items-center text-sm text-gray-500">
        <span v-if="hint">{{ hint }}</span>
        <span>{{ characterCount }}/{{ maxLength }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-polish-btn {
  transition: all 0.2s;
}

.task-prompt-textarea {
  font-family: Monaco, Menlo, 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
}
</style>
