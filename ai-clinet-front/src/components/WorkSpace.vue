<template>
  <div class="workspace-container">
    <!-- 头部区域 -->
    <div class="workspace-header">
      <div class="header-left">
        <h2 class="workspace-title">{{ $t('workspace.title') }}</h2>
      </div>
      <div class="header-right">
        <button class="close-btn" @click="handleClose">
          <CloseOutlined />
        </button>
      </div>
    </div>

    <!-- 任务状态区域 -->
    <div class="task-status">
      <div class="task-item completed">
        <span class="task-text">{{ $t('workspace.aiWorking') }}</span>
      </div>
    </div>

    <!-- 文件信息区域 -->
    <div class="file-section">
      <div class="file-container">
        <!-- 头部标题区域 -->
        <div class="file-header flex items-center justify-center">
          <span class="file-title">{{ title_name }}</span>
        </div>

        <!-- 中间内容区域 -->
        <div class="file-content">
          <div v-if="loading" class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">{{ $t('workspace.loadingFile') }}</div>
          </div>

          <div v-else-if="error" class="error-content">
            <div class="error-text">{{ error }}</div>
          </div>

          <div v-else class="todo-content" :class="`content-${fileType}`">
            <div
              class="markdown-body"
              v-if="fileType === 'md'"
              v-html="fileContent"
            ></div>
            <pre v-else-if="fileType === 'json'" class="json-content">{{
              fileContent
            }}</pre>
            <CsvViewer
              v-else-if="fileType === 'csv'"
              :source="fileContent"
              :hideHead="true"
            />
            <div v-else class="text-content">{{ fileContent }}</div>
          </div>
        </div>

        <!-- 底部进度条区域 -->
        <div class="file-progress">
          <div class="progress-controls">
            <button class="control-btn prev-btn">
              <StepBackwardOutlined />
            </button>
            <button class="control-btn play-btn">
              <StepForwardOutlined />
            </button>
          </div>

          <div class="progress-bar">
            <Progress
              :percent="99.99"
              :show-info="false"
              stroke-color="var(--primary-color)"
              trail-color="var(--border-color)"
              status="active"
              size="small"
            />
          </div>

          <div class="progress-status">
            <span class="status-dot"></span>
            <span class="status-text">{{ $t('workspace.realtime') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, defineAsyncComponent } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

// 使用异步组件按需加载 CsvViewer（避免首屏加载）
const CsvViewer = defineAsyncComponent(() => import('./CsvViewer.vue'))
import {
  CloseOutlined,
  StepBackwardOutlined,
  StepForwardOutlined
} from '@ant-design/icons-vue'
import { Progress } from 'ant-design-vue'

const { t } = useI18n()

// Props
const props = defineProps({
  source: {
    type: String,
    default: ''
  }
})
const title_name = ref('')
// Emits
const emit = defineEmits(['close', 'chat'])

// 响应式数据
const currentTime = ref('')
const fileContent = ref('')
const loading = ref(false)
const error = ref(null)
const fileType = ref('')

// 获取文件类型
const getFileType = url => {
  if (!url) return ''
  const fileName = url.split('/').pop()
  const extension = fileName.split('.').pop().toLowerCase()
  return extension
}

// 格式化文件内容
const formatContent = (content, type) => {
  switch (type) {
    case 'json':
      try {
        const parsed = JSON.parse(content)
        return JSON.stringify(parsed, null, 2)
      } catch (e) {
        return content
      }
    case 'md':
      try {
        const html = marked(content)
        return DOMPurify.sanitize(html)
      } catch (e) {
        return content
      }
    case 'csv':
      // CSV内容保持原样，可以后续添加表格渲染
      return content
    default:
      return content
  }
}

// 加载文件内容
const loadFileContent = async () => {
  if (!props.source || !props.source.startsWith('http')) {
    fileContent.value = props.source
    return
  }
  loading.value = true
  error.value = null
  title_name.value = props.source.split('/').pop()
  try {
    const type = getFileType(props.source)
    fileType.value = type

    let response
    if (type === 'json') {
      response = await axios.get(props.source, {
        responseType: 'json'
      })
      fileContent.value = formatContent(JSON.stringify(response.data), type)
    } else {
      response = await axios.get(props.source, {
        responseType: 'text'
      })
      fileContent.value = formatContent(response.data, type)
    }
  } catch (err) {
    console.error('加载文件失败:', err)
    error.value = `${t('workspace.loadFailed')}: ${err.message || t('docViewer.unknownError')}`
    fileContent.value = `${t('workspace.loadFailed')}: ${err.message}`
  } finally {
    loading.value = false
  }
}

// 更新时间
const updateTime = () => {
  const now = new Date()
  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')
  currentTime.value = `${hours}:${minutes}`
}

// 处理关闭
const handleClose = () => {
  emit('close')
}

// 监听source变化
watch(
  () => props.source,
  () => {
    console.info('loadFileContent0: ', props.source)
    loadFileContent()
  },
  { immediate: true }
)

// 组件挂载时启动时间更新
let timeInterval
onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 60000) // 每分钟更新一次
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.workspace-container {
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 20px 12px 20px;
}

.header-left {
  flex: 1;
}

.workspace-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.timestamp {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-tertiary);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.workspace-tabs {
  display: flex;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-light);
}

