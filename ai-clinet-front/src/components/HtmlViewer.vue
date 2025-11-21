<template>
  <div class="html-viewer-container">
    <div class="html-toolbar">
      <div class="html-info">{{ title_name }}</div>
      <div class="html-actions">
        <!-- 下载按钮 -->
        <button @click="downloadHtml" class="toolbar-btn" :title="$t('docViewer.download')">
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

    <div class="html-content" ref="htmlContainer">
      <iframe
        v-if="iframeSource && !error"
        :src="iframeSource"
        class="html-iframe"
        ref="iframeRef"
        @load="onIframeLoad"
        @error="onIframeError"
        sandbox="allow-same-origin allow-scripts allow-forms"
        :style="{ display: loading ? 'none' : 'block' }"
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
import DOMPurify from 'dompurify'

const { t } = useI18n()

const props = defineProps({
  source: {
    type: [String, Object, Blob],
    required: true,
    description: 'HTML源，可以是URL、文本内容或File对象'
  },
  title: {
    type: String,
    default: '',
    description: 'HTML文档标题'
  },
  // 控制放大状态
  expand: {
    type: Boolean,
    default: false
  },
  filename: {
    type: String,
    default: '',
    description: 'HTML文档文件名'
  }
})

const emit = defineEmits(['loaded', 'error', 'close', 'fullscreen', 'shrink'])

// 获取 store 中的移动端状态
const store = useStore()
const isMobile = computed(() => store.getters['device/isMobile'])

// 状态管理
const iframeRef = ref(null)
const htmlContainer = ref(null)
const loading = ref(true)
const error = ref(null)
const htmlBlob = ref(null)
const htmlContent = ref('')
const htmlBlobUrl = ref(null) // 存储创建的 blob URL
const isExpanded = ref(props.expand)
const title_name = ref('')

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
    // 如果是直接的HTML内容，使用默认标题
    return t('docViewer.htmlDocument')
  }

  if (props.source instanceof File) {
    return props.source.name
  }

  if (props.source instanceof Blob) {
    return t('docViewer.htmlDocument')
  }

  return t('docViewer.htmlDocument')
})

// 计算iframe的src属性
const iframeSource = computed(() => {
  if (htmlBlobUrl.value) {
    // 如果有blob URL，直接返回
    return htmlBlobUrl.value
  } else if (typeof props.source === 'string') {
    // 如果是URL，直接返回（public目录中的文件可以直接加载）
    if (props.source.startsWith('http') || props.source.startsWith('/')) {
      return props.source
    }
  } else if (props.source instanceof Blob || props.source instanceof File) {
    // 如果是Blob或File对象，且还没有创建URL，则创建
    if (!htmlBlobUrl.value) {
      htmlBlobUrl.value = URL.createObjectURL(props.source)
    }
    return htmlBlobUrl.value
  }

  return null
})

