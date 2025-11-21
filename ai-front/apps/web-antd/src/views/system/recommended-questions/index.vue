<script lang="ts" setup>
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { RecommendedQuestion, SysRoleResult } from '#/api';

import { computed, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createRecommendedQuestionApi,
  deleteRecommendedQuestionApi,
  getAllSysRoleApi,
  getRecommendedQuestionListApi,
  updateRecommendedQuestionApi,
} from '#/api';

import { querySchema, useColumns, useFormSchema } from './data';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: querySchema,
};

// 角色选项用于列展示角色名称
const roleSelectOptions = ref<SysRoleResult[]>([]);
const fetchAllSysRole = async () => {
  try {
    roleSelectOptions.value = await getAllSysRoleApi();
  } catch (error) {
    console.error(error);
  }
};
fetchAllSysRole();

const gridOptions: VxeTableGridOptions<RecommendedQuestion> = {
  rowConfig: { keyField: 'id' },
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
  columns: useColumns(onActionClick, roleSelectOptions),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        return await getRecommendedQuestionListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        });
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

function onActionClick({ code, row }: OnActionClickParams<RecommendedQuestion>) {
  switch (code) {
    case 'delete': {
      deleteRecommendedQuestionApi(row.id).then(() => {
        message.success({
          content: $t('ui.actionMessage.deleteSuccess', [row.title]),
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      modalApi.setData(row).open();
      break;
    }
  }
}

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  showDefaultActions: false,
  schema: useFormSchema(roleSelectOptions),
});

interface FormRQParams {
  id?: number;
  title: string;
  content: string;
  role_ids?: number[];
  sort_order?: number;
  status?: number;
  is_default?: boolean;
}

const formData = ref<FormRQParams>();

const modalTitle = computed(() => {
  return formData.value?.id
    ? $t('@recommended-questions.editTitle')
    : $t('@recommended-questions.createTitle');
});

const [Modal, modalApi] = useVbenModal({
  destroyOnClose: true,
  closeOnClickModal: false,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      const data = await formApi.getValues<FormRQParams>();
      try {
        await (formData.value?.id
          ? updateRecommendedQuestionApi(formData.value.id!, data)
          : createRecommendedQuestionApi(data));
        await modalApi.close();
        onRefresh();
      } catch (error: any) {
        const msg = error?.message || $t('ui.actionMessage.operationFailed');
        message.error(msg);
      } finally {
        modalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = modalApi.getData<FormRQParams>();
      formApi.resetForm();
      if (data) {
        formData.value = data;
        formApi.setValues(formData.value);
      } else {
        formData.value = undefined;
      }
    }
  },
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton @click="() => modalApi.setData(null).open()">
          <MaterialSymbolsAdd class="size-5" />
          {{ $t('@recommended-questions.addQuestion') }}
        </VbenButton>
      </template>
    </Grid>
    <Modal :title="modalTitle">
      <Form />
    </Modal>
  </Page>
</template>
