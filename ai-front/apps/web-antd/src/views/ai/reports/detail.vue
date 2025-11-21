<script setup lang="ts">
// 类型导入
import type { ReportData, TabType } from './types';

// Vue相关导入
import { ref } from 'vue';

import { $t } from '@vben/locales';
// 组件和工具导入
import { formatDate } from '@vben/utils';

// 子组件导入
import DocumentDetail from './document_detail.vue';
import TableDetail from './table_detail.vue';

// 定义Props
const props = defineProps<{
  report: ReportData;
}>();

// 响应式数据
const activeTab = ref<TabType>('doc');

// 事件处理
const handleTabChange = (tab: TabType) => {
  activeTab.value = tab;
};

// 工具函数：获取分析时间范围
const getAnalysisTime = (reportData: ReportData): string => {
  try {
    // 从prompt_data中获取数据时间范围信息
    if (reportData.prompt_data && typeof reportData.prompt_data === 'object') {
      const dataTimeRangeType = reportData.prompt_data.data_time_range_type;
      const dataTimeValue = reportData.prompt_data.data_time_value;

      if (dataTimeRangeType && dataTimeValue) {
        const unit = $t(`@reports.timeUnits.${dataTimeRangeType}`) || dataTimeRangeType;
        return $t('@reports.recentTime', { value: dataTimeValue, unit });
      }
    }

    // 如果没有时间范围信息，则显示报告创建时间
    const analysisTime =
      reportData.created_time ||
      reportData.assistant?.last_analysis_time ||
      reportData.updated_time;
    if (analysisTime) {
      const result = formatDate(analysisTime);
      return typeof result === 'string' ? result : String(analysisTime);
    }

    return $t('@reports.unknownTime');
  } catch (error) {
    console.warn($t('@reports.getAnalysisTimeError'), error);
    return $t('@reports.unknownTime');
  }
};

// 工具函数：格式化时间
const formatTime = (time: any): string => {
  if (!time) return $t('@reports.unknown');
  try {
    // 使用完整的日期时间格式
    const result = formatDate(time, 'YYYY-MM-DD HH:mm:ss');
    return typeof result === 'string' ? result : String(result);
  } catch {
    return String(time);
  }
};

// 工具函数：获取用户数量
const getUserCount = (reportData: ReportData): number => {
  // member_ids是JSON字符串格式，需要解析
  if (reportData.member_ids) {
    try {
      const memberIdsArray = JSON.parse(reportData.member_ids);
      return Array.isArray(memberIdsArray) ? memberIdsArray.length : 1;
    } catch (error) {
      console.warn($t('@reports.parseUserIdsError'), error);
    }
  }
  // 如果没有member_ids或解析失败，则使用ai_response中的user_count
  return reportData.ai_response?.user_count || 1;
};

// 工具函数：获取用户ID显示文本
const getUserIdsDisplay = (reportData: ReportData): string => {
  if (reportData.member_ids) {
    try {
      const memberIdsArray = JSON.parse(reportData.member_ids);
      if (Array.isArray(memberIdsArray)) {
        return memberIdsArray.join(', ');
      }
    } catch (error) {
      console.warn($t('@reports.parseUserIdsError'), error);
    }
  }
  return props.report.member_id?.toString() || $t('@reports.unknown');
};

// 工具函数：获取数据源名称
const getDataSourceNames = (reportData: ReportData): string => {
  try {
    // 从prompt_data中获取data_sources
    if (reportData.prompt_data && typeof reportData.prompt_data === 'object') {
      const dataSources = reportData.prompt_data.data_sources;
      if (Array.isArray(dataSources)) {
        const names = dataSources.map((source) => source.collection_name).filter(Boolean);
        return names.length > 0 ? names.join(', ') : $t('@reports.noDataSource');
      }
    }
    return $t('@reports.noDataSource');
  } catch (error) {
    console.warn($t('@reports.getDataSourceError'), error);
    return $t('@reports.noDataSource');
  }
};

