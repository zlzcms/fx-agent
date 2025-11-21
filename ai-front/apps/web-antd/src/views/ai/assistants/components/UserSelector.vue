<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Search } from '@vben/icons';
import { $t } from '@vben/locales';

import { Input, message, Modal, Table } from 'ant-design-vue';

import { getWarehouseAgentsApi, getWarehouseCrmUsersApi, getWarehouseUsersApi } from '#/api/user';

const props = defineProps({
  modalVisible: {
    type: Boolean,
    default: false,
  },
  modalType: {
    type: String,
    default: 'employee', // employee, crm_user, agent
  },
  selectedItems: {
    type: Array,
    default: () => [],
  },
  selectionType: {
    type: String,
    default: 'checkbox', // checkbox or radio
    validator: (val: string) => ['checkbox', 'radio'].includes(val),
  },
});

const emit = defineEmits(['update:modalVisible', 'update:selectedItems', 'confirm', 'cancel']);

// 本地状态
const searchKeyword = ref('');
const itemList = ref<Array<any>>([]);
const loading = ref(false);
const selectedRowKeys = ref<string[]>([]);
const pagination = ref({
  total: 0,
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  pageSizeOptions: ['10', '20', '50'],
});

// 计算属性
const modalTitle = computed(() => {
  switch (props.modalType) {
    case 'agent': {
      return $t('@ai-assistants.selectAgent');
    }
    case 'crm_user': {
      return $t('@ai-assistants.selectCrmUser');
    }
    case 'employee': {
      return $t('@ai-assistants.selectEmployeeFirst');
    }
    default: {
      return $t('@ai-assistants.selectPerson');
    }
  }
});

const searchPlaceholder = computed(() => {
  switch (props.modalType) {
    case 'agent': {
      return $t('@ai-assistants.searchAgentName');
    }
    case 'crm_user': {
      return $t('@ai-assistants.searchUsernameNicknameEmail');
    }
    case 'employee': {
      return $t('@ai-assistants.searchUsernameNicknameEmail');
    }
    default: {
      return $t('@ai-assistants.search');
    }
  }
});

const columns = computed(() => {
  const commonColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
  ];

  // 根据类型返回不同的列定义
  if (props.modalType === 'employee' || props.modalType === 'crm_user') {
    return [
      ...commonColumns,
      {
        title: '昵称',
        dataIndex: 'nickname',
        key: 'nickname',
        ellipsis: true,
      },
      {
        title: '用户名',
        dataIndex: 'username',
        key: 'username',
        ellipsis: true,
        customRender: ({ text }: { text: any }) => text || '-',
      },
      {
        title: '邮箱',
        dataIndex: 'email',
        key: 'email',
        ellipsis: true,
        customRender: ({ text }: { text: any }) => text || '-',
      },
    ];
  } else if (props.modalType === 'agent') {
    return [
      ...commonColumns,
      {
        title: '代理商名称',
        dataIndex: 'username',
        key: 'username',
        ellipsis: true,
      },
      {
        title: '昵称',
        dataIndex: 'nickname',
        key: 'nickname',
        ellipsis: true,
        customRender: ({ text }: { text: any }) => text || '-',
      },
      {
        title: '邮箱',
        dataIndex: 'email',
        key: 'email',
        ellipsis: true,
        customRender: ({ text }: { text: any }) => text || '-',
      },
    ];
  }

  return commonColumns;
});

// 当modal可见或选中项改变时，初始化选中项
function initializeSelectedKeys() {
  selectedRowKeys.value = props.selectedItems.map((item: any) => item.id);
}

