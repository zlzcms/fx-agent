<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { $t } from '@vben/locales';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { getAnalyticsTrendsApi } from '#/api/dashboard';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// 加载趋势数据
const loadTrendsData = async () => {
  try {
    const data = await getAnalyticsTrendsApi();

    // 验证数据格式
    if (!data || typeof data !== 'object') {
      console.warn('Trends data is not an object:', data);
      throw new Error('Invalid data format');
    }

    const hours = data.hours || [];
    const loginData = data.loginData || [];
    const operationData = data.operationData || [];

    // 获取当前小时，用于标记统计中的时间段
    const currentHour = new Date().getHours();

    renderEcharts({
      grid: {
        bottom: 0,
        containLabel: true,
        left: '1%',
        right: '1%',
        top: '15%',
      },
      legend: {
        data: [
          $t('views.dashboard.analytics.loginTrend'),
          $t('views.dashboard.analytics.operationTrend'),
        ],
        top: '5%',
      },
      series: [
        {
          areaStyle: {
            opacity: 0.3,
          },
          data: loginData,
          itemStyle: {
            color: '#1890ff',
          },
          lineStyle: {
            color: '#1890ff',
            width: 2,
          },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: {
              color: '#ccc',
              type: 'dashed',
              width: 1,
            },
            label: {
              show: true,
              position: 'end',
              formatter: $t('views.dashboard.analytics.counting'),
              fontSize: 12,
              color: '#999',
            },
            data: [
              {
                xAxis: currentHour,
              },
            ],
          },
          name: $t('views.dashboard.analytics.loginTrend'),
          smooth: true,
          type: 'line',
        },
        {
          areaStyle: {
            opacity: 0.3,
          },
          data: operationData,
          itemStyle: {
            color: '#52c41a',
          },
          lineStyle: {
            color: '#52c41a',
            width: 2,
          },
          name: $t('views.dashboard.analytics.operationTrend'),
          smooth: true,
          type: 'line',
        },
      ],
      tooltip: {
        axisPointer: {
          lineStyle: {
            color: '#666',
            width: 1,
          },
        },
        formatter: (params: any) => {
          const currentHour = new Date().getHours();
          let result = `<div style="margin-bottom: 4px;">${params[0].axisValue}</div>`;
          params.forEach((param: any) => {
            const hourIndex = hours.indexOf(param.axisValue);
            const isCurrentHour = hourIndex === currentHour;
            const suffix = isCurrentHour
              ? ` <span style="color:#999;font-size:12px;">(${$t('views.dashboard.analytics.counting')})</span>`
              : '';
            result += `<div style="margin: 2px 0;">
              <span style="display:inline-block;width:10px;height:10px;background-color:${param.color};border-radius:50%;margin-right:4px;"></span>
              ${param.seriesName}: ${param.value}${suffix}
            </div>`;
          });
          return result;
        },
        trigger: 'axis',
      },
      xAxis: {
        axisTick: {
          show: false,
        },
        boundaryGap: false,
        data: hours,
        splitLine: {
          lineStyle: {
            type: 'solid',
            width: 1,
          },
          show: true,
        },
        type: 'category',
      },
      yAxis: [
        {
          axisTick: {
            show: false,
          },
          max:
            loginData.length > 0 || operationData.length > 0
              ? Math.ceil(Math.max(...loginData, ...operationData) * 1.2) || 100
              : 100,
          splitArea: {
            show: true,
          },
          splitNumber: 4,
          type: 'value',
        },
      ],
    });
  } catch (error) {
    console.error('Failed to load trends data:', error);
    // 使用默认数据
    const currentHour = new Date().getHours();
    const defaultHours = Array.from({ length: 24 }).map(
      (_item, index) => `${index.toString().padStart(2, '0')}:00`,
    );
    const defaultData = Array.from({ length: 24 }).fill(0) as number[];

    renderEcharts({
      grid: {
        bottom: 0,
        containLabel: true,
        left: '1%',
        right: '1%',
        top: '15%',
      },
      legend: {
        data: [
          $t('views.dashboard.analytics.loginTrend'),
          $t('views.dashboard.analytics.operationTrend'),
        ],
        top: '5%',
      },
      series: [
        {
          areaStyle: {
            opacity: 0.3,
          },
          data: defaultData,
          itemStyle: {
            color: '#1890ff',
          },
          lineStyle: {
            color: '#1890ff',
            width: 2,
          },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: {
              color: '#ccc',
              type: 'dashed',
              width: 1,
            },
            label: {
              show: true,
              position: 'end',
              formatter: $t('views.dashboard.analytics.counting'),
              fontSize: 12,
              color: '#999',
            },
            data: [
              {
                xAxis: currentHour,
              },
            ],
          },
          name: $t('views.dashboard.analytics.loginTrend'),
          smooth: true,
          type: 'line',
        },
        {
          areaStyle: {
            opacity: 0.3,
          },
          data: defaultData,
          itemStyle: {
            color: '#52c41a',
          },
          lineStyle: {
            color: '#52c41a',
            width: 2,
          },
          name: $t('views.dashboard.analytics.operationTrend'),
          smooth: true,
          type: 'line',
        },
      ],
      tooltip: {
        axisPointer: {
          lineStyle: {
            color: '#666',
            width: 1,
          },
        },
        formatter: (params: any) => {
          const currentHour = new Date().getHours();
          let result = `<div style="margin-bottom: 4px;">${params[0].axisValue}</div>`;
          params.forEach((param: any) => {
            const hourIndex = defaultHours.indexOf(param.axisValue);
            const isCurrentHour = hourIndex === currentHour;
            const suffix = isCurrentHour
              ? ` <span style="color:#999;font-size:12px;">(${$t('views.dashboard.analytics.counting')})</span>`
              : '';
            result += `<div style="margin: 2px 0;">
              <span style="display:inline-block;width:10px;height:10px;background-color:${param.color};border-radius:50%;margin-right:4px;"></span>
              ${param.seriesName}: ${param.value}${suffix}
            </div>`;
          });
          return result;
        },
        trigger: 'axis',
      },
      xAxis: {
        axisTick: {
          show: false,
        },
        boundaryGap: false,
        data: defaultHours,
        splitLine: {
          lineStyle: {
            type: 'solid',
            width: 1,
          },
          show: true,
        },
        type: 'category',
      },
      yAxis: [
        {
          axisTick: {
            show: false,
          },
          max: 100,
          splitArea: {
            show: true,
          },
          splitNumber: 4,
          type: 'value',
        },
      ],
    });
  }
};

onMounted(() => {
  loadTrendsData();
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
