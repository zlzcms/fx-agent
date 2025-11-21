<script setup lang="ts">
// Type imports
import type { AgentItem, CrmUserItem, UserItem } from '#/api/user';

import { ref, watch } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Search } from '@vben/icons';

import { Input, message, Modal, Table } from 'ant-design-vue';

// API imports
import { RiskType } from '#/api/risk';
import {
  getWarehouseAgentDetailApi,
  getWarehouseAgentsApi,
  getWarehouseCrmUserDetailApi,
  getWarehouseCrmUsersApi,
  getWarehouseUserDetailApi,
  getWarehouseUsersApi,
} from '#/api/user';

const props = defineProps({
  modelValue: {
    type: String,
    default: RiskType.ALL_EMPLOYEE,
  },
  permissionValues: {
    type: Array as () => string[],
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'update:permissionValues', 'change']);

// Permission selection state
const permissionType = ref(props.modelValue || RiskType.ALL_EMPLOYEE);
const selectedPermissionValues = ref<string[]>(props.permissionValues || []);

// Modal visibility states
const employeeModalVisible = ref(false);
const crmUserModalVisible = ref(false);
const agentModalVisible = ref(false);

// Employee selection state
const employeeSearchKeyword = ref('');
const employeeList = ref<UserItem[]>([]);
const selectedEmployees = ref<Array<{ id: string; name: string }>>([]);
const employeeLoading = ref(false);
const employeeSelectedRowKeys = ref<(number | string)[]>([]);
const employeePagination = ref({
  total: 0,
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50'],
});

// CRM user selection state
const crmUserSearchKeyword = ref('');
const crmUserList = ref<CrmUserItem[]>([]);
const selectedCrmUsers = ref<Array<{ id: string; name: string }>>([]);
const crmUserLoading = ref(false);
const crmUserSelectedRowKeys = ref<(number | string)[]>([]);
const crmUserPagination = ref({
  total: 0,
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50'],
});

// Agent selection state
const agentSearchKeyword = ref('');
const agentList = ref<AgentItem[]>([]);
const selectedAgents = ref<Array<{ id: string; name: string }>>([]);
const agentLoading = ref(false);
const agentSelectedRowKeys = ref<(number | string)[]>([]);
const agentPagination = ref({
  total: 0,
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50'],
});

// Table column definitions
const employeeColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80,
  },
  {
    title: '昵称',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true,
  },
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
];

const crmUserColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80,
  },
  {
    title: '昵称',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true,
  },
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
];

const agentColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80,
  },
  {
    title: '代理商名称',
    dataIndex: 'username',
    key: 'username',
    ellipsis: true,
  },
  {
    title: '昵称',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    ellipsis: true,
    customRender: ({ text }: { text: string }) => text || '-',
  },
];

// Computed props for display
const permissionOptions = [
  { label: '全体员工', value: RiskType.ALL_EMPLOYEE },
  { label: 'CRM用户', value: RiskType.CRM_USER },
  { label: '代理商', value: RiskType.AGENT_USER },
];

const selectedOptions = ref<Array<{ label: string; value: string }>>([]);

// Watch for prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== permissionType.value) {
      permissionType.value = newValue;
    }
  },
);

watch(
  () => props.permissionValues,
  (newValue) => {
    if (JSON.stringify(newValue) !== JSON.stringify(selectedPermissionValues.value)) {
      selectedPermissionValues.value = [...newValue];
      updateSelectedOptions();
    }
  },
);

// Update local state when selection changes
watch(permissionType, (newType) => {
  emit('update:modelValue', newType);

  // Reset selections when changing permission type
  selectedPermissionValues.value = [];
  selectedOptions.value = [];
  emit('update:permissionValues', []);

  // Open appropriate modal based on selection
  switch (newType) {
    case RiskType.AGENT_USER: {
      agentModalVisible.value = true;
      fetchAgentList();

      break;
    }
    case RiskType.ALL_EMPLOYEE: {
      employeeModalVisible.value = true;
      fetchEmployeeList();

      break;
    }
    case RiskType.CRM_USER: {
      crmUserModalVisible.value = true;
      fetchCrmUserList();

      break;
    }
    // No default
  }

  emit('change', { type: newType, values: [] });
});

