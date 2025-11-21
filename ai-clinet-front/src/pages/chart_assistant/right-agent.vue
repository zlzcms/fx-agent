<script setup lang="ts">
import { defineEmits, defineProps, h, defineAsyncComponent, type Component } from 'vue'

// 使用异步组件按需加载所有 Viewer 组件（避免首屏加载，减少打包体积）
// @ts-ignore - 异步组件类型在编译时无法确定，运行时正常
const MarkdownViewer: Component = defineAsyncComponent(() => import('@/components/MarkdownViewer.vue'))
// @ts-ignore
const PdfViewer: Component = defineAsyncComponent(() => import('@/components/PdfViewer.vue'))
// @ts-ignore
const CsvViewer: Component = defineAsyncComponent(() => import('@/components/CsvViewer.vue'))
// @ts-ignore
const WorkSpace: Component = defineAsyncComponent(() => import('@/components/WorkSpace.vue'))
// @ts-ignore
const HtmlViewer: Component = defineAsyncComponent(() => import('@/components/HtmlViewer.vue'))

// Props
const props = defineProps({
  type: {
    type: String,
    default: 'workspace',
    validator: (value: string) => ['md', 'pdf', 'csv', 'workspace'].includes(value)
  },
  // 通用源文件（用于 markdown、pdf 和 csv）
  source: {
    type: [String, Object, Blob],
    default: ''
  },
  // 控制子组件放大状态
  expand: {
    type: Boolean,
    default: false
  },
  // 文件名（用于显示和下载）
  filename: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['loaded', 'error', 'close', 'fullscreen', 'shrink','tab-change'])

// 事件处理函数 - 直接向上传递事件
const handleClose = () => {
  emit('close')
}
// 全屏
const handleFullscreen = () => {
  emit('fullscreen')
}

const handleLoaded = () => {
  emit('loaded')
}
const handleShrink = () => {
  emit('shrink')
}

const handleError = (error: any) => {
  emit('error', error)
}

// 动态组件渲染
const renderComponent = () => {
  switch (props.type) {
    case 'html':
      return h(HtmlViewer, {
        source: props.source,
        expand: props.expand,
        onClose: handleClose,
        onFullscreen: handleFullscreen,
        onLoaded: handleLoaded,
        onError: handleError,
        onShrink: handleShrink,
        filename: props.filename
      })
    case 'md':
      return h(MarkdownViewer, {
        source: props.source,
        expand: props.expand,
        onClose: handleClose,
        onFullscreen: handleFullscreen,
        onLoaded: handleLoaded,
        onError: handleError,
        onShrink: handleShrink,
        filename: props.filename
      })
    case 'pdf':
      return h(PdfViewer, {
        source: props.source,
        expand: props.expand,
        onClose: handleClose,
        onLoaded: handleLoaded,
        onError: handleError,
        onFullscreen: handleFullscreen,
        onShrink: handleShrink
      })
    case 'csv':
      return h(CsvViewer, {
        source: props.source,
        expand: props.expand,
        onClose: handleClose,
        onLoaded: handleLoaded,
        onError: handleError,
        onFullscreen: handleFullscreen,
        onShrink: handleShrink
      })
    case 'workspace':
      return h(WorkSpace, {
        source: props.source,
        onClose: handleClose,
      })
    default:
      return h(WorkSpace, {
        visible: true,
        onClose: handleClose
      })
  }
}

</script>

<template>
  <div class="right-agent-proxy">
    <component :is="renderComponent()" />
  </div>
</template>

<style scoped>
.right-agent-proxy {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
