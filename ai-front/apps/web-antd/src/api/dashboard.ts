import { requestClient } from '#/api/request';

// 数据概览接口
export interface AnalyticsOverviewResponse {
  userCount: {
    totalValue: number;
    value: number;
  };
  chatCount: {
    totalValue: number;
    value: number;
  };
  reportCount: {
    totalValue: number;
    value: number;
  };
  riskCount: {
    totalValue: number;
    value: number;
  };
}

// 使用趋势接口
export interface AnalyticsTrendsResponse {
  hours: string[];
  loginData: number[];
  operationData: number[];
}

// 月使用量接口
export interface AnalyticsMonthlyResponse {
  months: number[];
}

// 国家统计接口
export interface CountryStatItem {
  name: string;
  value: number;
}

// AI统计接口
export interface AIStatItem {
  name: string;
  value: number;
}

/**
 * 获取数据概览统计信息
 */
export async function getAnalyticsOverviewApi(): Promise<AnalyticsOverviewResponse> {
  const response = await requestClient.get<AnalyticsOverviewResponse>(
    '/api/v1/dashboard/analytics/overview',
  );
  return response;
}

/**
 * 获取使用趋势数据
 */
export async function getAnalyticsTrendsApi(): Promise<AnalyticsTrendsResponse> {
  const response = await requestClient.get<AnalyticsTrendsResponse>(
    '/api/v1/dashboard/analytics/trends',
  );
  return response;
}

/**
 * 获取月使用量数据
 */
export async function getAnalyticsMonthlyApi(): Promise<AnalyticsMonthlyResponse> {
  const response = await requestClient.get<AnalyticsMonthlyResponse>(
    '/api/v1/dashboard/analytics/monthly',
  );
  return response;
}

/**
 * 获取国家统计数据
 */
export async function getAnalyticsCountriesApi(): Promise<CountryStatItem[]> {
  const response = await requestClient.get<CountryStatItem[]>(
    '/api/v1/dashboard/analytics/countries',
  );
  return response;
}

/**
 * 获取AI统计数据
 */
export async function getAnalyticsAIStatsApi(): Promise<AIStatItem[]> {
  const response = await requestClient.get<AIStatItem[]>('/api/v1/dashboard/analytics/ai-stats');
  return response;
}
