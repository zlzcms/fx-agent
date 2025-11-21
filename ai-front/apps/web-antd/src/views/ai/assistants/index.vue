<script setup lang="ts">
import type { AIAssistant, AIAssistantParams, UpdateAIAssistantParams } from '#/api';

import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { createIconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { getAIAssistantListApi, getAllAssistantTypesApi, updateAIAssistantApi } from '#/api';
import CustomTabs from '#/components/CustomTabs.vue';

const AndroidOutlined = createIconifyIcon('ant-design:android-outlined');

const loading = ref({
  tabs: false,
  list: false,
  enable: false,
  disable: false,
  template: false,
  cancelTemplate: false,
  createAssistant: false,
  search: false,
});

let searchTimer: null | ReturnType<typeof setTimeout> = null;

const debounce = (fn: Function, delay: number) => {
  return (...args: any[]) => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      fn(...args);
      searchTimer = null;
    }, delay);
  };
};

const tabTabs = ref<any[]>([]);
const activeTab = ref('');
const onTabChange = (key: string) => {
  activeTab.value = key;
  listQuery({ page: 1, size: 10, name: '', assistant_type_id: key });
};

const handleSearch = debounce((value: string) => {
  loading.value.search = true;
  listQuery({
    page: 1,
    size: 10,
    name: value,
    assistant_type_id: activeTab.value,
  });
}, 500); // 500ms防抖延迟

const handleDateRangeChange = debounce((dates: any) => {
  if (!dates || dates.length !== 2) {
    return;
  }
  loading.value.search = true;

  const params: AIAssistantParams = {
    page: 1,
    size: 10,
    name: search.value,
    assistant_type_id: activeTab.value,
  };
  listQuery(params);
}, 500);

const handleStatusChange = debounce((value: string) => {
  loading.value.search = true;

  const params: AIAssistantParams = {
    page: 1,
    size: 10,
    name: search.value,
    assistant_type_id: activeTab.value,
  };

  if (value === 'enabled') {
    params.status = true;
  } else if (value === 'disabled') {
    params.status = false;
  }

  listQuery(params);
}, 500);

const search = ref('');
const dateRange = ref([]);
const status = ref();
const selectedAssistantId = ref<null | string>(null);
const statusOptions = computed(() => [
  { value: '', label: $t('@ai-assistants.allStatus') },
  { value: 'enabled', label: $t('@ai-assistants.enabled') },
  { value: 'disabled', label: $t('@ai-assistants.disabled') },
]);

const enableModalVisible = ref(false);
const disableModalVisible = ref(false);
const templateModalVisible = ref(false);
const cancelTemplateModalVisible = ref(false);
const createAssistantModalVisible = ref(false);
const currentAssistant = ref<any>(null);

const assistantCategories = ref<Array<{ key: string; label: string }>>([]);
const selectedCategory = ref('');

const templateAssistants = ref<AIAssistant[]>([]);

const filteredTemplateAssistants = computed(() => {
  return selectedCategory.value === $t('@ai-assistants.all') || selectedCategory.value === ''
    ? templateAssistants.value
    : templateAssistants.value.filter((item) => item.assistant_type_id === selectedCategory.value);
});

const getAvatarStyle = (assistantType: string) => {
  if (assistantType.includes('销售')) {
    return { backgroundColor: '#f0f7ff', color: '#1677ff' };
  } else if (assistantType.includes('风控')) {
    return { backgroundColor: '#fff1f0', color: '#ff4d4f' };
  } else if (assistantType.includes('财务')) {
    return { backgroundColor: '#f6ffed', color: '#52c41a' };
  } else if (assistantType.includes('管理')) {
    return { backgroundColor: '#e6f7ff', color: '#1890ff' };
  } else {
    return { backgroundColor: '#f9f0ff', color: '#722ed1' };
  }
};

const getTagColor = (type: string) => {
  if (type.includes('销售')) {
    return 'blue';
  } else if (type.includes('风控')) {
    return 'red';
  } else if (type.includes('财务')) {
    return 'green';
  } else if (type.includes('管理')) {
    return 'blue';
  } else {
    return 'purple';
  }
};

