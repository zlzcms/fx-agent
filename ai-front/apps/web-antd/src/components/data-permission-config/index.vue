<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  Button as AButton,
  Input as AInput,
  Modal as AModal,
  Select as ASelect,
  SelectOption as ASelectOption,
  Tag as ATag,
} from 'ant-design-vue';

// 权限数据类型定义
interface PermissionItem {
  id: string;
  name: string;
  permission_type: string;
  permission_config: any;
  description: string;
  status: boolean;
  created_time: string;
  updated_time?: string;
}

// 导出类型供外部使用
export type { PermissionItem };

// Props
interface Props {
  modelValue?: string[];
  options?: PermissionItem[];
}

// Emits
interface Emits {
  (e: 'update:modelValue', value: string[]): void;
  (e: 'change', value: string[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  options: () => [],
});

const emit = defineEmits<Emits>();

// 响应式数据
const showModal = ref(false);
const showDetailModal = ref(false);
const searchText = ref('');
const filterType = ref('');
// 从 modelValue 提取 ID 数组初始化 selectedPermissions
const getIdsFromModelValue = (modelValue: any[]) => {
  return modelValue.map((item: any) => (typeof item === 'string' ? item : item.id));
};

const selectedPermissions = ref<string[]>(getIdsFromModelValue(props.modelValue || []));
const currentPermission = ref<null | PermissionItem>(null);

// 计算属性
const selectedPermissionsData = computed(() => {
  // 处理 modelValue，支持字符串数组和对象数组
  const modelValueToUse = props.modelValue || [];

  // 提取ID数组
  const selectedIds = new Set(
    modelValueToUse.map((item: any) => (typeof item === 'string' ? item : item.id)),
  );

  return props.options.filter((item) => selectedIds.has(item.id));
});

const filteredPermissions = computed(() => {
  let filtered = props.options;

  // 搜索过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase();
    filtered = filtered.filter(
      (item) =>
        item.name.toLowerCase().includes(search) || item.description.toLowerCase().includes(search),
    );
  }

  // 类型过滤
  if (filterType.value) {
    filtered = filtered.filter((item) => item.permission_type === filterType.value);
  }

  return filtered;
});

// 方法
function getPermissionIcon(type: string) {
  // 根据权限类型返回对应的图标组件
  switch (type) {
    case 'custom': {
      return 'div';
    } // 自定义图标
    case 'data_scope': {
      return 'div';
    } // 数据图标
    case 'field_level': {
      return 'div';
    } // 字段图标
    case 'ip_range': {
      return 'div';
    } // 网络图标
    case 'time_range': {
      return 'div';
    } // 时钟图标
    case 'user_scope': {
      return 'div';
    } // 用户图标
    default: {
      return 'div';
    } // 默认图标
  }
}

function getPermissionTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    time_range: '时间范围',
    user_scope: '用户范围',
    ip_range: 'IP范围',
    data_scope: '数据范围',
    field_level: '字段级别',
    custom: '自定义',
  };
  return labelMap[type] || type;
}

function getConfigPreview(permission: PermissionItem): Record<string, string> {
  const config = permission.permission_config;
  const preview: Record<string, string> = {};

  switch (permission.permission_type) {
    case 'custom': {
      preview['自定义规则'] = config.custom_rules?.length
        ? `${config.custom_rules.length}条`
        : '未设置';
      preview['需要审批'] = config.approval_required ? '是' : '否';
      break;
    }
    case 'data_scope': {
      preview['最大行数'] = config.max_rows?.toLocaleString() || '未限制';
      preview['允许数据库'] = config.allowed_databases?.length
        ? `${config.allowed_databases.length}个`
        : '未设置';
      break;
    }
    case 'field_level': {
      preview['允许字段'] = config.allowed_fields?.length
        ? `${config.allowed_fields.length}个`
        : '未设置';
      preview['屏蔽字段'] = config.blocked_fields?.length
        ? `${config.blocked_fields.length}个`
        : '未设置';
      break;
    }
    case 'ip_range': {
      preview['允许IP'] = config.allowed_ips?.length ? `${config.allowed_ips.length}个` : '未设置';
      preview['VPN访问'] = config.allow_vpn ? '允许' : '禁止';
      break;
    }
    case 'time_range': {
      preview['工作时间'] = `${config.start_time} - ${config.end_time}`;
      preview['工作日'] = config.weekdays?.length ? `${config.weekdays.length}天` : '未设置';
      break;
    }
    case 'user_scope': {
      preview['允许用户'] = config.allowed_users?.length
        ? `${config.allowed_users.length}个`
        : '未设置';
      preview['允许部门'] = config.allowed_departments?.length
        ? `${config.allowed_departments.length}个`
        : '未设置';
      break;
    }
  }

  return preview;
}

