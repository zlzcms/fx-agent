<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { VbenButton } from '@vben/common-ui';
import { MaterialSymbolsEdit } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { getAllAIModelsApi, getDefaultAIModelApi, setDefaultAIModelApi } from '#/api';
import { aiModelSchema } from '#/plugins/config/views/data';

const [Form, formApi] = useVbenForm({
  showDefaultActions: false,
  schema: aiModelSchema,
  commonConfig: {
    componentProps: {
      class: 'w-1/3',
    },
    disabled: true,
    labelClass: 'justify-start ml-2',
    labelWidth: 140,
    hideRequiredMark: true,
  },
});

const editButtonShow = ref<boolean>(true);
const modelOptions = ref<Array<{ label: string; value: string }>>([]);
const defaultModelId = ref<null | string>(null);

// 加载AI模型列表（从ai_models表获取所有启用的模型）
const loadModelOptions = async () => {
  try {
    const models = await getAllAIModelsApi(); // 后端已过滤只返回启用的模型
    modelOptions.value = models.map((model) => ({
      label: model.name,
      value: model.id,
    }));

    // 更新表单的选项
    formApi.setState((prev: any) => {
      return {
        schema: prev.schema?.map((item: any) => {
          if (item.fieldName === 'ai_default_model_id') {
            return {
              ...item,
              componentProps: {
                ...item.componentProps,
                options: modelOptions.value,
              },
            };
          }
          return item;
        }),
      };
    });
  } catch (error) {
    console.error('加载AI模型列表失败:', error);
    message.error('加载AI模型列表失败');
  }
};

// 获取当前默认模型
const fetchConfigList = async () => {
  try {
    await loadModelOptions();
    const defaultModel = await getDefaultAIModelApi();
    if (defaultModel) {
      defaultModelId.value = defaultModel.id;
      formApi.setValues({ ai_default_model_id: defaultModel.id });
    } else {
      defaultModelId.value = null;
      formApi.setValues({ ai_default_model_id: undefined });
    }
  } catch (error) {
    console.error('获取默认模型配置失败:', error);
    message.error('获取默认模型配置失败');
  }
};

// 保存配置
const saveAIModelConfig = async () => {
  const { valid } = await formApi.validate();
  if (!valid) {
    return;
  }

  try {
    const data: Record<string, any> = await formApi.getValues();
    const selectedModelId = data.ai_default_model_id;

    if (!selectedModelId) {
      message.warning($t('@sys-config.selectDefaultAIModel'));
      return;
    }

    await setDefaultAIModelApi(selectedModelId);
    message.success($t('ui.actionMessage.operationSuccess'));
    editButtonShow.value = true;
    formApi.setState({ commonConfig: { disabled: true } });
    await fetchConfigList();
  } catch (error: any) {
    console.error('保存配置失败:', error);
    message.error(error?.message || '保存配置失败');
  }
};

onMounted(() => {
  fetchConfigList();
});

defineExpose({
  fetchConfigList,
});
</script>

<template>
  <div>
    <Form />
    <VbenButton
      v-show="editButtonShow"
      class="ml-1.5 mt-3"
      @click="
        () => {
          editButtonShow = false;
          formApi.setState({ commonConfig: { disabled: false } });
        }
      "
    >
      <MaterialSymbolsEdit class="mr-1" />
      {{ $t('@sys-config.edit') }}
    </VbenButton>
    <VbenButton v-show="!editButtonShow" class="ml-1.5 mt-3" @click="saveAIModelConfig">
      <MaterialSymbolsEdit class="mr-1" />
      {{ $t('@sys-config.save') }}
    </VbenButton>
    <VbenButton
      v-show="!editButtonShow"
      class="ml-5 mt-5"
      variant="outline"
      @click="
        () => {
          editButtonShow = true;
          formApi.setState({ commonConfig: { disabled: true } });
          fetchConfigList();
        }
      "
    >
      <MaterialSymbolsEdit class="mr-1" />
      {{ $t('@sys-config.cancel') }}
    </VbenButton>
  </div>
</template>
