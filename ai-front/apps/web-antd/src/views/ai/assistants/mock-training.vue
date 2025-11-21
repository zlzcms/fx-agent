<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import { $t } from '@vben/locales';
import { useAccessStore } from '@vben/stores';

import { AiAction } from '@maxpro/ai-action';
import { Col as ACol, Row as ARow, message, Modal } from 'ant-design-vue';

import { RiskType } from '#/api/risk';
import { getWarehouseAgentsApi, getWarehouseCrmUsersApi, getWarehouseUsersApi } from '#/api/user';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  assistantName: {
    type: String,
    default: '',
    description: $t('@ai-assistants.assistantName'),
  },
  assistantId: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['update:open']);

// 获取 access store 用于获取 token
const accessStore = useAccessStore();

onMounted(() => {
  // 初始加载时只加载第一页数据，减少初始加载时间
  loadUserData(dataPermission.value, '', 1, 50);
});

// 使用统一的风控类型枚举
type DataPermissionType = RiskType;
const DATA_PERMISSION = RiskType;

// 定义时间范围类型
type TimeRangeType = 'day' | 'month' | 'quarter' | 'year';

// 定义用户信息接口
interface UserInfo {
  id: string;
  name: string;
}

// 定义数据源项接口
interface DataSourceItem {
  key: string;
  title: string;
  description: string;
}

// 模拟测试相关状态
const mockTrainingVisible = ref(false);
watch(
  () => props.open,
  (newVal) => {
    mockTrainingVisible.value = newVal;
  },
);

// 数据权限和时间范围的状态
const dataPermission = ref<DataPermissionType>(RiskType.ALL_EMPLOYEE);
const dataPermissionValues = ref<string[]>([]);
const dataTimeRangeType = ref<TimeRangeType>('month');
const dataTimeValue = ref<number>(1);

// 已选择的用户
const selectedEmployees = ref<UserInfo[]>([]);
const selectedCrmUsers = ref<UserInfo[]>([]);
const selectedAgents = ref<UserInfo[]>([]);

// 下拉列表相关状态
const sourceData = ref<DataSourceItem[]>([]);
const targetKeys = ref<string[]>([]);
const searchQuery = ref<string>('');
const loading = ref<boolean>(false);
const total = ref(0);

// 构建 askContent 用于 ai-action
const askContent = computed(() => {
  if (targetKeys.value.length === 0 || !dataTimeValue.value) {
    return '';
  }

  // 获取用户类型名称
  let userType = $t('@ai-assistants.customer');
  switch (dataPermission.value) {
    case DATA_PERMISSION.AGENT_USER: {
      userType = $t('@ai-assistants.agent');
      break;
    }
    case DATA_PERMISSION.CRM_USER: {
      userType = $t('@ai-assistants.crmUser');
      break;
    }
    case DATA_PERMISSION.PAYMENT: {
      userType = $t('@ai-assistants.paymentUser');
      break;
    }
    default: {
      userType = $t('@ai-assistants.customer');
    }
  }

  // 获取选中的用户名称列表
  let selectedUsers: UserInfo[] = [];
  switch (dataPermission.value) {
    case DATA_PERMISSION.AGENT_USER: {
      selectedUsers = selectedAgents.value;
      break;
    }
    case DATA_PERMISSION.CRM_USER: {
      selectedUsers = selectedCrmUsers.value;
      break;
    }
    default: {
      selectedUsers = selectedEmployees.value;
    }
  }

  const userNames = selectedUsers.map((u) => u.name).join('、');

  // 获取时间范围描述
  const timeUnitMap: Record<TimeRangeType, string> = {
    day: $t('@ai-assistants.days'),
    month: $t('@ai-assistants.months'),
    quarter: $t('@ai-assistants.quarters'),
    year: $t('@ai-assistants.years'),
  };
  const timeDesc = `${$t('@ai-assistants.recent')}${dataTimeValue.value}${timeUnitMap[dataTimeRangeType.value]}`;

  // 构建 askContent
  return `${$t('@ai-assistants.pleaseUse')}${props.assistantName}${$t('@ai-assistants.analyze')}${userType}${userNames}，${timeDesc}${$t('@ai-assistants.riskData')}`;
});