function togglePermission(permissionId: string) {
  const index = selectedPermissions.value.indexOf(permissionId);
  if (index === -1) {
    selectedPermissions.value.push(permissionId);
  } else {
    selectedPermissions.value.splice(index, 1);
  }
}

function removePermission(permissionId: string) {
  const index = selectedPermissions.value.indexOf(permissionId);
  if (index !== -1) {
    selectedPermissions.value.splice(index, 1);
  }
  emit('update:modelValue', selectedPermissions.value);
  emit('change', selectedPermissions.value);
}

function showPermissionDetail(permission: PermissionItem) {
  currentPermission.value = permission;
  showDetailModal.value = true;
}

function confirmSelection() {
  emit('update:modelValue', selectedPermissions.value);
  emit('change', selectedPermissions.value);
  showModal.value = false;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString('zh-CN');
}

// 监听props变化
watch(
  () => props.modelValue,
  (newValue) => {
    selectedPermissions.value = getIdsFromModelValue(newValue || []);
  },
  { immediate: true },
);
</script>

<template>
  <div class="data-permission-config">
    <!-- 触发器按钮区域 -->
    <div class="permission-selector-wrapper">
      <div class="selected-permissions-display">
        <div v-if="selectedPermissionsData.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg
              class="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <p class="empty-text">
            {{ $t('page.components.dataPermissionConfig.noPermissionsSelected') }}
          </p>
          <p class="empty-hint">
            {{ $t('page.components.dataPermissionConfig.clickToConfigure') }}
          </p>
        </div>

        <div v-else class="selected-list">
          <div
            v-for="permission in selectedPermissionsData"
            :key="permission.id"
            class="permission-tag"
          >
            <div class="tag-icon">
              <component :is="getPermissionIcon(permission.permission_type)" class="w-4 h-4" />
            </div>
            <div class="tag-content">
              <span class="tag-name">{{ permission.name }}</span>
              <span class="tag-type">{{ getPermissionTypeLabel(permission.permission_type) }}</span>
            </div>
            <button class="tag-remove" @click="removePermission(permission.id)">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <button class="config-button" @click="showModal = true">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        {{ $t('page.components.dataPermissionConfig.configureDataPermission') }}
      </button>
    </div>

    <!-- 权限配置模态框 -->
    <AModal
      v-model:open="showModal"
      :title="$t('page.components.dataPermissionConfig.dataPermissionConfig')"
      width="900px"
      :footer="null"
      class="permission-config-modal"
    >
      <div class="modal-content">
        <!-- 搜索和筛选 -->
        <div class="search-bar">
          <AInput
            v-model:value="searchText"
            :placeholder="$t('page.components.dataPermissionConfig.searchPermission')"
            class="search-input"
          >
            <template #prefix>
              <svg
                class="w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </template>
          </AInput>

          <ASelect
            v-model:value="filterType"
            :placeholder="$t('page.components.dataPermissionConfig.filterPermissionType')"
            class="type-filter"
            allow-clear
          >
            <ASelectOption value="">
              {{ $t('page.components.dataPermissionConfig.allTypes') }}
            </ASelectOption>
            <ASelectOption value="time_range">
              {{ $t('page.components.dataPermissionConfig.timeRange') }}
            </ASelectOption>
            <ASelectOption value="user_scope">
              {{ $t('page.components.dataPermissionConfig.userScope') }}
            </ASelectOption>
            <ASelectOption value="ip_range">
              {{ $t('page.components.dataPermissionConfig.ipRange') }}
            </ASelectOption>
            <ASelectOption value="data_scope">
              {{ $t('page.components.dataPermissionConfig.dataScope') }}
            </ASelectOption>
            <ASelectOption value="field_level">
              {{ $t('page.components.dataPermissionConfig.fieldLevel') }}
            </ASelectOption>
            <ASelectOption value="custom">
              {{ $t('page.components.dataPermissionConfig.custom') }}
            </ASelectOption>
          </ASelect>
        </div>

        <!-- 权限列表 -->
        <div class="permissions-grid">
          <div
            v-for="permission in filteredPermissions"
            :key="permission.id"
            class="permission-card"
            :class="{ selected: selectedPermissions.includes(permission.id) }"
            @click="togglePermission(permission.id)"
          >
            <!-- 选中状态指示器 -->
            <div class="selection-indicator">
              <div class="checkbox">
                <svg
                  v-if="selectedPermissions.includes(permission.id)"
                  class="w-3 h-3 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </div>

            <!-- 权限卡片内容 -->
            <div class="card-header">
              <div class="permission-icon">
                <component :is="getPermissionIcon(permission.permission_type)" class="w-6 h-6" />
              </div>
              <div class="permission-info">
                <h3 class="permission-name">{{ permission.name }}</h3>
                <span class="permission-type-badge">{{
                  getPermissionTypeLabel(permission.permission_type)
                }}</span>
              </div>
            </div>

            <p class="permission-description">{{ permission.description }}</p>

            <!-- 权限配置概览 -->
            <div class="config-preview">
              <div
                class="config-item"
                v-for="(value, key) in getConfigPreview(permission)"
                :key="key"
              >
                <span class="config-key">{{ key }}:</span>
                <span class="config-value">{{ value }}</span>
              </div>
            </div>

            <!-- 详细配置按钮 -->
            <div class="card-actions">
              <button class="detail-button" @click.stop="showPermissionDetail(permission)">
                {{ $t('page.components.dataPermissionConfig.viewDetailConfig') }}
              </button>
            </div>
          </div>
        </div>

        <!-- 底部操作按钮 -->
        <div class="modal-footer">
          <AButton @click="showModal = false">
            {{ $t('page.components.dataPermissionConfig.cancel') }}
          </AButton>
          <AButton type="primary" @click="confirmSelection">
            {{ $t('page.components.dataPermissionConfig.confirmSelection') }} ({{
              selectedPermissions.length
            }})
          </AButton>
        </div>
      </div>
    </AModal>

    <!-- 权限详情模态框 -->
    <AModal
      v-model:open="showDetailModal"
      :title="`${$t('page.components.dataPermissionConfig.permissionDetail')} - ${currentPermission?.name}`"
      width="700px"
      :footer="null"
      class="permission-detail-modal"
    >
      <div v-if="currentPermission" class="detail-content">
        <div class="detail-header">
          <div class="permission-icon">
            <component :is="getPermissionIcon(currentPermission.permission_type)" class="w-8 h-8" />
          </div>
          <div class="permission-meta">
            <h3>{{ currentPermission.name }}</h3>
            <p class="permission-description">{{ currentPermission.description }}</p>
            <span class="permission-type-badge">{{
              getPermissionTypeLabel(currentPermission.permission_type)
            }}</span>
          </div>
        </div>

        <div class="config-detail">
          <h4>{{ $t('page.components.dataPermissionConfig.detailConfig') }}</h4>
          <pre class="config-json">{{
            JSON.stringify(currentPermission.permission_config, null, 2)
          }}</pre>
        </div>

        <div class="permission-meta-info">
          <div class="meta-item">
            <span class="meta-label"
              >{{ $t('page.components.dataPermissionConfig.permissionId') }}:</span
            >
            <span class="meta-value">{{ currentPermission.id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label"
              >{{ $t('page.components.dataPermissionConfig.createdTime') }}:</span
            >
            <span class="meta-value">{{ formatDate(currentPermission.created_time) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">{{ $t('page.components.dataPermissionConfig.status') }}:</span>
            <span class="meta-value">
              <ATag :color="currentPermission.status ? 'green' : 'red'">
                {{
                  currentPermission.status
                    ? $t('page.components.dataPermissionConfig.enabled')
                    : $t('page.components.dataPermissionConfig.disabled')
                }}
              </ATag>
            </span>
          </div>
        </div>
      </div>
    </AModal>
  </div>
</template>

<style scoped>
.data-permission-config {
  width: 100%;
}

.permission-selector-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-permissions-display {
  min-height: 80px;
  padding: 16px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-icon {
  margin-bottom: 8px;
}

.empty-text {
  margin: 0 0 4px;
  font-weight: 500;
  color: #6b7280;
}

.empty-hint {
  margin: 0;
  font-size: 14px;
  color: #9ca3af;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permission-tag {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.permission-tag:hover {
  border-color: #9ca3af;
  box-shadow: 0 2px 4px rgb(0 0 0 / 5%);
}

.tag-icon {
  color: #6b7280;
}

.tag-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tag-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.tag-type {
  font-size: 12px;
  color: #6b7280;
}

.tag-remove {
  padding: 2px;
  color: #9ca3af;
  cursor: pointer;
  background: none;
  border: none;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.tag-remove:hover {
  color: #ef4444;
  background: #fee2e2;
}

.config-button {
  display: flex;
  align-items: center;
  align-self: flex-start;
  padding: 10px 16px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.config-button:hover {
  background: #2563eb;
  box-shadow: 0 4px 8px rgb(59 130 246 / 30%);
  transform: translateY(-1px);
}

/* 模态框内容样式 */
.modal-content {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
}

.type-filter {
  width: 150px;
}

.permissions-grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  max-height: 500px;
  padding-right: 8px;
  overflow-y: auto;
}

.permission-card {
  position: relative;
  padding: 16px;
  cursor: pointer;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.permission-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 8px rgb(0 0 0 / 10%);
  transform: translateY(-2px);
}

.permission-card.selected {
  background: rgb(59 130 246 / 5%) !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 1px rgb(59 130 246 / 10%) !important;
}

.selection-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
}

.checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.permission-card.selected .checkbox {
  background: #3b82f6;
  border-color: #3b82f6;
}

.card-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.permission-icon {
  flex-shrink: 0;
  color: #6b7280;
}

.permission-info {
  flex: 1;
}

.permission-name {
  margin: 0 0 6px;
  font-weight: 600;
  color: #374151;
}

.permission-type-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background: #e5e7eb;
  border-radius: 12px;
}

.permission-description {
  margin: 0 0 12px;
  line-height: 1.4;
  color: #6b7280;
}

.config-preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.config-key {
  font-weight: 500;
  color: #6b7280;
}

.config-value {
  font-weight: 600;
  color: #374151;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

.detail-button {
  padding: 6px 12px;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.detail-button:hover {
  color: #3b82f6;
  border-color: #3b82f6;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  margin-top: 20px;
  border-top: 1px solid #e5e7eb;
}

/* 详情模态框样式 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.permission-meta h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
}

.config-detail h4 {
  margin: 0 0 12px;
  font-weight: 600;
}

.config-json {
  max-height: 300px;
  padding: 12px;
  overflow: auto;
  font-family: Monaco, Menlo, 'Ubuntu Mono', monospace;
  font-size: 12px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.permission-meta-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-label {
  font-weight: 500;
  color: #6b7280;
}

.meta-value {
  font-weight: 600;
  color: #374151;
}
</style>
