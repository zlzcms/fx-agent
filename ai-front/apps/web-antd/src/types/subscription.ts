/**
 * 订阅类型枚举定义
 * 与后端枚举保持一致
 */

// 订阅类型枚举
export enum SubscriptionType {
  CLIENT = 'client',
  SERVER = 'server',
}

// 订阅类型显示名称映射
export const SubscriptionTypeLabels: Record<SubscriptionType, string> = {
  [SubscriptionType.CLIENT]: '客户端',
  [SubscriptionType.SERVER]: '服务端',
};

// 订阅类型选项（用于下拉选择）
export const subscriptionTypeOptions = [
  { label: SubscriptionTypeLabels[SubscriptionType.CLIENT], value: SubscriptionType.CLIENT },
  { label: SubscriptionTypeLabels[SubscriptionType.SERVER], value: SubscriptionType.SERVER },
];

// 获取订阅类型显示名称
export function getSubscriptionTypeLabel(type: SubscriptionType): string {
  return SubscriptionTypeLabels[type] || type;
}

// 获取所有订阅类型值
export function getSubscriptionTypeValues(): SubscriptionType[] {
  return Object.values(SubscriptionType);
}
