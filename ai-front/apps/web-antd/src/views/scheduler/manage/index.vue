<script setup lang="ts">
import type { CreateTaskSchedulerParams, TaskSchedulerResult } from '#/api';

import { computed, onMounted, onUnmounted, ref } from 'vue';

import { confirm, EllipsisText, Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';
import dayjs from 'dayjs';

import { useVbenForm } from '#/adapter/form';
import {
  createTaskSchedulerApi,
  deleteTaskSchedulerApi,
  executeTaskSchedulerApi,
  getAllTaskSchedulerApi,
  updateTaskSchedulerApi,
  updateTaskSchedulerStatusApi,
} from '#/api';
import { router } from '#/router';
import { useWebSocketStore } from '#/store';

import { schema } from './data';

const wsStore = useWebSocketStore();

const taskWorkerStatus = ref<any>(null);
const taskSchedulerList = ref<TaskSchedulerResult[]>();

const fetchTaskSchedulerList = async () => {
  try {
    taskSchedulerList.value = await getAllTaskSchedulerApi();
  } catch (error) {
    console.error(error);
  }
};

const [Form, formApi] = useVbenForm({
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  showDefaultActions: false,
  schema,
});

interface formTaskSchedulerParams extends CreateTaskSchedulerParams {
  id?: number;
}

const formData = ref<formTaskSchedulerParams>();

const modalTitle = computed(() => {
  return formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('@scheduler.task')])
    : $t('ui.actionTitle.create', [$t('@scheduler.task')]);
});

const [Modal, modalApi] = useVbenModal({
  class: 'w-5/12',
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      const data = await formApi.getValues<CreateTaskSchedulerParams>();
      const args = ref();
      if (data.args) {
        try {
          args.value = JSON.parse(data.args);
        } catch {
          const argsStr = data.args.trim().startsWith('[')
            ? data.args.trim().slice(1, -1)
            : data.args;
          args.value = argsStr.split(',').map((item) => {
            const trimmed = item.trim();
            const num = Number(trimmed);
            return Number.isNaN(num) ? trimmed : num;
          });
        }
        data.args = JSON.stringify(args.value);
      }
      try {
        await (formData.value?.id
          ? updateTaskSchedulerApi(formData.value?.id, data)
          : createTaskSchedulerApi(data));
        message.success(formData.value?.id ? $t('common.updateSuccess') : $t('common.addSuccess'));
        await modalApi.close();
        await formApi.resetForm();
        await fetchTaskSchedulerList();
      } catch (error) {
        console.error(error);
      } finally {
        modalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = modalApi.getData<formTaskSchedulerParams>();
      formApi.resetForm();
      if (data) {
        formData.value = data;
        data.crontab = data.id ? data.crontab : '* * * * *';
        if (data.start_time) {
          data.start_time = dayjs(data.start_time, 'YYYY-MM-DD HH:mm:ss');
        }
        if (data.expire_time) {
          data.expire_time = dayjs(data.start_time, 'YYYY-MM-DD HH:mm:ss');
        }
        formApi.setValues(data);
      }
    }
  },
});

function deleteConfirm(pk: number) {
  confirm({
    icon: 'warning',
    content: $t('@scheduler.confirmDeleteTask'),
  }).then(async () => {
    try {
      await deleteTaskSchedulerApi(pk);
      message.success($t('common.deleteSuccess'));
      await fetchTaskSchedulerList();
    } catch (error) {
      console.error(error);
    }
  });
}

const executeTask = async (pk: number) => {
  try {
    await executeTaskSchedulerApi(pk);
    message.success($t('@scheduler.executeSuccess'));
  } catch (error) {
    console.error(error);
  }
};

const searchLog = (task: string) => {
  router.push({ path: `/ai-service/scheduler-record`, query: { name: task } });
};

const handleStatusChange = async (id: number) => {
  try {
    await updateTaskSchedulerStatusApi(id);
    message.success($t('common.toggleStatusSuccess'));
    await fetchTaskSchedulerList();
  } catch (error) {
    console.error(error);
    // 恢复开关状态
    const task = taskSchedulerList.value?.find((t) => t.id === id);
    if (task) {
      task.enabled = !task.enabled;
    }
  }
};

const intervalId = ref<any>(null);
const consecutiveFailures = ref(0);
const maxFailures = 3; // 连续失败3次后暂停轮询