const showCreateAssistantModal = () => {
  loadTemplateAssistants();
  createAssistantModalVisible.value = true;
};

const quickCreateModalVisible = ref(false);
const quickCreateUserInput = ref('');
const isCreating = ref(false);
const showInputForm = ref(true);

const showQuickCreate = () => {
  quickCreateModalVisible.value = true;
  quickCreateUserInput.value = '';
  showInputForm.value = true;
  isCreating.value = false;
};

const showCustomCreate = async () => {
  createAssistantModalVisible.value = false;
  await new Promise((resolve) => setTimeout(resolve, 100));
  await router.push('/ai/assistants/add');
};

const useTemplateToCreate = async (templateData: any) => {
  createAssistantModalVisible.value = false;
  await new Promise((resolve) => setTimeout(resolve, 100));
  await router.push({
    path: '/ai/assistants/add',
    query: {
      from: 'template',
      templateId: templateData.id,
    },
  });
};

const confirmQuickCreate = async () => {
  if (!quickCreateUserInput.value.trim()) {
    message.warning($t('@ai-assistants.pleaseEnterAssistantDesc'));
    return;
  }

  try {
    showInputForm.value = false;
    isCreating.value = true;
    loading.value.createAssistant = true;

    quickCreateModalVisible.value = false;
    createAssistantModalVisible.value = false;
    await new Promise((resolve) => setTimeout(resolve, 100));

    await router.push({
      path: '/ai/assistants/add',
      query: {
        from: 'quickCreate',
        question: quickCreateUserInput.value,
      },
    });
  } catch (error) {
    console.error($t('@ai-assistants.jumpFailed'), error);
    message.error($t('@ai-assistants.jumpFailed'));
    quickCreateModalVisible.value = true;
  } finally {
    isCreating.value = false;
    loading.value.createAssistant = false;

    setTimeout(() => {
      showInputForm.value = true;
    }, 300);
  }
};

const onStatusChange = (checked: boolean, item: any) => {
  currentAssistant.value = item;
  if (checked) {
    enableModalVisible.value = true;
    item.status = false;
  } else {
    disableModalVisible.value = true;
    item.status = true;
  }
};

const confirmEnableAssistant = async () => {
  if (currentAssistant.value) {
    try {
      loading.value.enable = true;
      await updateAIAssistantApi(currentAssistant.value.id, {
        status: true,
      } as UpdateAIAssistantParams);
      currentAssistant.value.status = true;
      message.success($t('@ai-assistants.assistantEnabled'));
    } catch {
      message.error($t('@ai-assistants.enableFailed'));
    } finally {
      enableModalVisible.value = false;
      loading.value.enable = false;
    }
  }
};

const confirmDisableAssistant = async () => {
  if (currentAssistant.value) {
    try {
      loading.value.disable = true;
      await updateAIAssistantApi(currentAssistant.value.id, {
        status: false,
      } as UpdateAIAssistantParams);
      currentAssistant.value.status = false;
      message.success($t('@ai-assistants.assistantDisabled'));
    } catch {
      message.error($t('@ai-assistants.disableFailed'));
    } finally {
      disableModalVisible.value = false;
      loading.value.disable = false;
    }
  }
};

const onSetTemplate = (item: any) => {
  currentAssistant.value = item;
  templateModalVisible.value = true;
};

const confirmSetTemplate = async () => {
  if (currentAssistant.value) {
    try {
      loading.value.template = true;
      await updateAIAssistantApi(currentAssistant.value.id, {
        is_template: true,
      } as UpdateAIAssistantParams);
      message.success($t('@ai-assistants.setAsTemplateSuccess'));
      await listQuery({
        page: 1,
        size: 10,
        name: search.value,
        assistant_type_id: activeTab.value,
      });
    } catch {
      message.error($t('@ai-assistants.setAsFailed'));
    } finally {
      templateModalVisible.value = false;
      loading.value.template = false;
    }
  }
};