// 加载缺失的员工信息
async function loadMissingEmployees(ids: string[]) {
  if (!ids || ids.length === 0) return;
  const existingIds = new Set(employeeList.value.map((emp) => emp.id));
  const missingIds = ids.filter((id) => !existingIds.has(id));
  if (missingIds.length === 0) return;

  try {
    const promises = missingIds.map((id) => getWarehouseUserDetailApi(id).catch(() => null));
    const results = await Promise.all(promises);
    const newEmployees = results
      .filter((item): item is UserItem => item !== null)
      .map((user) => ({
        id: user.id,
        name: user.name || '',
        email: user.email || '',
        username: user.username || '',
      }));
    employeeList.value = [...employeeList.value, ...newEmployees];
  } catch (error) {
    console.error('Failed to load missing employees:', error);
  }
}

// 加载缺失的CRM用户信息
async function loadMissingCrmUsers(ids: string[]) {
  if (!ids || ids.length === 0) return;
  const existingIds = new Set(crmUserList.value.map((user) => user.id));
  const missingIds = ids.filter((id) => !existingIds.has(id));
  if (missingIds.length === 0) return;

  try {
    const promises = missingIds.map((id) => getWarehouseCrmUserDetailApi(id).catch(() => null));
    const results = await Promise.all(promises);
    const newUsers = results
      .filter((item): item is CrmUserItem => item !== null)
      .map((user) => ({
        id: user.id,
        name: user.name || '',
        email: user.email || '',
        username: user.username || '',
      }));
    crmUserList.value = [...crmUserList.value, ...newUsers];
  } catch (error) {
    console.error('Failed to load missing CRM users:', error);
  }
}

// 加载缺失的代理信息
async function loadMissingAgents(ids: string[]) {
  if (!ids || ids.length === 0) return;
  const existingIds = new Set(agentList.value.map((agent) => agent.id));
  const missingIds = ids.filter((id) => !existingIds.has(id));
  if (missingIds.length === 0) return;

  try {
    const promises = missingIds.map((id) => getWarehouseAgentDetailApi(id).catch(() => null));
    const results = await Promise.all(promises);
    const newAgents = results
      .filter((item): item is AgentItem => item !== null)
      .map((agent) => ({
        id: agent.id,
        name: agent.name || '',
        region: agent.region || '',
        contact_person: agent.contact_person || '',
        contact_phone: agent.contact_phone || '',
        status: agent.status,
        create_time: agent.create_time,
        last_login_time: agent.last_login_time,
      }));
    agentList.value = [...agentList.value, ...newAgents];
  } catch (error) {
    console.error('Failed to load missing agents:', error);
  }
}

// Update the selectedOptions display based on the current selection
async function updateSelectedOptions() {
  // 先加载缺失的用户信息
  if (selectedPermissionValues.value.length > 0) {
    switch (permissionType.value) {
      case RiskType.AGENT_USER: {
        await loadMissingAgents(selectedPermissionValues.value);
        break;
      }
      case RiskType.ALL_EMPLOYEE: {
        await loadMissingEmployees(selectedPermissionValues.value);
        break;
      }
      case RiskType.CRM_USER: {
        await loadMissingCrmUsers(selectedPermissionValues.value);
        break;
      }
      // No default
    }
  }

  // We need to update selected options based on the currently selected type
  // and available list data
  switch (permissionType.value) {
    case RiskType.AGENT_USER: {
      const options = agentList.value
        .filter((agent) => selectedPermissionValues.value.includes(agent.id))
        .map((agent) => ({
          label: agent.name || agent.contact_person || agent.contact_phone || '' || '未知代理商',
          value: agent.id,
        }));

      selectedOptions.value = options;
      selectedAgents.value = options.map((opt) => ({ id: opt.value, name: opt.label }));
      agentSelectedRowKeys.value = selectedPermissionValues.value;

      break;
    }
    case RiskType.ALL_EMPLOYEE: {
      const options = employeeList.value
        .filter((emp) => selectedPermissionValues.value.includes(emp.id))
        .map((emp) => ({
          label:
            emp.name || emp.username || (emp.email ? emp.email.split('@')[0] : '') || '未知用户',
          value: emp.id,
        }));

      selectedOptions.value = options;
      selectedEmployees.value = options.map((opt) => ({ id: opt.value, name: opt.label }));
      employeeSelectedRowKeys.value = selectedPermissionValues.value;

      break;
    }
    case RiskType.CRM_USER: {
      const options = crmUserList.value
        .filter((user) => selectedPermissionValues.value.includes(user.id))
        .map((user) => ({
          label:
            user.name ||
            user.username ||
            (user.email ? user.email.split('@')[0] : '') ||
            '未知用户',
          value: user.id,
        }));

      selectedOptions.value = options;
      selectedCrmUsers.value = options.map((opt) => ({ id: opt.value, name: opt.label }));
      crmUserSelectedRowKeys.value = selectedPermissionValues.value;

      break;
    }
    // No default
  }
}

