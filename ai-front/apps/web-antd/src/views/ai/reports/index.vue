<script setup lang="ts">
import type { ReportConfig } from './report-data';

import type { AiAssistantReportLog } from '#/api/ai_assistant_report_log';

import { ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
import { $t } from '@vben/locales';

import Detail from './detail.vue';
import ReportList from './list.vue';

// 报告配置
const reportConfig: ReportConfig = {
  title: $t('@reports.title'),
  i18nPrefix: '@reports',
  reportType: 'ai_assistant',
};

// 当前选中的报告
const currentReport = ref<AiAssistantReportLog | null>(null);

// 使用vben Modal
const [Modal, modalApi] = useVbenModal({
  destroyOnClose: true,
  onClosed() {
    currentReport.value = null;
  },
});

// 查看详情
const handleViewDetail = (report: AiAssistantReportLog) => {
  currentReport.value = report;
  modalApi.setData({ report });
  modalApi.open();
};
</script>

<template>
  <Page auto-content-height>
    <ReportList :report-config="reportConfig" @view-detail="handleViewDetail" key="list" />

    <Modal
      :title="$t('@reports.reportDetail')"
      class="!w-[90%] !max-w-[1200px] !min-h-[600px]"
      content-class="!min-h-[500px]"
      :footer="false"
    >
      <Detail v-if="currentReport" :report="currentReport as any" />
    </Modal>
  </Page>
</template>

<style scoped></style>
