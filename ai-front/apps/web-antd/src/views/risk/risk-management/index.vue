<script setup lang="ts">
import type { OnActionClickParams, VxeGridProps, VxeTableGridOptions } from '#/adapter/vxe-table';

import { onMounted, ref } from 'vue';

import { getRiskLevelColor } from '@vben/utils';

import {
  Button as AButton,
  Card as ACard,
  RangePicker as ARangePicker,
  Tag as ATag,
} from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { pagerPresets } from '#/configs/pager';

// 定义风险用户数据类型
interface RiskUserItem {
  id: string;
  name: string;
  riskLevel: {
    level: string;
    score: number;
  };
  time: string;
  status: string;
  description: string;
  tags: string[];
}

// 响应式数据
const activeTab = ref('all');
const activeRiskFilter = ref('');
const searchText = ref('');
const dateRange = ref();
// 已移除未使用的分页与加载状态变量，避免 ESLint 报错

// 数据统计
const statistics = {
  lowRisk: 30,
  highRisk: 10,
  processed: 10,
  pending: 30,
  noProcess: 5,
};

// Tab切换处理
const handleTabChange = (tab: string) => {
  activeTab.value = tab;
};

// 日期快捷选择
const handleDateSelect = (period: string) => {
  console.warn('选择日期:', period);
  // 这里可以根据选择的日期范围更新数据
};

// 风险等级筛选
const handleRiskFilter = (level: string) => {
  console.warn('风险等级:', level);
  // 这里可以根据风险等级筛选数据
};

// 表格列定义
const useColumns = (
  _onActionClick: (params: OnActionClickParams<RiskUserItem>) => void,
): VxeGridProps<RiskUserItem>['columns'] => [
  {
    type: 'seq',
    width: 60,
    title: '序号',
  },
  {
    field: 'id',
    title: '客户信息',
    width: 120,
    slots: {
      default: 'customerInfo',
    },
  },
  {
    field: 'riskLevel',
    title: '风险等级',
    width: 120,
    slots: {
      default: 'riskLevel',
    },
  },
  {
    field: 'time',
    title: '风险时间',
    width: 180,
  },
  {
    field: 'status',
    title: '风险检查',
    width: 120,
    slots: {
      default: 'riskStatus',
    },
  },
  {
    field: 'description',
    title: '推荐处理建议',
    minWidth: 300,
  },
  {
    field: 'operation',
    title: '处理状态',
    width: 100,
    fixed: 'right',
    slots: {
      default: 'operation',
    },
  },
  {
    field: 'actions',
    title: '操作',
    width: 120,
    fixed: 'right',
    slots: {
      default: 'actions',
    },
  },
];

// 模拟数据
const mockData: RiskUserItem[] = [
  {
    id: '001',
    name: 'Li Ping',
    riskLevel: { level: 'R1', score: 100 },
    time: '2025-04-28 14:08',
    status: '交易异常',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: ['高频交易'],
  },
  {
    id: '002',
    name: 'Li tt',
    riskLevel: { level: 'R1', score: 100 },
    time: '2025-04-28 14:08',
    status: '指标异常',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: ['高频交易', '指标异常'],
  },
  {
    id: '003',
    name: 'Li cc',
    riskLevel: { level: 'R2', score: 80 },
    time: '2025-04-28 14:08',
    status: '高频指标',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '004',
    name: 'Li nn',
    riskLevel: { level: 'R2', score: 80 },
    time: '2025-04-28 14:08',
    status: '反向交易',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '003',
    name: 'Li cc',
    riskLevel: { level: 'R2', score: 80 },
    time: '2025-04-28 14:08',
    status: '高频指标',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '004',
    name: 'Li nn',
    riskLevel: { level: 'R3', score: 60 },
    time: '2025-04-28 14:08',
    status: '反向交易',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '003',
    name: 'Li cc',
    riskLevel: { level: 'R3', score: 60 },
    time: '2025-04-28 14:08',
    status: '高频指标',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '004',
    name: 'Li nn',
    riskLevel: { level: 'R3', score: 60 },
    time: '2025-04-28 14:08',
    status: '反向交易',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: [],
  },
  {
    id: '004',
    name: 'Li nn',
    riskLevel: { level: 'R4', score: 60 },
    time: '2025-04-28 14:08',
    status: '风向交易',
    description: '联系客户确认交易人本人操作/活跃用户并及时跟进代表',
    tags: ['监控订单'],
  },
];