.tab-btn {
  background: none;
  border: none;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-tertiary);
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  font-weight: 500;
}

.tab-btn:hover {
  color: var(--primary-color);
}

.tab-btn.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.task-status {
  padding: 0px 10px;
}

.task-item {
  display: inline-flex;
  align-items: center;
  padding: 6px 15px;
  background-color: var(--bg-tertiary);
  border-radius: 16px;
  font-size: 12px;
  transform: scale(0.8);
  transform-origin: left center;
}

.task-item.completed {
  color: var(--text-secondary);
}

.task-icon {
  font-size: 16px;
}

.task-text {
  font-size: 14px;
  font-weight: 500;
}

.file-section {
  margin: 16px;
  height: calc(100% - 320px);
  display: flex;
  flex-direction: column;
  flex: 1;
}

.file-container {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.file-header {
  background: var(--bg-secondary);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

.file-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.file-content {
  height: 100%;
  overflow: auto;
  background: var(--bg-primary);
  padding: 10px;
  flex: 1;
  overflow-y: auto;
}

.todo-content {
  height: 100%;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.todo-content h4 {
  margin: 16px 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-color);
}

.todo-content h4:first-child {
  margin-top: 0;
}

.todo-content p {
  color: var(--text-secondary);
}

/* 加载状态样式 */
.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-light);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
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
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 错误状态样式 */
.error-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--error-color);
}

.error-text {
  font-size: 14px;
  text-align: center;
}

/* 不同文件类型的样式 */
.content-json .json-content {
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
  white-space: pre-wrap;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.content-csv .csv-content {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  overflow-x: auto;
  white-space: pre-wrap;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.content-md {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.content-md h1,
.content-md h2,
.content-md h3,
.content-md h4,
.content-md h5,
.content-md h6 {
  margin: 16px 0 8px 0;
  font-weight: 600;
  color: var(--text-primary);
}

.content-md h1:first-child,
.content-md h2:first-child,
.content-md h3:first-child,
.content-md h4:first-child,
.content-md h5:first-child,
.content-md h6:first-child {
  margin-top: 0;
}

.content-md p {
  margin: 8px 0;
  line-height: 1.6;
}

.content-md code {
  background: var(--bg-tertiary);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
}

.content-md pre {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  overflow-x: auto;
  margin: 12px 0;
}

.content-md pre code {
  background: none;
  padding: 0;
}

.content-md ul,
.content-md ol {
  padding-left: 20px;
  margin: 8px 0;
}

.content-md li {
  margin: 4px 0;
}

.content-md blockquote {
  border-left: 4px solid var(--primary-color);
  padding-left: 12px;
  margin: 12px 0;
  color: var(--text-secondary);
  font-style: italic;
}

.text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.file-progress {
  background: var(--bg-secondary);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-top: 1px solid var(--border-light);
}

.progress-controls {
  display: flex;
  gap: 4px;
}

.control-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  background: var(--active-bg);
  color: var(--primary-color);
}

.progress-bar {
  flex: 1;
  display: flex;
  align-items: center;
}

.progress-bar :deep(.ant-progress) {
  width: 100%;
}

.progress-bar :deep(.ant-progress-line) {
  margin-bottom: 0;
}

.progress-bar :deep(.ant-progress-bg) {
  height: 4px;
  border-radius: 2px;
}

.progress-bar :deep(.ant-progress-outer) {
  height: 4px;
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--error-color);
  border-radius: 50%;
}

.status-text {
  font-weight: 500;
}

.floating-chat-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  background: var(--primary-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px var(--shadow-color);
  transition: all 0.2s;
  color: white;
}

.floating-chat-btn:hover {
  background: var(--primary-hover);
  transform: scale(1.05);
  box-shadow: 0 4px 12px var(--shadow-color);
}

.floating-chat-btn svg {
  font-size: 16px;
}

/* 动画效果 */
.workspace-container {
  animation: slideIn 0.3s ease-out;
  height: 100%;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workspace-container {
    top: 10px;
    right: 10px;
    left: 10px;

    /* width: auto; */
  }
}

.markdown-body {
  line-height: 1.6;
  color: var(--text-primary);
}

/* Markdown样式 */
.markdown-body :deep(h1) {
  font-size: 2rem;
  font-weight: 600;
  margin: 1.5rem 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.markdown-body :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 1.25rem 0 0.75rem 0;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border-light);
}

.markdown-body :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

.markdown-body :deep(h4) {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0.75rem 0 0.5rem 0;
}

.markdown-body :deep(h5) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.5rem 0;
}

.markdown-body :deep(h6) {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0.5rem 0;
}

.markdown-body :deep(p) {
  margin: 0.75rem 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

.markdown-body :deep(li) {
  margin: 0.25rem 0;
}

.markdown-body :deep(blockquote) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-left: 4px solid var(--primary-color);
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
}

.markdown-body :deep(code) {
  background-color: var(--bg-tertiary);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875em;
}

.markdown-body :deep(pre) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 0.5rem;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: var(--bg-secondary);
  font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
  background-color: var(--bg-secondary);
}

.markdown-body :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 2rem 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(del) {
  text-decoration: line-through;
  color: var(--text-tertiary);
}
</style>
