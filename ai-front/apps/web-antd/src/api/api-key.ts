import { requestClient } from './request';

export interface ApiKeyResult {
  id: number;
  key_name: string;
  description?: string;
  api_key_prefix?: string;
  api_key?: string; // 仅在创建时返回完整值
  status: number;
  expires_at?: string;
  ip_whitelist?: string;
  permissions?: string;
  usage_count: number;
  last_used_at?: string;
  last_used_ip?: string;
  user_id: number;
  created_time: string;
  updated_time: string;
}

export interface ApiKeyListParams {
  key_name?: string;
  status?: number;
  user_id?: number;
  page?: number;
  size?: number;
}

export interface CreateApiKeyParams {
  key_name: string;
  description?: string;
  expires_at?: string;
  ip_whitelist?: string;
  permissions?: string;
}

export interface UpdateApiKeyParams {
  key_name?: string;
  description?: string;
  status?: number;
  expires_at?: string;
  ip_whitelist?: string;
  permissions?: string;
}

export interface DeleteApiKeyParams {
  ids: number[];
}

export interface ApiKeyListResponse {
  items: ApiKeyResult[];
  page: number;
  size: number;
  total: number;
  total_pages: number;
}

/**
 * 获取API Key列表
 */
export async function getApiKeyListApi(params?: ApiKeyListParams) {
  return requestClient.get<ApiKeyListResponse>('/api/v1/sys/api-keys', { params });
}

/**
 * 获取API Key详情
 */
export async function getApiKeyDetailApi(apiKeyId: number) {
  return requestClient.get<ApiKeyResult>(`/api/v1/sys/api-keys/${apiKeyId}`);
}

/**
 * 创建API Key
 */
export async function createApiKeyApi(data: CreateApiKeyParams) {
  return requestClient.post<ApiKeyResult>('/api/v1/sys/api-keys', data);
}

/**
 * 更新API Key
 */
export async function updateApiKeyApi(apiKeyId: number, data: UpdateApiKeyParams) {
  return requestClient.put<ApiKeyResult>(`/api/v1/sys/api-keys/${apiKeyId}`, data);
}

/**
 * 删除API Key
 */
export async function deleteApiKeyApi(apiKeyId: number) {
  return requestClient.delete(`/api/v1/sys/api-keys/${apiKeyId}`);
}

/**
 * 批量删除API Key
 */
export async function deleteApiKeysBatchApi(data: DeleteApiKeyParams) {
  return requestClient.delete('/api/v1/sys/api-keys', { data });
}
