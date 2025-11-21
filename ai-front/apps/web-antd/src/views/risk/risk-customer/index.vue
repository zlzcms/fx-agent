<script setup lang="ts">
import RiskPage from '../shared/RiskPage.vue';
import Detail from '../shared/RiskDetail.vue';
import { customerRiskConfig } from './data';
</script>

<template>
  <RiskPage
    :risk-config="customerRiskConfig"
    :detail-component="Detail"
  />
</template>

<style scoped>
</style>
