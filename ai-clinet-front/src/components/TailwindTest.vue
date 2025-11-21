<template>
  <div class="tailwind-test-container">
    <!-- 文本样式 -->
    <div
      class="text-xs text-sm text-base text-lg text-xl text-2xl text-3xl"
    ></div>

    <!-- 间距样式 -->
    <div class="p-1 p-2 p-3 p-4 p-5 p-6 p-8 p-10 p-12 p-16 p-20 p-24"></div>
    <div class="m-1 m-2 m-3 m-4 m-5 m-6 m-8 m-10 m-12 m-16 m-20 m-24"></div>

    <!-- 尺寸样式 -->
    <div
      class="w-1 w-2 w-3 w-4 w-5 w-6 w-8 w-10 w-12 w-16 w-20 w-24 w-full w-auto"
    ></div>
    <div
      class="h-1 h-2 h-3 h-4 h-5 h-6 h-8 h-10 h-12 h-16 h-20 h-24 h-full h-auto"
    ></div>

    <!-- 布局样式 -->
    <div class="flex grid block inline hidden"></div>
    <div
      class="items-center items-start items-end justify-center justify-start justify-end"
    ></div>

    <!-- 颜色样式 -->
    <div
      class="bg-red-500 bg-blue-500 bg-green-500 bg-yellow-500 bg-gray-500"
    ></div>
    <div
      class="text-red-500 text-blue-500 text-green-500 text-yellow-500 text-gray-500"
    ></div>

    <!-- 边框样式 -->
    <div class="border border-2 border-4 rounded rounded-lg rounded-xl"></div>

    <!-- 阴影样式 -->
    <div class="shadow shadow-md shadow-lg shadow-xl"></div>
  </div>
</template>

<script setup lang="ts">
// 这个组件仅用于触发 Tailwind CSS 样式生成
</script>

<style scoped>
.tailwind-test-container {
  display: none; /* 隐藏这个测试组件 */
}
</style>
