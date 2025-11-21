import type { SubscriptionType } from '#/types/subscription';

/**
 * @Author: zhujinlong
 * @Date:   2025-06-11 14:29:23
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-07-05 15:46:23
 */
import { longTimeoutRequestClient, requestClient } from './request';

// AI模型相关接口
export interface AIModel {
  id: string;
  name: string;
  ai_model_id: string;
  description: string;
  status: boolean;
  created_time: string;
  updated_time: string;
}

export interface AIModelParams {
  name?: string;
  ai_model_id?: string;
  status?: boolean;
  page?: number;
  size?: number;
}

export interface CreateAIModelParams {
  name: string;
  ai_model_id: string;
  description: string;
  status?: boolean;
}

export interface UpdateAIModelParams {
  name?: string;
  ai_model_id?: string;
  description?: string;
  status?: boolean;
}

// 新增人员数据接口
export interface PersonnelData {
  personnel_id: string;
  username: string;
  email: string;
}

// AI助手相关接口
export interface AIAssistant {
  id: string;
  name: string;
  type: string;
  assistant_type_id?: string;
  assistant_type_display?: string;
  ai_model_id: string;
  ai_model_name?: string;
  avatar?: string;
  description?: string;
  model_definition?: string; // 模型定义
  execution_frequency?: string; // 执行频率：每天、每周、每月
  execution_time?: string; // 执行时间：具体时间点
  execution_minutes?: number; // 分钟间隔
  execution_hours?: number; // 小时间隔
  execution_weekday?: string; // 执行星期
  execution_weekly_time?: string; // 每周执行时间
  execution_day?: string; // 执行日期
  execution_monthly_time?: string; // 每月执行时间
  responsible_persons?: Array<PersonnelData | string>; // 指定人员（多选）
  notification_methods?: Array<string | { id: string; name: string; type: string }>; // 通知方式（多选）
  status: boolean;
  is_template?: boolean; // 设为模板
  is_view_myself?: boolean; // 本人查看
  // 数据源相关
  data_sources?: Array<{
    collection_id: string;
    tables: Array<{
      data_limit?: number;
      selected_field_names?: string[];
      selected_fields: string[];
      table_description?: string;
      table_name: string;
    }>;
  }>; // 分析数据源（多选）
  data_permissions?: string[]; // 数据权限范围（多选）
  data_permission: string;
  data_permission_values?: string[]; // 数据权限具体值列表
  data_time_range_type?: string; // 数据时间范围类型
  data_time_value?: number; // 数据时间范围值
  data_limit?: number; // 数据限制条数

  // 输出相关
  output_format?: string; // 输出方式：表格、文档
  output_data?: string; // 输出数据：table格式时存储JSON字符串，document格式时存储Markdown文本
  include_charts?: boolean; // 包含图表
  auto_export?: boolean; // 自动导出
  export_formats?: string[]; // 导出格式
  // 文档格式相关
  document_template?: string; // 文档模板
  custom_template?: string; // 自定义模板
  settings?: Record<string, any>;
  created_time: string;
  updated_time: string;
}

export interface AIAssistantParams {
  name?: string;
  assistant_type_id: string;
  ai_model_id?: string;
  responsible_person?: string;
  status?: boolean;
  is_template?: boolean;
  page?: number;
  size?: number;
}

export interface CreateAIAssistantParams {
  name: string;
  type: string;
  assistant_type_id: string;
  ai_model_id: string;
  avatar?: string;
  description?: string;
  model_definition?: string;
  execution_frequency?: string;
  execution_time?: string;
  execution_minutes?: number;
  execution_hours?: number;
  execution_weekday?: string;
  execution_weekly_time?: string;
  execution_day?: string;
  execution_monthly_time?: string;
  responsible_persons?: PersonnelData[];
  notification_methods?: string[];
  status?: boolean;
  is_template?: boolean;
  is_view_myself?: boolean;
  data_sources?: Array<{
    collection_id: string;
    tables: Array<{
      data_limit?: number;
      selected_field_names?: string[];
      selected_fields: string[];
      table_description?: string;
      table_name: string;
    }>;
  }>;
  data_permissions?: string[];
  data_permission?: string;
  data_permission_values?: string[]; // 新增：数据权限具体值
  data_time_range_type?: string; // 新增：数据时间范围类型
  data_time_value?: number; // 新增：数据时间范围值
  data_limit?: number;
  output_format?: string;
  output_data?: string;
  include_charts?: boolean;
  auto_export?: boolean;
  export_formats?: string[];
  document_template?: string;
  custom_template?: string;
  settings?: Record<string, any>;
}

