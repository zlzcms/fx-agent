<script setup lang="ts">
import type { RiskReportItem } from '@vben/types';

import type { RiskConfig } from './risk-data';

import type { VbenFormProps } from '#/adapter/form';
import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { RiskReportParams } from '#/api/risk';

import { computed, onMounted, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';
import { $t } from '@vben/locales';
import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';
// 导入常量和工具函数
import { formatDateTime, getProcessStatusColor, getRiskLevelColor } from '@vben/utils';

import { AiAction } from '@maxpro/ai-action';
import { Tag as ATag, message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getRiskReportListApi, processRiskReportApi, RiskType } from '#/api/risk';
import { pagerPresets } from '#/configs/pager';
import { useRiskStore } from '#/store/risk';
import {
  formatDetectionWindowInfo,
  getAnalysisTypeLabel,
  getTriggerSourcesLabel,
} from '#/types/risk';

// 导入共享配置
import { createColumns, createProcessFormSchema, createQuerySchema } from './risk-data';

const props = defineProps<Props>();

// 定义事件
const emit = defineEmits(['viewDetail']);

const accessStore = useAccessStore();

// 定义Props
interface Props {
  riskConfig: RiskConfig;
}

// 处理弹窗相关
const currentRow = ref<null | RiskReportItem>(null);

// 标签映射
const riskStore = useRiskStore();

// 加载标签映射
onMounted(async () => {
  try {
    await riskStore.fetchRiskTags();
  } catch (error) {
    console.warn('Failed to load risk tags:', error);
  }
});

const tagMap = computed(() => riskStore.getRiskTagMap());

// 转换标签ID数组为标签名称数组
function convertTagIdsToNames(tagIds: string | string[] | undefined): string[] {
  if (!tagIds) return [];

  let ids: string[] = [];
  if (typeof tagIds === 'string') {
    try {
      ids = JSON.parse(tagIds);
    } catch {
      // 如果解析失败，尝试按逗号分割（向后兼容）
      ids = tagIds
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean);
    }
  } else if (Array.isArray(tagIds)) {
    ids = tagIds;
  }
  return Array.isArray(ids) ? ids.map((id) => tagMap.value[id] || id) : [tagMap.value[ids] || ids];
}

// 操作处理函数
function onActionClick({ code, row }: OnActionClickParams<RiskReportItem>) {
  switch (code) {
    case 'operation': {
      currentRow.value = row;
      processModalApi.setData(row).open();
      break;
    }
    case 'prompt': {
      currentRow.value = row;
      promptModalApi.setData(row).open();
      break;
    }
    case 'view': {
      emit('viewDetail', row.id);
      break;
    }
  }
}

// 格式化AI响应内容
function formatAiResponse(aiResponse: any): string {
  if (!aiResponse) {
    return $t('@risk-customer.noAiResponse');
  }

  try {
    // 创建ai_response的副本
    const formattedResponse = { ...aiResponse };

    // 如果ai_response有content字段，解析content
    if (formattedResponse.content) {
      const contentStr =
        typeof formattedResponse.content === 'string'
          ? formattedResponse.content
          : JSON.stringify(formattedResponse.content);

      // 尝试解析content为JSON
      try {
        const parsedContent = JSON.parse(contentStr);
        formattedResponse.content = parsedContent;
      } catch {
        // 如果解析失败，保持原始content
        formattedResponse.content = contentStr;
      }
    }

    // 显示完整的格式化JSON，包含所有字段
    return JSON.stringify(formattedResponse, null, 2);
  } catch {
    return JSON.stringify(aiResponse, null, 2);
  }
}

const [ProcessForm, processFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: createProcessFormSchema(props.riskConfig.i18nPrefix),
});

const [processModal, processModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await processFormApi.validate();
    if (valid) {
      processModalApi.lock();
      try {
        if (!currentRow.value) return;

        // 获取表单数据
        const formData = await processFormApi.getValues();

        // 调用API处理风险报告，传入ID和表单数据
        await processRiskReportApi(currentRow.value.id, formData);

        message.success($t('@risk-customer.processSuccess'));
        await processModalApi.close();

        // 刷新表格数据
        gridApi.query();
      } catch (error) {
        console.error('处理失败:', error);
        message.error($t('@risk-customer.processFailed'));
      } finally {
        processModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = processModalApi.getData();
      processFormApi.resetForm();
      if (data) {
        processFormApi.setValues({
          processStatus: $t('@risk-customer.processed'),
          processReason: $t('@risk-customer.situation1'),
          processComment: '',
          uploadFiles: [],
        });
      }
    }
  },
});

