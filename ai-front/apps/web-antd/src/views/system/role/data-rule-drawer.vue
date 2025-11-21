<script setup lang="ts">
import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { SysDataScopeRulesResult } from '#/api';

import { useVbenDrawer } from '@vben/common-ui';
import { $t } from '@vben/locales';
import { useVbenVxeGrid } from '@vben/plugins/vxe-table';

import { getSysDataScopeRulesApi } from '#/api';
import { drawerDataRuleColumns } from '#/views/system/role/data';

const [Drawer, drawerApi] = useVbenDrawer({
  destroyOnClose: true,
  header: false,
  footer: false,
  class: 'w-2/5',
});

const dataScopeRuleOptions: VxeTableGridOptions<SysDataScopeRulesResult> = {
  rowConfig: {
    keyField: 'id',
  },
  height: 'auto',
  virtualYConfig: {
    enabled: true,
    gt: 0,
  },
  pagerConfig: {
    enabled: false,
  },
  columns: drawerDataRuleColumns,
  proxyConfig: {
    ajax: {
      query: async () => {
        const res = await getSysDataScopeRulesApi(drawerApi.getData().clickedDataScopeRow.id);
        return res.rules;
      },
    },
  },
};
const [Grid] = useVbenVxeGrid({
  gridOptions: dataScopeRuleOptions,
});
</script>

<template>
  <Drawer :title="$t('@sys-role.dataPermissionRuleDetails')">
    <Grid>
      <template #toolbar-actions>
        <a-alert class="mb-2" type="warning" show-icon>
          <template #message>
            {{ $t('@sys-role.dataDisplayOnly') }}
          </template>
        </a-alert>
      </template>
    </Grid>
  </Drawer>
</template>