export interface UpdateAIAssistantParams {
  name?: string;
  type?: string;
  assistant_type_id?: string;
  ai_model_id?: string;
  avatar?: string;
  description?: string;
  model_definition?: string;
  execution_frequency?: string;
  execution_time?: string;
  execution_minutes?: number;
  execution_hours?: number;
  execution_weekday?: string;
  execution_weekly_time?: string;
  execution_day?: string;
  execution_monthly_time?: string;
  responsible_persons?: PersonnelData[];
  notification_methods?: string[];
  status?: boolean;
  is_template?: boolean;
  is_view_myself?: boolean;
  data_sources?: Array<{
    collection_id: string;
    tables: Array<{
      data_limit?: number;
      selected_field_names?: string[];
      selected_fields: string[];
      table_description?: string;
      table_name: string;
    }>;
  }>;
  data_permissions?: string[];
  data_permission?: string;
  data_permission_values?: string[]; // 新增：数据权限具体值
  data_time_range_type?: string; // 新增：数据时间范围类型
  data_time_value?: number; // 新增：数据时间范围值
  data_limit?: number;
  output_format?: string;
  output_data?: string;
  include_charts?: boolean;
  auto_export?: boolean;
  export_formats?: string[];
  document_template?: string;
  custom_template?: string;
  settings?: Record<string, any>;
}

// ================== AI模型 API ==================

/**
 * 获取AI模型列表
 */
export async function getAIModelListApi(params: AIModelParams) {
  return requestClient.get<{
    records: AIModel[];
    total: number;
  }>('/api/v1/ai/models', { params });
}

/**
 * 获取所有AI模型（不分页）
 */
export async function getAllAIModelsApi() {
  return requestClient.get<AIModel[]>('/api/v1/ai/models/all');
}

/**
 * 获取AI模型详情
 */
export async function getAIModelApi(id: string) {
  return requestClient.get<AIModel>(`/api/v1/ai/models/${id}`);
}

/**
 * 创建AI模型
 */
export async function createAIModelApi(data: CreateAIModelParams) {
  return requestClient.post<AIModel>('/api/v1/ai/models', data);
}

/**
 * 更新AI模型
 */
export async function updateAIModelApi(id: string, data: UpdateAIModelParams) {
  return requestClient.put<AIModel>(`/api/v1/ai/models/${id}`, data);
}

/**
 * 删除AI模型
 */
export async function deleteAIModelApi(ids: string[]) {
  return requestClient.delete('/api/v1/ai/models', {
    data: { ids },
  });
}

/**
 * 获取系统默认AI模型
 */
export async function getDefaultAIModelApi() {
  return requestClient.get<AIModel | null>('/api/v1/ai/models/default');
}

/**
 * 设置系统默认AI模型
 */
export async function setDefaultAIModelApi(modelId: string) {
  return requestClient.put<{ message: string; model_id: string; success: boolean }>(
    `/api/v1/ai/models/default/${modelId}`,
  );
}

/**
 * 切换AI模型状态
 */
export async function toggleAIModelStatusApi(id: string, status: boolean) {
  return requestClient.put(`/api/v1/ai/models/${id}/status`, { status });
}

/**
 * 测试AI模型连接
 */
export async function testAIModelConnectionApi(id: string) {
  return requestClient.post<{ message?: string; success: boolean }>(`/api/v1/ai/models/${id}/test`);
}

// ================== AI助手 API ==================

/**
 * 获取AI助手列表
 */
export async function getAIAssistantListApi(params: AIAssistantParams) {
  return requestClient.get<{
    items: AIAssistant[];
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
  }>('/api/v1/ai/assistants', { params });
}

/**
 * 获取所有AI助手（不分页）
 */
export async function getAllAIAssistantsApi() {
  return requestClient.get<AIAssistant[]>('/api/v1/ai/assistants/all');
}

/**
 * 获取AI助手详情
 */
export async function getAIAssistantApi(id: string) {
  return requestClient.get<AIAssistant>(`/api/v1/ai/assistants/${id}`);
}

/**
 * 创建AI助手
 */
export async function createAIAssistantApi(data: CreateAIAssistantParams) {
  return requestClient.post<AIAssistant>('/api/v1/ai/assistants', data);
}

/**
 * 更新AI助手
 */
export async function updateAIAssistantApi(id: string, data: UpdateAIAssistantParams) {
  return requestClient.put<AIAssistant>(`/api/v1/ai/assistants/${id}`, data);
}

/**
 * 删除AI助手
 */
