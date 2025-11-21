<template>
  <div class="markdown-viewer-container">
    <div class="markdown-toolbar">
      <div class="markdown-info">{{ title_name }}</div>
      <div class="markdown-actions">
        <!-- 下载按钮下拉菜单 -->
        <Dropdown :trigger="['click']" placement="bottomRight">
          <button class="toolbar-btn" :title="$t('docViewer.downloadMarkdown')">
            <DownloadOutlined />
          </button>
          <template #overlay>
            <Menu>
              <MenuItem key="markdown" @click="downloadMarkdown">
                <div class="flex items-center">
                  <FileMarkdownOutlined />
                  <span class="ml-2">{{ $t('docViewer.downloadMarkdown') }}</span>
                </div>
              </MenuItem>
              <MenuItem key="pdf" @click="downloadPDF" :disabled="pdfGenerating">
                <div class="flex items-center">
                <FilePdfOutlined />
                <span class="ml-2">{{ $t('docViewer.downloadPdf') }}</span>
              </div>
              </MenuItem>
            </Menu>
          </template>
        </Dropdown>

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

    <div class="markdown-content" ref="markdownContainer">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">{{ $t('docViewer.loading') }}</div>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <div
        v-if="!loading && !error"
        class="markdown-body"
        v-html="renderedContent"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import {
  ArrowsAltOutlined,
  DownloadOutlined,
  CloseOutlined,
  ShrinkOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined
} from '@ant-design/icons-vue'
import { Dropdown, Menu, MenuItem } from 'ant-design-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import axios from 'axios'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  source: {
    type: [String, Object, Blob],
    required: true,
    description: 'Markdown源，可以是URL、文本内容或File对象'
  },
  title: {
    type: String,
    default: '',
    description: 'Markdown文档标题'
  },
  // 控制放大状态
  expand: {
    type: Boolean,
    default: false
  },
  filename: {
    type: String,
    default: '',
    description: 'Markdown文档文件名'
  }
})

const emit = defineEmits(['loaded', 'error', 'close', 'fullscreen', 'shrink'])

// 获取 store 中的移动端状态
const store = useStore()
const isMobile = computed(() => store.getters['device/isMobile'])

// 状态管理
const loading = ref(true)
const error = ref(null)
const markdownContent = ref('')
const isExpanded = ref(props.expand)
const pdfGenerating = ref(false) // PDF 生成状态
const markdownContainer = ref(null) // Markdown 容器引用

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

// 配置 marked 渲染器
const renderer = new marked.Renderer()

// 重写 code 方法来处理 mermaid 和 echarts 代码块
renderer.code = function({ text, lang, escaped }) {
  // 如果是 mermaid 代码块，保持原始文本不转义
  if (lang === 'mermaid') {
    return `<pre class="mermaid-code"><code class="language-mermaid">${text}</code></pre>`
  }
  
  // 如果是 echarts 代码块，保持原始文本不转义
  if (lang === 'echarts') {
    return `<pre class="echarts-code"><code class="language-echarts">${text}</code></pre>`
  }
  
  // 其他代码块使用默认渲染（需要转义）
  const language = lang || ''
  const code = escaped ? text : escapeHtml(text)
  const languageClass = language ? ` class="language-${language}"` : ''
  
  return `<pre><code${languageClass}>${code}</code></pre>`
}

// HTML 转义函数
function escapeHtml(html) {
  return html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// 渲染后的HTML内容
const renderedContent = computed(() => {
  if (!markdownContent.value) return ''

  try {
    // 使用marked渲染markdown，使用自定义渲染器
    const rawHtml = marked(markdownContent.value, {
      breaks: true,
      gfm: true,
      headerIds: true,
      mangle: false,
      renderer: renderer
    })

    // 使用DOMPurify清理HTML，防止XSS攻击
    // 需要允许 mermaid 相关的类名和标签
    return DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['class', 'data-processed'],
      ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr', 
                     'strong', 'em', 'del', 'a', 'img', 'ul', 'ol', 'li', 
                     'blockquote', 'pre', 'code', 'table', 'thead', 'tbody', 
                     'tr', 'th', 'td', 'div', 'span'],
      ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'id', 'data-processed']
    })
  } catch (err) {
    console.error('Markdown渲染错误:', err)
    return `<pre>${markdownContent.value}</pre>`
  }
})

