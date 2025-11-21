<script setup lang="ts">
import type { TableFieldConfigEmits, TableFieldConfigProps, TableFieldItem } from './types';

import { computed, ref, watch } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd, MaterialSymbolsDeleteOutline } from '@vben/icons';
import { $t } from '@vben/locales';

import { Input, Select, SelectOption } from 'ant-design-vue';

import { getFieldTypeOptions } from './types';

const props = withDefaults(defineProps<TableFieldConfigProps>(), {
  modelValue: () => [],
});

const emit = defineEmits<TableFieldConfigEmits>();

// 动态生成字段类型选项
const fieldTypeOptions = computed(() => getFieldTypeOptions($t));

// 内部字段列表
const fields = ref<TableFieldItem[]>([]);

// 防止循环更新的标志
let isInternalUpdate = false;

// 生成唯一ID
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
};

// 防抖函数
const debounce = (func: Function, delay: number) => {
  let timeoutId: NodeJS.Timeout;
  return (...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// 触发变化事件
const emitChange = () => {
  if (isInternalUpdate) return;

  const value = fields.value.map((field) => ({
    fieldName: field.fieldName,
    fieldType: field.fieldType,
    fieldDesc: field.fieldDesc,
  }));

  emit('update:modelValue', value);
  emit('change', value);
};

// 防抖版本的触发变化事件
const debouncedEmitChange = debounce(emitChange, 300);

// 添加字段
const addField = () => {
  const newField: TableFieldItem = {
    id: generateId(),
    fieldName: '',
    fieldType: 'string',
    fieldDesc: '',
  };
  fields.value.push(newField);
  emitChange();
};

// 删除字段
const deleteField = (index: number) => {
  fields.value.splice(index, 1);
  emitChange();
};

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    // 避免循环更新
    if (isInternalUpdate) return;

    if (newValue && Array.isArray(newValue)) {
      isInternalUpdate = true;

      // 只有当数据真正不同时才更新
      const newFields = newValue.map((item) => ({
        id: generateId(),
        ...item,
      }));

      // 简单的深度比较，避免不必要的更新
      const fieldsChanged =
        fields.value.length !== newFields.length ||
        fields.value.some((field, index) => {
          const newField = newFields[index];
          return (
            !newField ||
            field.fieldName !== newField.fieldName ||
            field.fieldType !== newField.fieldType ||
            field.fieldDesc !== newField.fieldDesc
          );
        });

      if (fieldsChanged) {
        fields.value = newFields;
      }

      // 延迟重置标志，确保内部更新完成
      setTimeout(() => {
        isInternalUpdate = false;
      }, 0);
    } else if (fields.value.length > 0) {
      isInternalUpdate = true;
      fields.value = [];
      setTimeout(() => {
        isInternalUpdate = false;
      }, 0);
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="table-field-config-wrapper">
    <div class="table-field-config">
      <!-- Table header -->
      <div class="table-header">
        <div class="header-cell field-name">
          {{ $t('page.components.tableFieldConfig.fieldName') }}
        </div>
        <div class="header-cell field-type">
          {{ $t('page.components.tableFieldConfig.fieldType') }}
        </div>
        <div class="header-cell field-desc">
          {{ $t('page.components.tableFieldConfig.fieldDesc') }}
        </div>
        <div class="header-cell field-action">
          <VbenButton
            size="sm"
            variant="outline"
            @click="addField"
            style="background-color: white; border-color: #d1d5db"
          >
            <MaterialSymbolsAdd class="size-4" />
          </VbenButton>
        </div>
      </div>

      <!-- Table body -->
      <div class="table-body">
        <div v-for="(field, index) in fields" :key="field.id" class="table-row">
          <!-- 字段名输入框 -->
          <div class="body-cell field-name">
            <Input
              v-model:value="field.fieldName"
              :placeholder="$t('page.components.tableFieldConfig.enterFieldName')"
              @input="debouncedEmitChange"
            />
          </div>

          <!-- 类型选择框 -->
          <div class="body-cell field-type">
            <Select
              v-model:value="field.fieldType"
              :placeholder="$t('page.components.tableFieldConfig.selectType')"
              @change="emitChange"
            >
              <SelectOption
                v-for="option in fieldTypeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </SelectOption>
            </Select>
          </div>

          <!-- 描述输入框 -->
          <div class="body-cell field-desc">
            <Input
              v-model:value="field.fieldDesc"
              :placeholder="$t('page.components.tableFieldConfig.enterDescription')"
              @input="debouncedEmitChange"
            />
          </div>

          <!-- 删除按钮 -->
          <div class="body-cell field-action">
            <VbenButton
              variant="outline"
              size="sm"
              @click="deleteField(index)"
              style="padding: 4px 8px; color: #ef4444"
            >
              <MaterialSymbolsDeleteOutline class="size-4" />
            </VbenButton>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="fields.length === 0" class="empty-state">
          <div class="empty-text">{{ $t('page.components.tableFieldConfig.emptyText') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 响应式设计 */
@media (max-width: 768px) {
  .field-name {
    flex: 0 0 25%;
  }

  .field-type {
    flex: 0 0 20%;
  }

  .field-desc {
    flex: 1;
  }

  .field-action {
    flex: 0 0 80px;
  }

  .header-cell,
  .body-cell {
    padding: 8px;
    font-size: 12px;
  }
}

.table-field-config {
  overflow: hidden;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.table-header {
  display: flex;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.table-body {
  min-height: 100px;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background: #f9fafb;
}

.table-row:last-child {
  border-bottom: none;
}

.header-cell,
.body-cell {
  display: flex;
  align-items: center;
  padding: 12px;
}

.field-name {
  flex: 0 0 30%;
  border-right: 1px solid #f3f4f6;
}

.field-type {
  flex: 0 0 20%;
  border-right: 1px solid #f3f4f6;
}

.field-desc {
  flex: 1;
  border-right: 1px solid #f3f4f6;
}

.field-action {
  flex: 0 0 100px;
  justify-content: center;
}

.body-cell .ant-input,
.body-cell .ant-select {
  width: 100%;
}

.empty-state {
  padding: 40px 20px;
  color: #9ca3af;
  text-align: center;
}

.empty-text {
  font-size: 14px;
}
</style>
