<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Card as ACard, Empty as AEmpty, Table as ATable } from 'ant-design-vue';

const loading = ref(false);
const tableColumns = ref<any[]>([]);
const tableDataSource = ref<any[]>([]);

const props = defineProps<{
  report?: any;
}>();

function loadReportTableData() {
  loading.value = true;

  try {
    // 优先使用ai_response.property_analysis数据
    if (props.report && props.report.ai_response && props.report.ai_response.property_analysis) {
      const reportData = props.report.ai_response.property_analysis || [];
      processReportData(reportData);
    } else if (props.report && props.report.report_table) {
      // 备用：使用report_table数据
      const reportData = props.report.report_table || [];
      processReportData(reportData);
    } else {
      // 如果没有数据，清空表格
      tableColumns.value = [];
      tableDataSource.value = [];
    }
  } catch (error) {
    console.error('获取报表数据失败:', error);
    // 清空表格
    tableColumns.value = [];
    tableDataSource.value = [];
  } finally {
    loading.value = false;
  }
}

function processReportData(reportData: any[]) {
  tableColumns.value = [];
  tableDataSource.value = [];

  if (reportData.length > 0) {
    const firstItem = reportData[0];
    if (firstItem && typeof firstItem === 'object' && !Array.isArray(firstItem)) {
      const allKeys = new Set<string>();
      reportData.forEach((item) => {
        Object.keys(item).forEach((key) => allKeys.add(key));
      });

      const headers = Array.from(allKeys);
      tableColumns.value = headers.map((header) => ({
        title: header,
        dataIndex: header,
        key: header,
        align: 'left',
        width: 150,
        ellipsis: true,
      }));

      tableDataSource.value = reportData.map((item, index) => ({
        key: index,
        ...item,
      }));
    } else {
      const headers = Object.keys(reportData[0]);
      tableColumns.value = headers.map((header) => ({
        title: header,
        dataIndex: header,
        key: header,
        align: typeof reportData[0][header] === 'number' ? 'right' : 'left',
        width: 150,
      }));

      tableDataSource.value = reportData.map((item, index) => ({
        key: index,
        ...item,
      }));
    }
  }
}

onMounted(() => {
  loadReportTableData();
});
</script>

<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- 数据表格 -->
    <a-card class="shadow-sm flex-1 flex flex-col overflow-hidden">
      <div class="flex-1 overflow-auto">
        <a-table
          :columns="tableColumns"
          :dataSource="tableDataSource"
          :loading="loading"
          :pagination="false"
          bordered
          size="middle"
          :scroll="{ x: 'max-content' }"
        >
          <template #bodyCell="{ column, record }">
            {{ column.key && record ? record[column.key] : '' }}
          </template>
          <template #emptyText>
            <a-empty description="暂无数据" />
          </template>
        </a-table>
      </div>
    </a-card>
  </div>
</template>