// Employee functions
async function fetchEmployeeList(keyword = '', page = 1, pageSize = 10) {
  employeeLoading.value = true;
  try {
    const response = await getWarehouseUsersApi({
      keyword,
      status: true,
      page,
      page_size: pageSize,
    });

    if (response && response.items && response.items.length > 0) {
      employeeList.value = response.items.map((user) => ({
        id: user.id,
        name: user.name || '',
        email: user.email || '',
        username: user.username || '',
      }));

      // Update pagination info
      if (response.total !== undefined) {
        employeePagination.value = {
          ...employeePagination.value,
          total: response.total,
          current: response.page || page,
          // eslint-disable-next-line unicorn/explicit-length-check
          pageSize: response.size || pageSize,
        };
      }

      // Restore selection state
      employeeSelectedRowKeys.value = selectedPermissionValues.value;
      updateSelectedOptions();
    } else {
      employeeList.value = [];
    }
  } catch (error) {
    console.error('Failed to fetch employee list:', error);
    message.error('获取员工列表失败，请重试');
  } finally {
    employeeLoading.value = false;
  }
}

async function handleEmployeeSearch() {
  employeePagination.value.current = 1;
  await fetchEmployeeList(employeeSearchKeyword.value, 1, employeePagination.value.pageSize);
}

async function handleEmployeeTableChange(pagination: any) {
  if (
    pagination.current !== employeePagination.value.current ||
    pagination.pageSize !== employeePagination.value.pageSize
  ) {
    await fetchEmployeeList(employeeSearchKeyword.value, pagination.current, pagination.pageSize);
  }
}

function handleEmployeeSelectionChange(selectedRowKeys: (number | string)[]) {
  employeeSelectedRowKeys.value = selectedRowKeys;

  const newSelectedEmployees = employeeList.value
    .filter((emp) => selectedRowKeys.includes(emp.id))
    .map((emp) => ({
      id: emp.id,
      name: emp.name || emp.username || (emp.email ? emp.email.split('@')[0] : '') || '未知用户',
    }));

  selectedEmployees.value = newSelectedEmployees;

  // Update the selected options for display
  selectedOptions.value = newSelectedEmployees.map((emp) => ({
    label: emp.name,
    value: emp.id,
  }));

  // Update the model value
  selectedPermissionValues.value = selectedRowKeys as string[];
  emit('update:permissionValues', selectedPermissionValues.value);
}

// CRM user functions
async function fetchCrmUserList(keyword = '', page = 1, pageSize = 10) {
  crmUserLoading.value = true;
  try {
    const response = await getWarehouseCrmUsersApi({
      keyword,
      status: true,
      page,
      page_size: pageSize,
    });

    if (response && response.items && response.items.length > 0) {
      crmUserList.value = response.items.map((user) => ({
        id: user.id,
        name: user.name || '',
        email: user.email || '',
        username: user.username || '',
      }));

      // Update pagination info
      if (response.total !== undefined) {
        crmUserPagination.value = {
          ...crmUserPagination.value,
          total: response.total,
          current: response.page || page,
          // eslint-disable-next-line unicorn/explicit-length-check
          pageSize: response.size || pageSize,
        };
      }

      // Restore selection state
      crmUserSelectedRowKeys.value = selectedPermissionValues.value;
      updateSelectedOptions();
    } else {
      crmUserList.value = [];
    }
  } catch (error) {
    console.error('Failed to fetch CRM user list:', error);
    message.error('获取CRM用户列表失败，请重试');
  } finally {
    crmUserLoading.value = false;
  }
}

async function handleCrmUserSearch() {
  crmUserPagination.value.current = 1;
  await fetchCrmUserList(crmUserSearchKeyword.value, 1, crmUserPagination.value.pageSize);
}

async function handleCrmUserTableChange(pagination: any) {
  if (
    pagination.current !== crmUserPagination.value.current ||
    pagination.pageSize !== crmUserPagination.value.pageSize
  ) {
    await fetchCrmUserList(crmUserSearchKeyword.value, pagination.current, pagination.pageSize);
  }
}

