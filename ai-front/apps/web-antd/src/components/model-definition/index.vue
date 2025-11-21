<script setup lang="ts">
import { ref, watch } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { Settings } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

interface ModelDefinitionProps {
  modelValue?: string;
}

interface ModelDefinitionEmits {
  (event: 'update:modelValue', value: string): void;
  (event: 'change', value: string): void;
}

const props = withDefaults(defineProps<ModelDefinitionProps>(), {
  modelValue: '',
});

const emit = defineEmits<ModelDefinitionEmits>();

// 内部状态
const internalValue = ref(props.modelValue || '');
const aiPolishLoading = ref(false);

// 监听外部prop变化
watch(
  () => props.modelValue,
  (newValue) => {
    internalValue.value = newValue || '';
  },
  { immediate: true },
);

// 处理输入变化
function handleInput() {
  emit('update:modelValue', internalValue.value);
  emit('change', internalValue.value);
}

// AI润色功能
async function handleAIPolish() {
  if (!internalValue.value?.trim()) {
    message.warning($t('page.components.modelDefinition.pleaseInputFirst'));
    return;
  }

  aiPolishLoading.value = true;
  try {
    // 模拟AI润色处理
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 这里应该调用真实的AI润色API
    const originalText = internalValue.value.trim();

    // 简单的文本优化处理（实际应该调用AI API）
    let polishedText = originalText;

    // 添加结构化格式
    if (!polishedText.includes('**') && !polishedText.includes('##')) {
      const lines = polishedText.split('\n').filter((line) => line.trim());
      polishedText =
        lines.length > 1
          ? `## ${$t('page.components.modelDefinition.modelOverview')}\n${lines[0]}\n\n## ${$t('page.components.modelDefinition.features')}\n${lines
              .slice(1)
              .map((line) => `- ${line}`)
              .join('\n')}`
          : `## ${$t('page.components.modelDefinition.modelDefinition')}\n${polishedText}\n\n## ${$t('page.components.modelDefinition.applicationScenarios')}\n- ${$t('page.components.modelDefinition.dataAnalysis')}\n- ${$t('page.components.modelDefinition.intelligentDecision')}\n- ${$t('page.components.modelDefinition.automatedReports')}`;
    }

    // 添加专业性提升
    polishedText = polishedText
      .replaceAll('数据', $t('page.components.modelDefinition.dataResources'))
      .replaceAll('分析', $t('page.components.modelDefinition.deepAnalysis'))
      .replaceAll('处理', $t('page.components.modelDefinition.intelligentProcessing'))
      .replaceAll('报告', $t('page.components.modelDefinition.analysisReports'));

    internalValue.value = polishedText;
    handleInput(); // 触发更新

    message.success($t('page.components.modelDefinition.aiPolishSuccess'));
  } catch (error: any) {
    console.error($t('page.components.modelDefinition.aiPolishFailed'), error);
    message.error($t('page.components.modelDefinition.aiPolishError'));
  } finally {
    aiPolishLoading.value = false;
  }
}
</script>

<template>
  <div class="model-definition-component p-4 rounded-lg bg-gray-50 border border-gray-200">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <label class="block text-sm font-medium text-gray-900 mb-2">
          {{ $t('page.components.modelDefinition.modelDefinition') }}
        </label>
        <p class="text-sm text-gray-500">
          {{ $t('page.components.modelDefinition.description') }}
        </p>
      </div>
      <VbenButton
        variant="outline"
        :loading="aiPolishLoading"
        @click="handleAIPolish"
        class="ai-polish-btn flex items-center"
      >
        <Settings class="mr-1 size-4" />
        {{ $t('page.components.modelDefinition.aiPolish') }}
      </VbenButton>
    </div>

    <textarea
      v-model="internalValue"
      @input="handleInput"
      :placeholder="$t('page.components.modelDefinition.placeholder')"
      class="model-definition-textarea w-full p-3 border border-gray-300 rounded-md resize-vertical focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      rows="4"
      maxlength="1000"
      style="min-height: 120px"
    ></textarea>
    <div class="mt-2 flex justify-between items-center text-sm text-gray-500">
      <span>{{ $t('page.components.modelDefinition.supportDescription') }}</span>
      <span>{{ internalValue?.length || 0 }}/1000</span>
    </div>
  </div>
</template>

<style scoped>
.model-definition-component {
  transition: all 0.2s ease;
}

.model-definition-component:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgb(0 0 0 / 5%);
}

.model-definition-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

/* AI润色按钮特殊样式 */
.ai-polish-btn {
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.ai-polish-btn:hover {
  box-shadow: 0 4px 12px rgb(102 126 234 / 40%);
  transform: translateY(-1px);
}

.ai-polish-btn:active {
  transform: translateY(0);
}

/* 模型定义区域样式优化 */
.model-definition-area {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border: 1px solid #e1e8ff;
}

.model-definition-textarea {
  background: rgb(255 255 255 / 90%);
  backdrop-filter: blur(10px);
}
</style>
