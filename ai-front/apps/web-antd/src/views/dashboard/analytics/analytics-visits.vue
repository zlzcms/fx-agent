<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { $t } from '@vben/locales';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { getAnalyticsMonthlyApi } from '#/api/dashboard';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// 加载月使用量数据
const loadMonthlyData = async () => {
  try {
    const data = await getAnalyticsMonthlyApi();

    renderEcharts({
      grid: {
        bottom: 0,
        containLabel: true,
        left: '1%',
        right: '1%',
        top: '2 %',
      },
      series: [
        {
          barMaxWidth: 80,
          data: data.months,
          type: 'bar',
        },
      ],
      tooltip: {
        axisPointer: {
          lineStyle: {
            width: 1,
          },
        },
        trigger: 'axis',
      },
      xAxis: {
        data: Array.from({ length: 12 }).map(
          (_item, index) => `${index + 1}${$t('views.dashboard.analytics.month')}`,
        ),
        type: 'category',
      },
      yAxis: {
        max: Math.ceil(Math.max(...data.months) * 1.2),
        splitNumber: 4,
        type: 'value',
      },
    });
  } catch (error) {
    console.error('Failed to load monthly data:', error);
    // 使用默认数据
    renderEcharts({
      grid: {
        bottom: 0,
        containLabel: true,
        left: '1%',
        right: '1%',
        top: '2 %',
      },
      series: [
        {
          barMaxWidth: 80,
          data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          type: 'bar',
        },
      ],
      tooltip: {
        axisPointer: {
          lineStyle: {
            width: 1,
          },
        },
        trigger: 'axis',
      },
      xAxis: {
        data: Array.from({ length: 12 }).map(
          (_item, index) => `${index + 1}${$t('views.dashboard.analytics.month')}`,
        ),
        type: 'category',
      },
      yAxis: {
        max: 100,
        splitNumber: 4,
        type: 'value',
      },
    });
  }
};

onMounted(() => {
  loadMonthlyData();
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
