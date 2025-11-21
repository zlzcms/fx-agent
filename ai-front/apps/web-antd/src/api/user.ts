/**
 * @Author: zhujinlong
 * @Date:   2025-06-07 18:18:33
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-07-07 19:54:15
 */

import { longTimeoutRequestClient, requestClient } from './request';

// 用户接口返回类型
export interface UserItem {
  id: string;
  name: string;
  username?: string;
  department?: string;
  email?: string;
  phone?: string;
  status?: boolean;
  create_time?: string;
  last_login_time?: string;
}

// 代理商接口返回类型
export interface AgentItem {
  id: string;
  name: string;
  region?: string;
  contact_person?: string;
  contact_phone?: string;
  status?: boolean;
  create_time?: string;
  last_login_time?: string;
}

// CRM用户接口返回类型
export interface CrmUserItem {
  id: string;
  name: string;
  username?: string;
  company?: string;
  email?: string;
  phone?: string;
  status?: boolean;
  create_time?: string;
  last_login_time?: string;
}

// 参数类型
export interface UserQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: boolean;
  department_id?: string;
  nickname?: string;
  email?: string;
  sex?: number;
  username?: string;
}

/**
 * 获取数据仓用户列表
 * @param params 查询参数
 */
export function getWarehouseUsersApi(params?: UserQueryParams) {
  return longTimeoutRequestClient.get<{
    items: UserItem[];
    links: {
      first: string;
      last: string;
      next: null | string;
      prev: null | string;
      self: string;
    };
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/warehouse/members', { params });
}

/**
 * 获取单个数据仓用户详情
 * @param id 用户ID
 */
export function getWarehouseUserDetailApi(id: number | string) {
  return requestClient.get<UserItem>(`/api/v1/warehouse/members/users/${id}`);
}

/**
 * 获取数据仓CRM用户列表
 * @param params 查询参数
 */
export function getWarehouseCrmUsersApi(params?: UserQueryParams) {
  return longTimeoutRequestClient.get<{
    items: CrmUserItem[];
    links: {
      first: string;
      last: string;
      next: null | string;
      prev: null | string;
      self: string;
    };
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/warehouse/members/crm-users', { params });
}

/**
 * 获取单个数据仓CRM用户详情
 * @param id 用户ID
 */
export function getWarehouseCrmUserDetailApi(id: number | string) {
  return requestClient.get<CrmUserItem>(`/api/v1/warehouse/members/crm-users/${id}`);
}

/**
 * 获取数据仓代理用户列表
 * @param params 查询参数
 */
export function getWarehouseAgentsApi(params?: UserQueryParams) {
  return longTimeoutRequestClient.get<{
    items: AgentItem[];
    links: {
      first: string;
      last: string;
      next: null | string;
      prev: null | string;
      self: string;
    };
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/warehouse/members/agents', { params });
}

/**
 * 获取单个数据仓代理商详情
 * @param id 用户ID
 */
export function getWarehouseAgentDetailApi(id: number | string) {
  return requestClient.get<AgentItem>(`/api/v1/warehouse/members/agents/${id}`);
}

/**
 * 获取所有数据仓用户（不分页）
 * @param params 查询参数
 * @param params.status 用户状态过滤
 */
export function getAllWarehouseUsersApi(params?: { status?: boolean }) {
  return requestClient.get<UserItem[]>('/api/v1/warehouse/members/users-all', { params });
}

/**
 * 获取所有数据仓代理商（不分页）
 * @param params 查询参数
 * @param params.status 代理商状态过滤
 */
export function getAllWarehouseAgentsApi(params?: { status?: boolean }) {
  return requestClient.get<AgentItem[]>('/api/v1/warehouse/members/agents-all', { params });
}

/**
 * 获取所有数据仓CRM用户（不分页）
 * @param params 查询参数
 * @param params.status CRM用户状态过滤
 */
export function getAllWarehouseCrmUsersApi(params?: { status?: boolean }) {
  return requestClient.get<CrmUserItem[]>('/api/v1/warehouse/members/crm-users-all', { params });
}