// AI 配置
const aiConfig = computed(() => ({
  askContent: askContent.value,
  token: accessStore.accessToken || '',
  id: props.assistantId,
}));

// 是否可以开始模拟测试
const canStartTest = computed(() => {
  return targetKeys.value.length > 0 && dataTimeValue.value > 0;
});

// 根据数据权限类型获取对应的单位标签
function getTimeUnitLabel(): string {
  const unitLabels: Record<TimeRangeType, string> = {
    day: '天',
    month: '个月',
    quarter: '个季度',
    year: '年',
  };
  return unitLabels[dataTimeRangeType.value] || '个月';
}

// 页码状态（用于加载数据）
const currentPage = ref(1);
// 远程搜索防抖定时器
const searchDebounceTimer = ref<NodeJS.Timeout | null>(null);

// 处理数据权限类型变化
function handleDataPermissionTypeChange(value: DataPermissionType) {
  dataPermission.value = value;
  selectedEmployees.value = [];
  selectedAgents.value = [];
  selectedCrmUsers.value = [];
  dataPermissionValues.value = [];
  targetKeys.value = [];
  searchQuery.value = '';
  currentPage.value = 1;
  // 加载默认数据（不搜索关键词，使用分页）
  loadUserData(value, '', 1, 50);
}

// 根据权限类型加载人员数据，支持远程搜索和分页
const loadUserData = async (
  type: DataPermissionType,
  keyword: string = '',
  page: number = 1,
  pageSize: number = 50,
): Promise<void> => {
  loading.value = true;
  try {
    let response;
    switch (type) {
      case DATA_PERMISSION.AGENT_USER: {
        response = await getWarehouseAgentsApi({
          keyword,
          status: true,
          page,
          page_size: pageSize,
        });
        if (response && response.items) {
          sourceData.value = response.items.map((item: any) => ({
            key: item.id,
            title:
              item.name ||
              item.nickname ||
              item.username ||
              `${$t('@ai-assistants.agent')}${item.id}`,
            description: item.email || '',
          }));
          total.value = response.total || 0;
        } else {
          sourceData.value = [];
          total.value = 0;
        }
        break;
      }
      case DATA_PERMISSION.ALL_EMPLOYEE:
      case DATA_PERMISSION.PAYMENT: {
        response = await getWarehouseUsersApi({
          keyword,
          status: true,
          page,
          page_size: pageSize,
        });
        if (response && response.items) {
          sourceData.value = response.items.map(
            (item: any): DataSourceItem => ({
              key: item.id,
              title:
                item.nickname ||
                item.username ||
                item.email ||
                `${$t('@ai-assistants.customer')}${item.id}`,
              description: item.email || '',
            }),
          );
          total.value = response.total || 0;
        } else {
          sourceData.value = [];
          total.value = 0;
        }
        break;
      }
      case DATA_PERMISSION.CRM_USER: {
        response = await getWarehouseCrmUsersApi({
          keyword,
          status: true,
          page,
          page_size: pageSize,
        });
        if (response && response.items) {
          sourceData.value = response.items.map((item: any) => ({
            key: item.id,
            title:
              item.nickname ||
              item.username ||
              item.email ||
              `${$t('@ai-assistants.crmUser')}${item.id}`,
            description: item.email || '',
          }));
          total.value = response.total || 0;
        } else {
          sourceData.value = [];
          total.value = 0;
        }
        break;
      }
      // No default
    }

    // 初始化已选人员
    switch (type) {
      case DATA_PERMISSION.AGENT_USER: {
        targetKeys.value = selectedAgents.value.map((item) => item.id);
        break;
      }
      case DATA_PERMISSION.ALL_EMPLOYEE:
      case DATA_PERMISSION.PAYMENT: {
        targetKeys.value = selectedEmployees.value.map((item) => item.id);
        break;
      }
      case DATA_PERMISSION.CRM_USER: {
        targetKeys.value = selectedCrmUsers.value.map((item) => item.id);
        break;
      }
      // No default
    }
  } catch {
    sourceData.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

// 远程搜索处理（使用防抖）
const handleSearch = (value: string): void => {
  // 清除之前的定时器
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value);
  }

  // 设置新的定时器，防抖处理
  searchDebounceTimer.value = setTimeout(() => {
    searchQuery.value = value;
    currentPage.value = 1;
    loadUserData(dataPermission.value, value, 1, 50);
  }, 300);
};

