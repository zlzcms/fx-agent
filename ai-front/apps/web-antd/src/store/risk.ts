import type { RiskTag, RiskLevel } from '#/api/risk';

import { ref } from 'vue';
import { defineStore } from 'pinia';
import { getAllRiskTagsApi, getAllRiskLevelsApi } from '#/api/risk';

export const useRiskStore = defineStore('risk', () => {
  const riskTags = ref<RiskTag[]>([]);
  const riskTagsLoaded = ref(false);
  const riskTagsLoading = ref(false);

  const riskLevels = ref<RiskLevel[]>([]);
  const riskLevelsLoaded = ref(false);
  const riskLevelsLoading = ref(false);

  // 获取风控标签（带缓存）
  async function fetchRiskTags(forceRefresh = false): Promise<RiskTag[]> {
    // 如果已加载且不强制刷新，直接返回缓存数据
    if (!forceRefresh && riskTagsLoaded.value) {
      return riskTags.value;
    }

    // 如果正在加载，等待完成
    if (riskTagsLoading.value) {
      return new Promise((resolve) => {
        const timer = setInterval(() => {
          if (!riskTagsLoading.value) {
            clearInterval(timer);
            resolve(riskTags.value);
          }
        }, 100);
      });
    }

    try {
      riskTagsLoading.value = true;
      const tags = await getAllRiskTagsApi();
      riskTags.value = tags;
      riskTagsLoaded.value = true;
      return tags;
    } finally {
      riskTagsLoading.value = false;
    }
  }

  // 获取风控等级（带缓存）
  async function fetchRiskLevels(forceRefresh = false): Promise<RiskLevel[]> {
    // 如果已加载且不强制刷新，直接返回缓存数据
    if (!forceRefresh && riskLevelsLoaded.value) {
      return riskLevels.value;
    }

    // 如果正在加载，等待完成
    if (riskLevelsLoading.value) {
      return new Promise((resolve) => {
        const timer = setInterval(() => {
          if (!riskLevelsLoading.value) {
            clearInterval(timer);
            resolve(riskLevels.value);
          }
        }, 100);
      });
    }

    try {
      riskLevelsLoading.value = true;
      const levels = await getAllRiskLevelsApi();
      riskLevels.value = levels;
      riskLevelsLoaded.value = true;
      return levels;
    } finally {
      riskLevelsLoading.value = false;
    }
  }

  // 获取标签映射表
  function getRiskTagMap(): Record<string, string> {
    return riskTags.value.reduce((map: Record<string, string>, tag: RiskTag) => {
      map[tag.id] = tag.name;
      return map;
    }, {});
  }

  // 获取等级映射表
  function getRiskLevelMap(): Record<string, string> {
    return riskLevels.value.reduce((map: Record<string, string>, level: RiskLevel) => {
      map[level.id] = level.name;
      return map;
    }, {});
  }

  // 清除缓存
  function clearCache() {
    riskTags.value = [];
    riskTagsLoaded.value = false;
    riskLevels.value = [];
    riskLevelsLoaded.value = false;
  }

  // 重置状态
  function $reset() {
    clearCache();
    riskTagsLoading.value = false;
    riskLevelsLoading.value = false;
  }

  return {
    riskTags,
    riskTagsLoaded,
    riskTagsLoading,
    riskLevels,
    riskLevelsLoaded,
    riskLevelsLoading,
    fetchRiskTags,
    fetchRiskLevels,
    getRiskTagMap,
    getRiskLevelMap,
    clearCache,
    $reset,
  };
});