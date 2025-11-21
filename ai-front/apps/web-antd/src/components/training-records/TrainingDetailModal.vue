<script setup lang="ts">
import type { AITrainingLog } from '#/api';

import { computed } from 'vue';

import { $t } from '@vben/locales';

import { Modal } from 'ant-design-vue';

import { renderMarkdown } from '#/utils/markdown';

interface Props {
  visible: boolean;
  training: AITrainingLog | null;
  i18nPrefix: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
}>();

const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
});

const formatScore = (score: number | undefined): string => {
  return `${((score || 0) * 100).toFixed(2)}%`;
};

const formatDate = (date: Date | string): string => {
  return new Date(date).toLocaleString();
};
</script>

<template>
  <Modal
    v-model:open="visible"
    :title="`${$t(`${i18nPrefix}.trainingRecordDetails`)} #${training?.id || ''}`"
    width="900px"
    :footer="null"
  >
    <div v-if="training" class="training-detail">
      <!-- 基本信息 -->
      <div class="mb-4 rounded-lg bg-gray-50 p-4">
        <div class="mb-2 text-lg font-medium">
          {{ $t(`${i18nPrefix}.basicInfo`) }}
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="text-sm">
            <div class="mb-1 font-semibold">{{ $t(`${i18nPrefix}.modelName`) }}</div>
            <div>{{ training.model_name }}</div>
          </div>
          <div class="text-sm">
            <div class="mb-1 font-semibold">{{ $t(`${i18nPrefix}.type`) }}</div>
            <div>{{ training.log_type }}</div>
          </div>
          <div class="text-sm">
            <div class="mb-1 font-semibold">{{ $t(`${i18nPrefix}.score`) }}</div>
            <div>{{ formatScore(training.score) }}</div>
          </div>
          <div class="text-sm">
            <div class="mb-1 font-semibold">{{ $t(`${i18nPrefix}.status`) }}</div>
            <div>
              <span
                :class="
                  training.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                "
                class="rounded px-2.5 py-0.5 text-xs font-medium"
              >
                {{ training.success ? $t(`${i18nPrefix}.success`) : $t(`${i18nPrefix}.failed`) }}
              </span>
            </div>
          </div>
          <div class="text-sm">
            <div class="mb-1 font-semibold">
              {{ $t(`${i18nPrefix}.createdTime`) || $t(`${i18nPrefix}.createTime`) }}
            </div>
            <div>{{ formatDate(training.created_time) }}</div>
          </div>
          <div class="text-sm">
            <div class="mb-1 font-semibold">{{ $t('views.common.updatedAt') }}</div>
            <div>{{ formatDate(training.updated_time) }}</div>
          </div>
        </div>
      </div>

      <!-- 训练数据 -->
      <div
        v-if="training.data?.columns && training.data?.rows"
        class="mb-4 rounded-lg bg-gray-50 p-4"
      >
        <div class="mb-2 text-lg font-medium">
          {{ $t(`${i18nPrefix}.trainingData`) }}
        </div>
        <div class="overflow-auto max-h-60">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-200 text-xs uppercase text-gray-700">
              <tr>
                <th v-for="(column, index) in training.data.columns" :key="index" class="px-3 py-2">
                  {{ column }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, rowIndex) in training.data.rows"
                :key="rowIndex"
                class="border-b bg-white"
              >
                <td
                  v-for="(cell, cellIndex) in row"
                  :key="cellIndex"
                  class="px-3 py-2 whitespace-nowrap"
                >
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 提示模板 -->
      <div v-if="training.prompt_template" class="mb-4 rounded-lg bg-gray-50 p-4">
        <div class="mb-2 text-lg font-medium">
          {{ $t(`${i18nPrefix}.promptTemplate`) }}
        </div>
        <pre class="bg-gray-100 p-3 rounded-md overflow-auto max-h-40 text-sm">{{
          training.prompt_template
        }}</pre>
      </div>

      <!-- AI 响应结果 -->
      <div class="mb-4 rounded-lg bg-gray-50 p-4">
        <div class="mb-2 text-lg font-medium">
          {{ $t(`${i18nPrefix}.aiResponseResult`) }}
        </div>
        <div class="bg-white border rounded-md p-4 prose max-w-none overflow-auto max-h-80">
          <VueMarkdownIt
            v-if="training.content"
            class="markdown-body"
            :source="renderMarkdown(training.content)"
          />
          <div v-else class="text-gray-500">
            {{ $t(`${i18nPrefix}.noResponseContent`) }}
          </div>
        </div>
      </div>
    </div>
    <div v-else class="py-10 text-center text-gray-500">
      {{ $t(`${i18nPrefix}.loadingTrainingDetails`) }}
    </div>
  </Modal>
</template>
