/**
 * Celery任务状态枚举定义
 * 与后端Celery状态保持一致
 */

// Celery标准任务状态枚举
export enum CeleryTaskStatus {
  /** 任务执行失败 */
  FAILURE = 'FAILURE',
  /** 任务等待执行或未知任务ID */
  PENDING = 'PENDING',
  /** 任务执行进度更新 */
  PROGRESS = 'PROGRESS',
  /** 任务已被worker接收（仅在事件中使用） */
  RECEIVED = 'RECEIVED',
  /** 任务正在重试 */
  RETRY = 'RETRY',
  /** 任务已被撤销 */
  REVOKED = 'REVOKED',
  /** 任务已被worker启动（需要启用task_track_started） */
  STARTED = 'STARTED',
  /** 任务执行成功 */
  SUCCESS = 'SUCCESS',
}

// 任务状态显示配置
export interface TaskStatusConfig {
  label: string;
  color: string;
  bgColor?: string;
  icon?: string;
}

// 任务状态配置映射
export const TASK_STATUS_CONFIG: Record<CeleryTaskStatus, TaskStatusConfig> = {
  [CeleryTaskStatus.PENDING]: {
    label: '等待中',
    color: 'text-amber-700',
    bgColor: 'bg-amber-100',
    icon: 'clock',
  },
  [CeleryTaskStatus.RECEIVED]: {
    label: '已接收',
    color: 'text-sky-700',
    bgColor: 'bg-sky-100',
    icon: 'inbox',
  },
  [CeleryTaskStatus.STARTED]: {
    label: '执行中',
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-100',
    icon: 'play',
  },
  [CeleryTaskStatus.PROGRESS]: {
    label: '进行中',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: 'loading',
  },
  [CeleryTaskStatus.SUCCESS]: {
    label: '成功',
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-100',
    icon: 'check-circle',
  },
  [CeleryTaskStatus.FAILURE]: {
    label: '失败',
    color: 'text-rose-700',
    bgColor: 'bg-rose-100',
    icon: 'x-circle',
  },
  [CeleryTaskStatus.RETRY]: {
    label: '重试中',
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    icon: 'refresh',
  },
  [CeleryTaskStatus.REVOKED]: {
    label: '已撤销',
    color: 'text-slate-700',
    bgColor: 'bg-slate-100',
    icon: 'ban',
  },
};

// 任务状态分组
export const TASK_STATUS_GROUPS = {
  /** 准备状态（已完成执行） */
  READY_STATES: [CeleryTaskStatus.SUCCESS, CeleryTaskStatus.FAILURE, CeleryTaskStatus.REVOKED],
  /** 未准备状态（未完成执行） */
  UNREADY_STATES: [
    CeleryTaskStatus.PENDING,
    CeleryTaskStatus.RECEIVED,
    CeleryTaskStatus.STARTED,
    CeleryTaskStatus.PROGRESS,
    CeleryTaskStatus.RETRY,
  ],
  /** 异常状态 */
  EXCEPTION_STATES: [CeleryTaskStatus.FAILURE, CeleryTaskStatus.RETRY, CeleryTaskStatus.REVOKED],
  /** 需要传播异常的状态 */
  PROPAGATE_STATES: [CeleryTaskStatus.FAILURE, CeleryTaskStatus.REVOKED],
};

/**
 * 获取任务状态配置
 * @param status 任务状态
 * @returns 状态配置
 */
export function getTaskStatusConfig(status: string): TaskStatusConfig {
  const taskStatus = status as CeleryTaskStatus;
  return (
    TASK_STATUS_CONFIG[taskStatus] || {
      label: status,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      icon: 'question-mark-circle',
    }
  );
}

/**
 * 检查任务是否已完成
 * @param status 任务状态
 * @returns 是否已完成
 */
export function isTaskReady(status: string): boolean {
  return TASK_STATUS_GROUPS.READY_STATES.includes(status as CeleryTaskStatus);
}

/**
 * 检查任务是否成功
 * @param status 任务状态
 * @returns 是否成功
 */
export function isTaskSuccess(status: string): boolean {
  return status === CeleryTaskStatus.SUCCESS;
}

/**
 * 检查任务是否失败
 * @param status 任务状态
 * @returns 是否失败
 */
export function isTaskFailed(status: string): boolean {
  return status === CeleryTaskStatus.FAILURE;
}
