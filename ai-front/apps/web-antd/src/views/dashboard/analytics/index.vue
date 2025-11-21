<script lang="ts" setup>
import type { AnalysisOverviewItem } from '@vben/common-ui';
import type { TabOption } from '@vben/types';

import { markRaw, onMounted, ref } from 'vue';

import { AnalysisChartCard, AnalysisChartsTabs, AnalysisOverview } from '@vben/common-ui';
import { createIconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import { getAnalyticsOverviewApi } from '#/api/dashboard';

import AnalyticsTrends from './analytics-trends.vue';
import AnalyticsVisitsSales from './analytics-visits-sales.vue';
import AnalyticsVisitsSource from './analytics-visits-source.vue';
import AnalyticsVisits from './analytics-visits.vue';

const overviewItems = ref<AnalysisOverviewItem[]>([]);

// 创建符合语义的图标
const UserIcon = markRaw(createIconifyIcon('lucide:users'));
const MessageIcon = markRaw(createIconifyIcon('lucide:message-circle'));
const FileTextIcon = markRaw(createIconifyIcon('lucide:file-text'));
const ShieldIcon = markRaw(createIconifyIcon('lucide:shield-alert'));

const chartTabs: TabOption[] = [
  {
    label: $t('views.dashboard.analytics.trafficTrends'),
    value: 'trends',
  },
  {
    label: $t('views.dashboard.analytics.monthlyVisits'),
    value: 'visits',
  },
];

// 加载概览数据
const loadOverviewData = async () => {
  try {
    const data = await getAnalyticsOverviewApi();

    // 验证数据格式
    if (!data || typeof data !== 'object') {
      console.warn('Overview data is not an object:', data);
      throw new Error('Invalid data format');
    }

    overviewItems.value = [
      {
        icon: UserIcon,
        iconColor: '#1890ff',
        title: $t('views.dashboard.analytics.userCount'),
        totalTitle: $t('views.dashboard.analytics.totalUserCount'),
        totalValue: data.userCount?.totalValue || 0,
        value: data.userCount?.value || 0,
      },
      {
        icon: MessageIcon,
        iconColor: '#52c41a',
        title: $t('views.dashboard.analytics.visitCount'),
        totalTitle: $t('views.dashboard.analytics.totalVisitCount'),
        totalValue: data.chatCount?.totalValue || 0,
        value: data.chatCount?.value || 0,
      },
      {
        icon: FileTextIcon,
        iconColor: '#fa8c16',
        title: $t('views.dashboard.analytics.downloadCount'),
        totalTitle: $t('views.dashboard.analytics.totalDownloadCount'),
        totalValue: data.reportCount?.totalValue || 0,
        value: data.reportCount?.value || 0,
      },
      {
        icon: ShieldIcon,
        iconColor: '#f5222d',
        title: $t('views.dashboard.analytics.usageCount'),
        totalTitle: $t('views.dashboard.analytics.totalUsageCount'),
        totalValue: data.riskCount?.totalValue || 0,
        value: data.riskCount?.value || 0,
      },
    ];
  } catch (error) {
    console.error('Failed to load overview data:', error);
    // 使用默认数据
    overviewItems.value = [
      {
        icon: UserIcon,
        iconColor: '#1890ff',
        title: $t('views.dashboard.analytics.userCount'),
        totalTitle: $t('views.dashboard.analytics.totalUserCount'),
        totalValue: 0,
        value: 0,
      },
      {
        icon: MessageIcon,
        iconColor: '#52c41a',
        title: $t('views.dashboard.analytics.visitCount'),
        totalTitle: $t('views.dashboard.analytics.totalVisitCount'),
        totalValue: 0,
        value: 0,
      },
      {
        icon: FileTextIcon,
        iconColor: '#fa8c16',
        title: $t('views.dashboard.analytics.downloadCount'),
        totalTitle: $t('views.dashboard.analytics.totalDownloadCount'),
        totalValue: 0,
        value: 0,
      },
      {
        icon: ShieldIcon,
        iconColor: '#f5222d',
        title: $t('views.dashboard.analytics.usageCount'),
        totalTitle: $t('views.dashboard.analytics.totalUsageCount'),
        totalValue: 0,
        value: 0,
      },
    ];
  }
};

onMounted(() => {
  loadOverviewData();
});
</script>

<template>
  <div class="p-5">
    <AnalysisOverview :items="overviewItems" />
    <AnalysisChartsTabs :tabs="chartTabs" class="mt-5">
      <template #trends>
        <AnalyticsTrends />
      </template>
      <template #visits>
        <AnalyticsVisits />
      </template>
    </AnalysisChartsTabs>

    <div class="mt-5 w-full md:flex">
      <!-- <AnalysisChartCard class="mt-5 md:mr-4 md:mt-0 md:w-1/3" :title="$t('views.dashboard.analytics.visitQuantity')">
        <AnalyticsVisitsData />
      </AnalysisChartCard> -->
      <AnalysisChartCard
        class="mt-5 md:mr-4 md:mt-0 md:w-1/2"
        :title="$t('views.dashboard.analytics.visitSource')"
      >
        <AnalyticsVisitsSource />
      </AnalysisChartCard>
      <AnalysisChartCard
        class="mt-5 md:mt-0 md:w-1/2"
        :title="$t('views.dashboard.analytics.aiStats')"
      >
        <AnalyticsVisitsSales />
      </AnalysisChartCard>
    </div>
  </div>
</template>
