import type { PaginationResult } from '#/types';

import { requestClient } from './request';

export interface LoginLogParams {
  username?: string;
  status?: number;
  ip?: string;
  page?: number;
  size?: number;
}

export interface LoginLogResult {
  id: number;
  username: string;
  status: number;
  ip: string;
  country?: string;
  region?: string;
  os?: string;
  browser?: string;
  device?: string;
  msg: string;
  login_time: string;
}

export type OperaLogParams = LoginLogParams;

export interface OperaLogResult {
  id: number;
  trace_id: string;
  username?: string;
  method: string;
  title: string;
  path: string;
  ip: string;
  country?: string;
  region?: string;
  city?: string;
  user_agent: string;
  os?: string;
  browser?: string;
  device?: string;
  args?: JSON;
  status: number;
  code: string;
  msg: string;
  cost_time: number;
  opera_time: string;
}

export async function getLoginLogListApi(params: LoginLogParams) {
  return requestClient.get<PaginationResult<LoginLogResult>>('/api/v1/logs/login', { params });
}

export async function deleteLoginLogApi(pks: number[]) {
  return requestClient.delete('/api/v1/logs/login', { data: { pks } });
}

export async function getOperaLogListApi(params: OperaLogParams) {
  return requestClient.get<PaginationResult<OperaLogResult>>('/api/v1/logs/opera', { params });
}

export async function deleteOperaLogApi(pks: number[]) {
  return requestClient.delete('/api/v1/logs/opera', { data: { pks } });
}

// Chat QA logs
export interface ChatLogParams {
  chat_id?: string;
  user_id?: number;
  page?: number;
  size?: number;
}

export interface ChatLogPaginatedParams {
  chat_id: string; // 必需参数
  start_message_id: string; // 起始消息ID（将根据其 created_time 进行过滤）
  size?: number; // 可选：获取条数，默认6条，范围1-100
  filter_symbol: '<' | '<=' | '>' | '>='; // 可选：过滤符号，默认">="
}

export interface ChatMessageItem {
  id: string;
  chat_id: string;
  role: string;
  user_id?: null | number;
  username?: null | string;
  nickname?: null | string;
  content?: null | string;
  response_data?: null | string;
  is_interrupted?: boolean | null;
  created_time: null | string;
  updated_time?: null | string;
}

export async function getChatLogListApi(params: ChatLogParams) {
  return requestClient.get<PaginationResult<ChatMessageItem>>('/api/v1/logs/chat', { params });
}

export async function getChatLogPaginatedApi(params: ChatLogPaginatedParams) {
  return requestClient.get<PaginationResult<ChatMessageItem>>('/api/v1/logs/chat/paginated', {
    params,
  });
}

// Notice logs
export interface NoticeLogParams {
  description?: string;
  notification_type?: string;
  is_success?: boolean;
  start_time?: string;
  end_time?: string;
  page?: number;
  size?: number;
}

export interface NoticeLogResult {
  id: number;
  description: string;
  notification_type: string;
  content: string;
  address: string;
  is_success: boolean;
  failure_reason?: string;
  created_time: string;
  updated_time?: string;
}

export async function getNoticeLogListApi(params: NoticeLogParams) {
  return requestClient.get<PaginationResult<NoticeLogResult>>('/api/v1/logs/notice', {
    params,
  });
}