const loadAssistantTypeOptions = async () => {
  try {
    loading.value.tabs = true;
    const response = await getAllAssistantTypesApi();
    const tabs = response.map((type: any) => ({
      label: type.name,
      key: type.id,
    }));
    tabs.unshift({
      label: $t('@ai-assistants.all'),
      key: '',
    });
    return tabs;
  } catch (error) {
    console.error($t('@ai-assistants.loadAssistantTypesFailed'), error);
    message.error($t('@ai-assistants.loadAssistantTypesFailed'));
    return [];
  } finally {
    loading.value.tabs = false;
  }
};

const loadTemplateAssistants = async () => {
  try {
    const response = await getAIAssistantListApi({
      page: 1,
      size: 100,
      assistant_type_id: '', // 空字符串表示所有类型
      is_template: true,
    });

    templateAssistants.value = response.items;
  } catch (error) {
    console.error($t('@ai-assistants.loadTemplateAssistantsFailed'), error);
    message.error($t('@ai-assistants.loadTemplateAssistantsFailed'));
  }
};

const listQuery = async (params: AIAssistantParams) => {
  try {
    loading.value.list = true;
    const response = await getAIAssistantListApi(params);
    assistants.value = response.items;
  } catch (error) {
    console.error('获取AI助手列表失败:', error);
    message.error($t('@ai-assistants.getListFailed'));
  } finally {
    loading.value.list = false;
    loading.value.search = false; // 完成搜索加载状态
  }
};
// mock 数据
const assistants = ref<AIAssistant[]>([
  // {
  //   id: 1,
  //   name: '交易订单风险助理',
  //   author: 'jason',// TODO  api数据暂未提供
  //   description: '您是一位擅长分析客户交易订单数据风险的CRM助理，您是一位擅长分析客户交易订单数据风险...',
  //   assistant_type_display:"风控类型",
  //   tags: ['风控类型', '表格'], // 助手类型： assistant_type_display， 输出格式标签：output_format 表格：table 文档：document 表格/文档：both
  //   dataCount: 28888, // TODO api数据暂未提供
  //   status: true,
  //   auto: true,
  //   selected: false,
  //   avatar: 'https://joeschmoe.io/api/v1/random',
  // }
]);

const onCancelTemplate = (item: AIAssistant) => {
  currentAssistant.value = item;
  cancelTemplateModalVisible.value = true;
};

const confirmCancelTemplate = async () => {
  if (currentAssistant.value) {
    try {
      loading.value.cancelTemplate = true;
      await updateAIAssistantApi(currentAssistant.value.id, {
        is_template: false,
      } as UpdateAIAssistantParams);
      message.success($t('@ai-assistants.cancelTemplateSuccess'));
      await listQuery({
        page: 1,
        size: 10,
        name: search.value,
        assistant_type_id: activeTab.value,
      });
    } catch (error) {
      console.error($t('@ai-assistants.cancelTemplateFailed'), error);
      message.error($t('@ai-assistants.cancelTemplateFailed'));
    } finally {
      cancelTemplateModalVisible.value = false;
      loading.value.cancelTemplate = false;
      currentAssistant.value = null;
    }
  }
};
onMounted(async () => {
  try {
    loading.value.tabs = true;
    loading.value.list = true;

    const assistantTypeOptions = await loadAssistantTypeOptions();
    tabTabs.value = assistantTypeOptions;

    assistantCategories.value = assistantTypeOptions;
    selectedCategory.value = assistantTypeOptions[0]?.key || '';

    await listQuery({ page: 1, size: 10, name: '', assistant_type_id: '' });

    await loadTemplateAssistants();
  } catch (error) {
    console.error($t('@ai-assistants.loadDataFailed'), error);
    message.error($t('@ai-assistants.loadDataFailed'));
  } finally {
    loading.value.tabs = false;
  }
});
const router = useRouter();

function onViewEdit(item: AIAssistant) {
  router.push(`/ai/assistants/edit/${item.id}`);
}

watch(
  () => search.value,
  (newValue) => {
    handleSearch(newValue);
  },
);

watch(
  () => dateRange.value,
  (newValue) => {
    if (newValue) {
      handleDateRangeChange(newValue);
    }
  },
  { deep: true },
);

watch(
  () => status.value,
  (newValue) => {
    handleStatusChange(newValue);
  },
);
</script>

