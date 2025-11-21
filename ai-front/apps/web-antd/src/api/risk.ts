/**
 * @Author: zhujinlong
 * @Date:   2025-06-23 10:15:15
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-23 18:18:24
 */

import { requestClient } from '#/api/request';

// ================== 风控类型枚举 ==================
export enum RiskType {
  AGENT_USER = 'agent_user', // 代理商风控
  ALL_EMPLOYEE = 'all_employee', // 客户风控，包含全部用户
  CRM_USER = 'crm_user', // 员工风控，特定用户
  PAYMENT = 'payment', // 财务风控
}

// ================== 风控等级相关接口 ==================

// 风控等级接口类型
export interface RiskLevel {
  id: string;
  name: string;
  start_score: number;
  end_score: number;
  created_time: string;
  updated_time: string;
}

export interface RiskLevelParams {
  name?: string;
  min_score?: number;
  max_score?: number;
  page?: number;
  size?: number;
}

export interface CreateRiskLevelParams {
  name: string;
  start_score: number;
  end_score: number;
}

export interface UpdateRiskLevelParams {
  name?: string;
  start_score?: number;
  end_score?: number;
}

// ================== 风控等级 API ==================

/**
 * 获取风控等级列表
 */
export async function getRiskLevelListApi(params: RiskLevelParams) {
  return requestClient.get<{
    items: RiskLevel[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/risk/risk-levels', { params });
}

/**
 * 获取所有风控等级（不分页）
 */
export async function getAllRiskLevelsApi() {
  return requestClient.get<RiskLevel[]>('/api/v1/risk/risk-levels/all');
}

/**
 * 获取风控等级详情
 */
export async function getRiskLevelApi(id: string) {
  return requestClient.get<RiskLevel>(`/api/v1/risk/risk-levels/${id}`);
}

/**
 * 创建风控等级
 */
export async function createRiskLevelApi(data: CreateRiskLevelParams) {
  return requestClient.post<RiskLevel>('/api/v1/risk/risk-levels', data);
}

/**
 * 更新风控等级
 */
export async function updateRiskLevelApi(id: string, data: UpdateRiskLevelParams) {
  return requestClient.put<RiskLevel>(`/api/v1/risk/risk-levels/${id}`, data);
}

/**
 * 删除风控等级
 */
export async function deleteRiskLevelApi(ids: string[]) {
  return requestClient.delete<{
    deleted_count: number;
  }>('/api/v1/risk/risk-levels', {
    data: { ids },
  });
}

// ================== 风控类型相关接口 ==================

/**
 * 获取所有风控类型（不分页）
 */
export async function getAllRiskTypesApi() {
  return requestClient.get<Array<{ label: string; value: string }>>(
    '/api/v1/risk/risk-tags/risk-types/all',
  );
}

// ================== 风控标签相关接口 ==================

// 风控标签接口类型
export interface RiskTag {
  id: number;
  risk_type: string;
  risk_type_name?: string;
  name: string;
  description?: string;
  created_time: string;
  updated_time: string;
}

export interface RiskTagParams {
  name?: string;
  risk_type?: string;
  page?: number;
  size?: number;
}

export interface CreateRiskTagParams {
  risk_type: string;
  name: string;
  description?: string;
}

export interface UpdateRiskTagParams {
  risk_type?: string;
  name?: string;
  description?: string;
}

// ================== 风控标签 API ==================

/**
 * 获取风控标签列表
 */
export async function getRiskTagListApi(params: RiskTagParams) {
  return requestClient.get<{
    items: RiskTag[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/risk/risk-tags', { params });
}

// ================== 风控报告相关接口 ==================

// 风控报告接口类型

export interface RiskReport {
  id: number;
  assistant_id: string;
  model_id: string;
  risk_type: RiskType;
  member_id: string; // 客户信息id
  report_score: number; // 风险评分,根据分数区分等级, R1: 100分。R2: 80+. R3: 60+. R4: 60-
  score: number;
  sql_data?: string;
  prompt_data?: string;
  input_prompt?: string;
  report_tags?: string; // 风险检查标签
  report_result?: string;
  report_table?: string;
  report_document?: string;
  report_status: boolean;
  is_processed: boolean; // 处理状态
  ai_response?: any;
  created_time: string; // 风险时间
  updated_time: string;
  handle_result?: string; // 处理结果
  handle_suggestion?: string; // 处理建议
  handle_time?: string; // 处理时间
  handle_user?: string; // 处理人（ID）
  handle_user_name?: string; // 处理人名称（后端补充）
  risk_level?: {
    description: string;
    name: string;
  };
  // 新增字段
  analysis_type?: string; // 分析类型
  trigger_sources?: string; // 触发来源
  detection_window_info?: string; // 检测窗口信息
  description?: string; // 风险描述，支持外部系统展示
}

export interface RiskReportParams {
  assistant_id?: string;
  model_id?: string;
  risk_type?: RiskType;
  member_id?: string;
  member_name?: string;
  is_processed?: boolean;
  risk_level_id?: string | string[]; // 风控等级筛选，表单数组转换为逗号分隔字符串
  risk_tags?: string | string[]; // 风险标签筛选，表单数组转换为逗号分隔字符串
  start_time?: string;
  end_time?: string;
  page?: number;
  size?: number;
}

// ================== 风控报告 API ==================

/**
 * 获取风控报告列表
 * @param params 查询参数
 */
export async function getRiskReportListApi(params: RiskReportParams = {}) {
  return requestClient.get<{
    items: RiskReport[];
    links: {
      first: string;
      last: string;
      next?: string;
      prev?: string;
      self: string;
    };
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/ai/reports/risk', { params });
}

/**
 * 获取风控报告详情
 * @param reportId 报告ID
 */
export async function getRiskReportDetailApi(reportId: number) {
  return requestClient.get<RiskReport>(`/api/v1/ai/reports/risk/${reportId}`);
}

/**
 * 处理风控报告
 * @param reportId 报告ID
 * @param data 处理数据
 */
export async function processRiskReportApi(reportId: number, data?: any) {
  return requestClient.put<{
    processed: boolean;
    report: RiskReport;
  }>(`/api/v1/ai/reports/risk/${reportId}/process`, data);
}

/**
 * 获取所有风控标签（不分页）
 */
export async function getAllRiskTagsApi(riskType?: string) {
  const params = riskType ? { risk_type: riskType } : {};
  return requestClient.get<RiskTag[]>('/api/v1/risk/risk-tags/all', { params });
}

/**
 * 根据风控类型获取风控标签
 */
export async function getRiskTagsByRiskTypeApi(riskType: string) {
  return requestClient.get<RiskTag[]>(`/api/v1/risk/risk-tags/risk-type/${riskType}`);
}

/**
 * 获取风控标签详情
 */
export async function getRiskTagApi(id: string) {
  return requestClient.get<RiskTag>(`/api/v1/risk/risk-tags/${id}`);
}

/**
 * 创建风控标签
 */
export async function createRiskTagApi(data: CreateRiskTagParams) {
  return requestClient.post<RiskTag>('/api/v1/risk/risk-tags', data);
}

/**
 * 更新风控标签
 */
export async function updateRiskTagApi(id: string, data: UpdateRiskTagParams) {
  return requestClient.put<RiskTag>(`/api/v1/risk/risk-tags/${id}`, data);
}

/**
 * 删除风控标签
 */
export async function deleteRiskTagApi(ids: string[]) {
  return requestClient.delete<{
    deleted_count: number;
  }>('/api/v1/risk/risk-tags', {
    data: { ids },
  });
}

// ================== 风控助手相关接口 ==================

// 风控助手接口类型
/**
 *
 *
 * report_tags： 风险检查
 */
export interface RiskAssistant {
  id: string;
  name: string;
  ai_model_id: string;
  ai_model_name?: string;
  role: string;
  risk_type?: RiskType;
  background?: string;
  task_prompt: string;
  variable_config?: string;
  report_config?: string;
  status: boolean;
  created_time: string;
  updated_time: string;
}

export interface RiskAssistantParams {
  name?: string;
  ai_model_id?: string;
  status?: boolean;
  page?: number;
  size?: number;
}

export interface CreateRiskAssistantParams {
  name: string;
  ai_model_id: string;
  role: string;
  risk_type?: RiskType;
  background?: string;
  task_prompt: string;
  variable_config?: string;
  report_config?: string;
  status?: boolean;
}

export interface UpdateRiskAssistantParams {
  name?: string;
  ai_model_id?: string;
  role?: string;
  risk_type?: RiskType;
  background?: string;
  task_prompt?: string;
  variable_config?: string;
  report_config?: string;
  status?: boolean;
}

// ================== 风控助手 API ==================

/**
 * 获取风控助手列表
 */
export async function getRiskAssistantListApi(params: RiskAssistantParams) {
  return requestClient.get<{
    items: RiskAssistant[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/risk/risk-assistants', { params });
}

/**
 * 获取所有风控助手（不分页）
 */
export async function getAllRiskAssistantsApi() {
  return requestClient.get<RiskAssistant[]>('/api/v1/risk/risk-assistants/all');
}

/**
 * 获取风控助手详情
 */
export async function getRiskAssistantApi(id: string) {
  return requestClient.get<RiskAssistant>(`/api/v1/risk/risk-assistants/${id}`);
}

/**
 * 创建风控助手
 */
export async function createRiskAssistantApi(data: CreateRiskAssistantParams) {
  return requestClient.post<RiskAssistant>('/api/v1/risk/risk-assistants', data);
}

/**
 * 更新风控助手
 */
export async function updateRiskAssistantApi(id: string, data: UpdateRiskAssistantParams) {
  return requestClient.put<RiskAssistant>(`/api/v1/risk/risk-assistants/${id}`, data);
}

/**
 * 删除风控助手
 */
// export async function deleteRiskAssistantApi(ids: string[]) {
//   return requestClient.delete<{
//     deleted_count: number;
//   }>('/api/v1/risk/risk-assistants', {
//     data: { ids },
//   });
// }

/**
 * 更新风控助手状态
 */
export async function updateRiskAssistantStatusApi(id: string, status: boolean) {
  return requestClient.put<RiskAssistant>(`/api/v1/risk/risk-assistants/${id}/status`, { status });
}

/**
 * 根据AI模型获取风控助手
 */
export async function getRiskAssistantsByModelApi(aiModelId: string) {
  return requestClient.get<RiskAssistant[]>(`/api/v1/risk/risk-assistants/by-model/${aiModelId}`);
}
