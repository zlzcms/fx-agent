<template>
  <div class="pdf-page-container">
    <div class="pdf-content-wrapper">
      <div class="pdf-sidebar" :class="{ hidden: !showSidebar }">
        <div class="sidebar-header">
          <h2>PDF文件</h2>
          <button @click="toggleSidebar" class="close-btn">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="file-upload">
          <label for="pdf-upload" class="upload-label">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>上传PDF文件</span>
          </label>
          <input
            type="file"
            id="pdf-upload"
            @change="handleFileUpload"
            class="hidden-input"
          />
        </div>
        <div class="sample-files">
          <h3>示例文件</h3>
          <ul>
            <li
              v-for="(file, index) in sampleFiles"
              :key="index"
              @click="loadSampleFile(file)"
              :class="{ active: currentFile === file.url }"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path
                  d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                ></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              <span>{{ file.name }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="pdf-main-content">
        <div class="sidebar-toggle" v-if="!showSidebar" @click="toggleSidebar">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </div>

        <div v-if="!currentFile" class="pdf-placeholder">
          <div class="placeholder-content">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
              ></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <h2>没有打开的PDF文件</h2>
            <p>请从左侧选择一个示例文件或上传您自己的PDF文件</p>
            <button @click="toggleSidebar" class="open-sidebar-btn">
              打开文件浏览器
            </button>
          </div>
        </div>

        <MarkdownViewer v-else :source="currentFile" />
        <!-- <PdfViewer 
          v-else 
          :source="currentFile" 
          :title="currentFileName" 
          @loaded="handlePdfLoaded" 
          @error="handlePdfError" 
        /> -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import PdfViewer from '@/components/PdfViewer.vue'
import MarkdownViewer from '../components/MarkdownViewer.vue'
// 状态管理
const showSidebar = ref(true)
const currentFile = ref(null)
const currentFileName = ref('')
const pdfLoaded = ref(false)
const pdfError = ref(null)

// 示例PDF文件
const sampleFiles = [
  {
    name: '示例PDF 1',
    url: 'https://raw.githubusercontent.com/mozilla/pdf.js/ba2edeae/web/compressed.tracemonkey-pldi-09.pdf'
  },
  {
    name: '示例PDF 2',
    url: 'https://raw.githubusercontent.com/mozilla/pdf.js/ba2edeae/test/pdfs/TAMReview.pdf'
  }
]

// 切换侧边栏显示
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

// 加载示例文件
const loadSampleFile = file => {
  currentFile.value = file.url
  currentFileName.value = file.name
  pdfError.value = null

  // 在移动设备上自动隐藏侧边栏
  if (window.innerWidth < 768) {
    showSidebar.value = false
  }
}

// 处理文件上传
const handleFileUpload = event => {
  const file = event.target.files[0]

  // 直接传递文件对象，组件内部会处理URL创建
  currentFile.value = file
  currentFileName.value = file.name
  pdfError.value = null

  // 在移动设备上自动隐藏侧边栏
  if (window.innerWidth < 768) {
    showSidebar.value = false
  }
}

// PDF加载事件处理
const handlePdfLoaded = data => {
  pdfLoaded.value = true
  pdfError.value = null
  console.log('PDF加载成功')
}

const handlePdfError = error => {
  pdfError.value = `加载PDF失败: ${error.message || '未知错误'}`
  console.error('PDF加载错误:', error)
}

// 组件挂载
onMounted(() => {
  // 响应式设计：在小屏幕上默认隐藏侧边栏
  if (window.innerWidth < 768) {
    showSidebar.value = false
  }
})

// 组件卸载时清理
onUnmounted(() => {
  // 清理工作由PdfViewer组件内部处理
})
</script>

<style scoped>
.pdf-page-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pdf-content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.pdf-sidebar {
  width: 280px;
  background-color: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: #f3f4f6;
}

.file-upload {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background-color 0.2s;
}

.upload-label:hover {
  border-color: #3b82f6;
  background-color: #f0f9ff;
}

.upload-label svg {
  margin-bottom: 0.5rem;
  color: #6b7280;
}

.hidden-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sample-files {
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

.sample-files h3 {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #4b5563;
}

.sample-files ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sample-files li {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sample-files li:hover {
  background-color: #f3f4f6;
}

.sample-files li.active {
  background-color: #e0f2fe;
  color: #0369a1;
}

.sample-files li svg {
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.pdf-main-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.sidebar-toggle {
  position: absolute;
  top: 1rem;
  left: 1rem;
  z-index: 10;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 0.5rem;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s;
}

.sidebar-toggle:hover {
  background-color: #f3f4f6;
}

.pdf-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f3f4f6;
}

.placeholder-content {
  text-align: center;
  padding: 2rem;
}

.placeholder-content svg {
  color: #9ca3af;
  margin-bottom: 1rem;
}

.placeholder-content h2 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: #374151;
}

.placeholder-content p {
  margin: 0 0 1.5rem;
  color: #6b7280;
}

.open-sidebar-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.open-sidebar-btn:hover {
  background-color: #2563eb;
}

@media (max-width: 768px) {
  .pdf-sidebar {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 20;
    transform: translateX(0);
  }

  .pdf-sidebar.hidden {
    transform: translateX(-100%);
  }

  .pdf-sidebar {
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }

  .pdf-sidebar.hidden {
    box-shadow: none;
  }
}
</style>