<template>
  <Page :auto-content-height="true">
    <div class="assistant-list-page bg-white">
      <div class="mb-2 flex items-center justify-between">
        <a-spin :spinning="loading.tabs" size="small">
          <CustomTabs :tabs="tabTabs" :active-tab="activeTab" @tab-change="onTabChange" />
        </a-spin>
      </div>
      <div
        class="flex items-center justify-between mb-4 gap-3 bg-white p-4 rounded-lg border border-gray-200"
      >
        <div class="flex items-center gap-3">
          <a-button type="primary" @click="showCreateAssistantModal">
            {{ $t('@ai-assistants.newAssistant') }}
          </a-button>
          <span class="text-gray-500">
            {{ $t('@ai-assistants.totalAssistants', { count: assistants.length }) }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <a-input
            v-model:value="search"
            :placeholder="$t('@ai-assistants.searchPlaceholder')"
            style="width: 200px"
            allow-clear
            :loading="loading.search"
          >
            <template #prefix>🔍</template>
          </a-input>
          <a-select
            v-model:value="status"
            style="width: 120px"
            class="ml-2"
            :options="statusOptions"
            allow-clear
            :placeholder="$t('@ai-assistants.allStatus')"
            :loading="loading.search"
          />
        </div>
      </div>

      <a-spin :spinning="loading.list" :tip="$t('@ai-assistants.loadingTip')">
        <div class="assistant-cards-container">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="item in assistants"
              :key="item.id"
              class="assistant-card border rounded-lg bg-white flex flex-col relative"
              :class="{ 'border-blue-500': selectedAssistantId === item.id }"
            >
              <!-- 卡片头部 -->
              <div class="card-header relative pt-4 px-4 pb-3">
                <a-tag :color="item.status ? 'green' : 'red'" class="absolute right-4 top-4">
                  {{ item.status ? $t('@ai-assistants.enabled') : $t('@ai-assistants.disabled') }}
                </a-tag>
                <div class="flex items-center gap-3 pr-20">
                  <a-avatar :src="item.avatar" :alt="item.name" class="size-12 flex-shrink-0">
                    {{ item.name?.charAt(0) || 'A' }}
                  </a-avatar>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-base text-gray-900 truncate">{{ item.name }}</div>
                  </div>
                </div>
              </div>

              <!-- 卡片内容区域 -->
              <div class="card-content flex-1 px-4 pb-3">
                <div class="text-sm text-gray-600 mb-4 mt-2 line-clamp-2 min-h-[40px]">
                  {{ item.description }}
                </div>

                <div class="flex flex-wrap gap-2 mb-4">
                  <a-tag :color="getTagColor(item.assistant_type_display || '')">
                    {{ item.assistant_type_display }}
                  </a-tag>
                </div>

                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-500">{{
                    $t('@ai-assistants.dataSourceCount', { count: item.data_sources?.length || 0 })
                  }}</span>
                  <a-switch
                    v-model:checked="item.status"
                    size="small"
                    @change="onStatusChange($event, item)"
                  />
                </div>
              </div>

              <!-- 卡片底部操作按钮 -->
              <div class="card-footer border-t border-gray-100 px-4 py-3 bg-gray-50 rounded-b-lg">
                <div class="card-actions flex justify-center gap-2">
                  <a-button
                    v-if="!item.is_template"
                    size="small"
                    class="flex-1"
                    @click="onSetTemplate(item)"
                  >
                    {{ $t('@ai-assistants.setAsTemplate') }}
                  </a-button>
                  <a-button v-else size="small" class="flex-1" @click="onCancelTemplate(item)">
                    {{ $t('@ai-assistants.cancelTemplate') }}
                  </a-button>
                  <a-button size="small" type="primary" class="flex-1" @click="onViewEdit(item)">
                    {{ $t('@ai-assistants.viewEdit') }}
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-spin>

      <a-modal
        v-model:visible="enableModalVisible"
        :closable="true"
        :footer="null"
        width="400px"
        class="confirm-modal"
      >
        <div class="flex items-start p-4">
          <div class="mr-3">
            <div class="flex justify-center items-center w-8 h-8 rounded-full bg-orange-50">
              <span class="text-orange-500 text-lg">!</span>
            </div>
          </div>
          <div class="flex-1">
            <div class="text-lg font-medium mb-2">{{ $t('@ai-assistants.confirmEnable') }}</div>
            <div class="text-gray-500 mb-4">{{ $t('@ai-assistants.confirmEnableDesc') }}</div>
            <div class="flex justify-end gap-2">
              <a-button @click="enableModalVisible = false">
                {{ $t('@ai-assistants.cancel') }}
              </a-button>
              <a-button type="primary" :loading="loading.enable" @click="confirmEnableAssistant">
                {{ $t('@ai-assistants.confirm') }}
              </a-button>
            </div>
          </div>
        </div>
      </a-modal>

      <a-modal
        v-model:visible="disableModalVisible"
        :closable="true"
        :footer="null"
        width="400px"
        class="confirm-modal"
      >
        <div class="flex items-start p-4">
          <div class="mr-3">
            <div class="flex justify-center items-center w-8 h-8 rounded-full bg-orange-50">
              <span class="text-orange-500 text-lg">!</span>
            </div>
          </div>
          <div class="flex-1">
            <div class="text-lg font-medium mb-2">{{ $t('@ai-assistants.confirmDisable') }}</div>
            <div class="text-gray-500 mb-4">{{ $t('@ai-assistants.confirmDisableDesc') }}</div>
            <div class="flex justify-end gap-2">
              <a-button @click="disableModalVisible = false">
                {{ $t('@ai-assistants.cancel') }}
              </a-button>
              <a-button
                type="primary"
                danger
                :loading="loading.disable"
                @click="confirmDisableAssistant"
              >
                {{ $t('@ai-assistants.disable') }}
              </a-button>
            </div>
          </div>
        </div>
      </a-modal>

      <a-modal
        v-model:visible="templateModalVisible"
        :closable="true"
        :footer="null"
        width="400px"
        class="confirm-modal"
      >
        <div class="flex items-start p-4">
          <div class="mr-3">
            <div class="flex justify-center items-center w-8 h-8 rounded-full bg-orange-50">
              <span class="text-orange-500 text-lg">!</span>
            </div>
          </div>
          <div class="flex-1">
            <div class="text-lg font-medium mb-2">
              {{ $t('@ai-assistants.confirmSetTemplate') }}
            </div>
            <div class="text-gray-500 mb-4">{{ $t('@ai-assistants.confirmSetTemplateDesc') }}</div>
            <div class="flex justify-end gap-2">
              <a-button @click="templateModalVisible = false">
                {{ $t('@ai-assistants.cancel') }}
              </a-button>
              <a-button type="primary" :loading="loading.template" @click="confirmSetTemplate">
                {{ $t('@ai-assistants.confirm') }}
              </a-button>
            </div>
          </div>
        </div>
      </a-modal>

      <a-modal
        v-model:visible="cancelTemplateModalVisible"
        :closable="true"
        :footer="null"
        width="400px"
        class="confirm-modal"
      >
        <div class="flex items-start p-4">
          <div class="mr-3">
            <div class="flex justify-center items-center w-8 h-8 rounded-full bg-orange-50">
              <span class="text-orange-500 text-lg">!</span>
            </div>
          </div>
          <div class="flex-1">
            <div class="text-lg font-medium mb-2">
              {{ $t('@ai-assistants.confirmCancelTemplate') }}
            </div>
            <div class="text-gray-500 mb-4">
              {{ $t('@ai-assistants.confirmCancelTemplateDesc') }}
            </div>
            <div class="flex justify-end gap-2">
              <a-button @click="cancelTemplateModalVisible = false">
                {{ $t('@ai-assistants.cancel') }}
              </a-button>
              <a-button
                type="primary"
                danger
                :loading="loading.cancelTemplate"
                @click="confirmCancelTemplate"
              >
                {{ $t('@ai-assistants.confirm') }}
              </a-button>
            </div>
          </div>
        </div>
      </a-modal>

      <a-modal
        v-model:visible="quickCreateModalVisible"
        :closable="showInputForm"
        :mask-closable="false"
        :keyboard="showInputForm"
        :footer="null"
        width="500px"
        :title="showInputForm ? $t('@ai-assistants.quickCreateAssistant') : ''"
        class="quick-create-modal"
      >
        <div v-if="showInputForm" class="p-4">
          <div class="mb-6">
            <div class="font-medium mb-2">{{ $t('@ai-assistants.describeYourAssistant') }}</div>
            <div class="text-gray-500 text-sm bg-gray-50 p-4 rounded-md mb-4">
              {{ $t('@ai-assistants.examplePrompt') }}
            </div>
            <a-textarea
              v-model:value="quickCreateUserInput"
              :rows="6"
              :placeholder="$t('@ai-assistants.assistantDescriptionPlaceholder')"
              class="w-full"
            />
          </div>
          <div class="flex justify-center">
            <a-button
              type="primary"
              class="w-full"
              @click="confirmQuickCreate"
              :loading="loading.createAssistant"
              :disabled="!quickCreateUserInput.trim()"
            >
              {{ $t('@ai-assistants.quickCreate') }}
            </a-button>
          </div>
        </div>

        <div v-else class="p-8 flex flex-col items-center justify-center">
          <a-spin size="large" />
          <div class="mt-4 text-lg">{{ $t('@ai-assistants.creating') }}</div>
        </div>
      </a-modal>

      <a-modal
        v-model:visible="createAssistantModalVisible"
        :closable="true"
        :footer="null"
        width="1000px"
        :title="$t('@ai-assistants.createAssistant')"
        class="create-assistant-modal"
      >
        <div class="flex p-4 border border-gray-200 rounded-lg">
          <div class="w-1/5 border-r pr-6 py-4">
            <div class="assistant-type-list">
              <div
                v-for="(category, index) in assistantCategories"
                :key="index"
                class="assistant-category-item py-4 px-5 mb-3 rounded-md cursor-pointer"
                :class="{
                  'bg-blue-50 text-blue-600 font-medium': selectedCategory === category.key,
                }"
                @click="selectedCategory = category.key"
              >
                {{ category.label }}
              </div>
            </div>
          </div>

          <div class="w-4/5 pl-8 py-4">
            <div class="flex items-center mb-8">
              <div
                class="flex items-center justify-around w-64 mr-8 border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all duration-300"
                @click="showQuickCreate"
              >
                <AndroidOutlined class="text-2xl text-blue-500" />
                <span>{{ $t('@ai-assistants.quickCreate') }}</span>
                <svg
                  viewBox="64 64 896 896"
                  focusable="false"
                  data-icon="plus-circle"
                  width="1.5em"
                  height="1.5em"
                  fill="#1677ff"
                  aria-hidden="true"
                >
                  <path
                    d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm192 472c0 4.4-3.6 8-8 8H544v152c0 4.4-3.6 8-8 8h-48c-4.4 0-8-3.6-8-8V544H328c-4.4 0-8-3.6-8-8v-48c0-4.4 3.6-8 8-8h152V328c0-4.4 3.6-8 8-8h48c4.4 0 8 3.6 8 8v152h152c4.4 0 8 3.6 8 8v48z"
                  />
                </svg>
              </div>
              <div
                class="flex items-center justify-around w-64 mr-8 border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all duration-300"
                @click="showCustomCreate"
              >
                <span>{{ $t('@ai-assistants.customCreate') }}</span>
                <svg
                  viewBox="64 64 896 896"
                  focusable="false"
                  data-icon="plus-circle"
                  width="1.5em"
                  height="1.5em"
                  fill="#1677ff"
                  aria-hidden="true"
                >
                  <path
                    d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm192 472c0 4.4-3.6 8-8 8H544v152c0 4.4-3.6 8-8 8h-48c-4.4 0-8-3.6-8-8V544H328c-4.4 0-8-3.6-8-8v-48c0-4.4 3.6-8 8-8h152V328c0-4.4 3.6-8 8-8h48c4.4 0 8 3.6 8 8v152h152c4.4 0 8 3.6 8 8v48z"
                  />
                </svg>
              </div>
            </div>

            <div
              class="grid grid-cols-2 gap-8 template-cards-container overflow-y-auto"
              style="height: 400px"
            >
              <div
                v-for="item in filteredTemplateAssistants"
                :key="item.id"
                class="assistant-template-card"
              >
                <div class="flex items-center mb-4">
                  <a-avatar
                    class="mr-3"
                    :size="46"
                    :style="getAvatarStyle(item.assistant_type_display || '其他')"
                  >
                    <template #icon>
                      {{ (item.assistant_type_display || '其他').charAt(0) }}
                    </template>
                  </a-avatar>
                  <div>
                    <div class="font-medium text-base">{{ item.name }}</div>
                  </div>
                </div>
                <div class="text-xs text-gray-600 mb-4 line-clamp-2">
                  {{ item.description }}
                </div>
                <div class="flex justify-between items-center mb-3">
                  <div class="flex gap-2">
                    <a-tag :color="getTagColor(item.assistant_type_display || '')">
                      {{ item.assistant_type_display }}
                    </a-tag>
                  </div>
                </div>
                <div class="flex justify-between items-center mb-4">
                  <div class="text-xs text-gray-400">
                    {{
                      $t('@ai-assistants.dataSourceCount', {
                        count: item.data_sources?.length || 0,
                      })
                    }}
                  </div>
                </div>
                <div class="mt-4">
                  <a-button type="primary" block @click="useTemplateToCreate(item)">
                    {{ $t('@ai-assistants.useThisTemplate') }}
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-modal>
    </div>
  </Page>
