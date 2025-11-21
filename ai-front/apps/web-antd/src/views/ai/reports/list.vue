<script setup lang="ts">
import type { ReportConfig } from './report-data';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { AiAssistantReportLog } from '#/api/ai_assistant_report_log';

import { $t } from '@vben/locales';

import { Tag as ATag } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getAiAssistantReportLogsApi } from '#/api/ai_assistant_report_log';

// 导入共享配置
import { createFormOptions, createGridOptions, getScoreColor } from './report-data';

// 定义Props
interface Props {
  reportConfig: ReportConfig;
}

const props = defineProps<Props>();

// 定义事件
const emit = defineEmits<{
  viewDetail: [report: AiAssistantReportLog];
}>();

// 操作处理函数
function onActionClick({ code, row }: { code: string; row: AiAssistantReportLog }) {
  switch (code) {
    case 'view': {
      emit('viewDetail', row);
      break;
    }
  }
}

// 表单配置
const formOptions = createFormOptions(props.reportConfig.i18nPrefix);

// 表格配置
const gridOptions: VxeTableGridOptions = {
  ...createGridOptions(props.reportConfig.i18nPrefix),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        try {
          // 处理日期范围参数
          const processedFormValues = { ...formValues };
          if (processedFormValues.dateRange && Array.isArray(processedFormValues.dateRange)) {
            const startDate = processedFormValues.dateRange[0];
            const endDate = processedFormValues.dateRange[1];
            if (startDate && typeof startDate.format === 'function') {
              processedFormValues.start_time = startDate.format('YYYY-MM-DDTHH:mm:ss');
            }
            if (endDate && typeof endDate.format === 'function') {
              processedFormValues.end_time = endDate.format('YYYY-MM-DDTHH:mm:ss');
            }
            delete processedFormValues.dateRange;
          }

          const params = {
            page: page.currentPage,
            size: page.pageSize,
            ...processedFormValues,
          };

          const response = await getAiAssistantReportLogsApi(params);

          const processedItems =
            response.items?.map((item: AiAssistantReportLog) => {
              // 尝试从多个可能的字段获取报告内容
              const analyticalReport = item.report_document || item.report_result || '';

              // 生成报告摘要（限制50字符）
              const generateSummary = (reportText: string) => {
                if (!reportText || reportText.trim() === '') return $t('@reports.noContent');
                const cleanText = reportText.replaceAll(/[\n\r\t]/g, ' ').trim();
                return cleanText.length > 50 ? `${cleanText.slice(0, 50)}...` : cleanText;
              };

              // 计算用户数量 - member_ids是JSON字符串格式
              let user_count = 1;
              if (item.member_ids) {
                try {
                  const memberIdsArray = JSON.parse(item.member_ids);
                  user_count = Array.isArray(memberIdsArray) ? memberIdsArray.length : 1;
                } catch (error) {
                  console.warn($t('@reports.parseError'), error);
                  user_count = 1;
                }
              }

              return {
                ...item,
                user_count,
                summary: generateSummary(analyticalReport),
              };
            }) || [];

          return {
            items: processedItems,
            total: response.total || 0,
          };
        } catch (error) {
          console.error($t('@reports.fetchError'), error);
          return {
            items: [],
            total: 0,
          };
        }
      },
    },
  },
};

// 使用vxe表格
const [Grid] = useVbenVxeGrid({ formOptions, gridOptions });
</script>

<template>
  <Grid>
    <!-- 报告评分插槽 -->
    <template #reportScore="{ row }">
      <ATag :color="getScoreColor(row.report_score)">
        {{ $t('@reports.scorePoints', { score: (row.report_score * 100).toFixed(1) }) }}
      </ATag>
    </template>

    <!-- 操作插槽 -->
    <template #action="{ row }">
      <a @click="onActionClick({ code: 'view', row })" class="text-blue-500 hover:text-blue-700">
        {{ $t('@reports.viewDetail') }}
      </a>
    </template>
  </Grid>
</template>

<style scoped>
/* 表格样式优化 */
:deep(.vxe-table .vxe-cell) {
  padding: 8px 6px !important;
  line-height: 1.4 !important;
  vertical-align: top !important;
  white-space: normal !important;
}

:deep(.vxe-table .vxe-cell--content) {
  word-break: break-all;
  word-wrap: break-word;
}
</style>