function handleCrmUserSelectionChange(selectedRowKeys: (number | string)[]) {
  crmUserSelectedRowKeys.value = selectedRowKeys;

  const newSelectedCrmUsers = crmUserList.value
    .filter((user) => selectedRowKeys.includes(user.id))
    .map((user) => ({
      id: user.id,
      name:
        user.name || user.username || (user.email ? user.email.split('@')[0] : '') || '未知用户',
    }));

  selectedCrmUsers.value = newSelectedCrmUsers;

  // Update the selected options for display
  selectedOptions.value = newSelectedCrmUsers.map((user) => ({
    label: user.name,
    value: user.id,
  }));

  // Update the model value
  selectedPermissionValues.value = selectedRowKeys as string[];
  emit('update:permissionValues', selectedPermissionValues.value);
}

// Agent functions
async function fetchAgentList(keyword = '', page = 1, pageSize = 10) {
  agentLoading.value = true;
  try {
    const response = await getWarehouseAgentsApi({
      keyword,
      status: true,
      page,
      page_size: pageSize,
    });

    if (response && response.items && response.items.length > 0) {
      agentList.value = response.items.map((agent) => ({
        id: agent.id,
        name: agent.name || '',
        region: agent.region || '',
        contact_person: agent.contact_person || '',
        contact_phone: agent.contact_phone || '',
        status: agent.status,
        create_time: agent.create_time,
        last_login_time: agent.last_login_time,
      }));

      // Update pagination info
      if (response.total !== undefined) {
        agentPagination.value = {
          ...agentPagination.value,
          total: response.total,
          current: response.page || page,
          // eslint-disable-next-line unicorn/explicit-length-check
          pageSize: response.size || pageSize,
        };
      }

      // Restore selection state
      agentSelectedRowKeys.value = selectedPermissionValues.value;
      updateSelectedOptions();
    } else {
      agentList.value = [];
    }
  } catch (error) {
    console.error('Failed to fetch agent list:', error);
    message.error('获取代理商列表失败，请重试');
  } finally {
    agentLoading.value = false;
  }
}

async function handleAgentSearch() {
  agentPagination.value.current = 1;
  await fetchAgentList(agentSearchKeyword.value, 1, agentPagination.value.pageSize);
}

async function handleAgentTableChange(pagination: any) {
  if (
    pagination.current !== agentPagination.value.current ||
    pagination.pageSize !== agentPagination.value.pageSize
  ) {
    await fetchAgentList(agentSearchKeyword.value, pagination.current, pagination.pageSize);
  }
}

function handleAgentSelectionChange(selectedRowKeys: (number | string)[]) {
  agentSelectedRowKeys.value = selectedRowKeys;

  const newSelectedAgents = agentList.value
    .filter((agent) => selectedRowKeys.includes(agent.id))
    .map((agent) => ({
      id: agent.id,
      name: agent.name || agent.contact_person || agent.contact_phone || '' || '未知代理商',
    }));

  selectedAgents.value = newSelectedAgents;

  // Update the selected options for display
  selectedOptions.value = newSelectedAgents.map((agent) => ({
    label: agent.name,
    value: agent.id,
  }));

  // Update the model value
  selectedPermissionValues.value = selectedRowKeys as string[];
  emit('update:permissionValues', selectedPermissionValues.value);
}

// Public methods
defineExpose({
  // Expose methods to parent component if needed
  openEmployeeModal: () => {
    employeeModalVisible.value = true;
    fetchEmployeeList();
  },
  openCrmUserModal: () => {
    crmUserModalVisible.value = true;
    fetchCrmUserList();
  },
  openAgentModal: () => {
    agentModalVisible.value = true;
    fetchAgentList();
  },
});
</script>

