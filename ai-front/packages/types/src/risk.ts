/**
 * 风险管理相关类型定义
 */

/**
 * 风险报告数据项接口
 */
export interface RiskReportItem {
  id: number;
  assistant_id?: string;
  model_id?: string;
  member_id?: string;
  member_name?: string; // 添加成员名称字段
  risk_type?: string;
  report_score: number;
  riskLevel: string;
  risk_level?: {
    description: string;
    name: string;
  };
  report_tags?: string;
  reportTags?: string[];
  report_result?: string;
  report_table?: string;
  report_document?: string;
  report_status?: boolean;
  is_processed: boolean;
  created_time: string;
  updated_time?: string;
  handle_result?: string;
  handle_suggestion?: string;
  handle_time?: string;
  handle_user?: string; // 处理人ID
  handle_user_name?: string; // 处理人名称（昵称优先）
  input_prompt?: string; // 输入提示词
  ai_response?: any; // AI响应结果
  description?: string; // 风险描述，支持外部系统展示
}

/**
 * 风险等级类型
 */
export type RiskLevel = 'HIGH' | 'LOW' | 'MEDIUM' | 'MEDIUM_HIGH' | 'MEDIUM_LOW';

/**
 * 处理状态类型
 */
export type ProcessStatus = 'PROCESSED' | 'UNPROCESSED';

/**
 * 处理状态颜色类型
 */
export type ProcessStatusColor = 'success' | 'warning';
