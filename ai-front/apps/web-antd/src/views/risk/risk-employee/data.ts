import type { RiskConfig } from '../shared/risk-data';

import { RiskType } from '#/api/risk';

// 导入共享函数
import {
  beforeUpload,
  createColumns,
  createProcessFormSchema,
  createQuerySchema,
} from '../shared/risk-data';

// 员工风险配置
export const employeeRiskConfig: RiskConfig = {
  riskType: RiskType.CRM_USER,
  i18nPrefix: '@risk.risk-employee',
};

// 为了向后兼容，重新导出共享函数
export { beforeUpload };

// 创建具体的配置实例
export const querySchema = createQuerySchema(
  employeeRiskConfig.i18nPrefix,
  employeeRiskConfig.riskType,
);
export const useColumns = (onActionClick?: any) =>
  createColumns(employeeRiskConfig.i18nPrefix, onActionClick);
export const processFormSchema = createProcessFormSchema(employeeRiskConfig.i18nPrefix);
