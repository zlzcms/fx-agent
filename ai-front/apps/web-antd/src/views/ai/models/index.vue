<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
// 导入API
import type { AIModel, AIModelParams, CreateAIModelParams, UpdateAIModelParams } from '#/api';

import { onMounted, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createAIModelApi,
  deleteAIModelApi,
  getAIModelApi,
  getAIModelListApi,
  updateAIModelApi,
} from '#/api';

import { querySchema, useAddSchema, useColumns, useEditSchema } from './data';

/**
 * 表格配置
 */
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('page.form.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<AIModel> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  virtualYConfig: {
    enabled: true,
    gt: 0,
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        return await getAIModelListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as AIModelParams);
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

function onActionClick(params: any) {
  const { code, row } = params;
  switch (code) {
    case 'delete': {
      deleteAIModelApi([row.id]).then(() => {
        message.success({
          content: $t('@ai-models.deleteSuccess', { name: row.name }),
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      editModel.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
  }
}

/**
 * 编辑表单
 */
const [EditForm, formApi] = useVbenForm({
  showDefaultActions: false,
  schema: useEditSchema(),
});

const editModel = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await formApi.getValues<UpdateAIModelParams>();
      try {
        await updateAIModelApi(editModel.value, data);
        await editModalApi.close();
        message.success($t('@ai-models.updateSuccess'));
        onRefresh();
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<AIModel>();
      formApi.resetForm();
      if (data && data.id) {
        try {
          // 通过接口获取完整的未脱敏数据
          const fullData = await getAIModelApi(data.id);
          formApi.setValues(fullData);
        } catch (error) {
          console.error($t('@ai-models.getDetailFailed'), error);
          message.error($t('@ai-models.getDetailFailed'));
          // 如果接口调用失败，使用原始数据
          formApi.setValues(data);
        }
      }
    }
  },
});

/**
 * 添加表单
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: useAddSchema(),
});

const [addModal, addModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateAIModelParams>();
      try {
        await createAIModelApi(data);
        await addModalApi.close();
        message.success($t('@ai-models.addSuccess'));
        onRefresh();
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = addModalApi.getData();
      addFormApi.resetForm();
      if (data) {
        addFormApi.setValues(data);
      }
    }
  },
});

onMounted(() => {
  // 初始化数据
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton @click="() => addModalApi.setData(null).open()">
          <MaterialSymbolsAdd class="size-5" />
          {{ $t('@ai-models.addModel') }}
        </VbenButton>
      </template>
      <template #api_key="{ row }">
        <span class="font-mono text-sm">
          {{
            row.api_key
              ? `${row.api_key.substring(0, 8)}***${row.api_key.substring(row.api_key.length - 4)}`
              : ''
          }}
        </span>
      </template>
      <template #model_type="{ row }">
        <a-tag
          :color="
            row.model_type === 'OpenAI'
              ? 'green'
              : row.model_type === 'Anthropic'
                ? 'blue'
                : 'purple'
          "
        >
          {{ row.model_type }}
        </a-tag>
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal :title="$t('@ai-models.editTitle')">
      <EditForm />
    </editModal>

    <!-- 添加模态框 -->
    <addModal :title="$t('@ai-models.addTitle')">
      <AddForm />
    </addModal>
  </Page>
</template>
