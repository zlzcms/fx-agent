<template>
    <!-- 消息滚动区域 -->
    <div class="scroll-wrap" :style="scrollContainerStyle" ref="scrollContainerRef" @scroll="handleScroll">
        <!-- 加载历史消息的 Loading 指示器 -->
        <div v-if="isLoadingMore" class="loading-more-indicator">
            <Spin size="small" />
        </div>
        
        <!-- 内容居中容器 -->
        <div :style="chatStyle">
            <!-- 🌟 消息列表 -->
            <Bubble.List 
                ref="bubbleListRef" 
                :items="bubbleItems" 
                :roles="roles" 
                :style="messageStyle"
            />
        </div>

        <!-- 浮动滚动到底部按钮 -->
        <div v-if="showScrollToBottom" class="scroll-to-bottom-btn" @click="scrollToBottom(true)" title="滚动到底部">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 13l5 5 5-5" />
                <path d="M7 6l5 5 5-5" />
            </svg>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { BubbleListProps } from 'ant-design-x-vue'
import { Bubble } from 'ant-design-x-vue'
import { Spin } from 'ant-design-vue'
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { CSSProperties } from 'vue'

// Props 定义
interface Props {
    bubbleItems: BubbleListProps['items']
    roles: BubbleListProps['roles']
    scrollContainerStyle: any
    chatStyle: any
    userScrolled: boolean
    programmaticScroll: boolean
    isLoadingMore?: boolean // 是否正在加载更多历史消息
}
const messageStyle = computed<CSSProperties>(() => {
  return {
    'flex': '1',
    // 横向滚动按需出现
    overflowX: 'auto',
    'width': '100%', // 确保宽度为100%
  }
})
// Emits 定义
interface Emits {
    (e: 'update:userScrolled', value: boolean): void
    (e: 'update:programmaticScroll', value: boolean): void
    (e: 'scroll'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式引用
const scrollContainerRef = ref<HTMLElement | null>(null)
const bubbleListRef = ref<any>(null)
const showScrollToBottom = ref(false)

// 拖拽滚动条相关状态
const isDraggingScrollbar = ref(false)
const dragStartY = ref(0)
const dragStartScrollTop = ref(0)

// 触摸滚动相关状态
const isTouchScrolling = ref(false)
const touchStartY = ref(0)
const touchStartScrollTop = ref(0)
const touchStartTime = ref(0)

// 计算属性 - 本地响应式状态
const userScrolled = computed({
    get: () => props.userScrolled,
    set: (value) => emit('update:userScrolled', value)
})

const programmaticScroll = computed({
    get: () => props.programmaticScroll,
    set: (value) => emit('update:programmaticScroll', value)
})

// 清理表格样式，确保使用自然布局
const alignTableColumns = async () => {
    await nextTick()
    
    const tableContainers = document.querySelectorAll('.table-scroll-container')
    tableContainers.forEach((container) => {
        const table = container.querySelector('table')
        if (!table) return
        
        // 确保表格使用自然布局
        table.style.tableLayout = 'auto'
        table.style.width = 'max-content'
        
        // 清除所有内联样式，让CSS控制布局
        const allCells = table.querySelectorAll('th, td') as NodeListOf<HTMLElement>
        allCells.forEach((cell) => {
            cell.style.width = ''
            cell.style.minWidth = ''
        })
    })
}

// 滚动到底部
const scrollToBottom = async (force = false) => {
    // 如果用户已经滚动且不是强制滚动，则不执行自动滚动
    if (userScrolled.value && !force) {
        console.info("unScrolling....")
        return;
    }

    await nextTick()
    const scrollToBottomImpl = () => {
        // 标记为程序触发的滚动
        programmaticScroll.value = true;

        // 优先使用Bubble.List组件的scrollTo方法
        // 回退到使用DOM元素的scrollTop属性
        const scrollContainer = scrollContainerRef.value;
        if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }

        // 延迟重置标志，确保滚动事件处理完成
        setTimeout(() => {
            programmaticScroll.value = false;
        }, 100);
    }
    // 立即执行一次
    scrollToBottomImpl()

    // 如果是强制滚动（比如用户点击滚动到底部按钮），重置用户滚动状态
    if (force) {
        userScrolled.value = false;
        console.info("user force scroll to bottom and set userScrolled false")
    }
}

// 检查是否需要显示滚动到底部按钮
const checkScrollPosition = () => {
    const scrollContainer = scrollContainerRef.value;
    if (!scrollContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px的容差
    showScrollToBottom.value = !isAtBottom;
    // 如果用户滚动到底部，重置用户滚动状态
    if (isAtBottom) {
        userScrolled.value = false;
        console.info("isAtBottom set userScrolled false!")
    }
}

// 监听滚动事件
const handleScroll = () => {

    // 标记用户已经滚动
    // userScrolled.value = true;
    // console.info("handleScroll - user scrolled:", userScrolled.value)
    checkScrollPosition();

    // 通知父组件滚动事件
    emit('scroll');
}

// 监听滚轮事件
const handleWheel = (event: WheelEvent) => {
    // 标记用户已经滚动
    userScrolled.value = true;
    // console.info("handleWheel - user scrolled via wheel:", userScrolled.value)
    checkScrollPosition()
    // 通知父组件滚动事件
    emit('scroll');
}

// 监听鼠标按下事件（可能开始拖拽滚动条）
const handleMouseDown = (event: MouseEvent) => {
    const scrollContainer = scrollContainerRef.value;
    if (!scrollContainer) return;

    // 检查是否点击在滚动条区域
    const rect = scrollContainer.getBoundingClientRect();
    const scrollbarWidth = 16; // 滚动条宽度估计值
    
    // 检查是否点击在右侧滚动条区域
    if (event.clientX > rect.right - scrollbarWidth) {
        isDraggingScrollbar.value = true;
        dragStartY.value = event.clientY;
        dragStartScrollTop.value = scrollContainer.scrollTop;
        // 标记用户开始拖拽
        userScrolled.value = true;
        console.info("handleMouseDown - user started dragging scrollbar");
        
        // 添加全局鼠标事件监听器
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }
}

// 监听鼠标移动事件（拖拽滚动条过程中）
const handleMouseMove = (event: MouseEvent) => {
    if (!isDraggingScrollbar.value) return;
    
    const scrollContainer = scrollContainerRef.value;
    if (!scrollContainer) return;
    
    // 计算拖拽距离
    const deltaY = event.clientY - dragStartY.value;
    const newScrollTop = dragStartScrollTop.value + deltaY;
    
    // 更新滚动位置
    scrollContainer.scrollTop = Math.max(0, Math.min(newScrollTop, scrollContainer.scrollHeight - scrollContainer.clientHeight));
    
    // 标记用户正在拖拽滚动
    userScrolled.value = true;
    // console.info("handleMouseMove - user dragging scrollbar");
    
    // 检查滚动位置
    checkScrollPosition();
}

// 监听鼠标释放事件（结束拖拽滚动条）
const handleMouseUp = () => {
    if (isDraggingScrollbar.value) {
        isDraggingScrollbar.value = false;
        // console.info("handleMouseUp - user stopped dragging scrollbar");
        
        // 移除全局鼠标事件监听器
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    }
}

// 监听触摸开始事件
const handleTouchStart = (event: TouchEvent) => {
    const scrollContainer = scrollContainerRef.value;
    if (!scrollContainer) return;
    
    // 记录触摸开始信息
    touchStartY.value = event.touches[0].clientY;
    touchStartScrollTop.value = scrollContainer.scrollTop;
    touchStartTime.value = Date.now();
    
    // 标记开始触摸滚动
    isTouchScrolling.value = true;
    userScrolled.value = true;
    // console.info("handleTouchStart - user started touch scrolling");
}

// 监听触摸移动事件
const handleTouchMove = (event: TouchEvent) => {
    if (!isTouchScrolling.value) return;
    
    const scrollContainer = scrollContainerRef.value;
    if (!scrollContainer) return;
    
    // 计算触摸移动距离
    const currentY = event.touches[0].clientY;
    const deltaY = touchStartY.value - currentY; // 触摸移动方向与滚动方向相反
    
    // 更新滚动位置
    const newScrollTop = touchStartScrollTop.value + deltaY;
    scrollContainer.scrollTop = Math.max(0, Math.min(newScrollTop, scrollContainer.scrollHeight - scrollContainer.clientHeight));
    
    // 标记用户正在触摸滚动
    userScrolled.value = true;
    // console.info("handleTouchMove - user touch scrolling");
    
    // 检查滚动位置
    checkScrollPosition();
}

// 监听触摸结束事件
const handleTouchEnd = (event: TouchEvent) => {
    if (!isTouchScrolling.value) return;
    
    const touchEndTime = Date.now();
    const touchDuration = touchEndTime - touchStartTime.value;
    
    // 如果触摸时间很短（小于100ms），可能是点击事件，不标记为滚动
    if (touchDuration < 100) {
        const scrollContainer = scrollContainerRef.value;
        if (scrollContainer) {
            const currentScrollTop = scrollContainer.scrollTop;
            const scrollDelta = Math.abs(currentScrollTop - touchStartScrollTop.value);
            
            // 如果滚动距离很小（小于5px），可能是点击，重置用户滚动状态
            if (scrollDelta < 5) {
                userScrolled.value = false;
                console.info("handleTouchEnd - touch was likely a tap, reset userScrolled");
            }
        }
    }
    
    // 结束触摸滚动
    isTouchScrolling.value = false;
    // console.info("handleTouchEnd - user stopped touch scrolling");
}

// 监听bubbleItems变化，滚动到底部
watch(() => props.bubbleItems, () => {
    scrollToBottom()
    // 新内容渲染后重新对齐表格列
    alignTableColumns()
}, { deep: true })

// 在组件挂载时初始化
onMounted(() => {
    // 检查bubbleListRef是否正确获取到
    console.info("bubbleListRef:", bubbleListRef.value)
    if (bubbleListRef.value && bubbleListRef.value.scrollTo) {
        console.info("Bubble.List的scrollTo方法可用")
    } else {
        console.warn("Bubble.List的scrollTo方法不可用，将使用DOM滚动")
    }

    // 添加滚动监听器
    const scrollContainer = scrollContainerRef.value;
    if (scrollContainer) {
        // scrollContainer.addEventListener('scroll', handleScroll);
        // 添加滚轮事件监听器
        scrollContainer.addEventListener('wheel', handleWheel, { passive: false });
        // 添加鼠标按下事件监听器（检测拖拽滚动条）
        scrollContainer.addEventListener('mousedown', handleMouseDown);
        // 添加触摸事件监听器（检测移动端滑动）
        scrollContainer.addEventListener('touchstart', handleTouchStart, { passive: false });
        scrollContainer.addEventListener('touchmove', handleTouchMove, { passive: false });
        scrollContainer.addEventListener('touchend', handleTouchEnd, { passive: false });
        // 初始检查滚动位置
        checkScrollPosition();
    }
    // 初始化时对齐表格列
    alignTableColumns()
})

// 组件卸载时清理
onUnmounted(() => {
    // 移除滚动监听器
    const scrollContainer = scrollContainerRef.value;
    if (scrollContainer) {
        scrollContainer.removeEventListener('scroll', handleScroll);
        scrollContainer.removeEventListener('wheel', handleWheel);
        scrollContainer.removeEventListener('mousedown', handleMouseDown);
        scrollContainer.removeEventListener('touchstart', handleTouchStart);
        scrollContainer.removeEventListener('touchmove', handleTouchMove);
        scrollContainer.removeEventListener('touchend', handleTouchEnd);
    }
    
    // 移除全局鼠标事件监听器
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
})

// 暴露方法给父组件
defineExpose({
    scrollToBottom,
    checkScrollPosition,
    scrollContainerRef
})
</script>

<style lang="scss" scoped>
/* 浮动滚动到底部按钮样式 */
.scroll-to-bottom-btn {
    position: absolute;
    bottom: 140px;
    left: 50%;
    transform: translateX(-50%);
    width: 38px;
    height: 38px;
    background: rgba(40, 40, 40, 0.7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: white;
    transition: all 0.3s ease;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.scroll-to-bottom-btn:hover {
    background: rgba(0, 0, 0, 0.8);
    transform: translateX(-50%) scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.scroll-to-bottom-btn svg {
    transition: transform 0.2s ease;
}

.scroll-to-bottom-btn:hover svg {
    transform: translateY(2px);
}

:deep(.ant-design-x-vue-bubble-list) {
/* 默认隐藏滚动条 */
    &::-webkit-scrollbar-thumb {
    background: transparent;
    transition: background 0.3s ease;
    /* 自定义滚动条长度 - 使用固定高度 */
    }

    /* 当滚动条不滚动时隐藏 */
    &:hover::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    }

    /* 当容器悬浮时显示滚动条 */
    &:hover::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    }
}
.scroll-wrap {
  padding-bottom: 25px;
}

/* 加载历史消息的 Loading 指示器 */
.loading-more-indicator {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: transparent;

}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary, #666);
}
/** 用于控制markdown 内容生成后的间距  */
.scroll-wrap :deep(.ant-bubble-content .combined-content){
 color: var(--text-primary) !important;
 .ant-typography,.ant-typography.ant-typography-secondary {
  color: var(--text-primary) !important;
 }
}
.scroll-wrap :deep(.ant-bubble-content ol) {
  padding-left: 25px;
}
.scroll-wrap :deep(.ant-bubble-content ul) {
  padding-left: 20px;
}


.scroll-wrap :deep(.ant-thought-chain-item-header){
    margin-bottom: 0px !important;
   
}



</style>
<style lang="scss">
.combined-content .ant-tag{
  display: flex;
  align-items: center;
  width: fit-content;
  max-width: 100%;
  overflow: auto
}
.execute-ele {
  padding: 4px 12px;
  border-radius: 15px;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-agent);
  cursor: pointer;  display: flex;
  width: fit-content;
  &:hover{
    background-color: var(--active-bg);
  }
}
.execute-ele-none {
  padding: 5px 15px;
  border-radius: 15px;
  background-color: var(--hover-bg);
  display: flex;
  width: fit-content;
}
/* 思维链和markdown内容组合样式 */
.combined-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 100%;
  .ant-thought-chain-item-desc {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    text-overflow: unset !important;
  }