<template>
  <div class="data-permission-selector">
    <div class="flex gap-4">
      <!-- Permission Type Selection -->
      <div class="flex-1">
        <select
          v-model="permissionType"
          class="form-select block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          :disabled="disabled"
        >
          <option v-for="option in permissionOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <!-- Permission Values Selection Display -->
      <div class="flex-1 flex items-center">
        <div v-if="selectedOptions.length > 0" class="flex flex-wrap gap-1">
          <div
            v-for="option in selectedOptions.slice(0, 3)"
            :key="option.value"
            class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-md flex items-center"
          >
            {{ option.label }}
          </div>
          <div
            v-if="selectedOptions.length > 3"
            class="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-md"
          >
            +{{ selectedOptions.length - 3 }}项
          </div>
        </div>
        <div v-else class="text-gray-500 text-sm">请选择具体范围</div>

        <button
          v-if="!disabled"
          class="ml-2 text-blue-600 hover:text-blue-800"
          @click="
            () => {
              if (permissionType === RiskType.ALL_EMPLOYEE) {
                employeeModalVisible = true;
                fetchEmployeeList();
              } else if (permissionType === RiskType.CRM_USER) {
                crmUserModalVisible = true;
                fetchCrmUserList();
              } else if (permissionType === RiskType.AGENT_USER) {
                agentModalVisible = true;
                fetchAgentList();
              }
            }
          "
        >
          选择
        </button>
      </div>
    </div>

    <!-- Employee Selection Modal -->
    <Modal
      v-model:open="employeeModalVisible"
      title="选择员工"
      width="700px"
      :footer="null"
      @cancel="employeeModalVisible = false"
    >
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Input
            v-model:value="employeeSearchKeyword"
            placeholder="搜索用户名/昵称/邮箱"
            allow-clear
            @press-enter="handleEmployeeSearch"
          >
            <template #prefix>
              <Search class="text-gray-400" />
            </template>
          </Input>
          <VbenButton type="primary" @click="handleEmployeeSearch">搜索</VbenButton>
        </div>
        <div class="text-sm text-gray-500">已选择 {{ employeeSelectedRowKeys.length }} 项</div>
      </div>

      <Table
        row-key="id"
        :loading="employeeLoading"
        :columns="employeeColumns"
        :data-source="employeeList"
        :row-selection="{
          selectedRowKeys: employeeSelectedRowKeys,
          onChange: handleEmployeeSelectionChange,
        }"
        :pagination="employeePagination"
        size="middle"
        bordered
        @change="handleEmployeeTableChange"
      />

      <div class="mt-4 flex justify-end gap-2">
        <VbenButton @click="employeeModalVisible = false">确定</VbenButton>
      </div>
    </Modal>

    <!-- CRM User Selection Modal -->
    <Modal
      v-model:open="crmUserModalVisible"
      title="选择CRM用户"
      width="700px"
      :footer="null"
      @cancel="crmUserModalVisible = false"
    >
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Input
            v-model:value="crmUserSearchKeyword"
            placeholder="搜索用户名/昵称/邮箱"
            allow-clear
            @press-enter="handleCrmUserSearch"
          >
            <template #prefix>
              <Search class="text-gray-400" />
            </template>
          </Input>
          <VbenButton type="primary" @click="handleCrmUserSearch">搜索</VbenButton>
        </div>
        <div class="text-sm text-gray-500">已选择 {{ crmUserSelectedRowKeys.length }} 项</div>
      </div>

      <Table
        row-key="id"
        :loading="crmUserLoading"
        :columns="crmUserColumns"
        :data-source="crmUserList"
        :row-selection="{
          selectedRowKeys: crmUserSelectedRowKeys,
          onChange: handleCrmUserSelectionChange,
        }"
        :pagination="crmUserPagination"
        size="middle"
        bordered
        @change="handleCrmUserTableChange"
      />

      <div class="mt-4 flex justify-end gap-2">
        <VbenButton @click="crmUserModalVisible = false">确定</VbenButton>
      </div>
    </Modal>

    <!-- Agent Selection Modal -->
    <Modal
      v-model:open="agentModalVisible"
      title="选择代理商"
      width="700px"
      :footer="null"
      @cancel="agentModalVisible = false"
    >
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Input
            v-model:value="agentSearchKeyword"
            placeholder="搜索代理商名称"
            allow-clear
            @press-enter="handleAgentSearch"
          >
            <template #prefix>
              <Search class="text-gray-400" />
            </template>
          </Input>
          <VbenButton type="primary" @click="handleAgentSearch">搜索</VbenButton>
        </div>
        <div class="text-sm text-gray-500">已选择 {{ agentSelectedRowKeys.length }} 项</div>
      </div>

      <Table
        row-key="id"
        :loading="agentLoading"
        :columns="agentColumns"
        :data-source="agentList"
        :row-selection="{
          selectedRowKeys: agentSelectedRowKeys,
          onChange: handleAgentSelectionChange,
        }"
        :pagination="agentPagination"
        size="middle"
        bordered
        @change="handleAgentTableChange"
      />

      <div class="mt-4 flex justify-end gap-2">
        <VbenButton @click="agentModalVisible = false">确定</VbenButton>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.data-permission-selector {
  width: 100%;
}
</style>