// 根据modal类型获取数据
async function fetchItems(
  keyword = searchKeyword.value,
  page = pagination.value.current,
  pageSize = pagination.value.pageSize,
) {
  loading.value = true;
  try {
    let response;

    // 根据类型调用不同的API
    switch (props.modalType) {
      case 'agent': {
        response = await getWarehouseAgentsApi({
          keyword,
          status: true,
          page,
          page_size: pageSize,
        });

        break;
      }
      case 'crm_user': {
        response = await getWarehouseCrmUsersApi({
          keyword,
          status: true,
          page,
          page_size: pageSize,
        });

        break;
      }
      case 'employee': {
        response = await getWarehouseUsersApi({ keyword, status: true, page, page_size: pageSize });

        break;
      }
      // No default
    }

    if (response && response.items && response.items.length > 0) {
      itemList.value = response.items.map((item) => ({
        id: item.id,
        name: item.name || '',
        email: (item as any).email || '',
        username: (item as any).username || '',
      }));

      // 更新分页信息
      if (response.total !== undefined) {
        pagination.value = {
          ...pagination.value,
          total: response.total,
          current: response.page || page,
          // eslint-disable-next-line unicorn/explicit-length-check
          pageSize: response.size || pageSize,
        };
      }
    } else {
      itemList.value = [];
      pagination.value.total = 0;
    }
  } catch (error) {
    console.error(`获取${modalTitle.value}列表失败:`, error);
    message.error(`获取${modalTitle.value}列表失败，请重试`);
    itemList.value = [];
  } finally {
    loading.value = false;
  }
}

// 处理搜索
function handleSearch() {
  pagination.value.current = 1;
  fetchItems(searchKeyword.value, 1, pagination.value.pageSize);
}

// 处理分页变化
function handleTableChange(paginationInfo: any) {
  if (
    paginationInfo.current !== pagination.value.current ||
    paginationInfo.pageSize !== pagination.value.pageSize
  ) {
    fetchItems(searchKeyword.value, paginationInfo.current, paginationInfo.pageSize);
  }
}

// 处理选择变化
function handleSelectionChange(newSelectedRowKeys: string[]) {
  // 如果是单选模式，确保只有一个选中的项
  if (props.selectionType === 'radio' && newSelectedRowKeys.length > 1) {
    // 仅保留最新选择的项
    newSelectedRowKeys = [newSelectedRowKeys[newSelectedRowKeys.length - 1]!];
  }

  selectedRowKeys.value = newSelectedRowKeys;

  // 更新选中项
  const newSelectedItems = itemList.value
    .filter((item) => newSelectedRowKeys.includes(item.id))
    .map((item) => ({
      id: item.id,
      name: item.name,
    }));

  emit('update:selectedItems', newSelectedItems);
}

// 确认选择
function confirmSelection() {
  emit('confirm', {
    type: props.modalType,
    items: props.selectedItems,
  });
  emit('update:modalVisible', false);
}

// 取消选择
function cancelSelection() {
  emit('cancel');
  emit('update:modalVisible', false);
}

// 监听modal可见性
watch(
  () => props.modalVisible,
  (visible) => {
    if (visible) {
      initializeSelectedKeys();
      fetchItems();
    }
  },
);

// 监听选中项
watch(
  () => props.selectedItems,
  () => {
    if (props.modalVisible) {
      initializeSelectedKeys();
    }
  },
  { deep: true },
);

// Expose methods
defineExpose({
  fetchItems,
  initializeSelectedKeys,
});
</script>

<template>
  <Modal
    :open="modalVisible"
    :title="modalTitle"
    width="700px"
    :footer="null"
    @cancel="cancelSelection"
  >
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Input
          v-model:value="searchKeyword"
          :placeholder="searchPlaceholder"
          allow-clear
          @press-enter="handleSearch"
        >
          <template #prefix>
            <Search class="text-gray-400" />
          </template>
        </Input>
        <VbenButton type="primary" @click="handleSearch">搜索</VbenButton>
      </div>
      <div class="text-sm text-gray-500">已选择 {{ selectedRowKeys.length }} 项</div>
    </div>

    <Table
      row-key="id"
      :loading="loading"
      :columns="columns"
      :data-source="itemList"
      :row-selection="{
        selectedRowKeys,
        onChange: (selectedRowKeys: any[]) => handleSelectionChange(selectedRowKeys as string[]),
        type: selectionType as any,
      }"
      :pagination="pagination"
      size="middle"
      bordered
      @change="handleTableChange"
    />

    <div class="mt-4 flex justify-end gap-2">
      <VbenButton @click="cancelSelection">取消</VbenButton>
      <VbenButton type="primary" @click="confirmSelection">确定</VbenButton>
    </div>
  </Modal>
</template>
