<script setup lang="ts">
import { ref } from 'vue';
import { Page } from '@vben/common-ui';
import { useVbenModal } from '@vben/common-ui';
import RiskList from './RiskList.vue';
import type { RiskConfig } from './risk-data';

// 定义Props
interface Props {
  riskConfig: RiskConfig;
  detailComponent: any;
}

const props = defineProps<Props>();

// 当前选中的客户ID
const currentCustomerId = ref('');

// 使用vben Modal - 根据文档配置最佳实践
const [Modal, modalApi] = useVbenModal({
  connectedComponent: props.detailComponent,
  destroyOnClose: true,
  showCancelButton: false,
  showConfirmButton: false,
  onOpenChange: (isOpen: boolean) => {
    if (!isOpen) {
      // 关闭时清理数据
      currentCustomerId.value = '';
    }
  },
});

// 查看详情 - 优化的打开方式
const handleViewDetail = async (id: string) => {
  if (!id) {
    return;
  }
  currentCustomerId.value = id;
  modalApi.setData({ customerId: id });
  modalApi.open();
};
</script>

<template>
  <Page auto-content-height>
    <RiskList
      :risk-config="riskConfig"
      @viewDetail="handleViewDetail"
      key="list"
    />
    
    <Modal />
  </Page>
</template>

<style scoped>
</style>