/**
 * Celery Worker 状态回调处理函数
 *
 * @param data - 后端返回的 worker 状态数据对象
 *
 * 当 worker 正常运行时 (通过 Celery inspect 获取)，data 包含以下字段：
 * - status: 'running' - worker 状态
 * - worker_name: string - worker 名称 (如: 'celery@1cb3fc7a77c9')
 * - active_tasks: number - 当前正在执行的任务数量
 * - registered_tasks: number - 已注册的任务类型数量
 * - total_processed: object - 总处理任务统计，按任务类型分组 (如: {"scheduled_risk_analysis": 1, "process_single_user_risk_analysis": 2})
 * - pool_info: object - 进程池信息
 *   - pool: string - 池实现类型 (如: 'celery.concurrency.gevent:TaskPool')
 *   - max_concurrency: number - 最大并发数
 *   - processes: array - 进程ID列表 (gevent模式下为空数组)
 * - broker_info: object - 消息代理信息
 *   - transport: string - 传输协议 (如: 'redis')
 *   - hostname: string - 代理主机名 (如: 'fba_redis')
 * - rusage: object - 资源使用统计 (Resource Usage)
 *   - utime: number - 用户态CPU时间 (秒)
 *   - stime: number - 内核态CPU时间 (秒)
 *   - maxrss: number - 最大常驻内存大小 (KB)
 *   - ixrss: number - 共享内存大小 (通常为0)
 *   - idrss: number - 非共享数据大小 (通常为0)
 *   - isrss: number - 非共享栈大小 (通常为0)
 *   - minflt: number - 次要页面错误数 (不需要I/O的页面错误)
 *   - majflt: number - 主要页面错误数 (需要I/O的页面错误)
 *   - nswap: number - 交换次数 (通常为0)
 *   - inblock: number - 输入块操作数
 *   - oublock: number - 输出块操作数
 *   - msgsnd: number - 发送消息数 (通常为0)
 *   - msgrcv: number - 接收消息数 (通常为0)
 *   - nsignals: number - 接收到的信号数
 *   - nvcsw: number - 主动上下文切换数
 *   - nivcsw: number - 被动上下文切换数
 * - clock: string - worker 时钟 (用于同步，字符串格式)
 * - timestamp: string - 状态获取时间戳 (ISO格式)
 *
 * 当 worker 停止或出错时，data 包含：
 * - status: 'stopped' | 'error' - worker 状态
 * - message: string - 错误信息或状态描述 (仅在 error 状态时)
 * - timestamp: string - 状态获取时间戳
 */
const taskWorkerStatusCallback = (data: any) => {
  taskWorkerStatus.value = data;

  // 检查是否为正常的 worker 状态
  const hasNormalWorker = data && data.status === 'running';

  // 智能轮询：如果连续失败，暂停轮询
  if (hasNormalWorker) {
    consecutiveFailures.value = 0; // 重置失败计数
  } else {
    consecutiveFailures.value++;
    if (consecutiveFailures.value >= maxFailures) {
      console.warn('Worker 连续不可用，暂停轮询');
      if (intervalId.value) {
        clearInterval(intervalId.value);
        intervalId.value = null;
      }
    }
  }
};

const emitTWS = () => {
  wsStore.emit('task_worker_status', {});
};

const startPolling = () => {
  if (!intervalId.value) {
    consecutiveFailures.value = 0;
    intervalId.value = setInterval(emitTWS, 10_000);
  }
};

// 计算属性：检查是否有正常的 worker
const hasNormalWorker = computed(() => {
  return taskWorkerStatus.value && taskWorkerStatus.value.status === 'running';
});

// 获取 worker 状态消息
const getWorkerStatusMessage = () => {
  if (consecutiveFailures.value >= maxFailures) {
    return $t('@scheduler.workerUnavailable');
  }

  if (
    taskWorkerStatus.value &&
    taskWorkerStatus.value.status === 'error' &&
    taskWorkerStatus.value.message
  ) {
    return `${$t('@scheduler.workerError')}${taskWorkerStatus.value.message}`;
  }

  return $t('@scheduler.workerUnavailableContact');
};

onMounted(async () => {
  await fetchTaskSchedulerList();
  // 使用具名函数，确保能正确清理
  wsStore.on('task_worker_status', taskWorkerStatusCallback);
  emitTWS();
  // 使用智能轮询
  startPolling();
});