// 选择变化处理
const handleSelectChange = (selectedKeys: string[]): void => {
  targetKeys.value = selectedKeys;
  dataPermissionValues.value = selectedKeys;

  switch (dataPermission.value) {
    case DATA_PERMISSION.AGENT_USER: {
      selectedAgents.value = sourceData.value
        .filter((item) => selectedKeys.includes(item.key))
        .map((item): UserInfo => ({ id: item.key, name: item.title }));

      break;
    }
    case DATA_PERMISSION.ALL_EMPLOYEE:
    case DATA_PERMISSION.PAYMENT: {
      selectedEmployees.value = sourceData.value
        .filter((item) => selectedKeys.includes(item.key))
        .map((item): UserInfo => ({ id: item.key, name: item.title }));

      break;
    }
    case DATA_PERMISSION.CRM_USER: {
      selectedCrmUsers.value = sourceData.value
        .filter((item) => selectedKeys.includes(item.key))
        .map((item): UserInfo => ({ id: item.key, name: item.title }));

      break;
    }
    // No default
  }
};

// 关闭模拟测试弹窗
function closeMockTraining(): void {
  emit('update:open', false);
  selectedEmployees.value = [];
  selectedAgents.value = [];
  selectedCrmUsers.value = [];
  dataPermissionValues.value = [];
  targetKeys.value = [];
}

// 验证并显示提示
function validateBeforeTest(): boolean {
  if (targetKeys.value.length === 0) {
    message.warning($t('@ai-assistants.pleaseSelectUserFirst'));
    return false;
  }
  if (!dataTimeValue.value || dataTimeValue.value < 1) {
    message.warning($t('@ai-assistants.pleaseEnterValidTimeValue'));
    return false;
  }
  return true;
}
</script>

