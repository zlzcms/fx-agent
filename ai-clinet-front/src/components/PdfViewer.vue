<template>
  <div class="pdf-viewer-container">
    <div class="pdf-toolbar">
      <div class="pdf-actions">
        <!-- 下载按钮 -->
        <button @click="downloadPdf" class="toolbar-btn" :title="$t('docViewer.download')">
          <DownloadOutlined />
        </button>

        <!-- 全屏按钮 - 移动端隐藏 -->
        <button
          v-if="!isMobile"
          @click="ArrowsOrShrink"
          class="toolbar-btn"
          :title="isExpanded ? $t('docViewer.shrink') : $t('docViewer.expand')"
        >
          <ArrowsAltOutlined v-if="!isExpanded" />
          <ShrinkOutlined v-else />
        </button>

        <!-- 关闭按钮 -->
        <button @click="closeViewer" class="toolbar-btn close-btn" :title="$t('docViewer.close')">
          <CloseOutlined />
        </button>
      </div>
    </div>

    <div class="pdf-content" ref="pdfContainer">
      <iframe
        v-if="source"
        :src="iframeSource"
        class="pdf-iframe"
        ref="iframeRef"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>

      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">{{ $t('docViewer.loading') }}</div>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  ArrowsAltOutlined,
  DownloadOutlined,
  CloseOutlined,
  ShrinkOutlined
} from '@ant-design/icons-vue'
import axios from 'axios'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  source: {
    type: [String, Object, Blob],
    required: true,
    description: 'PDF源，可以是URL或File对象'
  },
  title: {
    type: String,
    default: '',
    description: 'PDF文档标题'
  },
  // 控制放大状态
  expand: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['loaded', 'error', 'close', 'fullscreen', 'shrink'])

// 获取 store 中的移动端状态
const store = useStore()
const isMobile = computed(() => store.getters['device/isMobile'])

// 状态管理
const iframeRef = ref(null)
const pdfContainer = ref(null)
const loading = ref(true)
const error = ref(null)
const pdfBlob = ref(null)
const isExpanded = ref(props.expand)

watch(
  () => props.expand,
  val => {
    isExpanded.value = !!val
    if (val) {
      emit('fullscreen')
    }
  },
  { immediate: true }
)
// 计算显示标题
const displayTitle = computed(() => {
  if (props.title) {
    return props.title
  }

  if (typeof props.source === 'string') {
    // 如果是URL，尝试从URL中提取文件名
    if (props.source.startsWith('http') || props.source.startsWith('/')) {
      const url = new URL(props.source, window.location.origin)
      const pathname = url.pathname
      const filename = pathname.split('/').pop()
      if (filename && filename.includes('.')) {
        return filename
      }
    }
    // 如果是直接的PDF内容，使用默认标题
    return t('docViewer.pdfDocument')
  }

  if (props.source instanceof File) {
    return props.source.name
  }

  if (props.source instanceof Blob) {
    return t('docViewer.pdfDocument')
  }

  return t('docViewer.pdfDocument')
})

// 计算iframe的src属性
const iframeSource = computed(() => {
  let sourceUrl = ''

  if (pdfBlob.value) {
    // 如果有blob数据，使用blob URL
    sourceUrl = URL.createObjectURL(pdfBlob.value)
  } else if (typeof props.source === 'string') {
    // 如果是URL，直接返回
    sourceUrl = props.source
  } else if (props.source instanceof Blob || props.source instanceof File) {
    // 如果是Blob或File对象，创建对象URL
    sourceUrl = URL.createObjectURL(props.source)
  }

  console.info('sourceUrl:', sourceUrl)

  // 为PDF URL添加默认100%缩放参数
  if (sourceUrl && sourceUrl.toLowerCase().includes('.pdf')) {
    const url = new URL(sourceUrl, window.location.origin)
    url.searchParams.set('zoom', '1') // 设置默认100%放大倍数
    url.searchParams.set('toolbar', '1') // 显示工具栏
    url.searchParams.set('navpanes', '1') // 显示导航面板（目录）
    url.searchParams.set('scrollbar', '1') // 显示滚动条
    url.searchParams.set('statusbar', '1') // 显示状态栏
    url.searchParams.set('messages', '1') // 显示消息
    url.searchParams.set('view', 'Fit') // 设置默认视图模式
    console.info('searchParams url:', url)
    return url.toString()
  }

  return sourceUrl
})

