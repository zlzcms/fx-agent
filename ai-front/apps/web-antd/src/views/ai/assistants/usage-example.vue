<script setup lang="ts">
import { ref } from 'vue';

import { RiskType } from '#/api/risk';
import { DataPermissionSelector } from '#/components/data-permission-config';

// Component state
const permissionType = ref(RiskType.ALL_EMPLOYEE);
const permissionValues = ref<string[]>([]);

// Handle changes
function handlePermissionChange(data: { type: string; values: string[] }) {
  console.warn('Permission changed:', data);
  // Update your form data or perform other actions
}
</script>

<template>
  <div>
    <h2>Data Permission Selector Example</h2>

    <div class="my-4">
      <div class="mb-2 font-medium">数据权限范围:</div>
      <DataPermissionSelector
        v-model="permissionType"
        v-model:permission-values="permissionValues"
        @change="handlePermissionChange"
      />
    </div>

    <div class="mt-4 p-4 bg-gray-100 rounded">
      <div class="font-medium">Selected Values:</div>
      <div>Type: {{ permissionType }}</div>
      <div>Values: {{ permissionValues }}</div>
    </div>
  </div>
</template>