export async function deleteAIAssistantApi(ids: string[]) {
  return requestClient.delete('/api/v1/ai/assistants', {
    data: { ids },
  });
}

/**
 * 复制AI助手
 */
export async function cloneAIAssistantApi(id: string, name: string) {
  return requestClient.post<AIAssistant>(`/api/v1/ai/assistants/${id}/clone`, { name });
}

// ================== 数据源管理 API ==================

// 数据源相关接口
export interface DataSource {
  id: string; // 集合ID
  collection_name: string; // 集合名称
  collection_description?: string; // 集合描述
  status: boolean; // 集合状态
  data_sources_count: number; // 数据源总数
  query_name: string; // 查询名称
  created_time: string;
  updated_time: string;
}

// 单个数据源信息接口
export interface DataSourceItem {
  id: string;
  database_name: string;
  table_name: string;
  description?: string;
  data_count: number;
  collection_id: string;
  relation_field?: string;
  created_time: string;
  updated_time: string;
  // 关联集合信息
  collection_name?: string;
  collection_status?: boolean;
}

// 国家信息接口
export interface Country {
  mark: string;
  lang: string;
  name: string;
  code: string;
  phone_code?: string;
  code_s: string;
}

// 数据源查询参数
export interface DataSourceParams {
  collection_name?: string;
  collection_id?: string;
  status?: boolean;
  page?: number;
  size?: number;
}

export interface CreateDataSourceParams {
  collection_name: string;
  collection_description?: string;
  query_name: string;
  status?: boolean;
}

export interface UpdateDataSourceParams {
  collection_name?: string;
  collection_description?: string;
  query_name?: string;
  status?: boolean;
}

// 批量创建数据源参数
export interface BatchCreateDataSourceParams {
  collection_name: string;
  collection_description?: string;
  query_name: string;
  status: boolean;
  data_sources: Array<{
    database_name: string;
    description?: string;
    relation_field?: string;
    table_name: string;
  }>;
}

// 批量创建响应
export interface BatchCreateDataSourceResponse {
  collection_id: string;
  collection_name: string;
  created_count: number;
  datasources: DataSourceItem[];
}

// 数据库表结构接口
export interface DatabaseInfo {
  name: string;
  tables: string[];
}

// 数据源详情响应接口
export interface DataSourceDetailResponse {
  id: string;
  collection_id: string;
  collection_name: string;
  collection_description?: string;
  status: boolean;
  data_sources_count: number;
  created_time: string;
  updated_time: string;
  datasources: DataSourceItem[];
  collection: {
    created_time: string;
    description?: string;
    id: string;
    name: string;
    status: boolean;
    updated_time: string;
  };
}

/**
 * 获取数据源列表
 */
