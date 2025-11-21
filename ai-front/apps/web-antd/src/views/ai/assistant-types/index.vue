<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
// 导入API
import type {
  AssistantType,
  AssistantTypeParams,
  CreateAssistantTypeParams,
  UpdateAssistantTypeParams,
} from '#/api';

import { onMounted, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createAssistantTypeApi,
  deleteAssistantTypeApi,
  getAssistantTypeApi,
  getAssistantTypeListApi,
  updateAssistantTypeApi,
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

const gridOptions: VxeTableGridOptions<AssistantType> = {
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
        return await getAssistantTypeListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as AssistantTypeParams);
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

function onActionClick({ code, row }: OnActionClickParams<AssistantType>) {
  switch (code) {
    case 'delete': {
      deleteAssistantTypeApi([row.id]).then(() => {
        message.success({
          content: $t('@ai-assistantTypes.deleteSuccess', { name: row.name }),
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      editType.value = row.id;
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

const editType = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await formApi.getValues<UpdateAssistantTypeParams>();
      try {
        await updateAssistantTypeApi(editType.value, data);
        await editModalApi.close();
        message.success($t('@ai-assistantTypes.updateSuccess'));
        onRefresh();
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<AssistantType>();
      formApi.resetForm();
      if (data && data.id) {
        try {
          // 通过接口获取完整的数据
          const fullData = await getAssistantTypeApi(data.id);
          formApi.setValues(fullData);
        } catch (error) {
          console.error($t('@ai-assistantTypes.getDetailFailed'), error);
          message.error($t('@ai-assistantTypes.getDetailFailed'));
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
      const data = await addFormApi.getValues<CreateAssistantTypeParams>();
      try {
        await createAssistantTypeApi(data);
        await addModalApi.close();
        message.success($t('@ai-assistantTypes.addSuccess'));
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
          {{ $t('@ai-assistantTypes.addType') }}
        </VbenButton>
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal :title="$t('@ai-assistantTypes.editTitle')">
      <EditForm />
    </editModal>

    <!-- 添加模态框 -->
    <addModal :title="$t('@ai-assistantTypes.addTitle')">
      <AddForm />
    </addModal>
  </Page>
</template>