const title_name = ref('')
// 加载markdown内容
const loadMarkdownContent = async () => {
  loading.value = true
  error.value = null
  try {
    if (typeof props.source === 'string') {
      if (props.source.startsWith('http')) {
        // 使用axios请求（需要授权）
        const response = await axios.get(props.source, {
          responseType: 'text',
          headers: {
            'Content-Type': 'text/plain'
          }
        })
        title_name.value = props.source.split('/').pop()
        markdownContent.value = response.data
      } else if (props.source.startsWith('/')) {
        // 使用fetch请求（不需要授权）
        const response = await fetch(props.source)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        title_name.value = props.source.split('/').pop()
        markdownContent.value = await response.text()
      } else {
        // 如果是markdown文本内容
        title_name.value = props.filename || t('docViewer.markdownDocument')
        markdownContent.value = props.source
      }
    } else if (props.source instanceof Blob || props.source instanceof File) {
      // 如果是Blob或File对象
      markdownContent.value = await props.source.text()
    } else {
      throw new Error(t('docViewer.unsupportedSourceType'))
    }

    emit('loaded', { success: true })
  } catch (err) {
    console.error('加载Markdown失败:', err)
    error.value = `${t('docViewer.loadFailed')}: ${err.message || t('docViewer.unknownError')}`
    emit('error', err)
  } finally {
    loading.value = false
  }
}
const UserInfo = ref(undefined)
// 加载本地用户信息
const loadLocalUserInfo = () => {
  const userInfo = localStorage.getItem('user')
  const user = JSON.parse(userInfo)
  UserInfo.value = user
  console.info("userInfo: ", user.username)

}

// 渲染 Mermaid 图表
const renderMermaidCharts = async () => {
  await nextTick()
  
  const container = markdownContainer.value
  if (!container) {
    console.warn('Markdown 容器未找到')
    return
  }

  // 找到所有的 mermaid 代码块
  const mermaidBlocks = container.querySelectorAll('pre.mermaid-code code.language-mermaid')
  
  // 如果没有 mermaid 图表，无需加载库
  if (mermaidBlocks.length === 0) {
    return
  }
  
  try {
    // 🚀 动态加载 Mermaid 库（按需加载）
    console.log('⏳ 开始加载 Mermaid 库...')
    const { default: mermaid } = await import('mermaid')
    console.log('✅ Mermaid 库加载完成')
    
    // 初始化 Mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'inherit'
    })
    
    // 使用 for...of 而不是 forEach，以便正确处理 async
    for (let index = 0; index < mermaidBlocks.length; index++) {
      const block = mermaidBlocks[index]
      try {
        const code = block.textContent
        const pre = block.parentElement
        
        if (!code || !pre) continue
        
        // 创建一个新的 div 来替换 pre 标签
        const mermaidDiv = document.createElement('div')
        mermaidDiv.className = 'mermaid-diagram'
        mermaidDiv.setAttribute('data-processed', 'true')
        
        // 使用 mermaid 渲染
        const id = `mermaid-${Date.now()}-${index}`
        const { svg } = await mermaid.render(id, code)
        mermaidDiv.innerHTML = svg
        
        // 替换原来的 pre 标签
        if (pre.parentElement) {
          pre.parentElement.replaceChild(mermaidDiv, pre)
        }
      } catch (err) {
        console.error(`Mermaid 渲染失败 (索引 ${index}):`, err)
        // 渲染失败时保留原始代码
      }
    }
  } catch (error) {
    console.error('加载 Mermaid 库失败:', error)
  }
}

