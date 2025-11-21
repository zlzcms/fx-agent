<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { ApiKeyResult, CreateApiKeyParams, UpdateApiKeyParams } from '#/api';

import { computed, h, ref } from 'vue';

import { Page, useVbenModal, VbenButton } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { useClipboard } from '@vueuse/core';
import { Modal as AntModal, Button, message } from 'ant-design-vue';
import dayjs from 'dayjs';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { createApiKeyApi, deleteApiKeyApi, getApiKeyListApi, updateApiKeyApi } from '#/api';

import { querySchema, schema, useColumns } from './api-key/data';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<ApiKeyResult> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
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
        return await getApiKeyListApi({
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

function onActionClick({ code, row }: OnActionClickParams<ApiKeyResult>) {
  switch (code) {
    case 'delete': {
      AntModal.confirm({
        title: $t('ui.actionMessage.deleteConfirm'),
        content: $t('ui.actionMessage.deleteConfirmContent', [row.key_name]),
        onOk: async () => {
          try {
            await deleteApiKeyApi(row.id);
            message.success({
              content: $t('ui.actionMessage.deleteSuccess', [row.key_name]),
              key: 'action_process_msg',
            });
            onRefresh();
          } catch (error) {
            console.error(error);
          }
        },
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
  schema,
});

interface FormApiKeyParams extends CreateApiKeyParams {
  id?: number;
  status?: number;
}

const formData = ref<FormApiKeyParams>();

const modalTitle = computed(() => {
  return formData.value?.id ? $t('@sys-config.editApiKey') : $t('@sys-config.createApiKey');
});

const [Modal, modalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      const formDataValues = await formApi.getValues<any>();
      // 处理日期格式，转换为ISO字符串
      let expiresAt: string | undefined;
      if (formDataValues.expires_at) {
        expiresAt =
          typeof formDataValues.expires_at === 'string'
            ? formDataValues.expires_at
            : formDataValues.expires_at.format('YYYY-MM-DD HH:mm:ss');
      }
      const data: CreateApiKeyParams | UpdateApiKeyParams = {
        ...formDataValues,
        expires_at: expiresAt,
      };
      try {
        if (formData.value?.id) {
          await updateApiKeyApi(formData.value.id, data as UpdateApiKeyParams);
          message.success($t('ui.actionMessage.updateSuccess'));
        } else {
          const result = await createApiKeyApi(data as CreateApiKeyParams);
          // 创建成功后显示完整的API Key
          if (result.api_key) {
            const handleCopyCreatedKey = () => {
              copy(result.api_key!);
              message.success($t('common.copied'));
            };

            AntModal.success({
              title: $t('@sys-config.createApiKeySuccess'),
              width: 650,
              content: h('div', { class: 'space-y-3' }, [
                h('div', { class: 'mb-2 text-gray-700' }, $t('@sys-config.apiKeyCreated')),
                h(
                  'div',
                  {
                    class: 'flex items-center gap-2 p-3 bg-gray-50 rounded border',
                  },
                  [
                    h(
                      'code',
                      {
                        class: 'font-mono text-sm flex-1 break-all',
                        style: 'word-break: break-all; color: #333;',
                      },
                      result.api_key,
                    ),
                    h(
                      Button,
                      {
                        size: 'small',
                        type: 'primary',
                        onClick: handleCopyCreatedKey,
                      },
                      {
                        default: () => `📋 ${$t('common.copy')}`,
                      },
                    ),
                  ],
                ),
                h('div', { class: 'text-red-500 text-sm mt-2' }, $t('@sys-config.apiKeyWarning')),
              ]),
            });
          }
        }
        await modalApi.close();
        onRefresh();
      } catch (error: any) {
        console.error(error);
        message.error(error?.message || $t('ui.actionMessage.operationFailed'));
      } finally {
        modalApi.unlock();
      }
    }
  },
  onOpenChange(idOpen) {
    if (idOpen) {
      const data = modalApi.getData<FormApiKeyParams>();
      formApi.resetForm();
      if (data) {
        formData.value = data;
        // 转换时间格式，将字符串转换为dayjs对象
        const formValues: any = { ...data };
        if (data.expires_at) {
          formValues.expires_at =
            typeof data.expires_at === 'string' ? dayjs(data.expires_at) : data.expires_at;
        }
        formApi.setValues(formValues);
      } else {
        formData.value = undefined;
      }
    }
  },
});

const fetchConfigList = async () => {
  onRefresh();
};

const { copy } = useClipboard({ legacy: true });

defineExpose({
  fetchConfigList,
});
</script>

<template>
  <div class="h-full">
    <Page auto-content-height>
      <Grid>
        <template #toolbar-actions>
          <VbenButton @click="() => modalApi.setData(null).open()">
            <MaterialSymbolsAdd class="size-5" />
            {{ $t('@sys-config.createApiKey') }}
          </VbenButton>
        </template>
      </Grid>
      <Modal :title="modalTitle">
        <Form />
      </Modal>
    </Page>
  </div>
</template>
