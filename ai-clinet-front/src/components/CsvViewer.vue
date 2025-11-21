<template>
  <div class="csv-viewer-container">
    <div class="csv-toolbar">
      <!-- 标题 -->
      <div class="csv-title" v-if="!hideHead">
        <h3>{{ displayTitle }}</h3>
      </div>

      <div class="csv-actions" v-if="!hideHead">
        <!-- 下载按钮 -->
        <button @click="downloadCsv" class="toolbar-btn" :title="$t('docViewer.download')">
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

    <div class="csv-content" ref="csvContainer">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text">{{ $t('docViewer.loading') }}</div>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <div v-if="!loading && !error" class="luckysheet-container">
        <!-- LuckySheet 容器 -->
        <div
          id="luckysheet-container"
          ref="luckysheetContainer"
          class="luckysheet-wrapper"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import {
  ArrowsAltOutlined,
  DownloadOutlined,
  CloseOutlined,
  ShrinkOutlined
} from '@ant-design/icons-vue'
import axios from 'axios'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'
import { loadLuckySheet, isLuckySheetLoaded } from '@/utils/luckysheet-loader'

const { t } = useI18n()
const props = defineProps({
  source: {
    type: [String, Object, Blob],
    required: true,
    description: 'CSV源，可以是URL、文本内容或File对象'
  },
  title: {
    type: String,
    default: '',
    description: 'CSV文档标题'
  },
  hideHead: {
    type: Boolean,
    default: false
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
    // 如果是直接的CSV内容，使用默认标题
    return t('docViewer.csvData')
  }

  if (props.source instanceof File) {
    return props.source.name
  }

  if (props.source instanceof Blob) {
    return t('docViewer.csvFile')
  }

  return t('docViewer.csvData')
})

// 状态管理
const csvContainer = ref(null)
const luckysheetContainer = ref(null)
const loading = ref(true)
const error = ref(null)
const csvContent = ref('')
const luckysheetInstance = ref(null)
const csvData = ref([])
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

// 解析CSV内容
const parseCsv = content => {
  try {
    const lines = content.trim().split('\n')
    if (lines.length === 0) {
      throw new Error(t('docViewer.csvParseErrorEmpty'))
    }

    // 解析CSV行，处理引号内的逗号
    const parseCsvLine = line => {
      const result = []
      let current = ''
      let inQuotes = false

      for (let i = 0; i < line.length; i++) {
        const char = line[i]

        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim())
          current = ''
        } else {
          current += char
        }
      }

      result.push(current.trim())
      return result
    }

    // 解析所有行
    const parsedLines = lines.map(line => parseCsvLine(line))

    if (parsedLines.length === 0) {
      throw new Error(t('docViewer.csvParseErrorFormat'))
    }

    // 检查每行的列数是否一致
    const firstRowLength = parsedLines[0].length

    // 确保所有行都有相同的列数
    const normalizedLines = parsedLines.map((line, index) => {
      if (line.length < firstRowLength) {
        // 如果列数不足，用空字符串填充
        const paddedLine = [...line]
        while (paddedLine.length < firstRowLength) {
          paddedLine.push('')
        }
        return paddedLine
      }
      return line
    })

    // 所有行作为数据（包括表头）
    csvData.value = normalizedLines
  } catch (err) {
    console.error('CSV解析错误:', err)
    error.value = `${t('docViewer.csvParseError')}: ${err.message}`
  }
}

// 检查LuckySheet依赖是否完整
const checkLuckySheetDependencies = () => {
  const dependencies = {
    jquery: typeof window.$ !== 'undefined',
    mousewheel: typeof window.$.fn.mousewheel !== 'undefined',
    luckysheet: typeof window.luckysheet !== 'undefined'
  }

  console.log('LuckySheet依赖检查:', dependencies)

  if (!dependencies.jquery) {
    console.error('jQuery未加载')
    return false
  }

  if (!dependencies.mousewheel) {
    console.error('jQuery mousewheel插件未加载')
    return false
  }

  if (!dependencies.luckysheet) {
    console.error('LuckySheet未加载')
    return false
  }

  return true
}