</template>

<style lang="scss" scoped>
.assistant-list-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
}

.assistant-cards-container {
  flex: 1;
  min-height: 400px;
  padding: 8px 0;
  overflow-y: auto;
  scrollbar-color: #d9d9d9 #f5f5f5;
  scrollbar-width: thin;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #d9d9d9;
    border-radius: 3px;

    &:hover {
      background-color: #bfbfbf;
    }
  }
}

.assistant-card {
  position: relative;
  height: 100%;
  min-height: 280px;
  box-shadow: 0 2px 8px 0 rgb(0 0 0 / 4%);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 16px 0 rgb(0 0 0 / 12%);
    transform: translateY(-2px);
  }

  .card-header {
    border-bottom: 1px solid rgb(0 0 0 / 6%);
  }

  .card-content {
    display: flex;
    flex-direction: column;
  }

  .card-footer {
    margin-top: auto;
    border-top: 1px solid rgb(0 0 0 / 6%);
    transition: background-color 0.2s;
  }

  &:hover .card-footer {
    background-color: #fafafa;
  }

  .card-actions {
    display: flex;
    gap: 8px;
    width: 100%;

    :deep(.ant-btn) {
      height: auto;
      min-height: 32px;
      padding: 4px 8px;
      line-height: 1.4;
      word-break: normal;
      overflow-wrap: anywhere;
      white-space: normal;
    }
  }
}

