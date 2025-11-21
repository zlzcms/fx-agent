<script setup lang="ts">
import RiskPage from '../shared/RiskPage.vue';
import Detail from '../shared/RiskDetail.vue';
import { employeeRiskConfig } from './data';
</script>

<template>
  <RiskPage :risk-config="employeeRiskConfig" :detail-component="Detail" />
</template>

<style scoped>
</style>