// 提示词弹窗
const [promptModal, promptModalApi] = useVbenModal({
  destroyOnClose: true,
  showCancelButton: false,
  showConfirmButton: false,
  onOpenChange(isOpen) {
    if (isOpen) {
      // 弹窗打开时可以进行一些初始化操作
    }
  },
});

const formOptions: VbenFormProps = {
  collapsed: false,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('page.form.query'),
  },
  schema: createQuerySchema(props.riskConfig.i18nPrefix, props.riskConfig.riskType),
  submitOnChange: true,
  submitOnEnter: true,
};

// 表格配置
const gridOptions: VxeTableGridOptions = {
  rowConfig: {
    keyField: 'id',
    isHover: true,
    resizable: true, // 启用行高调整功能，解决固定列高度同步问题
  },
  virtualYConfig: {
    enabled: false,
  },
  autoResize: true, // 启用自动重新计算
  exportConfig: {},
  height: 'auto',
  printConfig: {},
  toolbarConfig: {
    search: true,
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  pagerConfig: pagerPresets.standard,
  columns: createColumns(props.riskConfig.i18nPrefix, onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        try {
          // 处理数组参数，将数组转换为逗号分隔的字符串
          const processedFormValues = { ...formValues };
          // 处理风控等级ID数组
          if (
            processedFormValues.risk_level_id &&
            Array.isArray(processedFormValues.risk_level_id)
          ) {
            processedFormValues.risk_level_id = processedFormValues.risk_level_id.join(',');
          }
          // 处理风险标签ID数组
          if (processedFormValues.risk_tags && Array.isArray(processedFormValues.risk_tags)) {
            processedFormValues.risk_tags = processedFormValues.risk_tags.join(',');
          }

          const params: RiskReportParams = {
            page: page.currentPage,
            size: page.pageSize,
            risk_type: props.riskConfig.riskType,
            ...processedFormValues,
          };
          const response = await getRiskReportListApi(params);
          // 处理返回的数据
          const processedItems =
            response.items?.map((item) => {
              // 转换标签ID为标签名称
              const reportTags = convertTagIdsToNames(item.report_tags);

              return {
                ...item,
                created_time: formatDateTime(item.created_time),
                handle_time: item.handle_time ? formatDateTime(item.handle_time) : '-',
                reportTags,
                is_processed: item.is_processed || false,
                handle_result: item.handle_result || '',
                // 优先展示名称，无则回退到ID
                handle_user: (item as any).handle_user_name || item.handle_user || '',
                handle_suggestion: item.handle_suggestion || '',
                description: item.description || '',
                // 新增字段 - 在这里进行格式化
                analysis_type: getAnalysisTypeLabel(item.analysis_type),
                trigger_sources: getTriggerSourcesLabel(item.trigger_sources),
                detection_window_info: formatDetectionWindowInfo(item.detection_window_info),
              };
            }) || [];
          return {
            items: processedItems,
            total: response.total || 0,
          };
        } catch {
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
const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

// 风控类型显示函数
function getRiskTypeLabel(riskType: RiskType): string {
  switch (riskType) {
    case RiskType.AGENT_USER: {
      return $t('@risk-customer.agentRisk');
    }
    case RiskType.ALL_EMPLOYEE: {
      return $t('@risk-customer.customerRisk');
    }
    case RiskType.CRM_USER: {
      return $t('@risk-customer.employeeRisk');
    }
    case RiskType.PAYMENT: {
      return $t('@risk-customer.paymentRisk');
    }
    default: {
      return riskType;
    }
  }
}

const locale = preferences.app.locale || 'zh';
const aiConfig = ref({
  id: `risk_report_${props.riskConfig.riskType}`,
  token: accessStore.accessToken,
  askContent: '',
  locale,
});
function onAskAI(row: RiskReportItem) {
  if (props.riskConfig.riskType === RiskType.ALL_EMPLOYEE) {
    aiConfig.value.askContent =
      `请帮我分析用户${row.member_name}(id:${row.member_id})` + `的风控情况`;
  } else if (props.riskConfig.riskType === RiskType.CRM_USER) {
    aiConfig.value.askContent =
      `请帮我分析员工${row.member_name}(id:${row.member_id})` + `的风控情况`;
  } else {
    aiConfig.value.askContent =
      `请帮我分析用户${row.member_name}(id:${row.member_id})` + `的风控情况`;
  }
}
</script>

<template>
  <Grid>
    <template #memberName="{ row }">
      <AiAction
        :offset="6"
        aria-label="向 AI 提问"
        :ai="aiConfig"
        base-url="https://client.ai1center.com"
        @click="onAskAI(row)"
      >
        <span>{{ row.member_name }}</span>
      </AiAction>
    </template>
    <template #riskLevel="{ row }">
      <div>
        <span :style="{ color: getRiskLevelColor(row.risk_level?.name) }">
          {{ `${row.risk_level?.name}:${row.risk_level?.description}` }}</span
        >
      </div>
    </template>

    <template #riskType="{ row }">
      <div>
        <ATag :color="getRiskLevelColor(row.risk_level?.name || '')">
          {{ getRiskTypeLabel(row.risk_type) }}
        </ATag>
      </div>
    </template>

    <template #riskStatus="{ row }">
      <div>
        <ATag :color="getProcessStatusColor(row.is_processed)">
          {{ row.is_processed ? $t('@risk-customer.processed') : $t('@risk-customer.unprocessed') }}
        </ATag>
      </div>
    </template>

    <!-- 风险标签插槽 -->
    <template #rick_tags="{ row }">
      <div class="risk-tags-container">
        <template v-if="!row.reportTags || row.reportTags.length === 0">
          <span class="text-gray-400">{{ $t('@risk-customer.noTags') }}</span>
        </template>
        <template v-else>
          <div class="risk-tags-wrap">
            <ATag v-for="tag in row.reportTags" :key="tag" color="blue" class="risk-tag-item">
              {{ tag }}
            </ATag>
          </div>
        </template>
      </div>
    </template>

    <!-- 处理结果插槽 -->
    <template #handle_result="{ row }">
      <div>
        <div v-if="row.handle_result">{{ row.handle_result }}</div>
        <div v-else class="text-gray-400">{{ $t('@risk-customer.unprocessed') }}</div>
      </div>
    </template>

    <!-- 处理人插槽 -->
    <template #handle_user="{ row }">
      <div>
        <div v-if="row.handle_user">{{ row.handle_user }}</div>
        <div v-else class="text-gray-400">-</div>
      </div>
    </template>
  </Grid>

  <!-- 处理弹窗 -->
  <processModal :title="$t('@risk-customer.processOperation')">
    <ProcessForm />
  </processModal>

  <!-- 日志弹窗 -->
  <promptModal :title="$t('@risk-customer.viewLog')" class="w-[1200px]">
    <div class="p-4">
      <div class="mb-4">
        <h4 class="text-lg font-semibold mb-2">
          {{ $t('@risk-customer.userName') }}: {{ currentRow?.member_name || '-' }}
        </h4>
        <p class="text-sm text-gray-500 mb-4">
          {{ $t('@risk-customer.userID') }}: {{ currentRow?.member_id || '-' }}
        </p>
      </div>

      <!-- 输入提示词部分 -->
      <div class="mb-6">
        <h5 class="text-md font-semibold mb-3 text-blue-600">
          {{ $t('@risk-customer.inputPrompt') }}
        </h5>
        <div class="bg-gray-50 rounded-lg p-4 overflow-y-auto max-h-100">
          <pre class="whitespace-pre-wrap text-sm leading-relaxed">{{
            currentRow?.input_prompt || $t('@risk-customer.noPrompt')
          }}</pre>
        </div>
      </div>

      <!-- AI响应结果部分 -->
      <div>
        <h5 class="text-md font-semibold mb-3 text-green-600">
          {{ $t('@risk-customer.aiResponse') }}
        </h5>
        <div class="bg-gray-50 rounded-lg p-4 overflow-y-auto max-h-100">
          <pre class="whitespace-pre-wrap text-sm leading-relaxed">{{
            formatAiResponse(currentRow?.ai_response)
          }}</pre>
        </div>
      </div>
    </div>
  </promptModal>
</template>

<style scoped>
.risk-tags-container {
  width: 100%;
  min-height: 32px;
  padding: 4px 0;
}

.risk-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: flex-start;
  line-height: 1.2;
}

.risk-tag-item {
  flex-shrink: 0;
  max-width: 100%;
  margin: 0;
  font-size: 12px;
  text-align: center;
  word-break: break-all;
}

/* 表格样式优化 - 移除height: auto !important以修复固定列高度同步问题 */
:deep(.vxe-table .vxe-cell) {
  padding: 8px 6px !important;
  line-height: 1.4 !important;
  vertical-align: top !important;
  white-space: normal !important;
}

/* 保持内容自适应但不强制覆盖VXE Table的高度计算 */
:deep(.vxe-table .vxe-cell--content) {
  word-break: break-all;
  word-wrap: break-word;
}

/* 文本截断样式 */
.truncate {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
