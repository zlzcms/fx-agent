<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
// 导入API
import type {
  CreateRiskLevelParams,
  RiskLevel,
  RiskLevelParams,
  UpdateRiskLevelParams,
} from '#/api';

import { onMounted, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createRiskLevelApi,
  deleteRiskLevelApi,
  getRiskLevelApi,
  getRiskLevelListApi,
  updateRiskLevelApi,
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

const gridOptions: VxeTableGridOptions<RiskLevel> = {
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
        const result = await getRiskLevelListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as RiskLevelParams);

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

function onActionClick({ code, row }: OnActionClickParams<RiskLevel>) {
  switch (code) {
    case 'delete': {
      deleteRiskLevelApi([row.id]).then(() => {
        message.success({
          content: `删除等级"${row.name}"成功`,
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      editLevel.value = row.id;
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

const editLevel = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await formApi.getValues<UpdateRiskLevelParams>();

      // 验证分数范围
      if (
        data.start_score !== undefined &&
        data.end_score !== undefined &&
        data.start_score >= data.end_score
      ) {
        message.error('结束分必须大于开始分');
        editModalApi.unlock();
        return;
      }

      try {
        await updateRiskLevelApi(editLevel.value, data);
        await editModalApi.close();
        message.success('更新等级成功');
        onRefresh();
      } catch {
        // message.error(error?.response?.data?.msg || '更新等级失败');
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<RiskLevel>();
      formApi.resetForm();
      if (data && data.id) {
        try {
          // 通过接口获取完整的数据
          const fullData = await getRiskLevelApi(data.id);
          formApi.setValues(fullData);
        } catch (error) {
          console.error('获取等级详情失败:', error);
          message.error('获取等级详情失败');
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
      const data = await addFormApi.getValues<CreateRiskLevelParams>();

      // 验证分数范围
      if (data.start_score >= data.end_score) {
        message.error('结束分必须大于开始分');
        addModalApi.unlock();
        return;
      }

      try {
        await createRiskLevelApi(data);
        await addModalApi.close();
        message.success('添加等级成功');
        onRefresh();
      } catch (error: any) {
        message.error(error?.response?.data?.msg || '添加等级失败');
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
          {{ $t('@risk.risk-levels.addLevel') }}
        </VbenButton>
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal :title="$t('@risk.risk-levels.editRiskLevel')">
      <EditForm />
    </editModal>

    <!-- 添加模态框 -->
    <addModal :title="$t('@risk.risk-levels.addRiskLevel')">
      <AddForm />
    </addModal>
  </Page>
</template>
