<script lang="ts" setup>
import type { VbenFormProps } from '@vben/common-ui';

import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { ChatMessageItem } from '#/api';

import { nextTick, ref } from 'vue';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { getChatLogListApi } from '#/api';
import { pagerPresets } from '#/configs/pager';

import bubblelistl from './bubblelistl.vue';

const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('views.common.query'),
  },
  schema: [
    {
      component: 'Input',
      fieldName: 'chat_id',
      label: $t('@log-qa.sessionId'),
    },
    {
      component: 'InputNumber',
      fieldName: 'user_id',
      label: $t('@log-qa.userId'),
      componentProps: { min: 1, style: { width: '100%' } },
    },
  ],
};
const chatMessageItem = ref<ChatMessageItem | null>(null);

// 滚动到 Drawer 内容区域底部的函数
function scrollDrawerToBottom() {
  nextTick(() => {
    // console.info('scroll to bottom');
    setTimeout(() => {
      // 查找 Drawer 的内容区域
      const drawerContent = document.querySelector('.drawer-message-list .overflow-y-auto');
      if (drawerContent) {
        drawerContent.scrollTop = drawerContent.scrollHeight;
        // console.info('scroll to bottom');
      }
    }, 300); // 等待 Drawer 动画完成
  });
}

// 处理数据加载完成事件
function onDataLoaded() {
  scrollDrawerToBottom();
}

function onActionClick({ code, row }: OnActionClickParams<ChatMessageItem>) {
  switch (code) {
    case 'details': {
      chatMessageItem.value = row;
      drawerApi.open();
      // 数据加载完成后会自动滚动到底部
    }
  }
}
const [Drawer, drawerApi] = useVbenDrawer({
  destroyOnClose: true,
  footer: false,
  class: 'drawer-message-list w-2/5',
});

interface ChatRow extends ChatMessageItem {
  res_file?: any;
  file_name?: null | string;
}

function openFile(url?: string) {
  if (url) {
    window.open(url, '_blank');
  }
}
const gridOptions: VxeTableGridOptions<ChatRow> = {
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
  pagerConfig: pagerPresets.standard,
  columns: [
    { field: 'chat_id', title: $t('@log-qa.sessionId'), width: 220 },
    { field: 'role', title: $t('@log-qa.role'), width: 80 },
    { field: 'user_id', title: $t('@log-qa.userId'), width: 100 },
    { field: 'username', title: $t('@log-qa.username'), width: 140 },
    { field: 'nickname', title: $t('@log-qa.nickname'), width: 140 },
    { field: 'content', title: $t('@log-qa.content'), minWidth: 240 },
    { field: 'is_interrupted', title: $t('@log-qa.isInterrupted'), width: 100 },
    { field: 'created_time', title: $t('@log-qa.createdTime'), width: 180 },
    { field: 'updated_time', title: $t('@log-qa.updatedTime'), width: 180 },
    {
      field: 'file_name',
      title: $t('@log-qa.generatedFile'),
      width: 180,
      fixed: 'right',
      slots: { default: 'file_name_default' },
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 100,
      cellRender: {
        attrs: {
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'details',
            text: $t('@log-qa.sessionDetails'),
          },
        ],
      },
    },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const res = await getChatLogListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        });

        res.items = res.items.map((it) => {
          let res_file: any = null;
          let file_name = null;
          if (it.role === 'assistant' && it.response_data) {
            const listStream: Array<any> = JSON.parse(it.response_data);
            res_file = listStream.find((chunk: any) => chunk.type === 'final' && chunk.file);
            if (res_file) {
              file_name = res_file.file.url.split('/').pop();
            }
          }

          return {
            ...it,
            res_file,
            file_name,
          };
        });
        // console.info('response:', res);
        return res;
      },
    },
  },
};

const [Grid] = useVbenVxeGrid({ formOptions, gridOptions });
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #file_name_default="{ row }">
        <a-button
          v-if="row.file_name"
          type="link"
          size="small"
          @click="() => openFile(row.res_file?.file?.url)"
        >
          {{ row.file_name }}
        </a-button>
        <span v-else>{{ $t('@log-qa.none') }}</span>
      </template>
    </Grid>

    <Drawer :title="$t('@log-qa.sessionDetails')">
      <bubblelistl
        v-if="chatMessageItem"
        :chat-message-item="chatMessageItem"
        @data-loaded="onDataLoaded"
      />
    </Drawer>
  </Page>
</template>