// 加载PDF内容
const loadPdfContent = async () => {
  try {
    loading.value = true
    error.value = null

    if (typeof props.source === 'string') {
      if (props.source.startsWith('http')) {
        // 使用axios请求（需要授权）
        const response = await axios.get(props.source, {
          responseType: 'blob',
          headers: {
            'Content-Type': 'application/pdf'
          }
        })
        pdfBlob.value = response.data
      } else if (props.source.startsWith('/')) {
        // 使用fetch请求（不需要授权）
        const response = await fetch(props.source)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        pdfBlob.value = await response.blob()
      } else {
        // 其他情况，可能是本地文件路径
        const response = await fetch(props.source)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        pdfBlob.value = await response.blob()
      }
    } else if (props.source instanceof Blob) {
      pdfBlob.value = props.source
    } else if (props.source instanceof File) {
      pdfBlob.value = props.source
    }
  } catch (err) {
    console.error('加载PDF失败:', err)
    error.value = err.message || t('docViewer.pdfLoadFailed')
  } finally {
    loading.value = false
    loading.value = false
  }
}

// 下载PDF
const downloadPdf = () => {
  if (typeof props.source === 'string') {
    // 如果是URL，创建一个临时的a标签来下载
    const link = document.createElement('a')
    link.href = props.source
    link.download = props.title || 'document.pdf'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } else if (props.source instanceof Blob || props.source instanceof File) {
    // 如果是Blob或File对象，直接下载
    const url = URL.createObjectURL(props.source)
    const link = document.createElement('a')
    link.href = url
    link.download = props.title || props.source.name || 'document.pdf'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
}

// 关闭查看器
const closeViewer = () => {
  emit('close')
}

// 放大缩小切换
const ArrowsOrShrink = () => {
  if (isExpanded.value) {
    isExpanded.value = false
    emit('shrink')
  } else {
    isExpanded.value = true
    emit('fullscreen')
  }
}

// 事件处理
const onIframeLoad = () => {
  loading.value = false
  error.value = null
  emit('loaded', { success: true })
}

const onIframeError = err => {
  loading.value = false
  error.value = `${t('docViewer.pdfLoadFailed')}: ${err.message || t('docViewer.unknownError')}`
  emit('error', err)
}

// 监听源变化，重新加载内容
watch(
  () => props.source,
  () => {
    loadPdfContent()
  },
  { immediate: true }
)

// 组件挂载时加载内容
onMounted(() => {
  loadPdfContent()
})

// 组件卸载时清理对象URL
onUnmounted(() => {
  // 如果source是Blob或File对象，释放对象URL
  if (
    typeof props.source !== 'string' &&
    iframeSource.value.startsWith('blob:')
  ) {
    URL.revokeObjectURL(iframeSource.value)
  }
  // 清理pdfBlob创建的对象URL
  if (pdfBlob.value && iframeSource.value.startsWith('blob:')) {
    URL.revokeObjectURL(iframeSource.value)
  }
})
</script>

<style scoped>
.pdf-viewer-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-secondary);
  position: relative;
}

.pdf-toolbar {
  display: flex;
  position: absolute;
  top: 0;
  right: 0;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
  padding: 0.75rem 1rem;
  background-color: var(--bg-primary);
  opacity: 0.9;
}

.pdf-actions {
  display: flex;
  position: absolute;
  right: 5px;
  z-index: 99;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toolbar-btn {
  padding: 0.25rem;
  border: none;
  background: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.toolbar-btn :deep(svg) {
  width: 18px;
  height: 18px;
}

.toolbar-btn:hover {
  background-color: var(--hover-bg);
}

.close-btn:hover {
  background-color: var(--error-color);
  color: white;
}

.pdf-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-primary);
  opacity: 0.8;
  z-index: 10;
}

.spinner {
  border: 3px solid var(--border-light);
  border-radius: 50%;
  border-top: 3px solid var(--primary-color);
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.error-message {
  padding: 1rem;
  background-color: var(--bg-secondary);
  color: var(--error-color);
  border-radius: 0.375rem;
  max-width: 28rem;
  margin: 1rem auto;
  text-align: center;
}
</style>
