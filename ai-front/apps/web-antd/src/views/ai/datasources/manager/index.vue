<template>
    <Page>
      <div class="flex h-full flex-col">
      <!-- 顶部标签页 -->
      <div class="mb-4">
        <a-tabs v-model="activeTab">
          <a-tab-pane key="finance" tab="财务出入金处理" />
          <a-tab-pane key="user" tab="用户画像助理" />
        </a-tabs>
            </div>

      <!-- 搜索和筛选区域 -->
      <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-4">
          <a-input-search
            v-model="searchText"
            placeholder="搜索"
            style="width: 200px"
            @search="onSearch"
          />
          <a-range-picker
            v-model="dateRange"
            :placeholder="['开始日期', '结束日期']"
            @change="onDateChange"
          />
        </div>
        </div>

      <!-- 列表区域 -->
        <div class="flex-1">
          <a-table
          :data-source="tableData"
          :columns="columns"
            :loading="loading"
          :pagination="pagination"
          @change="handleTableChange"
          >
          <!-- 自定义列模板 -->
            <template #bodyCell="{ column, record }">
            <!-- 报告信息列 -->
            <template v-if="column.key === 'report'">
              <div class="flex items-center">
                <span class="text-lg mr-2">📄</span>
                <div>
                  <div class="font-medium">{{ record.title }}</div>
                  <div class="text-gray-500 text-sm">{{ record.type }}</div>
                </div>
                </div>
              </template>

            <!-- 评分列 -->
            <template v-if="column.key === 'score'">
              <a-tag :color="getScoreColor(record.score)">
                {{ record.score }}分
                </a-tag>
              </template>

            <!-- 概要总结列 -->
            <template v-if="column.key === 'summary'">
              <div class="text-sm">
                <div>1、{{ record.userCount }}位用户出入金异常</div>
                <div>2、出金({{ record.outCount }}人)，入金({{ record.inCount }}人)</div>
                <div>3、{{ record.description }}</div>
                </div>
              </template>

            <!-- 操作列 -->
            <template v-if="column.key === 'action'">
              <a @click="viewDetail(record)">查看详情</a>
            </template>
            </template>
          </a-table>
        </div>
      </div>
    </Page>
  </template>

  <script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
  import {
    Table as ATable,
  Tabs as ATabs,
  TabPane as ATabPane,
  Input as AInput,
    Tag as ATag,
  DatePicker as ADatePicker,
  message
  } from 'ant-design-vue';

  // 响应式数据
const activeTab = ref('finance');
const searchText = ref('');
const dateRange = ref();
  const loading = ref(false);
const tableData = ref([]);

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 49053,
  showSizeChanger: true,
  showQuickJumper: true,
});

  // 表格列配置
const columns = [
    {
    title: '报告信息',
    key: 'report',
    dataIndex: 'title',
  },
  {
    title: '条数',
    key: 'count',
    dataIndex: 'count',
    width: 100,
    },
    {
    title: '评分',
    key: 'score',
    dataIndex: 'score',
      width: 100,
    },
    {
    title: '生成时间',
    key: 'createTime',
    dataIndex: 'createTime',
    width: 180,
    },
  {
    title: '概要总结',
    key: 'summary',
    dataIndex: 'summary',
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
  },
];

// 获取评分标签颜色
function getScoreColor(score: number) {
  if (score >= 90) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
  }

// 搜索处理
function onSearch(value: string) {
  console.log('搜索:', value);
  loadTableData();
}

// 日期范围变化处理
function onDateChange(dates: any) {
  console.log('日期范围:', dates);
  loadTableData();
}

// 表格变化处理
function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  loadTableData();
}

// 查看详情
function viewDetail(record: any) {
  message.info('查看报告详情: ' + record.title);
  }

// 加载表格数据
function loadTableData() {
    loading.value = true;
  // 模拟异步加载数据
  setTimeout(() => {
    tableData.value = [
      {
        id: 1,
        title: '财务出入金报告',
        type: '表格/文当',
        count: 100,
        score: 88,
        createTime: '2025-04-28 14:08',
        userCount: 4,
        outCount: 2,
        inCount: 2,
        description: '出金频率高、入金金额较大',
      },
      // ... 更多数据
    ];
      loading.value = false;
  }, 500);
}

// 组件挂载时加载数据
onMounted(() => {
  loadTableData();
  });
  </script>

  <style scoped>
.ant-table-tbody > tr > td {
  padding: 12px 8px;
  }
  </style>
