<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { $t } from '@vben/locales';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { getAnalyticsAIStatsApi } from '#/api/dashboard';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// AI统计数据名称映射（后端返回的中文 -> 国际化key）
const aiStatsNameMap: Record<string, string> = {
  助理报告: 'views.dashboard.analytics.assistantReport',
  风控报告: 'views.dashboard.analytics.riskReport',
  训练日志: 'views.dashboard.analytics.trainingLog',
};

// 加载AI统计数据
const loadAIStatsData = async () => {
  try {
    let data = await getAnalyticsAIStatsApi();

    // 验证数据格式
    if (!data || !Array.isArray(data)) {
      console.warn('AI stats data is not an array:', data);
      data = [];
    }

    // 转换数据中的名称
    const translatedData = data.map((item: { name: string; value: number }) => ({
      ...item,
      name: aiStatsNameMap[item.name] ? $t(aiStatsNameMap[item.name] as any) : item.name,
    }));

    renderEcharts({
      series: [
        {
          animationDelay() {
            return Math.random() * 400;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          center: ['50%', '50%'],
          data: translatedData.sort((a, b) => {
            return a.value - b.value;
          }),
          name: $t('views.dashboard.analytics.aiStatistics'),
          radius: '80%',
          roseType: 'radius',
          type: 'pie',
        },
      ],
      tooltip: {
        trigger: 'item',
      },
    });
  } catch (error) {
    console.error('Failed to load AI stats data:', error);
    // 使用默认数据
    renderEcharts({
      series: [
        {
          animationDelay() {
            return Math.random() * 400;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          center: ['50%', '50%'],
          data: [
            { name: $t('views.dashboard.analytics.assistantReport'), value: 0 },
            { name: $t('views.dashboard.analytics.riskReport'), value: 0 },
            { name: $t('views.dashboard.analytics.trainingLog'), value: 0 },
          ].sort((a, b) => {
            return a.value - b.value;
          }),
          name: $t('views.dashboard.analytics.aiStatistics'),
          radius: '80%',
          roseType: 'radius',
          type: 'pie',
        },
      ],
      tooltip: {
        trigger: 'item',
      },
    });
  }
};

onMounted(() => {
  loadAIStatsData();
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