  // .ant-thought-chain-item-icon {
  //   background-color: var(--bg-secondary) !important;
  // }
  .ant-thought-chain .ant-thought-chain-item-header::before{
     /* 定义虚线参数（可按需修改） */
    --dash-solid: 5px; /* 实线段长度 */
    --dash-gap: 5px;    /* 间隙长度 */
    --dash-cycle: calc(var(--dash-solid) + var(--dash-gap)); /* 单个循环周期高度 */
    background: linear-gradient(
      to bottom,
      var(--bg-chain-line) 0px,    /* 实线起始 */
      var(--bg-chain-line) var(--dash-solid),   /* 实线结束 */
      transparent var(--dash-solid),
      transparent var(--dash-cycle),

    );
    background-size: 2px var(--dash-cycle); /* 宽度2px，周期高度=实线+间隙 */
    background-repeat: repeat; /* 自动重复循环 */
    background-color: transparent !important;
  }
  .ant-thought-chain.ant-thought-chain-small .ant-thought-chain-item-desc{
    font-size: 14px !important;
  }
  .ant-thought-chain.ant-thought-chain-small .ant-thought-chain-item .ant-thought-chain-item-header .ant-thought-chain-item-header-box .ant-thought-chain-item-title{
    font-size: 14px !important;
    height: 22px !important;
    line-height: normal!important;
    max-height: 22px !important;
  }
  .ant-thought-chain.ant-thought-chain-small>.ant-thought-chain-item .ant-thought-chain-item-header::before{
    bottom: -14px;
  }
}
.scroll-wrap{
    .ant-collapse{
      margin-bottom: 10px;
    }
    .ant-collapse-header{
      font-size: 12px;
      padding: 6px 8px !important;
      color: var(--text-secondary)!important;
      .ant-collapse-expand-icon{
        height: 16px!important;
      }
    }
}
/* 文档卡片样式 */
.csv-document-card {
  margin: 0px 0 10px 0;
}

