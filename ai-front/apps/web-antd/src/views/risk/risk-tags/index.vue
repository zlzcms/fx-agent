<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
// 导入API
import type { CreateRiskTagParams, RiskTag, RiskTagParams, UpdateRiskTagParams } from '#/api';

import { ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createRiskTagApi,
  deleteRiskTagApi,
  getRiskTagApi,
  getRiskTagListApi,
  updateRiskTagApi,
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
  submitOnChange: true,
  submitOnEnter: true,
};

const gridOptions: VxeTableGridOptions<RiskTag> = {
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
        const result = await getRiskTagListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as RiskTagParams);

        return {
          items: result.items || [],
          total: result.total || 0,
        };
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

function onActionClick({ code, row }: OnActionClickParams<RiskTag>) {
  switch (code) {
    case 'delete': {
      deleteRiskTagApi([row.id.toString()]).then(() => {
        message.success({
          content: $t('@risk.risk-tags.deleteSuccess', { name: row.name }),
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      editTag.value = row.id;
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

const editTag = ref<number>(0);

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await formApi.getValues<UpdateRiskTagParams>();

      try {
        await updateRiskTagApi(editTag.value.toString(), data);
        await editModalApi.close();
        message.success($t('@risk.risk-tags.updateSuccess'));
        onRefresh();
      } catch (error: any) {
        message.error(error?.response?.data?.msg || $t('@risk.risk-tags.updateFailed'));
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<RiskTag>();
      formApi.resetForm();
      if (data && data.id) {
        try {
          // 通过接口获取完整的数据
          const fullData = await getRiskTagApi(data.id.toString());
          formApi.setValues(fullData);
        } catch (error) {
          console.error('获取标签详情失败:', error);
          message.error($t('@risk.risk-tags.getDetailFailed'));
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
      const data = await addFormApi.getValues<CreateRiskTagParams>();

      try {
        await createRiskTagApi(data);
        await addModalApi.close();
        message.success($t('@risk.risk-tags.addSuccess'));
        onRefresh();
      } catch (error: any) {
        message.error(error?.response?.data?.msg || $t('@risk.risk-tags.addFailed'));
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
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton @click="() => addModalApi.setData(null).open()">
          <MaterialSymbolsAdd class="size-5" />
          {{ $t('@risk.risk-tags.addTag') }}
        </VbenButton>
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal :title="$t('@risk.risk-tags.editTitle')">
      <EditForm />
    </editModal>

    <!-- 添加模态框 -->
    <addModal :title="$t('@risk.risk-tags.addTitle')">
      <AddForm />
    </addModal>
  </Page>
</template>
