import type { Ref } from 'vue';

import type { AITrainingLog } from '#/api';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { getAssistantTrainingLogsApi } from '#/api';

export interface TrainingLogsState {
  loading: boolean;
  data: {
    items: AITrainingLog[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  };
  pagination: {
    page: number;
    size: number;
  };
}

/**
 * 训练日志管理 Composable
 * @param assistantId 助手ID
 * @param logType 日志类型
 * @param i18nPrefix 国际化前缀
 */
export function useTrainingLogs(
  assistantId: Ref<string | undefined> | string | undefined,
  logType: string,
  i18nPrefix: string,
) {
  const trainingLogs = ref<TrainingLogsState>({
    loading: false,
    data: {
      items: [],
      total: 0,
      page: 1,
      size: 20,
      total_pages: 1,
    },
    pagination: {
      page: 1,
      size: 20,
    },
  });

  const trainingDetailVisible = ref(false);
  const selectedTraining = ref<AITrainingLog | null>(null);

  const assistantIdRef = computed(() => {
    return typeof assistantId === 'object' && 'value' in assistantId
      ? assistantId.value
      : assistantId;
  });

  // 加载训练日志
  async function loadTrainingLogs() {
    const id = assistantIdRef.value;
    if (!id) {
      return;
    }

    trainingLogs.value.loading = true;
    try {
      const { page, size } = trainingLogs.value.pagination;
      const params: any = { page, size, log_type: logType };

      const response = await getAssistantTrainingLogsApi(id, params);
      trainingLogs.value.data = response;
    } catch (error) {
      console.error($t(`${i18nPrefix}.getTrainingLogsFailed`), error);
      message.error(
        $t(`${i18nPrefix}.getTrainingLogsFailedRetry`) || $t(`${i18nPrefix}.getTrainingLogsRetry`),
      );
    } finally {
      trainingLogs.value.loading = false;
    }
  }

  // 刷新训练日志
  function refreshTrainingLogs() {
    loadTrainingLogs();
  }

  // 处理训练日志分页变化
  function handleTrainingLogPageChange(page: number, pageSize: number) {
    trainingLogs.value.pagination.page = page;
    trainingLogs.value.pagination.size = pageSize;
    loadTrainingLogs();
  }

  // 查看训练详情
  function viewTrainingDetail(record: AITrainingLog) {
    selectedTraining.value = record;
    trainingDetailVisible.value = true;
  }

  return {
    trainingLogs,
    trainingDetailVisible,
    selectedTraining,
    loadTrainingLogs,
    refreshTrainingLogs,
    handleTrainingLogPageChange,
    viewTrainingDetail,
  };
}