// 加载HTML内容
const loadHtmlContent = async () => {
  try {
    loading.value = true
    error.value = null

    if (typeof props.source === 'string') {
      if (props.source.startsWith('http')) {
        // 需要鉴权的远程HTML，使用axios携带认证信息获取，再通过blob注入iframe
        const response = await axios.get(props.source, {
          responseType: 'text',
          headers: {
            'Content-Type': 'text/html'
          }
        })
        title_name.value = props.source.split('/').pop()
        // 清理HTML内容，防止XSS攻击
        htmlContent.value = DOMPurify.sanitize(response.data, {
          ADD_TAGS: ['iframe', 'embed', 'object'],
          ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling']
        })
        htmlBlob.value = new Blob([htmlContent.value], { type: 'text/html' })
        // 使用blob URL 作为iframe的src，避免直接命中需要鉴权的地址
        htmlBlobUrl.value = URL.createObjectURL(htmlBlob.value)
        loading.value = false
      } else if (props.source.startsWith('/')) {
        // 以 / 开头的地址：区分 public 静态资源 和 需要鉴权的 /api/ 接口
        if (props.source.startsWith('/api/')) {
          // 需要鉴权的接口，同样通过axios获取内容再注入iframe
          const response = await axios.get(props.source, {
            responseType: 'text',
            headers: {
              'Content-Type': 'text/html'
            }
          })
          title_name.value = props.source.split('/').pop() || props.filename || t('docViewer.htmlDocument')
          htmlContent.value = DOMPurify.sanitize(response.data, {
            ADD_TAGS: ['iframe', 'embed', 'object'],
            ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling']
          })
          htmlBlob.value = new Blob([htmlContent.value], { type: 'text/html' })
          htmlBlobUrl.value = URL.createObjectURL(htmlBlob.value)
          loading.value = false
        } else {
          // 对于public目录中的HTML文件，直接使用iframe加载，不需要fetch和sanitize
          // 这样可以保证外部脚本（如Chart.js）能正常加载和执行
          title_name.value = props.source.split('/').pop() || props.filename || t('docViewer.htmlDocument')
          // 不需要创建blob，直接使用iframe加载URL
          // loading状态会在iframe的@load事件中处理（onIframeLoad函数）
          // 注意：iframe需要渲染才能触发load事件，所以我们在模板中允许iframe渲染但隐藏它
          return
        }
      } else {
        // 如果是HTML文本内容
        title_name.value = props.filename || t('docViewer.htmlDocument')
        // 清理HTML内容，防止XSS攻击
        htmlContent.value = DOMPurify.sanitize(props.source, {
          ADD_TAGS: ['iframe', 'embed', 'object'],
          ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling']
        })
        loading.value = false
      }
    } else if (props.source instanceof Blob || props.source instanceof File) {
      // 如果是Blob或File对象
      title_name.value = props.source instanceof File ? props.source.name : props.filename || t('docViewer.htmlDocument')
      const text = await props.source.text()
      // 清理HTML内容，防止XSS攻击
      htmlContent.value = DOMPurify.sanitize(text, {
        ADD_TAGS: ['iframe', 'embed', 'object'],
        ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling']
      })
      htmlBlob.value = new Blob([htmlContent.value], { type: 'text/html' })
      loading.value = false
    }
  } catch (err) {
    console.error('加载HTML失败:', err)
    error.value = err.message || t('docViewer.htmlLoadFailed')
    emit('error', err)
    loading.value = false
  }
  // 注意：对于以'/'开头的URL，上面的return会提前退出，不会执行到这里
}

// 下载HTML
const downloadHtml = () => {
  if (htmlContent.value) {
    const blob = new Blob([htmlContent.value], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = (props.filename || props.title || displayTitle.value || 'document') + '.html'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } else if (typeof props.source === 'string') {
    // 如果是URL，创建一个临时的a标签来下载
    const link = document.createElement('a')
    link.href = props.source
    link.download = props.title || displayTitle.value || 'document.html'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } else if (props.source instanceof Blob || props.source instanceof File) {
    // 如果是Blob或File对象，直接下载
    const url = URL.createObjectURL(props.source)
    const link = document.createElement('a')
    link.href = url
    link.download = props.title || props.source.name || 'document.html'
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
  error.value = `${t('docViewer.htmlLoadFailed')}: ${err.message || t('docViewer.unknownError')}`
  emit('error', err)
}

// 监听源变化，重新加载内容
watch(
  () => props.source,
  () => {
    loadHtmlContent()
  },
  { immediate: true }
)

// 组件挂载时加载内容
onMounted(() => {
  loadHtmlContent()
})

// 组件卸载时清理对象URL
onUnmounted(() => {
  // 清理所有创建的blob URL
  if (iframeSource.value && iframeSource.value.startsWith('blob:')) {
    URL.revokeObjectURL(iframeSource.value)
  }
  if (htmlBlob.value && iframeSource.value && iframeSource.value.startsWith('blob:')) {
    URL.revokeObjectURL(iframeSource.value)
  }
})
</script>

<style scoped>
.html-viewer-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  position: relative;
  overflow: hidden;
}

.html-toolbar {
  display: flex;
  position: absolute;
  top: 0;
  width: 100%;
  box-sizing: border-box;
  justify-content: space-between;
  background-color: var(--bg-secondary);
  align-items: center;
  z-index: 1000;
  padding: 0.75rem 1rem;
  opacity: 0.9;
}

.html-info {
  font-weight: 600;
  font-size: 1.2rem;
}

.html-actions {
  display: flex;
  position: absolute;
  right: 5px;
  z-index: 99;
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

.html-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  margin-top: 60px; /* 为工具栏留出空间 */
}

.html-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background-color: var(--bg-primary);
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
