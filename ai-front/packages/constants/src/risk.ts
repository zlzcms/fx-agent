/**
 * 风险管理相关常量定义
 */

/**
 * 文件上传相关常量
 */
export const FILE_SIZE_LIMIT = 2; // MB
export const MAX_UPLOAD_COUNT = 3;

/**
 * Plus图标SVG
 */
export const PLUS_ICON = `<svg viewBox="64 64 896 896" focusable="false" data-icon="plus" width="1em" height="1em" fill="currentColor" aria-hidden="true"><defs><style></style></defs><path d="M482 152h60q8 0 8 8v704q0 8-8 8h-60q-8 0-8-8V160q0-8 8-8z"></path><path d="M176 474h672q8 0 8 8v60q0 8-8 8H176q-8 0-8-8v-60q0-8 8-8z"></path></svg>`;

/**
 * 风险等级颜色映射
 */
export const RISK_LEVEL_COLORS = {
  HIGH: '#B91C1C', 
  MEDIUM_HIGH: '#E63535',
  MEDIUM: '#FB954B',
  MEDIUM_LOW: '#347AE2',
  LOW: 'green',
  DEFAULT: 'green'
} as const;

/**
 * 处理状态颜色
 */
export const PROCESS_STATUS_COLORS = {
  PROCESSED: 'success',
  UNPROCESSED: 'warning'
} as const;
