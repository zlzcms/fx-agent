import { requestClient } from './request';

// 推荐问法实体
export interface RecommendedQuestion {
  id: number;
  title: string;
  content: string;
  role_ids?: number[];
  sort_order: number;
  status: number; // 1: 正常, 0: 禁用
  is_default: boolean;
  created_time: string;
  updated_time?: string;
}

// 列表分页结果
export interface RecommendedQuestionPaginationResult {
  items: RecommendedQuestion[];
  page: number;
  size: number;
  total: number;
  total_pages: number;
}

// 创建/更新参数
export interface CreateRecommendedQuestionParams {
  title: string;
  content: string;
  role_ids?: number[];
  sort_order?: number;
  status?: number; // 默认启用
  is_default?: boolean;
}

export interface UpdateRecommendedQuestionParams {
  title?: string;
  content?: string;
  role_ids?: number[];
  sort_order?: number;
  status?: number;
  is_default?: boolean;
}

// 根据角色获取推荐问法
export async function getRecommendedQuestionsByRolesApi(roleIds: number[], limit = 3) {
  return requestClient.get<RecommendedQuestion[]>('/api/v1/sys/recommended-questions/by-roles', {
    params: {
      role_ids: roleIds.join(','),
      limit,
    },
  });
}

// 获取推荐问法列表（分页）
export async function getRecommendedQuestionListApi(params?: {
  is_default?: boolean;
  page?: number;
  size?: number;
  status?: number;
  title?: string;
}) {
  return requestClient.get<RecommendedQuestionPaginationResult>(
    '/api/v1/sys/recommended-questions',
    { params },
  );
}

// 获取详情
export async function getRecommendedQuestionDetailApi(pk: number) {
  return requestClient.get<RecommendedQuestion>(`/api/v1/sys/recommended-questions/${pk}`);
}

// 创建
export async function createRecommendedQuestionApi(data: CreateRecommendedQuestionParams) {
  return requestClient.post<RecommendedQuestion>('/api/v1/sys/recommended-questions', data);
}

// 更新
export async function updateRecommendedQuestionApi(
  pk: number,
  data: UpdateRecommendedQuestionParams,
) {
  return requestClient.put<RecommendedQuestion>(`/api/v1/sys/recommended-questions/${pk}`, data);
}

// 删除（单个）
export async function deleteRecommendedQuestionApi(pk: number) {
  return requestClient.delete(`/api/v1/sys/recommended-questions/${pk}`);
}

// 批量删除
export async function batchDeleteRecommendedQuestionsApi(pks: number[]) {
  return requestClient.delete('/api/v1/sys/recommended-questions', {
    data: { pks },
  });
}
