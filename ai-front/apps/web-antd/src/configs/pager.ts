/**
 * 统一的表格分页器配置
 * 用于保持整个系统中分页器样式的一致性
 */

export interface PagerConfigOptions {
  /** 默认页大小 */
  pageSize?: number;
  /** 可选的页大小列表 */
  pageSizes?: number[];
  /** 是否启用完美模式（带圆角边框） */
  perfect?: boolean;
}

/**
 * 获取默认的分页器配置
 * @param options 分页器选项
 * @returns 分页器配置对象
 */
export function getDefaultPagerConfig(options: PagerConfigOptions = {}): any {
  const { pageSize = 20, pageSizes = [10, 20, 50, 100], perfect = false } = options;

  return {
    enabled: true,
    pageSize,
    pageSizes,
    perfect,
  };
}

/**
 * 常用的分页器配置预设
 */
export const pagerPresets = {
  /** 标准列表页分页器 */
  standard: getDefaultPagerConfig(),

  /** 大数据量列表页分页器 */
  largeData: getDefaultPagerConfig({
    pageSize: 50,
    pageSizes: [20, 50, 100, 200],
  }),

  /** 小数据量列表页分页器 */
  smallData: getDefaultPagerConfig({
    pageSize: 10,
    pageSizes: [10, 20, 50],
  }),

  /** 不分页 */
  disabled: {
    enabled: false,
  },
};