// 初始化 LuckySheet
const initLuckySheet = async () => {
  if (!luckysheetContainer.value || csvData.value.length === 0) {
    console.log('LuckySheet初始化条件不满足')
    return
  }

  try {
    // 🚀 按需加载 LuckySheet（如果尚未加载）
    if (!isLuckySheetLoaded()) {
      console.log('⏳ 开始按需加载 LuckySheet...')
      loading.value = true
      try {
        await loadLuckySheet()
        console.log('✅ LuckySheet 加载完成')
      } catch (loadError) {
        console.error('❌ LuckySheet 加载失败:', loadError)
        error.value = `${t('docViewer.csvLoadError')}: ${loadError.message}`
        showFallbackTable()
        return
      } finally {
        loading.value = false
      }
    }

    // 检查所有依赖是否完整
    if (!checkLuckySheetDependencies()) {
      console.error('LuckySheet依赖不完整，使用回退表格')
      showFallbackTable()
      return
    }

    // 准备数据格式
    const celldata = []

    // 将 CSV 数据转换为 LuckySheet 的 celldata 格式
    csvData.value.forEach((row, rowIndex) => {
      row.forEach((cell, colIndex) => {
        celldata.push({
          r: rowIndex,
          c: colIndex,
          v: {
            v: cell,
            m: cell,
            ct: { fa: 'General', t: 'g' }
          }
        })
      })
    })

    // 配置选项
    const options = {
      container: 'luckysheet-container',
      title: props.title || 'CSV数据',
      lang: 'zh',
      showinfobar: false, // 隐藏信息栏
      showsheetbar: false, // 隐藏工作表栏
      showstatisticBar: false, // 隐藏统计栏
      enableAddRow: false, // 禁用添加行
      enableAddCol: false, // 禁用添加列
      allowEdit: false, // 允许编辑
      allowUpdate: true, // 允许更新
      data: [
        {
          name: 'Sheet1',
          color: '',
          index: 0,
          status: 1,
          order: 0,
          hide: 0,
          row: Math.max(csvData.value.length, 100), // 确保有足够的行
          column: Math.max(csvData.value[0]?.length || 0, 26), // 确保有足够的列
          defaultRowHeight: 25,
          defaultColWidth: 100,
          celldata: celldata,
          config: {
            merge: {},
            rowlen: {},
            columnlen: {},
            rowhidden: {},
            colhidden: {},
            borderInfo: []
          },
          scrollLeft: 0,
          scrollTop: 0,
          luckysheet_select_save: [],
          calcChain: [],
          isPivotTable: false,
          pivotTable: {},
          filter_select: {},
          filter: null,
          luckysheet_alternateformat_save: [],
          luckysheet_alternateformat_save_modelCustom: [],
          luckysheet_conditionformat_save: {},
          frozen: {},
          chart: [],
          zoomRatio: 1,
          image: [],
          showGridLines: 1,
          dataVerification: {}
        }
      ]
    }

    console.log('准备初始化 LuckySheet，选项:', options)

    // 初始化 LuckySheet
    try {
      luckysheetInstance.value = window.luckysheet.create(options)

      // 触发加载完成事件
      emit('loaded')
    } catch (initError) {
      console.error('LuckySheet初始化失败:', initError)
      showFallbackTable()
    }
  } catch (error) {
    console.error('LuckySheet初始化失败:', error)
    showFallbackTable()
  }
}