// 工具函数：获取数据权限
const getDataPermission = (reportData: ReportData): string => {
  try {
    // 从prompt_data中获取data_permission
    if (reportData.prompt_data && typeof reportData.prompt_data === 'object') {
      return reportData.prompt_data.data_permission || $t('@reports.unknown');
    }
    return $t('@reports.unknown');
  } catch (error) {
    console.warn($t('@reports.getDataPermissionError'), error);
    return $t('@reports.unknown');
  }
};
</script>

<template>
  <div class="page-container">
    <div class="flex h-full flex-col bg-white p-2">
      <!-- 信息卡片 -->
      <div class="bg-white rounded-lg p-6 mb-6 flex-shrink-0">
        <!-- 基本信息网格 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- 基本信息 -->
          <div
            class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100 hover:shadow-md transition-all duration-300"
          >
            <div class="flex items-center mb-3">
              <div class="w-6 h-6 bg-blue-500 rounded-md flex items-center justify-center mr-2">
                <svg
                  class="w-3 h-3 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 class="text-base font-semibold text-gray-800">{{ $t('@reports.basicInfo') }}</h3>
            </div>
            <div class="space-y-2">
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.assistantName') }}</span>
                <span
                  class="font-medium text-gray-900 max-w-[120px] truncate"
                  :title="props.report.assistant?.name || $t('@reports.unknown')"
                  >{{ props.report.assistant?.name || $t('@reports.unknown') }}
                </span>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.subscriptionName') }}</span>
                <span
                  class="font-medium text-gray-900 max-w-[120px] truncate"
                  :title="props.report.subscription_name || $t('@reports.unknown')"
                  >{{ props.report.subscription_name || $t('@reports.unknown') }}
                </span>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.modelName') }}</span>
                <span
                  class="font-medium text-gray-900 max-w-[120px] truncate"
                  :title="props.report.model_name || $t('@reports.unknown')"
                  >{{ props.report.model_name || $t('@reports.unknown') }}
                </span>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.reportScore') }}</span>
                <div class="flex items-center">
                  <span class="font-medium text-blue-600 text-xs mr-1">
                    {{ (props.report.report_score * 100).toFixed(1) }}%
                  </span>
                  <div class="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-500"
                      :style="{ width: `${props.report.report_score * 100}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 分析信息 -->
          <div
            class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-100 hover:shadow-md transition-all duration-300"
          >
            <div class="flex items-center mb-3">
              <div class="w-6 h-6 bg-green-500 rounded-md flex items-center justify-center mr-2">
                <svg
                  class="w-3 h-3 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h3 class="text-base font-semibold text-gray-800">
                {{ $t('@reports.analysisInfo') }}
              </h3>
            </div>
            <div class="space-y-2">
              <div class="py-1.5 px-2 bg-white/60 rounded text-xs">
                <div class="flex justify-between items-start mb-1">
                  <span class="text-gray-600">{{ $t('@reports.dataSource') }}</span>
                </div>
                <div class="text-green-600 text-xs leading-relaxed break-words">
                  {{ getDataSourceNames(props.report) }}
                </div>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.userCount') }}</span>
                <div class="flex items-center">
                  <span class="font-medium text-green-600 text-xs mr-0.5">{{
                    getUserCount(props.report)
                  }}</span>
                  <span class="text-gray-500 text-xs">{{ $t('@reports.peopleUnit') }}</span>
                </div>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.dataPermission') }}</span>
                <span
                  class="font-medium text-gray-900 text-xs max-w-[120px] truncate"
                  :title="getDataPermission(props.report)"
                  >{{ getDataPermission(props.report) }}
                </span>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.analysisTimeRange') }}</span>
                <span
                  class="font-medium text-gray-900 text-xs max-w-[120px] truncate"
                  :title="getAnalysisTime(props.report)"
                  >{{ getAnalysisTime(props.report) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 报告信息 -->
          <div
            class="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-4 border border-purple-100 hover:shadow-md transition-all duration-300"
          >
            <div class="flex items-center mb-3">
              <div class="w-6 h-6 bg-purple-500 rounded-md flex items-center justify-center mr-2">
                <svg
                  class="w-3 h-3 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 class="text-base font-semibold text-gray-800">{{ $t('@reports.reportInfo') }}</h3>
            </div>
            <div class="space-y-2">
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.reportId') }}</span>
                <span
                  class="font-mono text-xs text-gray-700 whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]"
                  :title="String(props.report.id || $t('@reports.unknown'))"
                  >{{ props.report.id || $t('@reports.unknown') }}
                </span>
              </div>
              <div class="py-1.5 px-2 bg-white/60 rounded">
                <div class="flex justify-between items-center mb-0.5">
                  <span class="text-gray-600 text-xs">{{ $t('@reports.userId') }}</span>
                </div>
                <span
                  class="font-mono text-xs text-gray-700 break-all bg-gray-100 px-1.5 py-0.5 rounded block"
                  >{{ getUserIdsDisplay(props.report) }}
                </span>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.reportStatus') }}</span>
                <div class="flex items-center">
                  <div
                    class="w-1.5 h-1.5 rounded-full mr-1"
                    :class="props.report.report_status ? 'bg-green-400' : 'bg-orange-400'"
                  ></div>
                  <span
                    class="font-medium text-xs"
                    :class="props.report.report_status ? 'text-green-600' : 'text-orange-600'"
                  >
                    {{
                      props.report.report_status
                        ? $t('@reports.completed')
                        : $t('@reports.processing')
                    }}
                  </span>
                </div>
              </div>
              <div
                class="flex justify-between items-center py-1.5 px-2 bg-white/60 rounded text-xs"
              >
                <span class="text-gray-600">{{ $t('@reports.generationTime') }}</span>
                <span
                  class="font-medium text-gray-900 text-xs max-w-[120px] truncate"
                  :title="formatTime(props.report.created_time)"
                  >{{ formatTime(props.report.created_time) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 详细信息展开区域 -->
      </div>

      <!-- 标签页 -->
      <div class="bg-white rounded-lg shadow-sm mb-6 flex-shrink-0">
        <div class="flex border-b border-gray-200">
          <button
            class="px-6 py-3 text-sm font-medium transition-colors duration-200 border-b-2 focus:outline-none"
            :class="
              activeTab === 'doc'
                ? 'text-blue-600 border-blue-600 bg-blue-50'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
            "
            @click="handleTabChange('doc')"
          >
            {{ $t('@reports.doc') }}
          </button>
          <button
            class="px-6 py-3 text-sm font-medium transition-colors duration-200 border-b-2 focus:outline-none"
            :class="
              activeTab === 'table'
                ? 'text-blue-600 border-blue-600 bg-blue-50'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
            "
            @click="handleTabChange('table')"
          >
            {{ $t('@reports.table') }}
          </button>
          <button
            class="px-6 py-3 text-sm font-medium transition-colors duration-200 border-b-2 focus:outline-none"
            :class="
              activeTab === 'prompt'
                ? 'text-blue-600 border-blue-600 bg-blue-50'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
            "
            @click="handleTabChange('prompt')"
          >
            {{ $t('@reports.prompt') }}
          </button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
        <DocumentDetail v-if="activeTab === 'doc'" class="h-full" :report="props.report" />
        <TableDetail v-if="activeTab === 'table'" class="h-full" :report="props.report" />
        <div v-if="activeTab === 'prompt'" class="h-full">
          <div class="p-4 bg-gray-50 rounded-lg h-full overflow-auto">
            <div class="mb-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">
                {{ $t('@reports.inputPrompt') }}
              </h4>
              <p
                class="text-gray-700 whitespace-pre-wrap leading-relaxed bg-white p-3 rounded border"
              >
                {{
                  props.report.input_prompt ||
                  props.report.prompt_data ||
                  $t('@reports.noPromptContent')
                }}
              </p>
            </div>
            <div v-if="props.report.sql_data">
              <h4 class="text-sm font-medium text-gray-700 mb-2">
                {{ $t('@reports.responseMetadata') }}
              </h4>
              <pre
                class="text-gray-700 whitespace-pre-wrap leading-relaxed bg-white p-3 rounded border text-xs overflow-auto"
                >{{ JSON.stringify(props.report.ai_response.response_metadata, null, 2) }}</pre
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped></style>