// 渲染 ECharts 图表
const renderEChartsCharts = async () => {
  await nextTick()
  
  const container = markdownContainer.value
  if (!container) {
    console.warn('Markdown 容器未找到')
    return
  }

  // 找到所有的 echarts 代码块
  const echartsBlocks = container.querySelectorAll('pre.echarts-code code.language-echarts')
  
  // 如果没有 echarts 图表，无需加载库
  if (echartsBlocks.length === 0) {
    return
  }
  
  try {
    // 🚀 动态加载 ECharts 库（按需加载）
    console.log('⏳ 开始加载 ECharts 库...')
    const echarts = await import('echarts')
    console.log('✅ ECharts 库加载完成')
    
    for (let index = 0; index < echartsBlocks.length; index++) {
      const block = echartsBlocks[index]
      try {
        const code = block.textContent
        const pre = block.parentElement
        
        if (!code || !pre) continue
              
        // 创建一个新的 div 来替换 pre 标签
        const echartsDiv = document.createElement('div')
        echartsDiv.className = 'echarts-diagram'
        echartsDiv.setAttribute('data-processed', 'true')
        
        // 动态计算图表宽度
        const calculateChartWidth = () => {
          const isMobile = window.innerWidth <= 768
          const isSmallMobile = window.innerWidth <= 480
          const containerPadding = 32 // 容器的左右 padding
          
          if (isSmallMobile) {
            // 超小屏幕：屏幕宽度 - 容器padding - 图表padding
            return Math.max(250, window.innerWidth - containerPadding - 16)
          } else if (isMobile) {
            // 移动端：屏幕宽度 - 容器padding - 图表padding
            return Math.max(280, window.innerWidth - containerPadding - 32)
          } else {
            // PC端：容器宽度或最小300px
            const containerWidth = container?.offsetWidth || 600
            return Math.max(300, Math.min(containerWidth - 32, 800))
          }
        }
        
        // 动态计算图表高度
        const calculateChartHeight = () => {
          const isMobile = window.innerWidth <= 768
          const isSmallMobile = window.innerWidth <= 480
          
          if (isSmallMobile) {
            return 250
          } else if (isMobile) {
            return 300
          } else {
            return 400
          }
        }
        
        const chartWidth = calculateChartWidth()
        const chartHeight = calculateChartHeight()
        echartsDiv.style.width = `${chartWidth}px`
        echartsDiv.style.height = `${chartHeight}px`
              
        // 解析 JSON 配置
        const config = JSON.parse(code)
        
        // 使用 ECharts 渲染
        const chart = echarts.init(echartsDiv, null, {
          width: chartWidth,
          height: chartHeight
        })
        chart.setOption(config)
      
      // 监听窗口大小变化，重新计算并调整图表大小
      const resizeHandler = () => {
        const newWidth = calculateChartWidth()
        const newHeight = calculateChartHeight()
        echartsDiv.style.width = `${newWidth}px`
        echartsDiv.style.height = `${newHeight}px`
        chart.resize({
          width: newWidth,
          height: newHeight
        })
      }
      window.addEventListener('resize', resizeHandler)
      
      // 清理事件监听器
      const cleanup = () => {
        window.removeEventListener('resize', resizeHandler)
        chart.dispose()
      }
      
      // 在组件卸载时清理
      if (echartsDiv.parentElement) {
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && !document.contains(echartsDiv)) {
              cleanup()
              observer.disconnect()
            }
          })
        })
        observer.observe(document.body, { childList: true, subtree: true })
      }
      
        // 替换原来的 pre 标签
        if (pre.parentElement) {
          pre.parentElement.replaceChild(echartsDiv, pre)
        }
      } catch (err) {
        console.error(`ECharts 渲染失败 (索引 ${index}):`, err)
        // 渲染失败时保留原始代码
      }
    }
  } catch (error) {
    console.error('加载 ECharts 库失败:', error)
  }
}