.assistant-card.selected {
  border-color: #1677ff;
}

.line-clamp-2 {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.confirm-modal {
  :deep(.ant-modal-content) {
    padding: 0;
  }
}

.create-assistant-modal {
  :deep(.ant-modal-content) {
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
  }

  :deep(.ant-modal-header) {
    margin-bottom: 30px;
  }

  .assistant-category-item {
    &:hover {
      background-color: #f0f7ff;
    }
  }

  .assistant-template-card {
    width: 100%;
    min-width: 320px;
    max-height: 280px;
    padding: 20px;
    border: 1px solid #e6e6e6;
    border-radius: 8px;
    transition: all 0.3s;

    &:hover {
      border-color: #1677ff;
      box-shadow: 0 4px 12px rgb(0 0 0 / 10%);
    }
  }

  .template-cards-container {
    scrollbar-color: #d9d9d9 #f5f5f5;
    scrollbar-width: thin;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f5f5f5;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background-color: #d9d9d9;
      border-radius: 3px;
    }
  }
}

.quick-create-modal {
  :deep(.ant-modal-content) {
    padding: 24px;
    border-radius: 8px;
  }

  :deep(.ant-modal-header) {
    margin-bottom: 16px;
  }

  :deep(.ant-modal-body) {
    min-height: 250px; // 确保高度一致，避免模态框大小变化
    padding: 0;
  }
}
</style>
