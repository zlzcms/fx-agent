/**
 * 风险管理相关工具函数
 */

import type { ProcessStatusColor } from '../../types/src/risk';

import { PROCESS_STATUS_COLORS, RISK_LEVEL_COLORS } from '../../constants/src/risk';

// 直接导出项目提供的日期时间格式化函数
export { formatDateTime } from '@vben-core/shared/utils';

/**
 * 解析报告标签
 * @param tags 标签字符串
 * @returns 标签数组
 */
export function parseReportTags(tags: string | undefined): string[] {
  if (!tags) return [];

  try {
    return JSON.parse(tags);
  } catch {
    return tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);
  }
}

/**
 * 获取风险等级颜色（根据R1-R5等级）
 * @param level 风险等级（如R1、R2、R3、R4、R5）
 * @returns 对应的颜色值
 */
export function getRiskLevelColor(level: string) {
  switch (level) {
    case 'R1': {
      return RISK_LEVEL_COLORS.HIGH;
    }
    case 'R2': {
      return RISK_LEVEL_COLORS.MEDIUM_HIGH;
    }
    case 'R3': {
      return RISK_LEVEL_COLORS.MEDIUM;
    }
    case 'R4': {
      return RISK_LEVEL_COLORS.MEDIUM_LOW;
    }
    case 'R5': {
      return RISK_LEVEL_COLORS.LOW;
    }
    default: {
      return RISK_LEVEL_COLORS.DEFAULT;
    }
  }
}

/**
 * 获取报告分数颜色（根据分数值）
 * @param score 风险分数
 * @returns 对应的颜色值
 */
export function getReportScoreColor(score: number) {
  if (Number.isNaN(score)) return RISK_LEVEL_COLORS.DEFAULT;

  if (score >= 80) return RISK_LEVEL_COLORS.HIGH;
  if (score >= 60) return RISK_LEVEL_COLORS.MEDIUM_HIGH;
  if (score >= 40) return RISK_LEVEL_COLORS.MEDIUM;
  if (score >= 20) return RISK_LEVEL_COLORS.MEDIUM_LOW;
  return RISK_LEVEL_COLORS.LOW;
}

/**
 * 获取处理状态颜色
 * @param isProcessed 是否已处理
 * @returns 对应的颜色值
 */
export function getProcessStatusColor(isProcessed: boolean): ProcessStatusColor {
  return isProcessed ? PROCESS_STATUS_COLORS.PROCESSED : PROCESS_STATUS_COLORS.UNPROCESSED;
}