// 回退到普通表格显示
const showFallbackTable = () => {
  console.log('使用回退表格显示')

  if (!luckysheetContainer.value) {
    console.error('回退表格：容器不存在')
    return
  }

  luckysheetContainer.value.innerHTML = ''

  if (csvData.value.length === 0) {
    luckysheetContainer.value.innerHTML =
      `<div style="text-align: center; color: var(--text-secondary); padding: 20px;">${t('docViewer.noData')}</div>`
    return
  }

  // 创建表格容器
  const tableContainer = document.createElement('div')
  tableContainer.style.cssText = `
    width: 100%;
    height: 100%;
    overflow: auto;
    position: relative;
    display: flex;
    flex-direction: column;
  `

  // 创建工具栏
  const toolbar = document.createElement('div')
  toolbar.style.cssText = `
    padding: 8px 12px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
  `

  // 添加文件名显示
  const fileName = document.createElement('span')
  fileName.textContent = displayTitle.value
  fileName.style.cssText = `
    font-weight: 600;
    color: var(--text-primary);
    font-size: 14px;
    margin-right: 16px;
  `
  toolbar.appendChild(fileName)

  // 添加搜索框
  const searchInput = document.createElement('input')
  searchInput.type = 'text'
  searchInput.placeholder = t('docViewer.search')
  searchInput.style.cssText = `
    padding: 4px 8px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 14px;
    min-width: 200px;
    background: var(--bg-primary);
    color: var(--text-primary);
  `
  toolbar.appendChild(searchInput)

  // 添加行数显示
  const rowCount = document.createElement('span')
  rowCount.textContent = t('docViewer.totalRows', { count: csvData.value.length - 1 })
  rowCount.style.cssText = `
    color: var(--text-secondary);
    font-size: 14px;
    margin-left: auto;
  `
  toolbar.appendChild(rowCount)

  tableContainer.appendChild(toolbar)

  // 创建表格
  const table = document.createElement('table')
  table.style.cssText = `
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    background: white;
    table-layout: fixed;
    min-width: max-content;
    flex: 1;
  `

  // 创建表头
  if (csvData.value[0]) {
    const thead = document.createElement('thead')
    const headerRow = document.createElement('tr')

    csvData.value[0].forEach((header, index) => {
      const th = document.createElement('th')
      th.textContent = header || `${t('docViewer.column')}${index + 1}`
      th.style.cssText = `
        padding: 12px 8px;
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
        font-weight: 600;
        text-align: center;
        word-wrap: break-word;
        overflow-wrap: break-word;
        position: sticky;
        top: 0;
        z-index: 10;
        min-width: 120px;
        max-width: 200px;
        cursor: pointer;
        user-select: none;
        color: var(--text-primary);
      `

      // 添加排序功能
      th.addEventListener('click', () => {
        sortTable(index)
      })

      headerRow.appendChild(th)
    })

    thead.appendChild(headerRow)
    table.appendChild(thead)
  }

  // 创建表体
  const tbody = document.createElement('tbody')
  let currentData = [...csvData.value.slice(1)] // 复制数据，排除表头

  // 排序功能
  const sortTable = columnIndex => {
    const th = table.querySelector(`th:nth-child(${columnIndex + 1})`)
    const isAscending = th.getAttribute('data-sort') !== 'asc'

    // 清除其他列的排序状态
    table.querySelectorAll('th').forEach(header => {
      header.removeAttribute('data-sort')
      header.textContent = header.textContent
        .replace(' ↑', '')
        .replace(' ↓', '')
    })

    // 设置当前列的排序状态
    th.setAttribute('data-sort', isAscending ? 'asc' : 'desc')
    th.textContent += isAscending ? ' ↑' : ' ↓'

    // 排序数据
    currentData.sort((a, b) => {
      const aVal = a[columnIndex] || ''
      const bVal = b[columnIndex] || ''

      if (isAscending) {
        return aVal.localeCompare(bVal)
      } else {
        return bVal.localeCompare(aVal)
      }
    })

    renderTableBody()
  }

  // 搜索功能
  const filterTable = searchTerm => {
    if (!searchTerm) {
      currentData = [...csvData.value.slice(1)]
    } else {
      currentData = csvData.value
        .slice(1)
        .filter(row =>
          row.some(
            cell =>
              cell &&
              cell.toString().toLowerCase().includes(searchTerm.toLowerCase())
          )
        )
    }
    renderTableBody()
    rowCount.textContent = t('docViewer.totalRows', { count: currentData.length })
  }

  // 渲染表体
  const renderTableBody = () => {
    tbody.innerHTML = ''

    currentData.forEach((row, rowIndex) => {
      const tr = document.createElement('tr')
      tr.style.cssText = `
        transition: background-color 0.2s;
      `

      // 添加行点击事件
      tr.addEventListener('click', () => {
        // 移除其他行的选中状态
        tbody.querySelectorAll('tr').forEach(r => {
          r.style.backgroundColor = ''
        })
        // 设置当前行选中状态
        tr.style.backgroundColor = 'var(--active-bg)'
      })

      // 添加行悬停效果
      tr.addEventListener('mouseenter', () => {
        if (!tr.style.backgroundColor.includes('var(--active-bg)')) {
          tr.style.backgroundColor = 'var(--hover-bg)'
        }
      })

      tr.addEventListener('mouseleave', () => {
        if (tr.style.backgroundColor.includes('var(--hover-bg)')) {
          tr.style.backgroundColor = ''
        }
      })

      row.forEach((cell, cellIndex) => {
        const td = document.createElement('td')
        td.textContent = cell || ''
        td.style.cssText = `
          padding: 8px;
          border: 1px solid var(--border-color);
          word-wrap: break-word;
          overflow-wrap: break-word;
          cursor: pointer;
          min-width: 120px;
          max-width: 200px;
          color: var(--text-primary);
          background: var(--bg-primary);
        `

        // 添加单元格点击事件
        td.addEventListener('click', e => {
          e.stopPropagation() // 阻止行点击事件
          // 可以在这里添加单元格编辑功能
          console.log('点击单元格:', {
            row: rowIndex + 1,
            col: cellIndex + 1,
            value: cell
          })
        })

        tr.appendChild(td)
      })

      tbody.appendChild(tr)
    })
  }

  // 绑定搜索事件
  searchInput.addEventListener('input', e => {
    filterTable(e.target.value)
  })

  // 初始渲染
  renderTableBody()

  table.appendChild(tbody)
  tableContainer.appendChild(table)
  luckysheetContainer.value.appendChild(tableContainer)

  console.log('回退表格显示完成')
}