onMounted(() => {
  loadLocalUserInfo()
})
// 从 markdownContent 第一行提取标题作为文件名备选
const getDefaultFilename = () => {
  if (props.filename) return props.filename
  if (props.title) return props.title
  
  // 从 markdownContent 第一行提取标题
  if (markdownContent.value) {
    const firstLine = markdownContent.value.split('\n')[0].trim()
    if (firstLine) {
      // 移除 markdown 标题标记（#、## 等）和前后空格
      const title = firstLine.replace(/^#+\s*/, '').trim()
      if (title) {
        // 清理文件名不合法字符
        return title.replace(/[<>:"/\\|?*]/g, '').substring(0, 100) // 限制长度避免文件名过长
      }
    }
  }
  
  return 'document'
}

// 下载Markdown
const downloadMarkdown = () => {
  if (!markdownContent.value) {
    return
  }

  const blob = new Blob([markdownContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = getDefaultFilename() + '.md'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 下载PDF
const downloadPDF = async () => {
  if (!markdownContent.value || pdfGenerating.value) {
    return
  }

  try {
    pdfGenerating.value = true
    
    // 🚀 动态加载 PDF 导出相关库（按需加载，减少首屏体积）
    console.log('⏳ 开始加载 PDF 导出库...')
    const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf')
    ])
    console.log('✅ PDF 导出库加载完成')
    
    // 获取 markdown 内容容器
    const markdownBody = document.querySelector('.markdown-body')
    if (!markdownBody) {
      throw new Error('找不到 Markdown 内容')
    }

    // 使用 html2canvas 将内容转换为图片
    const canvas = await html2canvas(markdownBody, {
      scale: 2, // 提高分辨率
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    })

    // 创建 PDF
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const imgData = canvas.toDataURL('image/png')
    
    // PDF 页面尺寸和内边距设置
    const pageWidth = 210 // A4 宽度 (mm)
    const pageHeight = 297 // A4 高度 (mm)
    const margin = 20 // 内边距 (mm)
    const contentWidth = pageWidth - 2 * margin // 内容区域宽度
    const contentHeight = pageHeight - 2 * margin // 内容区域高度
    
    // 计算图片在内容区域内的尺寸
    const imgHeight = (canvas.height * contentWidth) / canvas.width
    let heightLeft = imgHeight
    let position = margin // 从顶部内边距开始

    // 添加水印的函数
    const addWatermark = () => {
      pdf.saveGraphicsState()
      pdf.setGState(new pdf.GState({ opacity: 0.1 })) // 设置透明度
      pdf.setTextColor(128, 128, 128) // 灰色
      pdf.setFontSize(60) // 大字体
      
      // 旋转文本（对角线水印）
      const centerX = pageWidth / 2
      const centerY = pageHeight / 2
      const watermarkText = 'AI assistant ' + UserInfo.value.username
      pdf.text(watermarkText, centerX, centerY-100, {
        angle: 45, // 45度角
        align: 'center',
        baseline: 'middle'
      })
      pdf.text(watermarkText, centerX, centerY, {
        angle: 45, // 45度角
        align: 'center',
        baseline: 'middle'
      })
      pdf.text(watermarkText, centerX, centerY+100, {
        angle: 45, // 45度角
        align: 'center',
        baseline: 'middle'
      })
      pdf.text(watermarkText, centerX + 50, centerY+200, {
        angle: 45, // 45度角
        align: 'center',
        baseline: 'middle'
      })
      pdf.restoreGraphicsState()
    }

    // 添加第一页
    pdf.addImage(imgData, 'PNG', margin, position, contentWidth, imgHeight)
    addWatermark() // 添加水印
    heightLeft -= contentHeight

    // 如果内容超过一页，继续添加页面
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight + margin
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', margin, position, contentWidth, imgHeight)
      addWatermark() // 为每一页添加水印
      heightLeft -= contentHeight
    }

    // 下载 PDF
    const filename = getDefaultFilename() + '.pdf'
    pdf.save(filename)
  } catch (err) {
    console.error('生成PDF失败:', err)
    // 可以在这里添加错误提示
  } finally {
    pdfGenerating.value = false
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

// 监听渲染内容变化，触发 Mermaid 和 ECharts 渲染
watch(
  renderedContent,
  async (newContent) => {
    if (newContent && !loading.value) {
      await nextTick()
      await renderMermaidCharts()
      await renderEChartsCharts()
    }
  }
)

// 监听源变化，重新加载内容
watch(
  () => props.source,
  () => {
    loadMarkdownContent()
  },
  { immediate: true }
)
</script>

<style scoped>
.markdown-viewer-container {
  height: 100%;
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  position: relative;
  overflow: hidden; /* 防止父级产生滚动条 */
}

.markdown-toolbar {
  display: flex;
  position: absolute;
  top: 0;
  width: 100%;
  box-sizing: border-box;
  justify-content: space-between;
  background-color: var(--bg-secondary);
  align-items: center;
  z-index: 1;
  padding: 0.75rem 1rem;
}

.markdown-info {
  font-weight: 600;
  font-size: 1.2rem;
}

.markdown-actions {
  display: flex;
  position: absolute;
  right: 5px;
  z-index: 99;
  align-items: center;
  background-color: var(--bg-secondary);
  gap: 0.5rem;
  
}

.toolbar-btn {
  padding: 0.25rem;
  border: none;
  background: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
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

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-btn:disabled:hover {
  background-color: transparent;
}

.close-btn:hover {
  background-color: var(--error-color);
  color: white;
}

.markdown-content {
  flex: 1;
  min-width: 0;
  position: relative;
  overflow-x: auto;
  overflow-y: auto;
  padding: 1rem;
  margin-top: 60px; /* 为工具栏留出空间 */
  box-sizing: border-box;
  font-size: 14px;
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

.markdown-body {
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
  min-width: 100%; /* 至少占满容器宽度 */
  display: table; /* 使用 table 布局来确保宽度计算正确 */
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
  white-space: pre;
  word-wrap: normal;
  overflow-wrap: normal;
}

.markdown-body :deep(pre) {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
  white-space: pre;
  word-wrap: normal;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 1rem 0;
  width: max-content;
  min-width: 100%;
  white-space: nowrap;
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
  white-space: nowrap;
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

/* 自定义滚动条样式 */
.markdown-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.markdown-content::-webkit-scrollbar-track {
  background: var(--bg-secondary, #f1f1f1);
  border-radius: 4px;
}

.markdown-content::-webkit-scrollbar-thumb {
  background: var(--border-color, #c1c1c1);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.markdown-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary, #999);
}

/* Mermaid 图表样式 */
.markdown-body :deep(.mermaid-diagram) {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: var(--bg-secondary);
  border-radius: 0.5rem;
  overflow-x: auto;
  display: flex;
  justify-content: center;
  align-items: center;
}

.markdown-body :deep(.mermaid-diagram svg) {
  max-width: 100%;
  height: auto;
}

/* ECharts 图表样式 */
.markdown-body :deep(.echarts-diagram) {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: var(--bg-secondary);
  border-radius: 0.5rem;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  box-sizing: border-box;
}

.markdown-body :deep(.echarts-diagram canvas) {
  max-width: 100%;
  height: auto;
}

/* 移动端 ECharts 图表样式优化 */
@media (max-width: 768px) {
  .markdown-body :deep(.echarts-diagram) {
    margin: 1rem 0;
    padding: 0.5rem;
    height: 300px;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .markdown-body :deep(.echarts-diagram) {
    margin: 0.5rem 0;
    padding: 0.25rem;
    height: 250px;
  }
}
</style>