// 处理表格操作
function onActionClick({ code, row }: OnActionClickParams<RiskUserItem>) {
  if (code === 'view') {
    console.warn('查看详情', row);
  } else if (code === 'process') {
    console.warn('处理', row);
  }
}

// 表格配置
const gridOptions: VxeTableGridOptions<RiskUserItem> = {
  rowConfig: {
    keyField: 'id',
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  columns: useColumns(onActionClick),
  data: mockData,
  pagerConfig: pagerPresets.standard,
};

const formOptions = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: '查询',
  },
};

// 使用vxe表格
const [Grid] = useVbenVxeGrid({ formOptions, gridOptions });

// 已移除未使用的函数 getProcessStatusColor，避免 ESLint 报错

// 组件挂载时加载数据
onMounted(() => {
  console.warn('组件已挂载');
});
</script>

<template>
  <div class="flex h-full flex-col bg-gray-50 p-6">
    <!-- 时间选择 -->
    <div class="mb-4 flex">
      <AButton class="mr-2" @click="handleDateSelect('today')">昨日</AButton>
      <AButton class="mr-2" @click="handleDateSelect('week')">近一周</AButton>
      <AButton class="mr-2" @click="handleDateSelect('month')">近一月</AButton>
      <ARangePicker v-model:value="dateRange" :placeholder="['开始日期', '结束日期']" />
    </div>

    <!-- 数据统计卡片 -->
    <div class="grid grid-cols-5 gap-4 mb-4">
      <ACard class="shadow-sm">
        <div class="flex flex-col">
          <div class="text-gray-500 mb-2">极高风险</div>
          <div class="text-xl font-medium">{{ statistics.lowRisk }} 人</div>
        </div>
      </ACard>
      <ACard class="shadow-sm">
        <div class="flex flex-col">
          <div class="text-gray-500 mb-2">高风险</div>
          <div class="text-xl font-medium">{{ statistics.highRisk }} 人</div>
        </div>
      </ACard>
      <ACard class="shadow-sm">
        <div class="flex flex-col">
          <div class="text-gray-500 mb-2">已处理</div>
          <div class="text-xl font-medium">{{ statistics.processed }} 人</div>
        </div>
      </ACard>
      <ACard class="shadow-sm">
        <div class="flex flex-col">
          <div class="text-gray-500 mb-2">未处理</div>
          <div class="text-xl font-medium">{{ statistics.pending }} 人</div>
        </div>
      </ACard>
      <ACard class="shadow-sm">
        <div class="flex flex-col">
          <div class="text-gray-500 mb-2">无需处理</div>
          <div class="text-xl font-medium">{{ statistics.noProcess }} 人</div>
        </div>
      </ACard>
    </div>

    <!-- 处理状态标签页 -->
    <div class="mb-4">
      <div class="custom-tabs inline-flex border border-gray-200 rounded-md p-1">
        <button
          class="tab-item px-5 py-2 text-sm rounded-md mr-1 transition-colors"
          :class="{ active: activeTab === 'all' }"
          @click="handleTabChange('all')"
        >
          全部处理
        </button>
        <button
          class="tab-item px-5 py-2 text-sm rounded-md mr-1 transition-colors"
          :class="{ active: activeTab === 'processed' }"
          @click="handleTabChange('processed')"
        >
          已处理
        </button>
        <button
          class="tab-item px-5 py-2 text-sm rounded-md mr-1 transition-colors"
          :class="{ active: activeTab === 'pending' }"
          @click="handleTabChange('pending')"
        >
          未处理
        </button>
        <button
          class="tab-item px-5 py-2 text-sm rounded-md transition-colors"
          :class="{ active: activeTab === 'noprocess' }"
          @click="handleTabChange('noprocess')"
        >
          无需处理
        </button>
      </div>
    </div>

    <!-- 搜索和过滤卡片 -->
    <ACard class="mb-4 shadow-sm">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <span class="mr-2">显示30条（共2页）</span>
          <a-input-search v-model:value="searchText" placeholder="搜索" style="width: 200px" />
        </div>
        <div class="flex items-center">
          <span class="mr-2">金融等级</span>
          <AButton
            class="mr-1"
            :class="{ 'bg-blue-50': activeRiskFilter === 'R1' }"
            @click="handleRiskFilter('R1')"
          >
            R1
          </AButton>
          <AButton
            class="mr-1"
            :class="{ 'bg-blue-50': activeRiskFilter === 'R2' }"
            @click="handleRiskFilter('R2')"
          >
            R2
          </AButton>
          <AButton
            class="mr-1"
            :class="{ 'bg-blue-50': activeRiskFilter === 'R3' }"
            @click="handleRiskFilter('R3')"
          >
            R3
          </AButton>
          <AButton
            :class="{ 'bg-blue-50': activeRiskFilter === 'R4' }"
            @click="handleRiskFilter('R4')"
          >
            R4
          </AButton>
        </div>
      </div>
    </ACard>

    <!-- 表格 -->
    <div class="flex-1">
      <Grid>
        <template #customerInfo="{ row }">
          <div>
            <div class="font-medium">{{ row.id }}</div>
            <div class="text-gray-500">{{ row.name }}</div>
          </div>
        </template>

        <template #riskLevel="{ row }">
          <div>
            <ATag :color="getRiskLevelColor(row.riskLevel.level)">
              {{ row.riskLevel.level }}: {{ row.riskLevel.score }}分
            </ATag>
          </div>
        </template>

        <template #riskStatus="{ row }">
          <div>
            <ATag color="blue">{{ row.status }}</ATag>
            <div class="mt-1">
              <ATag v-for="tag in row.tags" :key="tag" color="blue" class="mr-1">
                {{ tag }}
              </ATag>
            </div>
          </div>
        </template>

        <template #operation="{ row }">
          <ATag v-if="row.id === '001'" color="blue">未处理</ATag>
          <ATag v-else-if="row.id === '002'" color="blue">未处理</ATag>
          <ATag v-else-if="row.id === '003'" color="green">已处理</ATag>
          <ATag v-else-if="row.id === '004'" color="green">已处理</ATag>
          <ATag v-else color="green">已处理</ATag>
        </template>

        <template #actions="{ row }">
          <div class="flex justify-center">
            <AButton v-if="row.id === '001' || row.id === '002'" type="link" class="text-red-500">
              未处理
            </AButton>
            <AButton v-else type="link" class="text-gray-500"> 已处理 </AButton>
            <AButton type="link" class="text-blue-500"> 详情 </AButton>
            <AButton type="link" class="text-blue-500"> 操作 </AButton>
          </div>
        </template>
      </Grid>
    </div>
  </div>
</template>

<style scoped>
/* 自定义Tab样式 */
.custom-tabs {
  border-radius: 6px;
}

.tab-item {
  font-size: 13px;
  font-weight: 400;
  color: #666;
  cursor: pointer;
  background-color: transparent;
  border: none;
}

.tab-item:hover {
  background-color: #f0f0f0;
}

.tab-item.active {
  color: #333;
  background-color: #f0f0f0;
}

/* 表格样式 */
:deep(.vxe-header--column) {
  background-color: #f9f9f9;
}

:deep(.vxe-body--column.col--fixed-right) {
  background-color: #fff;
  box-shadow: -2px 0 6px rgb(0 0 0 / 5%);
}

:deep(.vxe-body--column) {
  padding: 12px 8px;
}
</style>
