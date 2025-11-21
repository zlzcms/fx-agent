// AI报告相关类型定义

export interface AiResponseData {
  analytical_report: string;
  property_analysis: Array<Record<string, any>>;
  confidence: number;
  metrics: Record<string, any>;
  recommendations: string[];
  user_count: number;
  timestamp: string;
  success: boolean;
}

export interface Assistant {
  id: string;
  name: string;
  description: string;
  created_time: string;
  updated_time: string;
  last_analysis_time: string;
}

export interface ReportData {
  id: number;
  assistant_id: string;
  model_id: string;
  model_name: string;
  member_ids: string;
  member_id: number;
  report_status: boolean;
  report_score: number;
  report_result: string;
  report_table: any[] | null;
  report_document: string;
  sql_data: Record<string, any>;
  prompt_data: Record<string, any>;
  input_prompt: string;
  ai_response: AiResponseData;
  created_time: string;
  updated_time: string;
  assistant: Assistant;
}

export interface ReportDetailProps {
  report?: Partial<ReportData>;
}

export type TabType = 'doc' | 'prompt' | 'table';