<template>
  <Modal
    v-model:open="mockTrainingVisible"
    :title="$t('@ai-assistants.mockTraining')"
    width="900px"
    :footer="null"
    @cancel="closeMockTraining"
  >
    <div class="training-container" style="padding: 24px">
      <!-- 条件选择面板 -->
      <div class="mb-6">
        <div>
          <!-- 数据权限范围 -->
          <ARow class="mb-4">
            <ACol :span="4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ $t('@ai-assistants.dataPermissionRange') }} <span class="text-red-500">*</span>
              </label>
            </ACol>
            <ACol :span="20">
              <div class="flex flex-col items-center">
                <select
                  v-model="dataPermission"
                  @change="
                    (e: Event) =>
                      handleDataPermissionTypeChange(
                        (e.target as HTMLSelectElement).value as DataPermissionType,
                      )
                  "
                  class="w-full rounded-md border border-gray-300 py-2 px-3 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option :value="RiskType.ALL_EMPLOYEE">
                    {{ $t('@ai-assistants.customer') }}
                  </option>
                  <option :value="RiskType.AGENT_USER">{{ $t('@ai-assistants.agent') }}</option>
                  <option :value="RiskType.CRM_USER">{{ $t('@ai-assistants.crmUser') }}</option>
                  <option :value="RiskType.PAYMENT">{{ $t('@ai-assistants.paymentUser') }}</option>
                </select>
              </div>
            </ACol>
          </ARow>

          <!-- 客户/代理选择 -->
          <ARow class="mb-4">
            <ACol :span="4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                {{
                  dataPermission === DATA_PERMISSION.ALL_EMPLOYEE
                    ? $t('@ai-assistants.customer')
                    : $t('@ai-assistants.agent')
                }}
                <span class="text-red-500">*</span>
              </label>
            </ACol>
            <ACol :span="20">
              <a-select
                v-model:value="targetKeys"
                mode="multiple"
                :placeholder="
                  dataPermission === DATA_PERMISSION.ALL_EMPLOYEE
                    ? $t('@ai-assistants.pleaseSelectCustomerOrSearch')
                    : $t('@ai-assistants.pleaseSelectAgentOrSearch')
                "
                :loading="loading"
                :show-search="true"
                :filter-option="false"
                :not-found-content="
                  loading
                    ? $t('@ai-assistants.searching')
                    : searchQuery
                      ? $t('@ai-assistants.noSearchResult')
                      : $t('@ai-assistants.pleaseInputKeywordToSearch')
                "
                style="width: 100%"
                @search="handleSearch"
                @change="handleSelectChange"
              >
                <a-select-option v-for="item in sourceData" :key="item.key" :value="item.key">
                  {{ item.title }}
                </a-select-option>
              </a-select>
            </ACol>
          </ARow>

          <!-- 数据时间范围 -->
          <ARow class="mb-4">
            <ACol :span="4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ $t('@ai-assistants.dataTimeRange') }} <span class="text-red-500">*</span>
              </label>
            </ACol>
            <ACol :span="20">
              <div class="flex items-center">
                <div style="width: 360px">
                  <select
                    v-model="dataTimeRangeType"
                    class="w-full rounded-md border border-gray-300 py-2 px-3 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="day">{{ $t('@ai-assistants.byDay') }}</option>
                    <option value="month">{{ $t('@ai-assistants.byMonth') }}</option>
                    <option value="quarter">{{ $t('@ai-assistants.byQuarter') }}</option>
                    <option value="year">{{ $t('@ai-assistants.byYear') }}</option>
                  </select>
                </div>
                <div class="flex items-center ml-10" style="width: 360px">
                  <input
                    type="number"
                    v-model="dataTimeValue"
                    min="1"
                    max="100"
                    class="w-full rounded-md border border-gray-300 py-2 px-3 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <div class="ml-2 text-gray-600 w-1/5">{{ getTimeUnitLabel() }}</div>
                </div>
              </div>
            </ACol>
          </ARow>
        </div>

        <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div class="mb-2">
            <span class="font-medium text-gray-700">{{ $t('@ai-assistants.testTip') }}:</span>
          </div>
          <div class="text-sm text-gray-600 mb-2">
            <span class="text-red-500">*</span> {{ $t('@ai-assistants.requiredFieldsTip') }}
          </div>
          <div v-if="canStartTest" class="text-sm text-green-600">
            <svg class="inline-block w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
            {{ $t('@ai-assistants.currentTestQuestion') }}: {{ askContent }}
          </div>
          <div v-else class="text-sm text-gray-500">
            {{ $t('@ai-assistants.completeConfigTip') }}
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="mt-6 flex justify-end space-x-3 px-6 pb-4">
      <AiAction v-if="canStartTest" :ai="aiConfig" base-url="https://client.ai1center.com">
        <button
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!canStartTest"
          @click="validateBeforeTest"
        >
          {{ $t('@ai-assistants.startMockTest') }}
        </button>
      </AiAction>
      <button
        v-else
        class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled
      >
        {{ $t('@ai-assistants.startMockTest') }}
      </button>
      <button
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        @click="closeMockTraining"
      >
        {{ $t('views.common.close') }}
      </button>
    </div>
  </Modal>
</template>

<style scoped>
.training-container {
  max-height: 70vh;
  overflow-y: auto;
}

/* 自定义滚动条 */
.training-container::-webkit-scrollbar {
  width: 6px;
}

.training-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.training-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.training-container::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>