.file-card-header {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.file-card-content {
  display: flex;
  align-items: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-card-content:hover {
  background: var(--hover-bg);
  border-color: var(--border-color);
}

.file-icon {
  margin-right: 12px;
  font-size: 28px;

  &.md {
    color: #5375ff;
  }

  &.pdf {
    color: #b30000
  }

  &.csv {
    color: #0bd900;
  }

  &.xls {
    color: #5375ff;
  }
}

.file-info {
  flex: 1;
}

.file-filename {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.file-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.file-action {
  margin-left: 12px;
}

.view-icon {
  width: 32px;
  height: 32px;
  background: var(--bg-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-size: 14px;
  border: 1px solid var(--border-light);
}


/* Markdown样式 */
.md-wrap {
  line-height: 1.6;
  color: var(--text-primary);
  word-spacing: 1px;
  font-size: 14px;
  line-height: 22px;
  /* 让 Markdown 容器成为横向+纵向滚动容器，避免打破表格原生布局 */
  overflow: auto;
  
  ol, ul, menu {
      list-style: disc; 
  }

  /* 表格滚动容器样式 */
  .table-scroll-container {
    overflow: auto;      /* 横向滚动条在容器上 */
    margin: 12px 0;
    border: 1px solid var(--border-light);
    border-radius: 4px;
    max-height: 600px; /* 限制整个表格高度 */
    width: fit-content;
    max-width: 100%;
  }

  /* 表格样式 */
  table {
    /* 原生表格布局，列宽随内容自适应 */
    display: table;
    width: max-content;    /* 根据内容扩展，触发横向滚动 */
    border-collapse: collapse;
    margin: 0;             /* 移除margin，由容器控制 */
    table-layout: auto;    /* 列宽自适应内容 */

    display: block;

    tbody{
      padding-right: 12px; /* 预留纵向滚动条宽度（通常 12-16px） */
      box-sizing: content-box; /* 确保内边距不影响容器宽度计算 */
    }
  }


  /* Sticky 表头 */
  thead th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--bg-table-header);
  }
  

  th, td {
    border: 1px solid var(--border-light);
    padding: 8px 12px;
    text-align: left;
    white-space: nowrap; /* 不换行，列宽随最长内容扩展 */
  }

  th {
    position: sticky;
    font-weight: 600;
    white-space: nowrap; /* 头部不换行，利于根据内容自适应列宽 */
  }

  tr:nth-child(even) {
    background: var(--hover-bg);
  }
}

.thinking-process{
  font-size: 12px;
}
</style>