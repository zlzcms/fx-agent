/**
 * 风控相关枚举和工具函数
 */

/**
 * 风控分析类型枚举
 */
export enum RiskAnalysisType {
  INCREMENTAL = 'INCREMENTAL', // 增量分析
  STOCK = 'STOCK', // 存量分析
  TRIGGERED = 'TRIGGERED', // 触发式分析
}

/**
 * 触发源枚举
 */
export enum TriggerSource {
  NEW_LOGIN = 'new_login', // 新登录
  NEW_MT4_TRADE = 'new_mt4_trade', // MT4新交易
  NEW_MT5_TRADE = 'new_mt5_trade', // MT5新交易
  NEW_OPERATION = 'new_operation', // 新操作
  NEW_REGISTER = 'new_register', // 新注册
  NEW_TRANSFER = 'new_transfer', // 新转账
}

/**
 * 检测窗口信息接口
 */
export interface DetectionWindowInfo {
  time_window_hours?: number; // 时间窗口大小（小时）
  analysis_time?: string; // 分析时间
  trigger_source?: string; // 触发源
  risk_type?: string; // 风险类型
}

/**
 * 获取分析类型的显示名称
 */
export function getAnalysisTypeLabel(analysisType?: string): string {
  if (!analysisType) return '-';
  switch (analysisType) {
    case RiskAnalysisType.INCREMENTAL: {
      return '增量分析';
    }
    case RiskAnalysisType.STOCK: {
      return '存量分析';
    }
    case RiskAnalysisType.TRIGGERED: {
      return '触发式分析';
    }
    default: {
      return analysisType;
    }
  }
}

/**
 * 获取触发源的显示名称
 */
export function getTriggerSourceLabel(triggerSource: string): string {
  const sourceMap: Record<string, string> = {
    [TriggerSource.NEW_REGISTER]: '新注册',
    [TriggerSource.NEW_LOGIN]: '新登录',
    [TriggerSource.NEW_TRANSFER]: '新转账',
    [TriggerSource.NEW_OPERATION]: '新操作',
    [TriggerSource.NEW_MT4_TRADE]: 'MT4新交易',
    [TriggerSource.NEW_MT5_TRADE]: 'MT5新交易',
  };
  return sourceMap[triggerSource] || triggerSource;
}

/**
 * 获取多个触发源的显示名称（逗号分隔）
 */
export function getTriggerSourcesLabel(triggerSources?: string): string {
  if (!triggerSources) return '-';
  return triggerSources
    .split(',')
    .map((source) => getTriggerSourceLabel(source.trim()))
    .join(', ');
}

/**
 * 格式化检测窗口信息
 */
export function formatDetectionWindowInfo(
  detectionWindowInfo?: DetectionWindowInfo | string,
): string {
  if (!detectionWindowInfo || detectionWindowInfo === 'null' || detectionWindowInfo === '{}') {
    return '-';
  }

  try {
    const info =
      typeof detectionWindowInfo === 'string'
        ? JSON.parse(detectionWindowInfo)
        : detectionWindowInfo;

    const parts = [];

    if (info.time_window_hours) {
      parts.push(`时间窗口: ${info.time_window_hours}小时`);
    }
    if (info.analysis_time) {
      parts.push(`分析时间: ${new Date(info.analysis_time).toLocaleString()}`);
    }
    if (info.trigger_source) {
      parts.push(`触发源: ${getTriggerSourceLabel(info.trigger_source)}`);
    }
    if (info.risk_type) {
      parts.push(`风控类型: ${info.risk_type}`);
    }

    return parts.length > 0 ? parts.join(' | ') : '-';
  } catch {
    return '-';
  }
}