// 加载CSV内容
const loadCsvContent = async () => {
  loading.value = true
  error.value = null
  csvContent.value = ''

  try {
    if (typeof props.source === 'string') {
      if (props.source.startsWith('http')) {
        // 使用axios请求（需要授权）
        const response = await axios.get(props.source, {
          responseType: 'arraybuffer'
        })
        csvContent.value = new TextDecoder().decode(response.data)
      } else if (props.source.startsWith('/')) {
        // 使用fetch请求（不需要授权）
        const response = await fetch(props.source)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        csvContent.value = await response.text()
      } else {
        // 如果是直接的CSV内容
        csvContent.value = props.source
      }
    } else if (props.source instanceof Blob || props.source instanceof File) {
      // 如果是File对象
      csvContent.value = await props.source.arrayBuffer()
    } else {
      throw new Error('不支持的源类型')
    }

    // 解析CSV内容
    parseCsv(csvContent.value)

    // 等待DOM更新后初始化LuckySheet
    await nextTick()

    // 先设置 loading 为 false，让容器元素渲染
    loading.value = false

    // 等待容器元素准备好
    let attempts = 0
    const maxAttempts = 10

    while (!luckysheetContainer.value && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 100))
      attempts++
      console.log(
        `等待容器元素 (第${attempts}次):`,
        !!luckysheetContainer.value
      )
    }

    if (luckysheetContainer.value) {
      console.log('容器元素已准备好，开始初始化 LuckySheet')
      await initLuckySheet()
    } else {
      console.error('容器元素准备超时')
      error.value = '容器初始化失败'
      loading.value = false
    }
  } catch (err) {
    console.error('加载CSV失败:', err)
    error.value = `${t('docViewer.loadFailed')}: ${err.message}`
    emit('error', err)
    loading.value = false
  }
}

// 下载CSV文件
const downloadCsv = () => {
  try {
    let content = ''

    if (luckysheetInstance.value) {
      // 从 LuckySheet 获取数据
      const data = luckysheetInstance.value.getAllSheets()
      // 这里需要将 LuckySheet 数据转换回 CSV 格式
      content = csvContent.value
    } else {
      content = csvContent.value
    }

    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)

    // 使用显示标题作为下载文件名，确保有.csv扩展名
    let downloadName = displayTitle.value
    if (!downloadName.toLowerCase().endsWith('.csv')) {
      downloadName += '.csv'
    }
    link.setAttribute('download', downloadName)

    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('下载失败:', err)
  }
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

// 关闭查看器
const closeViewer = () => {
  emit('close')
}

// 监听source变化
watch(
  () => props.source,
  () => {
    if (props.source) {
      loadCsvContent()
    }
  },
  { immediate: true }
)

// 组件挂载时加载内容
onMounted(() => {
  if (props.source) {
    loadCsvContent()
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (luckysheetInstance.value) {
    // 清理 LuckySheet 实例
    try {
      luckysheetInstance.value.destroy()
    } catch (error) {
      console.error('清理LuckySheet实例失败:', error)
    }
  }
})

// // 暴露一些方法供父组件调用
// defineExpose({
//   downloadCsv,
//   ArrowsOrShrink,
//   closeViewer,
//   reload: loadCsvContent
// });
</script>

<style scoped>
.csv-viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-radius: 8px;
  overflow: hidden;
}

.csv-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.csv-title {
  flex: 1;
  text-align: left;
}

.csv-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.csv-actions {
  display: flex;
  position: absolute;
  right: 5px;
  z-index: 99;
  display: flex;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: var(--active-bg);
  color: var(--primary-color);
}

.toolbar-btn.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--error-color);
}

.csv-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  opacity: 0.9;
  z-index: 10;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-light);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
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
  margin-top: 12px;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-message {
  padding: 20px;
  color: var(--error-color);
  text-align: center;
  font-size: 14px;
}

.luckysheet-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.luckysheet-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 确保 LuckySheet 正确显示 */
#luckysheet-container {
  width: 100% !important;
  height: 100% !important;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

/* 隐藏 LuckySheet 的 logo 和标题 */
:deep(.luckysheet_info_detail) {
  display: none !important;
}
</style>
