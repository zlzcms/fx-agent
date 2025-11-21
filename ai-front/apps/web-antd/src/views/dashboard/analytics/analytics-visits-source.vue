<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { $t } from '@vben/locales';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import { preferences } from '@vben/preferences';

import { getAnalyticsCountriesApi } from '#/api/dashboard';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// 国家名称中英文映射表
const countryNameMap: Record<string, { en: string; zh: string }> = {
  美国: { zh: '美国', en: 'United States' },
  中国: { zh: '中国', en: 'China' },
  俄罗斯: { zh: '俄罗斯', en: 'Russia' },
  波兰: { zh: '波兰', en: 'Poland' },
  荷兰: { zh: '荷兰', en: 'Netherlands' },
  新加坡: { zh: '新加坡', en: 'Singapore' },
  韩国: { zh: '韩国', en: 'South Korea' },
  伊朗: { zh: '伊朗', en: 'Iran' },
  日本: { zh: '日本', en: 'Japan' },
  德国: { zh: '德国', en: 'Germany' },
  法国: { zh: '法国', en: 'France' },
  英国: { zh: '英国', en: 'United Kingdom' },
  印度: { zh: '印度', en: 'India' },
  巴西: { zh: '巴西', en: 'Brazil' },
  加拿大: { zh: '加拿大', en: 'Canada' },
  澳大利亚: { zh: '澳大利亚', en: 'Australia' },
  意大利: { zh: '意大利', en: 'Italy' },
  西班牙: { zh: '西班牙', en: 'Spain' },
  墨西哥: { zh: '墨西哥', en: 'Mexico' },
  印度尼西亚: { zh: '印度尼西亚', en: 'Indonesia' },
  土耳其: { zh: '土耳其', en: 'Turkey' },
  泰国: { zh: '泰国', en: 'Thailand' },
  越南: { zh: '越南', en: 'Vietnam' },
  菲律宾: { zh: '菲律宾', en: 'Philippines' },
  马来西亚: { zh: '马来西亚', en: 'Malaysia' },
  阿根廷: { zh: '阿根廷', en: 'Argentina' },
  南非: { zh: '南非', en: 'South Africa' },
  埃及: { zh: '埃及', en: 'Egypt' },
  沙特阿拉伯: { zh: '沙特阿拉伯', en: 'Saudi Arabia' },
  阿联酋: { zh: '阿联酋', en: 'United Arab Emirates' },
};

// 加载国家统计数据
const loadCountriesData = async () => {
  try {
    const data = await getAnalyticsCountriesApi();

    // 获取当前语言环境
    const currentLocale = preferences.app.locale;
    const isZh = currentLocale === 'zh-CN';

    // 转换数据中的名称
    const translatedData = data.map((item: { name: string; value: number }) => {
      // 处理空值或None
      if (!item.name || item.name === 'None' || item.name === '未知' || item.name.trim() === '') {
        return {
          ...item,
          name: $t('views.dashboard.analytics.unknown'),
        };
      }

      // 查找国家名称映射
      const countryInfo = countryNameMap[item.name];
      if (countryInfo) {
        // 根据当前语言返回对应名称
        return {
          ...item,
          name: isZh ? countryInfo.zh : countryInfo.en,
        };
      }

      // 如果没有映射，保持原样（可能是英文或其他语言的国家名）
      return item;
    });

    renderEcharts({
      legend: {
        bottom: '2%',
        left: 'center',
      },
      series: [
        {
          animationDelay() {
            return Math.random() * 100;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          avoidLabelOverlap: false,
          data: translatedData,
          emphasis: {
            label: {
              fontSize: '12',
              fontWeight: 'bold',
              show: true,
            },
          },
          itemStyle: {
            borderRadius: 10,
            borderWidth: 2,
          },
          label: {
            position: 'center',
            show: false,
          },
          labelLine: {
            show: false,
          },
          name: $t('views.dashboard.analytics.countryStatistics'),
          radius: ['40%', '65%'],
          type: 'pie',
        },
      ],
      tooltip: {
        trigger: 'item',
      },
    });
  } catch (error) {
    console.error('Failed to load countries data:', error);
    // 使用默认数据
    renderEcharts({
      legend: {
        bottom: '2%',
        left: 'center',
      },
      series: [
        {
          animationDelay() {
            return Math.random() * 100;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          avoidLabelOverlap: false,
          data: [{ name: $t('views.dashboard.analytics.unknown'), value: 0 }],
          emphasis: {
            label: {
              fontSize: '12',
              fontWeight: 'bold',
              show: true,
            },
          },
          itemStyle: {
            borderRadius: 10,
            borderWidth: 2,
          },
          label: {
            position: 'center',
            show: false,
          },
          labelLine: {
            show: false,
          },
          name: $t('views.dashboard.analytics.countryStatistics'),
          radius: ['40%', '65%'],
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
  loadCountriesData();
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
