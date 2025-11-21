<script setup lang="ts">
import { useVbenForm } from '#/adapter/form';

import { useBasicInfoPart1Schema } from '../data';

// Props
defineProps({
  modelOptions: {
    type: Array,
    default: () => [],
  },
  assistantTypeOptions: {
    type: Array,
    default: () => [],
  },
  personnelOptions: {
    type: Array,
    default: () => [],
  },
  notificationMethodOptions: {
    type: Array,
    default: () => [],
  },
  modelDefinitionValue: {
    type: String,
    default: '',
  },
  aiPolishLoading: {
    type: Boolean,
    default: false,
  },
});

// Emits
const emit = defineEmits([
  'update:modelDefinitionValue',
  'handleResponsiblePersonsChange',
  'handleNotificationMethodsChange',
  'aiPolish',
]);

/**
 * 基本信息表单 - 第一部分（基础信息）
 */
const [BasicFormPart1, basicFormPart1Api] = useVbenForm({
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 md:grid-cols-2',
  commonConfig: {
    labelWidth: 120,
  },
  schema: useBasicInfoPart1Schema(),
});

// 组合获取基本信息的函数
async function getBasicFormValues() {
  return await basicFormPart1Api.getValues();
}

// 组合验证基本信息的函数
async function validateBasicForms() {
  const part1Valid = await basicFormPart1Api.validate();

  const allErrors: string[] = [];
  if (part1Valid.errors) {
    if (Array.isArray(part1Valid.errors)) {
      allErrors.push(...part1Valid.errors);
    } else {
      Object.values(part1Valid.errors).forEach((error) => {
        if (typeof error === 'string') {
          allErrors.push(error);
        }
      });
    }
  }

  return {
    valid: part1Valid.valid,
    errors: allErrors,
  };
}

// 更新基本信息表单Schema
function updateBasicFormSchema(updates: any[]) {
  const part1Fields = new Set([
    'ai_model_id',
    'assistant_type_id',
    'avatar',
    'description',
    'model_definition',
    'name',
  ]);

  const part1Updates = updates.filter((update) => part1Fields.has(update.fieldName));

  if (part1Updates.length > 0) {
    basicFormPart1Api.updateSchema(part1Updates);
  }
}

// 设置基本信息表单值
function setBasicFormValues(values: any) {
  const part1Fields = new Set([
    'ai_model_id',
    'assistant_type_id',
    'avatar',
    'description',
    'model_definition',
    'name',
  ]);

  const part1Values: any = {};

  Object.keys(values).forEach((key) => {
    if (part1Fields.has(key)) {
      part1Values[key] = values[key];
    }
  });

  basicFormPart1Api.setValues(part1Values);
}

// 模型定义输入框变化处理
function handleModelDefinitionChange(value: string) {
  emit('update:modelDefinitionValue', value);
}

// AI润色
function handleAIPolish() {
  emit('aiPolish');
}

// 注释：处理指定人员变化和通知方式变化的函数已移除，因为未被使用

// 暴露给父组件的方法
defineExpose({
  basicFormPart1Api,
  getBasicFormValues,
  validateBasicForms,
  updateBasicFormSchema,
  setBasicFormValues,
});
</script>

<template>
  <div>
    <BasicFormPart1 />
    <!-- 模型定义区域 - 自定义实现，位于使用模型字段下方 -->
    <div class="pl-10">
      <div class="mb-4 p-4 rounded-lg model-definition-area">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <label class="block text-sm text-gray-900 mb-2"> 模型定义 </label>
            <p class="text-sm text-gray-500">
              详细描述模型的功能、能力和使用场景，AI润色功能可以帮助优化表达
            </p>
          </div>
          <VbenButton
            variant="outline"
            :loading="aiPolishLoading"
            @click="handleAIPolish"
            class="ai-polish-btn flex items-center"
          >
            AI润色
          </VbenButton>
        </div>

        <textarea
          :value="modelDefinitionValue"
          @input="handleModelDefinitionChange(($event.target as HTMLTextAreaElement).value)"
          placeholder="请输入模型的详细定义和能力描述"
          class="model-definition-textarea w-full p-3 border border-gray-300 rounded-md resize-vertical focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows="4"
          maxlength="1000"
          style="min-height: 120px"
        ></textarea>
        <div class="mt-2 flex justify-between items-center text-sm text-gray-500">
          <span>支持详细描述模型的功能特点、应用场景和技术要求</span>
          <span>{{ modelDefinitionValue?.length || 0 }}/1000</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-definition-area {
  background-color: #f9f9f9;
  border: 1px solid #eaeaea;
}

.model-definition-textarea {
  font-family:
    ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
}

.ai-polish-btn {
  color: #2563eb;
  background-color: #f0f7ff;
  border-color: #d0e3ff;
}

.ai-polish-btn:hover {
  background-color: #e5f0ff;
  border-color: #b0d0ff;
}
</style>
