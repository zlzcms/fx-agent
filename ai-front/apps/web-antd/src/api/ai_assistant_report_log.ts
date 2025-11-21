/**
 * @Author: AI Assistant
 * @Date:   2025-07-11
 * @Last Modified by:   AI Assistant
 * @Last Modified time: 2025-07-11
 */
import { requestClient } from './request';

export interface AiResponseData {
  analyze_data: string;
  property_analysis: Array<Record<string, any>>;
  output: string;
  data: {
    analytical_report: string;
    analyze_data: string;
  };
  prompt_data: string;
  confidence: number;
  metrics: Record<string, any>;
  recommendations: string[];
  user_count: number;
  timestamp: string;
  success: boolean;
}

// AI助手报告记录接口
export interface AiAssistantReportLog {
  id: number;
  assistant_id: string;
  member_id: number;
  model_id?: string;
  model_name?: string;
  sql_data?: string;
  prompt_data?: string;
  input_prompt?: string;
  report_status: boolean;
  report_score: number;
  report_result?: string;
  report_table?: string;
  report_document?: string;
  created_time: string;
  updated_time: string;
  ai_response?: AiResponseData;
  assistant: {
    assistant_type_display: string;
    created_time: string;
    id: number;
    last_analysis_time: string;
    name: string;
    updated_time: string;
  };
}

// AI助手报告记录分页结果接口
export interface AiAssistantReportLogPaginationResult {
  items: AiAssistantReportLog[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

// AI助手报告记录查询参数接口
export interface AiAssistantReportLogQueryParams {
  page?: number;
  size?: number;
  assistant_id?: string;
  assistant_name?: string;
  member_id?: number;
  model_id?: string;
  start_time?: string;
  end_time?: string;
  report_status?: boolean;
}

/**
 * 获取AI助手报告记录列表
 * @param params 查询参数
 */
export async function getAiAssistantReportLogsApi(params: AiAssistantReportLogQueryParams = {}) {
  return requestClient.get<AiAssistantReportLogPaginationResult>('/api/v1/ai/reports/assistant', {
    params,
  });
}

/**
 * 获取AI助手报告记录详情
 * @param report_id 报告ID
 */
export async function getAiAssistantReportLogDetailApi(report_id: number) {
  return requestClient.get<AiAssistantReportLog>(`/api/v1/ai/reports/assistant/${report_id}`);
}
