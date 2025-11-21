<script setup lang="ts">
import type { AITrainingLog } from '#/api';

import { computed } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Settings } from '@vben/icons';
import { $t } from '@vben/locales';

interface Props {
  loading: boolean;
  records: AITrainingLog[];
  pagination: {
    page: number;
    size: number;
  };
  total: number;
  showMockButton?: boolean;
  i18nPrefix: string; // 国际化前缀，如 '@ai-assistants' 或 '@risk.risk-assistants'
}

const props = defineProps<Props>();

const emit = defineEmits<{
  mockTraining: [];
  pageChange: [page: number, pageSize: number];
  refresh: [];
  viewDetail: [record: AITrainingLog];
}>();

const currentPage = computed({
  get: () => props.pagination.page,
  set: (value: number) => emit('pageChange', value, props.pagination.size),
});

const currentPageSize = computed({
  get: () => props.pagination.size,
  set: (value: number) => emit('pageChange', props.pagination.page, value),
});

const formatScore = (score: number | undefined): string => {
  return `${((score || 0) * 100).toFixed(2)}%`;
};

const formatDate = (date: Date | string): string => {
  return new Date(date).toLocaleString();
};
</script>

<template>
  <div class="mock-training-records">
    <div class="flex justify-between mb-4">
      <h3 class="text-lg font-medium">
        {{
          $t(`${props.i18nPrefix}.trainingRecordsList`) ||
          $t(`${props.i18nPrefix}.trainingRecordList`)
        }}
      </h3>

      <div class="flex items-center gap-2">
        <VbenButton v-if="props.showMockButton" variant="outline" @click="emit('mockTraining')">
          <Settings class="mr-1 size-4" />
          {{ $t(`${props.i18nPrefix}.mockTraining`) }}
        </VbenButton>
        <VbenButton variant="outline" @click="emit('refresh')" :loading="props.loading">
          {{ $t('views.common.refresh') }}
        </VbenButton>
      </div>
    </div>

    <div class="overflow-hidden rounded-lg border border-gray-200">
      <table class="w-full text-left text-sm">
        <thead class="bg-gray-50 text-xs uppercase text-gray-700">
          <tr>
            <th scope="col" class="px-6 py-3">{{ $t(`${props.i18nPrefix}.id`) || 'ID' }}</th>
            <th scope="col" class="px-6 py-3">{{ $t(`${props.i18nPrefix}.modelName`) }}</th>
            <th scope="col" class="px-6 py-3">{{ $t(`${props.i18nPrefix}.type`) }}</th>
            <th scope="col" class="px-6 py-3">{{ $t(`${props.i18nPrefix}.score`) }}</th>
            <th scope="col" class="px-6 py-3">{{ $t(`${props.i18nPrefix}.status`) }}</th>
            <th scope="col" class="px-6 py-3">
              {{ $t(`${props.i18nPrefix}.createdTime`) || $t(`${props.i18nPrefix}.createTime`) }}
            </th>
            <th scope="col" class="px-6 py-3">
              {{ $t(`${props.i18nPrefix}.operation`) || $t(`${props.i18nPrefix}.actions`) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading" class="border-b bg-white">
            <td colspan="7" class="px-6 py-8 text-center text-gray-500">
              {{ $t(`${props.i18nPrefix}.loadingData`) }}
            </td>
          </tr>
          <tr v-else-if="props.records.length === 0" class="border-b bg-white">
            <td colspan="7" class="px-6 py-8 text-center text-gray-500">
              {{ $t(`${props.i18nPrefix}.noTrainingRecords`) }}
            </td>
          </tr>
          <template v-else>
            <tr
              v-for="record in props.records"
              :key="record.id"
              class="border-b bg-white hover:bg-gray-50"
            >
              <td class="px-6 py-4">{{ record.id }}</td>
              <td class="px-6 py-4">{{ record.model_name }}</td>
              <td class="px-6 py-4">{{ record.log_type }}</td>
              <td class="px-6 py-4">{{ formatScore(record.score) }}</td>
              <td class="px-6 py-4">
                <span
                  :class="
                    record.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  "
                  class="rounded px-2.5 py-0.5 text-xs font-medium"
                >
                  {{
                    record.success
                      ? $t(`${props.i18nPrefix}.success`)
                      : $t(`${props.i18nPrefix}.failed`)
                  }}
                </span>
              </td>
              <td class="px-6 py-4">{{ formatDate(record.created_time) }}</td>
              <td class="px-6 py-4">
                <button
                  @click="emit('viewDetail', record)"
                  class="font-medium text-blue-600 hover:underline"
                >
                  {{ $t(`${props.i18nPrefix}.viewDetails`) }}
                </button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div class="mt-4 flex justify-end">
      <a-pagination
        v-model:current="currentPage"
        v-model:page-size="currentPageSize"
        :total="props.total"
        :show-size-changer="true"
        :page-size-options="['10', '20', '50', '100']"
        @change="(page: number, size: number) => emit('pageChange', page, size)"
        :show-total="
          (total: number) =>
            `${$t(`${props.i18nPrefix}.total`)} ${total} ${$t(`${props.i18nPrefix}.items`) || $t(`${props.i18nPrefix}.records`)}`
        "
      />
    </div>
  </div>
</template>