onUnmounted(() => {
  // 正确清理事件监听器
  wsStore.off('task_worker_status', taskWorkerStatusCallback);
  if (intervalId.value) {
    clearInterval(intervalId.value);
  }
});
</script>

<template>
  <Page>
    <VbenButton @click="() => modalApi.setData(null).open()">
      {{ $t('@scheduler.createTask') }}
    </VbenButton>
    <Modal :title="modalTitle">
      <Form />
    </Modal>
    <a-alert
      v-if="!hasNormalWorker"
      class="mt-4"
      :message="getWorkerStatusMessage()"
      :type="consecutiveFailures >= maxFailures ? 'error' : 'warning'"
      show-icon
    >
      <template #action v-if="consecutiveFailures >= maxFailures">
        <a-button size="small" @click="startPolling">{{ $t('@scheduler.recheck') }}</a-button>
      </template>
    </a-alert>
    <div class="mt-4">
      <!-- 网格容器 -->
      <div class="grid gap-6 lg:grid-cols-4">
        <a-card v-for="ts in taskSchedulerList" :key="ts.name">
          <template #title>
            {{ ts.name }}
          </template>
          <template #extra>
            <a-switch
              v-model:checked="ts.enabled"
              :checked-value="true"
              :checked-children="$t('@scheduler.taskStarted')"
              :un-checked-children="$t('@scheduler.taskStopped')"
              @change="handleStatusChange(ts.id)"
            />
          </template>
          <template #actions>
            <a-button :disabled="!hasNormalWorker" @click="executeTask(ts.id)" size="small">
              {{ $t('@scheduler.manualExecute') }}
            </a-button>
            <a-button size="small" @click="searchLog(ts.task)">
              {{ $t('@scheduler.log') }}
            </a-button>
            <a-button size="small" @click="modalApi.setData(ts).open()">
              {{ $t('@scheduler.edit') }}
            </a-button>
            <a-button size="small" danger @click="deleteConfirm(ts.id)">
              {{ $t('@scheduler.delete') }}
            </a-button>
          </template>
          <EllipsisText tooltip-when-ellipsis :tooltip-overlay-style="{ wordBreak: 'break-all' }">
            <span class="text-gray-500">{{ $t('@scheduler.taskInvocation') }}：</span>
            {{ ts.task }}
            <template #tooltip>
              {{ ts.task }}
            </template>
          </EllipsisText>
          <EllipsisText tooltip-when-ellipsis :tooltip-overlay-style="{ wordBreak: 'break-all' }">
            <span class="text-gray-500">{{ $t('@scheduler.positionalArgs') }}：</span>
            {{ ts.args || 'N/A' }}
            <template #tooltip>
              {{ ts.args }}
            </template>
          </EllipsisText>
          <EllipsisText tooltip-when-ellipsis :tooltip-overlay-style="{ wordBreak: 'break-all' }">
            <span class="text-gray-500">{{ $t('@scheduler.keywordArgs') }}：</span>
            {{ ts.kwargs || 'N/A' }}
            <template #tooltip>
              {{ ts.kwargs || 'N/A' }}
            </template>
          </EllipsisText>
          <p>
            <span class="text-gray-500">{{ $t('@scheduler.totalExecutions') }}：</span>
            {{ ts.total_run_count }} {{ $t('common.times') }}
          </p>
          <p>
            <span class="text-gray-500">{{ $t('@scheduler.lastExecution') }}：</span>
            {{ ts.last_run_time || 'N/A' }}
          </p>
          <p>
            <span class="text-gray-500">{{ $t('@scheduler.triggerPolicy') }}：</span>
            <span v-if="ts.type === 0">
              {{ $t('@scheduler.interval') }}
              <a-tag>{{ ts.interval_every }} {{ ts.interval_period }}</a-tag>
            </span>
            <span v-else>
              {{ $t('@scheduler.crontab') }}
              <a-tag>
                {{ ts.crontab }}
              </a-tag>
            </span>
          </p>
          <EllipsisText tooltip-when-ellipsis :tooltip-overlay-style="{ wordBreak: 'break-all' }">
            <span class="text-gray-500">{{ $t('@scheduler.taskDescription') }}：</span>
            {{ ts.remark || 'N/A' }}
            <template #tooltip>
              {{ ts.remark }}
            </template>
          </EllipsisText>
        </a-card>
      </div>
    </div>
  </Page>
</template>
