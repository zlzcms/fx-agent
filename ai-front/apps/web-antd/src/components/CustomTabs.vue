<script setup lang="ts">
interface Tab {
  key: string;
  label: string;
}

defineProps({
  tabs: {
    type: Array as () => Tab[],
    required: true,
    // [{ key: string, label: string }]
  },
  activeTab: {
    type: String,
    required: true,
  },
});

defineEmits(['tabChange']);
</script>

<template>
  <div class="custom-tabs inline-flex border border-gray-200 rounded-md p-1">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item px-5 py-2 text-sm rounded-md mr-1 transition-colors"
      :class="{ active: activeTab === tab.key }"
      @click="$emit('tabChange', tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.tab-item.active {
  color: #1677ff;
  background-color: #f5f7fa;
}
</style>
