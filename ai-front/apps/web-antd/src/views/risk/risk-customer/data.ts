import type { RiskConfig } from '../shared/risk-data';

import { RiskType } from '#/api/risk';

// 导入共享函数
import {
  beforeUpload,
  createColumns,
  createProcessFormSchema,
  createQuerySchema,
} from '../shared/risk-data';

// 客户风险配置
export const customerRiskConfig: RiskConfig = {
  riskType: RiskType.ALL_EMPLOYEE,
  i18nPrefix: '@risk-customer',
};

// 为了向后兼容，重新导出共享函数
export { beforeUpload };

// 创建具体的配置实例
export const querySchema = createQuerySchema(
  customerRiskConfig.i18nPrefix,
  customerRiskConfig.riskType,
);
export const useColumns = (onActionClick?: any) =>
  createColumns(customerRiskConfig.i18nPrefix, onActionClick);
export const processFormSchema = createProcessFormSchema(customerRiskConfig.i18nPrefix);