export async function getDataSourceListApi(params: DataSourceParams) {
  return requestClient.get<{
    items: DataSource[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/ai/datasources', { params });
}

/**
 * 获取所有数据源（不分页）
 */
export async function getAllDataSourcesApi(params?: { status?: boolean }) {
  return requestClient.get<DataSource[]>('/api/v1/ai/datasources/all', { params });
}

/**
 * 获取数据源详情
 */
export async function getDataSourceApi(id: string) {
  return requestClient.get<DataSourceDetailResponse>(`/api/v1/ai/datasources/${id}`);
}

/**
 * 获取国家列表
 */
export async function getCountriesApi() {
  return requestClient.get('/api/v1/ai/datasources/countries');
}

/**
 * 创建数据源
 */
export async function createDataSourceApi(data: CreateDataSourceParams) {
  // 使用批量创建API，但不包含实际的数据源
  const batchData: BatchCreateDataSourceParams = {
    collection_name: data.collection_name,
    collection_description: data.collection_description,
    query_name: data.query_name,
    status: data.status === undefined ? true : data.status,
    data_sources: [], // 空数组，不包含任何数据源
  };
  return requestClient.post<BatchCreateDataSourceResponse>(
    '/api/v1/ai/datasources/batch',
    batchData,
  );
}

/**
 * 批量创建数据源
 */
export async function batchCreateDataSourceApi(data: BatchCreateDataSourceParams) {
  return requestClient.post<BatchCreateDataSourceResponse>('/api/v1/ai/datasources/batch', data);
}

/**
 * 更新数据源
 */
export async function updateDataSourceApi(id: string, data: UpdateDataSourceParams) {
  return requestClient.put<DataSource>(`/api/v1/ai/datasources/${id}`, data);
}

/**
 * 删除数据源
 */
export async function deleteDataSourceApi(ids: string[]) {
  return requestClient.delete('/api/v1/ai/datasources', {
    data: { ids },
  });
}

/**
 * 切换数据源状态
 */
export async function toggleDataSourceStatusApi(id: string, status: boolean) {
  return requestClient.put(`/api/v1/ai/datasources/${id}/status`, { status });
}

/**
 * 获取表数据统计
 */
export async function getTableDataCountApi(databaseName: string, tableName: string) {
  return requestClient.get<{ count: number }>(
    `/api/v1/ai/datasources/databases/${databaseName}/tables/${tableName}/count`,
  );
}

// ================== 数据库管理 API ==================

export interface DatabaseTreeNode {
  id: string;
  name: string;
  type: 'database' | 'field' | 'table';
  description?: string;
  parent_id?: string;
  children?: DatabaseTreeNode[];
  // 字段特有属性
  field_type?: string;
  is_nullable?: boolean;
  default_value?: string;
  // 表特有属性
  table_rows?: number;
  table_size?: string;
}

export interface DatabaseTreeParams {
  database_name?: string;
  include_tables?: boolean;
  include_fields?: boolean;
}

export interface UpdateDatabaseDescriptionParams {
  updates: Array<{
    description: string;
    id: string;
    type: 'database' | 'field' | 'table';
  }>;
}

// 获取数据库列表（带描述）
export interface DatabaseListItem {
  id: string;
  name: string;
  description?: string;
}

export async function getDatabaseListApi() {
  return requestClient.get<DatabaseListItem[]>('/api/v1/ai/databases');
}

/**
 * 获取数据库树形结构
 */
export async function getDatabaseTreeApi(params?: DatabaseTreeParams) {
  return requestClient.get<DatabaseTreeNode[]>('/api/v1/ai/databases/tree', { params });
}

/**
 * 获取指定数据库的表列表（带字段信息）
 */
export async function getDatabaseTablesWithFieldsApi(databaseName: string) {
  return requestClient.get<DatabaseTreeNode[]>(
    `/api/v1/ai/databases/${databaseName}/tables-with-fields`,
  );
}

/**
 * 获取指定表的字段信息
 */
export async function getTableFieldsApi(databaseName: string, tableName: string) {
  return requestClient.get<DatabaseTreeNode[]>(
    `/api/v1/ai/databases/${databaseName}/tables/${tableName}/fields`,
  );
}

/**
 * 批量更新数据库、表、字段的描述信息
 */
export async function updateDatabaseDescriptionsApi(data: UpdateDatabaseDescriptionParams) {
  return requestClient.put('/api/v1/ai/databases/descriptions', data);
}

/**
 * 刷新数据库结构（重新扫描数据库）
 */
export async function refreshDatabaseStructureApi(databaseName?: string) {
  return longTimeoutRequestClient.post('/api/v1/ai/databases/refresh', {
    database_name: databaseName,
  });
}

// ================== 模板管理 API ==================

// 模板相关接口
export interface Template {
  id: string;
  name: string;
  category: string;
  content: string;
  description?: string;
  status: boolean;
  created_time: string;
  updated_time: string;
}

export interface TemplateParams {
  name?: string;
  category?: string;
  status?: boolean;
  page?: number;
  size?: number;
}

export interface CreateTemplateParams {
  name: string;
  category: string;
  content: string;
  description?: string;
  status?: boolean;
}

export interface UpdateTemplateParams {
  name?: string;
  category?: string;
  content?: string;
  description?: string;
  status?: boolean;
}

/**
 * 获取模板列表
 */
export async function getTemplateListApi(params: TemplateParams) {
  return requestClient.get<{
    records: Template[];
    total: number;
  }>('/api/v1/ai/templates', { params });
}

/**
 * 获取所有模板（不分页）
 */
export async function getAllTemplatesApi() {
  return requestClient.get<Template[]>('/api/v1/ai/templates/all');
}

/**
 * 获取模板详情
 */
export async function getTemplateApi(id: string) {
  return requestClient.get<Template>(`/api/v1/ai/templates/${id}`);
}

/**
 * 创建模板
 */
export async function createTemplateApi(data: CreateTemplateParams) {
  return requestClient.post<Template>('/api/v1/ai/templates', data);
}

/**
 * 更新模板
 */
export async function updateTemplateApi(id: string, data: UpdateTemplateParams) {
  return requestClient.put<Template>(`/api/v1/ai/templates/${id}`, data);
}

/**
 * 删除模板
 */
export async function deleteTemplateApi(ids: string[]) {
  return requestClient.delete('/api/v1/ai/templates', {
    data: { ids },
  });
}

/**
 * 切换模板状态
 */
export async function toggleTemplateStatusApi(id: string, status: boolean) {
  return requestClient.put(`/api/v1/ai/templates/${id}/status`, { status });
}

/**
 * 获取模板分类列表
 */
export async function getTemplateCategoriesApi() {
  return requestClient.get<{ label: string; value: string }[]>('/api/v1/ai/templates/categories');
}

/**
 * 复制模板
 */
export async function cloneTemplateApi(id: string, name: string) {
  return requestClient.post<Template>(`/api/v1/ai/templates/${id}/clone`, { name });
}

// ================== AI助手相关基础数据 API ==================

// 人员相关接口
export interface Personnel {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
  status: boolean;
  created_time: string;
  updated_time: string;
}

// 通知方式相关接口
export interface NotificationMethod {
  id: string;
  name: string;
  type: 'dingtalk' | 'email' | 'feishu' | 'sms' | 'wechat_work';
  config?: Record<string, any>;
  status: boolean;
  created_time: string;
  updated_time: string;
}

// 数据权限相关接口
export interface DataPermission {
  id: string;
  name: string;
  permission_type:
    | 'custom'
    | 'data_scope'
    | 'field_level'
    | 'ip_range'
    | 'time_range'
    | 'user_scope';
  permission_config?: Record<string, any>;
  description?: string;
  status: boolean;
  created_time: string;
  updated_time: string;
}

/**
 * 获取所有人员（不分页）
 */
export async function getAllPersonnelApi(params?: { status?: boolean }) {
  return requestClient.get<Personnel[]>('/api/v1/ai/assistants/personnel/all', { params });
}

/**
 * 获取通知方式列表
 */
export async function getNotificationMethodsApi() {
  return requestClient.get<NotificationMethod[]>('/api/v1/ai/assistants/notification-methods');
}

/**
 * 获取订阅通知方式列表
 */
export async function getSubscriptionNotificationMethodsApi() {
  return requestClient.get<NotificationMethod[]>('/api/v1/ai/subscriptions/notification-methods');
}

/**
 * 获取数据权限列表
 */
export async function getDataPermissionsApi() {
  return requestClient.get<DataPermission[]>('/api/v1/ai/assistants/data-permissions');
}

// ================== AI助手模板 API ==================

export interface AIAssistantTemplate {
  id: string;
  name: string;
  type: string;
  ai_model_id: string;
  avatar?: string;
  description?: string;
  template_is_open: boolean; // 模板开启状态
  status: boolean;
  created_time: string;
  updated_time: string;
}

export interface AIAssistantTemplateParams {
  page?: number;
  size?: number;
}

/**
 * 获取AI助手模板列表
 */
export async function getAIAssistantTemplateListApi(params: AIAssistantTemplateParams) {
  return requestClient.get<{
    items: AIAssistantTemplate[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>('/api/v1/ai/assistants/templates', { params });
}

/**
 * 切换AI助手模板状态
 */
export async function toggleAIAssistantTemplateStatusApi(id: string, is_open: boolean) {
  return requestClient.put<AIAssistantTemplate>(`/api/v1/ai/assistants/${id}/template/status`, {
    is_open,
  });
}

// ================== 助手类型相关接口 ==================

// 助手类型接口类型
export interface AssistantType {
  id: string;
  name: string;
  created_time: string;
  updated_time: string;
}

export interface AssistantTypeParams {
  name?: string;
  page?: number;
  size?: number;
}

export interface CreateAssistantTypeParams {
  name: string;
}

export interface UpdateAssistantTypeParams {
  name?: string;
}

// ================== 助手类型 API ==================

/**
 * 获取助手类型列表
 */
export async function getAssistantTypeListApi(params: AssistantTypeParams) {
  return requestClient.get<{
    records: AssistantType[];
    total: number;
  }>('/api/v1/ai/assistant-types', { params });
}

/**
 * 获取所有助手类型（不分页）
 */
export async function getAllAssistantTypesApi() {
  return requestClient.get<AssistantType[]>('/api/v1/ai/assistant-types/all');
}

/**
 * 获取助手类型详情
 */
export async function getAssistantTypeApi(id: string) {
  return requestClient.get<AssistantType>(`/api/v1/ai/assistant-types/${id}`);
}

/**
 * 创建助手类型
 */
export async function createAssistantTypeApi(data: CreateAssistantTypeParams) {
  return requestClient.post<AssistantType>('/api/v1/ai/assistant-types', data);
}

/**
 * 更新助手类型
 */
export async function updateAssistantTypeApi(id: string, data: UpdateAssistantTypeParams) {
  return requestClient.put<AssistantType>(`/api/v1/ai/assistant-types/${id}`, data);
}

/**
 * 删除助手类型
 */
export async function deleteAssistantTypeApi(ids: string[]) {
  return requestClient.delete<{
    deleted_count: number;
  }>('/api/v1/ai/assistant-types', {
    data: { ids },
  });
}

// ================== SQL生成器API ==================

// SQL生成请求接口
export interface SqlGenerateRequest {
  database_name: string;
  tables: Array<{
    data_limit?: number;
    relation_field?: null | string;
    selected_field_names: string[];
    table_description?: string;
    table_name: string;
  }>;
  condition?: any[];
  order_by?: string;
  order_direction?: string;
  data_permission?: string;
  data_permission_values?: any[];
  data_time_range_type?: string;
  data_time_value?: number;
  dataSourcesLinkField: any[];
}

// SQL生成响应接口
export interface SqlGenerateResponse {
  sql: string;
  description: string;
}

/**
 * 生成SQL查询语句
 */
export async function generateSqlApi(data: SqlGenerateRequest) {
  return requestClient.post<SqlGenerateResponse>('/api/v1/ai/sql-generator/generate', data);
}

/**
 * 测试执行SQL查询（限制返回前10条数据）
 */
export async function testExecuteSqlApi(data: SqlGenerateRequest) {
  return requestClient.post<{
    rows: any[];
    sql: string;
    total: number;
  }>('/api/v1/ai/sql-generator/test-execute', data);
}

// SQL验证请求接口
export interface SqlValidationRequest {
  sql: string;
}

// SQL执行请求接口
export interface SqlExecuteRequest {
  sql: string;
  limit?: number;
}

// 链接数据查询请求接口
export interface LinkedDataQueryRequest {
  primaryDataSourceResult: {
    columns: Array<{ column_description?: string; column_name: string }>;
    dataSourceId: string;
    dataSourcesLinkField: string;
    rows: any[];
  };
  noPrimaryDataSource: Array<{
    database_name: string;
    dataSourcesLinkField: { fromField: string; fromTable: string };
    tables: Array<{
      data_limit?: number;
      relation_field?: null | string;
      selected_field_names: string[];
      table_description?: string;
      table_name: string;
    }>;
  }>;
}

// 链接数据查询响应接口
export interface LinkedDataQueryResponse {
  rows: any[];
  compress_data: any;
  columns: Array<{ column_description?: string; column_name: string }>;
  message: string;
}

/**
 * 验证SQL查询语句
 */
export async function validateSqlApi(data: SqlValidationRequest) {
  return requestClient.post<{
    analysis: any;
    message: string;
    valid: boolean;
  }>('/api/v1/ai/sql-generator/validate', data);
}

/**
 * 执行SQL查询语句
 */
export async function executeSqlApi(data: SqlExecuteRequest) {
  return longTimeoutRequestClient.post<{
    columns: string[];
    message: string;
    rows: any[];
    success: boolean;
  }>('/api/v1/ai/sql-generator/execute', data);
}

/**
 * 检测数据条件 - 链接数据查询
 */
export async function checkDataConditionApi(data: LinkedDataQueryRequest) {
  return longTimeoutRequestClient.post<LinkedDataQueryResponse>(
    '/api/v1/ai/sql-generator/check-data-condition',
    data,
  );
}

// ================== 提示词生成器API ==================

// 提示词生成请求接口
export interface PromptGenerationRequest {
  name?: string;
  description?: string;
  prompt_definition?: string;
  data: Record<string, any>;
  output_format: string;
  output_data: any;
  role?: string;
  background?: string;
  variable_config?: any;
  report_config?: any;
  type?: string;
  risk_tags?: any;
}

// 提示词生成响应接口
export interface PromptGenerationResponse {
  prompt_template: string;
  success: boolean;
  message: string;
}

/**
 * 生成提示词模板
 */
export async function generatePromptApi(data: PromptGenerationRequest) {
  return requestClient.post<PromptGenerationResponse>('/api/v1/ai/agent/generate-prompt', data);
}

// ================== 分析报告生成API ==================

// 分析报告生成请求接口
export interface AnalysisReportRequest {
  model_id: string;
  basic_info: any;
  prompt: string;
  data?: Record<string, any>;
}

// 分析报告生成响应接口
export interface AnalysisReportResponse {
  content: string;
  score: number;
  success: boolean;
  message: string;
}

/**
 * 生成分析报告（非流式）
 */
export async function generateAnalysisReportApi(data: AnalysisReportRequest) {
  return longTimeoutRequestClient.post<AnalysisReportResponse>(
    '/api/v1/ai/agent/generate-report',
    data,
  );
}

export interface AITrainingLog {
  id: string;
  model_id: string;
  model_name: string;
  log_type: string;
  prompt_template?: string;
  base_info?: any[];
  data?: any;
  assistant_id?: string;
  success: boolean;
  score?: number;
  content?: string;
  ai_response?: any[];
  created_time: string;
  updated_time: string;
}

export interface AITrainingLogParams {
  assistant_id?: string;
  log_type?: string;
  success?: boolean;
  page?: number;
  size?: number;
}

/**
 * 获取特定AI助手的训练日志
 */
export async function getAssistantTrainingLogsApi(
  assistantId: string,
  params?: Omit<AITrainingLogParams, 'assistant_id'>,
) {
  return requestClient.get<{
    items: AITrainingLog[];
    page: number;
    size: number;
    total: number;
    total_pages: number;
  }>(`/api/v1/ai/assistants/${assistantId}/training-logs`, {
    params: {
      ...params,
      page: params?.page || 1,
      size: params?.size || 10,
    },
  });
}

export interface MCPDataRequest {
  query_types: any[];
  data_permission?: string;
  data_permission_values?: any[];
  data_time_range_type?: string;
  data_time_value?: number;
}

export interface MCPDataResponse {
  data: any;
  metadata?: any;
  success: boolean;
  message: string;
}

/**
 * 获取MCP数据
 * @param data MCP数据请求参数
 * @returns MCP数据响应
 */
export async function getMCPDataApi(data: MCPDataRequest) {
  return longTimeoutRequestClient.post<MCPDataResponse>(
    '/api/v1/ai/databases/mcp/query-data',
    data,
  );
}

// ================== 数据分析相关 API ==================

// 多用户数据分析请求接口
export interface MultiUserDataAnalysisRequest {
  query_types: any[];
  data_permission: string;
  data_permission_values: any[];
  data_time_range_type?: string;
  data_time_value?: number;
  basicInfo: any;
  condition?: any;
}

// 数据分析响应接口
export interface DataAnalysisResponse {
  task_id: string;
  message: string;
  success: boolean;
}

// 任务状态响应接口
export interface TaskStatusResponse {
  task_id: string;
  status: 'cancelled' | 'completed' | 'failed' | 'pending' | 'running';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
  created_at: string;
  updated_at?: string;
}

// 任务日志条目接口
export interface TaskLogEntry {
  timestamp: string;
  level: 'DEBUG' | 'ERROR' | 'INFO' | 'WARNING';
  message: string;
  details?: any;
  event_type:
    | 'completed'
    | 'error'
    | 'execute'
    | 'final'
    | 'info'
    | 'progress'
    | 'result'
    | 'warning';
  data: {
    [key: string]: any;
    file?: {
      [key: string]: any;
      url: string;
    };
    message: string;
  };
}

// 任务日志响应接口
export interface TaskLogsResponse {
  task_id: string;
  logs: TaskLogEntry[];
  log_count: number;
}

/**
 * 启动多用户数据分析
 */
export async function startMultiUserDataAnalysisApi(data: MultiUserDataAnalysisRequest) {
  return requestClient.post<DataAnalysisResponse>(
    '/api/v1/ai/data-analysis/analyze-multi-user',
    data,
  );
}

/**
 * 查询任务状态
 */
export async function getTaskStatusApi(taskId: string) {
  return requestClient.get<TaskStatusResponse>(`/api/v1/ai/data-analysis/task-status/${taskId}`);
}

/**
 * 获取任务日志
 */
export async function getTaskLogsApi(taskId: string) {
  return requestClient.get<TaskLogsResponse>(`/api/v1/ai/data-analysis/task-logs/${taskId}`);
}

/**
 * 获取所有任务列表
 */
export async function getAllTasksApi() {
  return requestClient.get<TaskStatusResponse[]>('/api/v1/ai/data-analysis/tasks');
}

/**
 * 中断模拟任务
 *
 */

export async function cancelTaskApi(taskId: string) {
  return requestClient.post(`/api/v1/ai/data-analysis/task/${taskId}/cancel`);
}

/**
 * 快速创建助手
 * data: {
 *  question: string;
 * }
 */
export async function quickCreateAssistantApi(data: any) {
  return requestClient.post(`/api/v1/ai/agent/smart-create-assistant`, data);
}

// ================== AI内容润色相关 API ==================

// AI内容润色请求接口
export interface AIPolishContentRequest {
  content: string; // 需要润色的内容
  role?: string; // 助手角色（可选）
  task?: string; // 助手任务（可选）
}

// AI内容润色响应接口
export interface AIPolishContentResponse {
  original_content: string; // 原始内容
  polished_content: string; // 润色后的内容
}

/**
 * AI内容润色
 * 用于对文本内容进行智能润色和优化
 */
export async function polishContentApi(data: AIPolishContentRequest) {
  return longTimeoutRequestClient.post<AIPolishContentResponse>(
    '/api/v1/ai/agent/polish-content',
    data,
  );
}

// ================== 助理订阅 API ==================

/**
 * 助理订阅接口类型
 */
export interface AISubscription {
  id: string;
  name: string;
  subscription_type: SubscriptionType;
  assistant_type_id?: string;
  assistant_id: string;
  assistant_name?: string;
  plan_cycle: string;
  execution_frequency: 'daily' | 'hours' | 'minutes' | 'monthly' | 'weekly';
  execution_time?: string;
  execution_hours?: number;
  execution_minutes?: number;
  execution_weekday?: string;
  execution_day?: string;
  notification_recipients: string[];
  notification_methods?: Array<string | { id: string; name: string; type: string }>;
  responsible_persons?: Array<PersonnelData | string>;
  status: boolean;
  created_time: string;
  updated_time: string;
}

/**
 * 助理订阅查询参数
 */
export interface AISubscriptionParams {
  name?: string;
  subscription_type?: string;
  assistant_type_id?: string;
  status?: boolean;
  page?: number;
  size?: number;
}

/**
 * 创建助理订阅参数
 */
export interface CreateAISubscriptionParams {
  name: string;
  subscription_type: SubscriptionType;
  assistant_type_id?: string;
  assistant_id: string;
  plan_cycle: string;
  execution_frequency: 'daily' | 'hours' | 'minutes' | 'monthly' | 'weekly';
  execution_time?: string;
  execution_hours?: number;
  execution_minutes?: number;
  execution_weekday?: string;
  execution_day?: string;
  notification_recipients: string[];
  status?: boolean;
}

/**
 * 更新助理订阅参数
 */
export interface UpdateAISubscriptionParams {
  name?: string;
  subscription_type?: SubscriptionType;
  assistant_type_id?: string;
  assistant_id?: string;
  plan_cycle?: string;
  execution_frequency?: 'daily' | 'hours' | 'minutes' | 'monthly' | 'weekly';
  execution_time?: string;
  execution_hours?: number;
  execution_minutes?: number;
  execution_weekday?: string;
  execution_day?: string;
  notification_recipients?: string[];
  status?: boolean;
}

/**
 * 获取助理订阅列表
 */
export async function getAISubscriptionListApi(params: AISubscriptionParams) {
  return requestClient.get<{
    items: AISubscription[];
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
  }>('/api/v1/ai/subscriptions', { params });
}

/**
 * 获取助理订阅详情
 */
export async function getAISubscriptionApi(id: string) {
  return requestClient.get<AISubscription>(`/api/v1/ai/subscriptions/${id}`);
}

/**
 * 创建助理订阅
 */
export async function createAISubscriptionApi(data: CreateAISubscriptionParams) {
  return requestClient.post<AISubscription>('/api/v1/ai/subscriptions', data);
}

/**
 * 更新助理订阅
 */
export async function updateAISubscriptionApi(id: string, data: UpdateAISubscriptionParams) {
  return requestClient.put<AISubscription>(`/api/v1/ai/subscriptions/${id}`, data);
}

/**
 * 删除助理订阅
 */
export async function deleteAISubscriptionApi(ids: string[]) {
  return requestClient.delete<{
    deleted_count: number;
  }>('/api/v1/ai/subscriptions', {
    data: { ids },
  });
}

/**
 * 切换助理订阅状态
 */
export async function toggleAISubscriptionStatusApi(id: string, status: boolean) {
  return requestClient.put<AISubscription>(`/api/v1/ai/subscriptions/${id}/status`, { status });
}

// ================== MCP 服务相关 API ==================

// MCP 服务状态接口
export interface MCPServiceStatus {
  status: 'healthy' | 'unhealthy';
  timestamp?: string;
  service?: string;
  version?: string;
  database?: 'connected' | 'disconnected' | 'error';
  error?: string;
}

/**
 * 获取 MCP 服务健康状态
 */
export async function getMCPServiceHealthApi() {
  // 使用 fetch 直接调用，绕过 requestClient 的响应拦截器
  const response = await fetch('/api/v1/health');
  if (response.ok) {
    return await response.json();
  } else {
    throw new Error(`Health check failed: ${response.status}`);
  }
}
