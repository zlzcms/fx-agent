<template>
  <div class="html-demo-page">
    <div class="demo-container">
      <HtmlViewer
        :source="htmlSource"
        :title="htmlTitle"
        :filename="htmlFilename"
        @loaded="handleLoaded"
        @error="handleError"
        @close="handleClose"
        @fullscreen="handleFullscreen"
        @shrink="handleShrink"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import HtmlViewer from '@/components/HtmlViewer.vue'

const htmlSource = ref('')
const htmlTitle = ref('客户画像分析报告')
const htmlFilename = ref('customer-profile-report.html')

// 加载HTML文件
const loadHtmlFile = () => {
  // 直接使用public目录中的HTML文件URL
  htmlSource.value = '/customer-profile-report.html'
}

// 事件处理
const handleLoaded = (data) => {
  console.log('HTML加载成功:', data)
}

const handleError = (error) => {
  console.error('HTML加载失败:', error)
}

const handleClose = () => {
  // 可以在这里添加关闭逻辑，比如返回上一页
  console.log('关闭查看器')
}

const handleFullscreen = () => {
  console.log('进入全屏')
}

const handleShrink = () => {
  console.log('退出全屏')
}

onMounted(() => {
  loadHtmlFile()
})
</script>

<style scoped>
.html-demo-page {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.demo-container {
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
</style>

