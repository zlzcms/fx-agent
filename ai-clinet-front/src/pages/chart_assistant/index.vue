<script setup lang="ts">
import type { AttachmentsProps, BubbleListProps, ConversationsProps, PromptsProps } from 'ant-design-x-vue'
import {
  CloudUploadOutlined,
  MenuOutlined,
  DownOutlined,
  PlusCircleOutlined,
} from '@ant-design/icons-vue'
import { 
  Flex, 
   Tooltip, 
   Typography, 
   Skeleton,
   Dropdown,
   Menu,
   MenuItem,
  Spin,
  } from 'ant-design-vue'
import {  
  CompassOutlined,
  MessageOutlined,
  AndroidOutlined,
  FileWordOutlined,
  GlobalOutlined,
 } from '@ant-design/icons-vue';
import {
  InfoCircleOutlined,
} from '@ant-design/icons-vue';
import {
  Attachments,
  Sender,
  useXChat,
  Welcome,
  Prompts,
} from 'ant-design-x-vue'
import { useStyles } from './composables/useStyles.ts'
import { useAgentConfig } from './composables/useAgentConfig.ts'
import { useMessageUtils } from './composables/useMessageUtils.ts'
import { useMessageHandler } from './composables/useMessageHandler.ts'
import { computed, h, ref, watch, onMounted, nextTick, onUnmounted, reactive } from 'vue'

import { createChat, getChatMessages, interrupAssistant } from '@/api/chat'
import { getRecommendedQuestions } from '@/api/recommendedQuestions' // 暂时注释，使用mock数据

import RightAgent from './right-agent.vue'
import LeftSide from './left-side.vue'
import BubbleListl from './bubblelistl.vue'
import demoPdf from '@/assets/demo.pdf'

defineOptions({ name: 'PlaygroundIndependentSetup' })

// 状态变量
const headerOpen = ref(false)
const content = ref('')
const attachedFiles = ref<AttachmentsProps['items']>([])
const agentRequestLoading = ref(false)
const conversationLoading = ref(true) // 会话切换时的加载状态
const activeConversation = ref<{ id: string, title: string } | null>(null)
const userScrolled = ref(false) // 跟踪用户是否主动滚动
const programmaticScroll = ref(false) // 标记是否为程序触发的滚动
const leftSideRef = ref<InstanceType<typeof LeftSide> | null>(null) // 左侧菜单组件的引用
const bubbleListlRef = ref<InstanceType<typeof BubbleListl> | null>(null) // 消息列表组件的引用

// 分页相关状态
const currentPage = ref(1) // 当前页码
const totalPages = ref(1) // 总页数
const isLoadingMore = ref(false) // 是否正在加载更多消息
const hasMoreMessages = ref(false) // 是否还有更多消息
let loadMoreTimer: ReturnType<typeof setTimeout> | null = null // 防抖定时器

const menuVisible = ref(true) // 控制菜单是否可见
const chatVisible = ref(true) // 控制聊天区域显示隐藏
const menuVisibleFlag = ref(false) // 开启菜单可隐藏
const showRightAgent = ref(false) // 控制右边区域显示隐藏

// RightAgent 代理组件相关变量
const rightAgentType = ref('workspace') // 代理组件类型：'workspace'
const rightAgentSource = ref('') // 通用源文件（用于 markdown 和 pdf）
const rightAgentExpand = ref(false) // 控制右侧查看器是否展开
const rightAgentFilename = ref('') // 文件名
const modelValue = ref('auto') // 代理组件类型：'auto', 'agent', 'chat'



// 推荐问法数据
const recommendedPrompts = ref<any[]>([])


// 获取推荐问法 - 暂时使用mock数据
const fetchRecommendedQuestions = async () => {
  // 暂时注释掉API调用，使用mock数据
  const response = await getRecommendedQuestions(3)
  recommendedPrompts.value = response.data.data.map((item: any) => ({
    id: item.id.toString(),
    label: item.title || '',
    description: item.content || '',
    icon: h(MessageOutlined, { style: { color: item.color || '#1890FF' } }),
    data: {
      content: item.content || ''
    },
    color: item.color || '#1890FF'
  }))
}

// 处理提示词点击
const handlePromptClick: PromptsProps['onItemClick'] = (item: any) => {
  console.info("handlePromptClick: ", item)
  content.value = item.data.data.content
  // 可以在这里添加其他逻辑，比如自动发送消息等
}
// 使用 store 中的设备检测
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

const store = useStore()
const { t } = useI18n()
const isMobile = computed(() => store.getters['device/isMobile'])
const autoSend = computed(() => store.getters['auth/autoSend'])

// iPhone 设备检测
const isIphone = computed(() => {
  const userAgent = navigator.userAgent
  return /iPhone/.test(userAgent)
})
const { styles} = useStyles({
  isMobile: computed(() => isMobile.value),
  showRightAgent: computed(() => showRightAgent.value),
  chatVisible: computed(() => chatVisible.value),
  activeConversation: computed(() => activeConversation.value)
})
// 增强setMessages函数，添加滚动功能
const setMessages = (updater: any) => {
  originalSetMessages(updater)
}
const { 
  formatMessageContent, 
} = useMessageUtils()

// 时间格式化函数：将时间格式化为年月日时分
const formatDateTime = (dateTime: string) => {
  try {
    const date = new Date(dateTime)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}`
  } catch (error) {
    console.error('时间格式化失败:', error)
    return dateTime // 如果格式化失败，返回原始值
  }
}

const createNewConversation = async (title) => {
  try {
    // 设置消息
    setMessages([{ role: 'local', message: title }])
      // 创建新会话
      const response = await createChat({
      title: title,
      channel: store.getters['auth/channel'] || null,
      model_id: 'fbef0dad-02be-4b60-857c-b1c05967f013' // 默认模型ID
    });

    const newConversation = {
      id: response.data.id,
      title: response.data.title
    };
    // 设置当前会话
    activeConversation.value = newConversation;
    // 保存到本地存储
    localStorage.setItem('store_chat_id', newConversation.id);

    // 通过子组件方法添加新会话
    console.log('leftSideRef.value:', leftSideRef.value);

    // 使用 nextTick 确保组件已经挂载
    nextTick(() => {
      if (leftSideRef.value && typeof leftSideRef.value.addNewConversation === 'function') {
        leftSideRef.value.addNewConversation(newConversation);
      } else {
        console.warn('leftSideRef 未准备好或 addNewConversation 方法不存在');
        console.log('leftSideRef.value 的类型:', typeof leftSideRef.value);
        console.log('leftSideRef.value 的内容:', leftSideRef.value);
      }
    });

    console.log('新会话创建成功:', newConversation);
  } catch (error) {
    console.error('创建新会话失败:', error);
    // 可以在这里添加错误提示
  }
}

// 辅助方法：显示 CSV 查看器
const showCsvViewer = async (source: string) => {
  try {
    let csvContent = source;
    
    rightAgentType.value = 'csv'
    rightAgentSource.value = csvContent
    showRightAgent.value = true
  } catch (error) {
    console.error('加载CSV文件失败:', error);
  }
  if(isMobile.value){
    chatVisible.value = false
  }
}

// 辅助方法：显示 Markdown 查看器
const showMarkdownViewer = (content: string) => {
  rightAgentType.value = 'md'
  rightAgentSource.value = content
  showRightAgent.value = true
  if(isMobile.value){
    chatVisible.value = false
  }
}

// 辅助方法：显示 PDF 查看器
const showPdfViewer = (source?: string) => {
  rightAgentType.value = 'pdf'
  rightAgentSource.value = source || demoPdf
  showRightAgent.value = true
  if(isMobile.value){
    chatVisible.value = false
  }
}

const showHtmlViewer = (source?: string) => {
  rightAgentType.value = 'html'
    rightAgentSource.value = source || 'demo.html'
    console.info("showHtmlViewer: ", rightAgentSource.value)
  showRightAgent.value = true
  if(isMobile.value){
    chatVisible.value = false
  }
}

const viewerHandlers = {
  showCsvViewer: showCsvViewer,
  showPdfViewer: showPdfViewer,
  showMarkdownViewer: showMarkdownViewer,
  showHtmlViewer: showHtmlViewer
}

// 辅助方法：显示工作空间
const onWorkSpaceShow = (data: any = {}) => {
  rightAgentType.value = 'workspace'
  rightAgentSource.value = data.source
  showRightAgent.value = true
  console.info("onWorkSpaceShow")
  if(isMobile.value){
    chatVisible.value = false
  }
}
const resultFormat = ref('word') // 默认选择 word
const dependencies = {
  isMobile,
  agentRequestLoading,
  setMessages,
  activeConversation,
  modelValue,
  resultFormat,
  bubbleListlRef,
  createNewConversation,
  onWorkSpaceShow,
  showCsvViewer,
  showPdfViewer,
  showMarkdownViewer,
  showHtmlViewer,
  store,
}
const { agent: useChatAgent } = useAgentConfig(dependencies)
const { handleAssistantMessages } = useMessageHandler()
// 模式选择相关
const modeOptions = computed(() => [
  { key: 'auto', label: t('modes.auto'), icon: "CompassOutlined" },
  { key: 'agent', label: t('modes.agent'), icon: "AndroidOutlined" },
  { key: 'chat', label: t('modes.chat'), icon: "MessageOutlined" }
])

const modelLabel = ref(t('modes.auto'))
watch(modelValue, (newVal)=> {
  const findIt = modeOptions.value.find((item) => item.key === newVal )
  if (findIt) {
    modelLabel.value = findIt['label']
  }
})

const handleModeSelect = ({ key }) => {
  modelValue.value = key
  handleDocClose()
}

// 结果格式选择相关
const resultFormatOptions = [
  { key: 'word', label:  t('chat.report'), icon: 'FileWordOutlined' },
  { key: 'html', label: t('chat.web'), icon: 'GlobalOutlined' }
]
// 结果格式选择

const resultFormatLabel = ref(t('chat.report'))

const handleResultFormatSelect = ({ key }) => {
  resultFormat.value = key
  const findIt = resultFormatOptions.find((item) => item.key === key)
  if (findIt) {
    resultFormatLabel.value = findIt.label
  }
  // 根据选择的格式显示对应的查看器
  // if (key === 'markdown') {
  //   showMarkdownViewer('# Markdown 示例\n\n这是一个 Markdown 示例文档')
  // } else if (key === 'pdf') {
  //   showPdfViewer()
  // } else if (key === 'html') {
    // showHtmlDemo()
  // }
}

// 菜单控制方法
const showMenu = () => {
  menuVisible.value = true;
}

const hideMenu = () => {
  if (!menuVisibleFlag.value) {
    return
  }
  menuVisible.value = false;
}

const toggleMenu = () => {
  if (isMobile.value) {
   
    return menuVisible.value = false
  }
  console.log('toggleMenu')
  menuVisibleFlag.value = !menuVisibleFlag.value;
}
watch(menuVisible, (newVal) => {
  console.log('menuVisible', newVal)
})



// 使用useXChat处理聊天状态
const { onRequest, messages, setMessages: originalSetMessages } = useXChat({
  agent: useChatAgent.value,
  transformMessage: ({ currentMessage, status, originMessage }) => {
    console.info("originMessage", originMessage)
    console.info("status", status)
    console.info("currentMessage type:", typeof currentMessage, currentMessage)


    return currentMessage
  },
})


// 对话角色定义
const roles: BubbleListProps['roles'] = {
  assistant: {
    placement: 'start',
    variant: 'borderless',
    styles: {
      content: {
        borderRadius: '16px',
      },
    },
  },
  user: {
    placement: 'end',
    variant: 'shadow',
    styles: {
      content: {
        border: '1px solid #efefef',
        "border-bottom-right-radius": "0px",
        'box-shadow': 'none',
        'background-color': '#fff',
      }
    }
  },
}



// 发送消息
function onSubmit(nextContent: string) {
  if (!nextContent) return
  userScrolled.value = false; // 重置用户滚动状态，允许新消息自动滚动
  console.info("userScrolled:3")
  onRequest(nextContent)
  content.value = ''
}


// 切换会话
const onConversationClick: ConversationsProps['onActiveChange'] = async (conversation: any) => {
  hideMenu()
  console.info("onConversationClick: ", conversation)
  try {
    // 中断当前请求
    abortCurrentChating()
    // 清空文件选择
    attachedFiles.value = []
    chatVisible.value = true
    // 如果是新建会话
    if (conversation === null) {
      setMessages([])
      activeConversation.value = null
      showRightAgent.value = false

      localStorage.setItem('store_chat_id', 'new');
      return
    }

    // 设置加载状态
    conversationLoading.value = true
    showRightAgent.value = false
    activeConversation.value = conversation

    // 获取会话消息（支持分页，默认获取第一页，每页4条）
    const key = conversation.id
    localStorage.setItem('store_chat_id', key);
    
    // 重置分页状态
    currentPage.value = 1
    totalPages.value = 1
    isLoadingMore.value = false
    hasMoreMessages.value = false
    // 清理防抖定时器
    if (loadMoreTimer) {
      clearTimeout(loadMoreTimer)
      loadMoreTimer = null
    }
    
    const response = await getChatMessages(key, { page: 1, size: 4 });
    // 处理分页响应：如果返回的是分页数据，使用 items；否则使用 data（向后兼容）
    const messagesData = response.data.items || response.data
    const pageData = response.data
    
    // 更新分页状态
    if (pageData && typeof pageData === 'object' && 'total_pages' in pageData) {
      totalPages.value = pageData.total_pages || 1
      hasMoreMessages.value = currentPage.value < totalPages.value
    }
    
    const dataLen = messagesData.length
    const chatMessages = messagesData.map((msg, index) => {
      if (msg.role === 'user') {
        return {
          id: msg.id,
              message: h('div', { innerHTML: formatMessageContent(msg.content) }),
          role: msg.role,
          status: msg.status,
        }
      } else {
        const isLast = dataLen === index + 1
        if(msg.response_data){
          const assistantMessage = handleAssistantMessages(msg.response_data, isLast,onWorkSpaceShow,viewerHandlers)
          
          return {
            id: msg.id,
            message: assistantMessage,
            role: msg.role,
            status: msg.status,
          }
        }else{
          return {
            
          }
        }
 
      }
    }
    );
    // 设置消息
    setMessages(chatMessages.length > 0 ? chatMessages : []);
    // 加上一个模拟数据
    // simulateStepMockData()
    bubbleListlRef.value?.scrollToBottom(true)
  } catch (error) {
    console.error('获取会话消息失败:', error);
    // 如果API调用失败，使用模拟数据
    setMessages([]);
  } finally {
    userScrolled.value = false; // 重置用户滚动状态
    console.info("userScrolled:4")
    // 关闭加载状态 
    conversationLoading.value = false
    await nextTick()
    bubbleListlRef.value?.scrollToBottom();
  }
}


const handleFileChange: AttachmentsProps['onChange'] = info => attachedFiles.value = info.fileList

// 中断当前聊天响应
const abortCurrentChating = () => {
  if (agentRequestLoading.value) {
    const chat_id = localStorage.getItem('store_chat_id');
    const res = interrupAssistant(chat_id)
    console.info("abortCurrentChating: ", res)
  }
}


// 添加新会话--重置对话输入框
async function onAddConversation(askContent) {
  try {
    // 中断当前请求
    abortCurrentChating()
    setMessages([])

    activeConversation.value = null
    showRightAgent.value = false
    attachedFiles.value = []
    conversationLoading.value = false
    chatVisible.value = true
    localStorage.setItem('store_chat_id', '');
    if(askContent){
      if(autoSend.value){
        onSubmit(askContent)
      }else{
        content.value = askContent
      }
    }
  } catch (error) {
    console.error('创建新会话失败:', error);
  }
}
// 转换消息格式以适应Bubble.List组件
const bubbleItems = computed<BubbleListProps['items']>(() => {
  return messages.value.map(({ id, message, status, role }) => {
    const processedContent = message;
    let roles = role ? role == 'assistant' ? 'assistant' : 'user' : status == 'local' ? 'user' : 'assistant'
    return {
      key: id,
      loading: status === 'custom_loading',
      role: roles,
      content: processedContent,
    };
  });
})
// 加载更多历史消息
const loadMoreMessages = async () => {
  if (!activeConversation.value || isLoadingMore.value || !hasMoreMessages.value) {
    return
  }

  const nextPage = currentPage.value + 1
  if (nextPage > totalPages.value) {
    hasMoreMessages.value = false
    return
  }

  try {
    isLoadingMore.value = true
    const key = activeConversation.value.id
    
    // 保存当前滚动位置和高度
    const scrollContainer = bubbleListlRef.value?.scrollContainerRef
    const oldScrollHeight = scrollContainer?.scrollHeight || 0
    const oldScrollTop = scrollContainer?.scrollTop || 0
    
    // 加载下一页消息
    const response = await getChatMessages(key, { page: nextPage, size: 4 })
    const pageData = response.data
    const newMessagesData = pageData.items || response.data
    
    if (!newMessagesData || newMessagesData.length === 0) {
      hasMoreMessages.value = false
      return
    }
    
    // 更新分页状态
    if (pageData && typeof pageData === 'object' && 'total_pages' in pageData) {
      totalPages.value = pageData.total_pages || 1
      hasMoreMessages.value = nextPage < totalPages.value
    }
    
    // 转换新消息格式
    const newChatMessages = newMessagesData.map((msg, index) => {
      if (msg.role === 'user') {
        return {
          id: msg.id,
          message: h('div', { innerHTML: formatMessageContent(msg.content) }),
          role: msg.role,
          status: msg.status,
        }
      } else {
        if (msg.response_data) {
          const assistantMessage = handleAssistantMessages(msg.response_data, false, onWorkSpaceShow, viewerHandlers)
          return {
            id: msg.id,
            message: assistantMessage,
            role: msg.role,
            status: msg.status,
          }
        } else {
          return {}
        }
      }
    }).filter(msg => msg.id) // 过滤空消息
    
    // 将新消息添加到现有消息前面（历史消息在顶部）
    const currentMessages = messages.value || []
    setMessages([...newChatMessages, ...currentMessages])
    
    // 更新当前页码
    currentPage.value = nextPage
    
    // 等待DOM更新后恢复滚动位置
    await nextTick()
    if (scrollContainer) {
      const newScrollHeight = scrollContainer.scrollHeight
      const scrollDiff = newScrollHeight - oldScrollHeight
      scrollContainer.scrollTop = oldScrollTop + scrollDiff
    }
  } catch (error) {
    console.error('加载更多消息失败:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// 处理子组件滚动事件
const handleBubbleListScroll = () => {
  // 检测是否滚动到顶部附近（距离顶部50px以内）
  const scrollContainer = bubbleListlRef.value?.scrollContainerRef
  if (!scrollContainer || isLoadingMore.value || !hasMoreMessages.value) {
    return
  }
  
  const scrollTop = scrollContainer.scrollTop
  // 当滚动到顶部附近时，使用防抖加载更多消息
  if (scrollTop <= 50) {
    // 清除之前的定时器
    if (loadMoreTimer) {
      clearTimeout(loadMoreTimer)
    }
    // 设置新的定时器，300ms后执行加载
    loadMoreTimer = setTimeout(() => {
      loadMoreMessages()
    }, 300)
  } else {
    // 如果不在顶部附近，清除定时器
    if (loadMoreTimer) {
      clearTimeout(loadMoreTimer)
      loadMoreTimer = null
    }
  }
}

// 监听 leftSideRef 的变化
watch(leftSideRef, (newRef) => {
  if (newRef) {
    console.log('leftSideRef 已获取到:', newRef);
    if (typeof newRef.addNewConversation === 'function') {
      console.log('addNewConversation 方法可用');
  } else {
      console.warn('addNewConversation 方法不可用');
    }
  }
}, { immediate: true });


const isSimpleAskContent = ref(false)
// 在组件挂载时初始化
onMounted(async () => {
  isSimpleAskContent.value = isAskContent()

  // 处理 iPhone Safari 浏览器地址栏动态高度
  if (isIphone.value) {
    // 设置初始视口高度CSS变量
    const setViewportHeight = () => {
      // 获取实际视口高度（包括地址栏）
      const vh = window.innerHeight * 0.01
      document.documentElement.style.setProperty('--vh', `${vh}px`)
    }
    
    // 初始设置
    setViewportHeight()
    
    // 监听窗口大小变化（包括地址栏的显示/隐藏）
    window.addEventListener('resize', setViewportHeight)
    window.addEventListener('orientationchange', setViewportHeight)
    
    // 清理监听器
    onUnmounted(() => {
      window.removeEventListener('resize', setViewportHeight)
      window.removeEventListener('orientationchange', setViewportHeight)
    })
  }
  
  // 获取推荐问法
  await fetchRecommendedQuestions()
})

const isAskContent = () => {
  const urlParams = new URLSearchParams(window.location.search)
  const askContent = urlParams.get('askContent')
  if (askContent) {
    console.info("检测到askContent参数:", askContent)
    modelValue.value = 'chat'
    return true
  }
  return false
}

watch(isMobile, (newVal) => {
  console.info("isMobile:", newVal)
  if (newVal) {
    menuVisibleFlag.value = true
    if (showRightAgent.value) {
      chatVisible.value = false
    }
    if (menuVisible.value) {
      menuVisible.value = false
    }
  } else {
    chatVisible.value = true
  }
}, { immediate: true })

// 组件卸载时清理
onUnmounted(() => {
  abortCurrentChating()
  // 清理防抖定时器
  if (loadMoreTimer) {
    clearTimeout(loadMoreTimer)
    loadMoreTimer = null
  }
})

// 处理文档放大
const handleDocExpand = () => {
  showRightAgent.value = true
  chatVisible.value = false
  console.info('handleDocExpand...')
}

//处理文档缩小
const handleDocShrink = () => {
  chatVisible.value = true
  rightAgentExpand.value =false
}

// 打开助理报告（使用模拟数据）
const handleOpenReport = async (report: any) => {
  try {
    
    // 中断当前请求
    abortCurrentChating()
    // const HOST = import.meta.env.VITE_API_HOST
    // console.info("报告md: ",report.report_result)
    // 文件名： 使用 中国区客户分析+ 时间 ，格式： 年月日时分
    const formattedTime = formatDateTime(report.created_time)
    const filename = '中国区客户分析' + formattedTime
    
    // 随机 ECharts 图表示例
//     const echartsExamples = [
//       `\n\n## 柱状图示例\n\`\`\`echarts
// {
//   "title": {
//     "text": "客户分布统计",
//     "left": "center"
//   },
//   "tooltip": {
//     "trigger": "axis"
//   },
//   "xAxis": {
//     "type": "category",
//     "data": ["华东区", "华南区", "华北区", "西南区", "其他"]
//   },
//   "yAxis": {
//     "type": "value"
//   },
//   "series": [{
//     "name": "客户数量",
//     "type": "bar",
//     "data": [120, 85, 70, 55, 25],
//     "itemStyle": {
//       "color": "#5470c6"
//     }
//   }]
// }
// \`\`\`\n`,
//       `\n\n## 饼图示例\n\`\`\`echarts
// {
//   "title": {
//     "text": "客户类型分布",
//     "left": "center"
//   },
//   "tooltip": {
//     "trigger": "item"
//   },
//   "series": [{
//     "name": "客户类型",
//     "type": "pie",
//     "radius": "50%",
//     "data": [
//       {"value": 335, "name": "个人客户"},
//       {"value": 310, "name": "企业客户"},
//       {"value": 234, "name": "代理客户"},
//       {"value": 135, "name": "VIP客户"},
//       {"value": 1548, "name": "普通客户"}
//     ],
//     "emphasis": {
//       "itemStyle": {
//         "shadowBlur": 10,
//         "shadowOffsetX": 0,
//         "shadowColor": "rgba(0, 0, 0, 0.5)"
//       }
//     }
//   }]
// }
// \`\`\`\n`,
//       `\n\n## 折线图示例\n\`\`\`echarts
// {
//   "title": {
//     "text": "月度交易趋势",
//     "left": "center"
//   },
//   "tooltip": {
//     "trigger": "axis"
//   },
//   "xAxis": {
//     "type": "category",
//     "data": ["1月", "2月", "3月", "4月", "5月", "6月"]
//   },
//   "yAxis": {
//     "type": "value"
//   },
//   "series": [{
//     "name": "交易金额",
//     "type": "line",
//     "data": [120, 200, 150, 80, 70, 110],
//     "smooth": true,
//     "itemStyle": {
//       "color": "#91cc75"
//     }
//   }]
// }
// \`\`\`\n`,
//       `\n\n## 散点图示例\n\`\`\`echarts
// {
//   "title": {
//     "text": "客户价值分析",
//     "left": "center"
//   },
//   "tooltip": {
//     "trigger": "item"
//   },
//   "xAxis": {
//     "type": "value",
//     "name": "交易频次"
//   },
//   "yAxis": {
//     "type": "value",
//     "name": "交易金额"
//   },
//   "series": [{
//     "name": "客户分布",
//     "type": "scatter",
//     "data": [
//       [10.0, 8.04], [8.0, 6.95], [13.0, 7.58], [9.0, 8.81],
//       [11.0, 8.33], [14.0, 9.96], [6.0, 7.24], [4.0, 4.26],
//       [12.0, 10.84], [7.0, 4.82], [5.0, 5.68]
//     ],
//     "itemStyle": {
//       "color": "#fac858"
//     }
//   }]
// }
// \`\`\`\n`,
//       `\n\n## 雷达图示例\n\`\`\`echarts
// {
//   "title": {
//     "text": "客户风险评估",
//     "left": "center"
//   },
//   "radar": {
//     "indicator": [
//       {"name": "交易频率", "max": 100},
//       {"name": "资金规模", "max": 100},
//       {"name": "活跃度", "max": 100},
//       {"name": "信用记录", "max": 100},
//       {"name": "风险偏好", "max": 100}
//     ]
//   },
//   "series": [{
//     "name": "客户A",
//     "type": "radar",
//     "data": [{
//       "value": [80, 90, 70, 85, 60],
//       "name": "客户A"
//     }]
//   }]
// }
// \`\`\`\n`
//     ]
    
//     // 随机选择一个 ECharts 图表
//     const randomEcharts = echartsExamples[Math.floor(Math.random() * echartsExamples.length)]

    rightAgentSource.value = report.report_result.output
    rightAgentType.value = 'md'
    rightAgentFilename.value = filename
    showRightAgent.value = true
    chatVisible.value = false
    rightAgentExpand.value = true

    
  } catch (error) {
    console.error('加载报告数据失败:', error)
    setMessages([])
  } finally {
    userScrolled.value = false
    conversationLoading.value = false
    await nextTick()
    bubbleListlRef.value?.scrollToBottom()
  }
}


// 处理文档加载完成
const handleDocLoaded = () => {
  console.log('handleLoaded')
}

// 处理文档错误
const handleDocError = (error: any) => {
  console.log('handleError', error)
}





// 处理文档关闭
const handleDocClose = () => {
  console.log('handleClose')
  showRightAgent.value = false
  chatVisible.value = true
  rightAgentExpand.value = false
  leftSideRef.value?.onDocClosed()
}


const indicator = h('div');


</script>

<template>
  <div :style="styles.layout" @click="hideMenu" class="bg-gray-100" :class="{ 'container-layout-iphone': isIphone }">
    <div>
      <!-- 可悬浮菜单 -->
      <LeftSide ref="leftSideRef" :menu-visible="menuVisible" :menu-visible-flag="menuVisibleFlag" :is-mobile="isMobile"
        :active-conversation="activeConversation" @add-conversation="onAddConversation"
        @conversation-click="onConversationClick" @hide-menu="hideMenu" @toggle-menu="toggleMenu" @open-report="handleOpenReport" />
    </div>
    <div class="chats-wrap">
      <div class="chat-container" :style="styles['chat-container']" v-show="chatVisible">
        
        <!-- 移动端标题 -->
        <template v-if="isMobile">
          <div v-if="!isSimpleAskContent" class="mobile-title flex items-center justify-between menu-outline">
            <div class="flex items-center pl-2">
              <MenuOutlined @click.stop="showMenu"/> 
              <Tooltip placement="bottom">
                <template #title>
                  <span>{{ activeConversation?.title  }}</span>
                </template>
                  <div class="conversation-title ml-2 font-bold" :title="activeConversation?.title ">{{ activeConversation?.title || $t('chat.newConversation') }}</div>
              </Tooltip>
            </div>
            <div class="mobile-add-conversation" @click="onAddConversation('')">
              <PlusCircleOutlined />
            </div>
          </div>
        </template>
        <div v-else class="head-wraper">
          <div class="menu-icon"  v-if="!menuVisible" @mouseenter="showMenu">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              class="lucide lucide-panel-left size-5 text-[var(--icon-secondary)]">
              <rect width="18" height="18" x="3" y="3" rx="2"></rect>
              <path d="M9 3v18"></path>
            </svg>
          </div>
          <div :style="styles['chat-style']">
            <div :style="styles['head-title']">
              <div class="conversation-title font-bold">{{ activeConversation?.title || $t('chat.newConversation') }}</div>
              <div>
                <InfoCircleOutlined />
              </div>
            </div>
          </div>
        </div>
          <!-- 消息滚动区域 -->
        <div v-if="activeConversation && conversationLoading" :style="styles['scroll-container']">
          <div :style="styles['chat-style']">
            <!-- 消息骨架屏 -->
            <div class="message-skeleton-container">
              <div class="message-skeleton-item user-skeleton">
                <Skeleton.Avatar :size="32" />
                <div class="skeleton-content">
                  <Skeleton :paragraph="{ rows: 2, width: ['60%', '40%'] }" :title="false" active />
          </div>
          </div>
              <div class="message-skeleton-item assistant-skeleton">
                <Skeleton.Avatar :size="32" />
                <div class="skeleton-content">
                  <Skeleton :paragraph="{ rows: 3, width: ['80%', '90%', '50%'] }" :title="false" active />
                </div>
              </div>
              <div class="message-skeleton-item user-skeleton">
                <Skeleton.Avatar :size="32" />
                <div class="skeleton-content">
                  <Skeleton :paragraph="{ rows: 1, width: ['70%'] }" :title="false" active />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="!activeConversation" class="wel-prompts-wrapper" :style="styles['prompts-style']">
          <!-- 🌟 提示词 -->
          <div class="prompts-container pb-1">
              <Welcome :title="$t('chat.welcome.title')"
                class="welcome-title"
                :description="$t('chat.welcome.description')" />
              
              <!-- 提示词组件 -->
              <div class="mt-6 custom-prompts-wrapper"  v-if="!isSimpleAskContent">
                <Prompts 
                  class="custom-prompts"
                  :items="recommendedPrompts" 
                  vertical
                  :styles="{ item: { width: '100%' } }"
                  @item-click="handlePromptClick"
                />
              </div>
              
          </div> 
        </div>
        <BubbleListl v-else ref="bubbleListlRef" :bubble-items="bubbleItems" :roles="roles"
          :scroll-container-style="styles['scroll-container']" :chat-style="styles['chat-style']"
           v-model:user-scrolled="userScrolled"
          v-model:programmatic-scroll="programmaticScroll" 
          :is-loading-more="isLoadingMore"
          @scroll="handleBubbleListScroll" />

        <!-- 底部区域 - 固定在底部 -->
        <div class="footer-wrapper pb-2">
          <div  :style="styles['sender-style']">
            <div class="footer-area">
              

              <!-- 🌟 输入框 -->
              <div class="sender-container"  v-if="!conversationLoading">
                <Sender v-if="!isSimpleAskContent" :value="content" :loading="agentRequestLoading" @submit="onSubmit" :placeholder="$t('chat.placeholder')"
                  @change="value => content = value" :actions="false" :auto-size="{ minRows: 1, maxRows: 2 }">
                  <template #footer="{ info: { components: { SendButton, LoadingButton, SpeechButton } } }">
                    <Flex justify="space-between" align="center">
                      <Flex gap="small" align="center">
                        <Spin :indicator="indicator" :spinning="agentRequestLoading">
                          <!-- 模式选择 -->
                          <!-- 移动端：下拉选择 -->
                          <template v-if="isMobile">

                            <Dropdown  placement="topLeft" :trigger="['click']">
                              <template #overlay>
                                <Menu @click="handleModeSelect">
                                  <Menu-item v-for="item in modeOptions" :key="item.key">
                                    <div class="result-menu-item flex items-center text-base	">
                                      <CompassOutlined v-if="item.key==='auto'"  class="mr-2"/>
                                      <AndroidOutlined v-else-if="item.key ==='agent'"  class="mr-2"/>
                                      <MessageOutlined v-else  class="mr-2"/>
                                      <div class="label">{{ item.label }}</div>
                                    </div>
                                  </Menu-item>
              
                                </Menu>
                              </template>
                              <div class="model-select-mobile">
                                <CompassOutlined v-if="modelValue==='auto'"/>
                                <AndroidOutlined v-else-if="modelValue ==='agent'"/>
                                <MessageOutlined v-else/>
                                <div class="txt">{{ modelLabel }}</div>
                              </div>
                            </Dropdown>
                          </template>
                          <!-- 桌面端：按钮组 -->
                          <div v-else class="model-select flex">
                            <Tooltip> 
                              <template #title>
                                <span>{{ $t('modes.auto') }}</span>
                              </template>
                                <div class="model-select-item  flex-col flex-1" :class="{ 'active': modelValue === 'auto' }"
                                  @click="modelValue = 'auto';handleDocClose()">
                                  <CompassOutlined />
                                </div>
                          </Tooltip>
                            <Tooltip> 
                              <template #title>
                                <span>{{ $t('modes.agent') }}</span>
                              </template>
                                <div class="model-select-item  flex-col flex-1"
                                  :class="{ 'active': modelValue === 'agent' }" @click="modelValue = 'agent';handleDocClose()">
                                  <AndroidOutlined />
                                </div>
                          </Tooltip>
                            <Tooltip> 
                              <template #title>
                                  <span>{{ $t('modes.chat') }}</span>                              
                              </template>
                                <div class="model-select-item flex-col flex-1" :class="{ 'active': modelValue === 'chat' }"
                                  @click="modelValue = 'chat';handleDocClose()">
                                  <MessageOutlined />
                                </div>
                            </Tooltip>
                          </div>
                        </Spin>
                        
                        <!-- 结果格式选择 -->
                        <Dropdown placement="topLeft" :trigger="['click']" v-if="modelValue!='chat'">
                          <template #overlay>
                            <Menu @click="handleResultFormatSelect" class="result-format-menu">
                              <Menu-item v-for="item in resultFormatOptions" :key="item.key">
                                <div class="result-menu-item flex items-center text-base">
                                  <FileWordOutlined v-if="item.icon === 'FileWordOutlined'" class="mr-2"/>
                                  <GlobalOutlined  v-else-if="item.icon === 'GlobalOutlined'" class="mr-2"/>
                                  <div class="label">{{ item.label }}</div>
                                </div>
                              </Menu-item>
                            </Menu>
                          </template>
                          <div class="result-format-select">
                            <svg t="1762249165203" class="tools-icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="14716" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64"><path d="M336.64 785.6h636.16v86.4H336.64zM972.8 152v86.4H336.64v-86.4z" fill="#707070" p-id="14717"></path><path d="M195.2 51.2a144 144 0 1 1 0 288 144 144 0 0 1 0-288z m0 86.4a57.6 57.6 0 1 0 0 115.2 57.6 57.6 0 0 0 0-115.2zM195.2 684.8a144 144 0 1 1 0 288 144 144 0 0 1 0-288z m0 86.4a57.6 57.6 0 1 0 0 115.2 57.6 57.6 0 0 0 0-115.2zM713.6 368a144 144 0 1 1 0 288 144 144 0 0 1 0-288z m0 86.4a57.6 57.6 0 1 0 0 115.2 57.6 57.6 0 0 0 0-115.2z" fill="#707070" p-id="14718"></path><path d="M623.488 468.8v86.4H108.8v-86.4h514.688z m349.312 0v86.4h-161.28v-86.4h161.28z" fill="#707070" p-id="14719"></path></svg>
                            
                            <div class="txt">{{ resultFormatLabel }}</div>
                          </div>
                        </Dropdown>
                      </Flex>

                      <Flex align="center">
                        <Divider type="vertical" />
                        <component :is="LoadingButton" v-if="agentRequestLoading" type="default"
                          @click="abortCurrentChating" />
                        <component :is="SendButton" v-else type="primary" class="flex justify-center items-center"
                          :disabled="!content" />
                      </Flex>
                    </Flex>
                  </template>

                  <template #header>
                    <Sender.Header :title="$t('chat.attachments')" :open="headerOpen" :styles="{ content: { padding: 0 } }"
                      @open-change="open => headerOpen = open">
                      <Attachments :before-upload="() => false" :items="attachedFiles" @change="handleFileChange">
                        <template #placeholder="type">
                          <Flex v-if="type && type.type === 'inline'" align="center" justify="center" vertical gap="2">
                            <Typography.Text style="font-size: 30px; line-height: 1;" content="CloudUploadOutlined">
                              <CloudUploadOutlined />
                            </Typography.Text>
                            <Typography.Title :level="5" style="margin: 0; font-size: 14px; line-height: 1.5;"
                              :content="$t('chat.uploadFiles')" />
                            <Typography.Text type="secondary" :content="$t('chat.uploadDescription')" />
                          </Flex>
                          <Typography.Text v-if="type && type.type === 'drop'" :content="$t('chat.dropFile')" />
                        </template>
                      </Attachments>
                    </Sender.Header>
                  </template>
                </Sender>
                <Sender v-else :value="content" :loading="agentRequestLoading" @submit="onSubmit" :placeholder="$t('chat.placeholder')" :auto-size="{ minRows: 1, maxRows: 3 }"></Sender>
              </div>

              <!-- 底部区域骨架屏 -->
              <div v-if="conversationLoading" class="sender-skeleton-container">
                <div class="sender-skeleton">
                  <Skeleton.Input :active="true" size="large" style="width: 100%; height: 60px;" />
                  <div class="sender-skeleton-actions">
                    <Skeleton.Button :active="true" size="small" />
                    <Skeleton.Button :active="true" size="small" />
                    <Skeleton.Button :active="true" size="small" />
                  </div>
                </div>
              </div>
              <div class="ai-tips pt-2" v-if="!isSimpleAskContent">{{ $t('chat.aiGeneratedContent') }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="right-agent-container" :style="styles.rightAgent" v-if="showRightAgent">
        <RightAgent :type="rightAgentType" :source="rightAgentSource" :expand="rightAgentExpand" :filename="rightAgentFilename" @close="handleDocClose"
          @fullscreen="handleDocExpand" @shrink="handleDocShrink" @loaded="handleDocLoaded" @error="handleDocError" />
      </div>
      
    </div>
  </div>
</template>

<style lang="scss">
.font-bold {
  font-weight: bold;
}

.mobile-title {
  width: 100%;
  padding: 10px 5px;
  background-color: var(--bg-secondary);
  
  /* 确保左侧内容不会挤压右侧按钮 */
  > div:first-child {
    flex: 1;
    min-width: 0; /* 允许flex子元素缩小到内容以下 */
    overflow: hidden;
  }

}
.conversation-title{
  flex: 1;
  min-width: 0; /* 关键：允许文本容器缩小 */
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mobile-add-conversation {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  min-width: 32px; /* 防止被挤压 */
  flex-shrink: 0; /* 不允许缩小 */
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-right: 10px;
  font-size: 22px;
  &:hover {
    background-color: var(--hover-bg);
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }
}
.chats-wrap{
  display:flex;
  width: 100%;
  overflow: auto;
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 5px;
}


::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.3s ease;
}
.container-layout-iphone{
    /* 
   * iPhone Safari 浏览器底部适配方案：
   * 1. safe-area-inset-bottom: 处理刘海屏（如 iPhone X/11/12/13/14/15 系列）的安全区域
   * 2. 额外的 24px: 为 Safari 浏览器底部地址栏预留空间
   * 
   * Safari 地址栏特性：
   * - 地址栏在滚动时会自动隐藏/显示
   * - 显示时占用约 44-50px 高度
   * - 隐藏时仍需要预留一定空间以便用户交互
   * 
   * 使用 max() 函数确保：
   * - 有刘海的设备：safe-area + 24px
   * - 无刘海的设备：至少 24px
   */
  /* 兼容 iOS < 11.2 版本（使用 constant 而非 env） */
  padding-bottom: calc(constant(safe-area-inset-bottom, 0px) + 78px);
  padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 78px);
}



::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* 当容器悬浮时显示滚动条 */
*:hover ::-webkit-scrollbar-thumb,
*:focus ::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
}

.scroll-wrap:hover ::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
}
</style>

<style lang="scss" scoped>
.menu--item{
  .label{
    width: 40px;
  }
}

.result-menu-item{

  min-width: 70px;
  
  .label{
    white-space: nowrap;
  }
  
  .ant-icon{
    font-size: 16px;
  }
}


.menu-icon{
  position: absolute;
  left: 15px;
  top: 15px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  z-index: 1000;
}
.model-select-mobile{
  display: flex;
  align-items: center;
  justify-content: space-around;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  width: 75px;
  height: 36px;
  line-height: 36px;
  padding: 5px 10px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background-color: var(--bg-tertiary);
  }
  
  .ant-icon{
    font-size: 14px;
  }
  .txt{
  font-size: 14px;
}
  .down{
  font-size: 14px;
  }
}

.result-format-select{
  display: flex;
  align-items: center;
  justify-content: space-around;
  border-radius: 19px;
  border: 1px solid var(--border-color);
  
  height: 32px;
  min-width: 72px;
  padding: 5px 10px;
  line-height: 32px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background-color: var(--bg-tertiary);
  }
  
  .tools-icon{
    width: 18px;
    height: 18px;
    padding:1px;
    color: var(--text-primary);
    font-weight: 600;
  }
  .txt{
    font-size: 14px;
  }
  .down{
    font-size: 14px;
  }
}
.model-select {
  display: flex;
  align-items: center;
  border-radius: 20px;
  background-color: var(--bg-tertiary);
  padding: 1px;
}

.model-select-item {
  cursor: pointer;
  font-size: 17px;
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: 20px;
  transition: background 0.3s ease;
  height: 30px;
  display: flex;
  align-items: stretch;
  justify-content: center;

  &.active {
    background-color: var(--bg-primary);
    font-size: 18px;
    font-weight: 600;
    color: var(--text-checked);
  }
}
.footer-wrapper{
  width: 100%;
  bottom: 0;
  background: transparent;
  /* 为移动端浏览器地址栏预留默认间距 */
}

.footer-area {
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  .ai-tips{
    font-size: 12px;
    display: flex;
    justify-content: center;
    color: var(--text-secondary)
  }
}

/* iPhone 适配的 footer-area */
.footer-area-iphone {
  padding-bottom: 8px;
  transition: padding-bottom 0.3s ease;
}

/* iPhone 适配的输入框 */
.sender-container-iphone {
  margin-bottom: 8px;
   
}
.prompts-container {

  :deep(.ant-welcome-icon) {
    height: fit-content;
    width: 40px;
  }
}

.sender-container {
  width: 100%;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 12px;
  border-color: var(--border-color);
  border-width: 1px;
  border-style: solid;
    &:focus-within{
      border-color: var(--border-more);
    }
    :deep(.ant-input){
      color: var(--text-primary);
      font-size: 15px;
    }
    :deep(textarea::placeholder) {
      color: var(--text-tertiary);
      font-size: 15px;
      color: #b6b6b6;
    }

    :deep(.ant-sender-actions-btn){
      display: flex;
      justify-content: center;
      align-items: center;
    }
}

.ant-sender{
  border-color:  #ffffff00;
  box-shadow: none;
}
.ant-sender:focus-within {
  border-color: #ffffff00;
  box-shadow: unset;
}

/* 消息骨架屏样式 */
.message-skeleton-container {
  padding: 20px 0;
}

.message-skeleton-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 12px;
}

.user-skeleton {
  flex-direction: row-reverse;
}

.assistant-skeleton {
  flex-direction: row;
}

.skeleton-content {
  flex: 1;
  max-width: 70%;
}

.user-skeleton .skeleton-content {
  text-align: right;
}

/* 底部区域骨架屏样式 */
.sender-skeleton-container {
  padding: 16px 0;
}

.sender-skeleton {
  position: relative;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 16px;
  background: var(--bg-primary);
}

.sender-skeleton-actions {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Welcome组件主题适配 */
.welcome-title {
  background: var(--bg-secondary) !important;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.welcome-title :deep(.ant-typography) {
  color: var(--text-primary) !important;
}

.welcome-title :deep(.ant-typography-title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}

.welcome-title :deep(.ant-typography-paragraph) {
  color: var(--text-secondary) !important;
  margin-bottom: 0;
}


.custom-prompts-wrapper :deep(*[class*="item"]) {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.custom-prompts-wrapper :deep(*[class*="item"]:hover) {
  background-color: var(--hover-bg) !important;
}
.custom-prompts-wrapper :deep(*[class*="item"]) {
  background-color: var(--bg-tertiary) !important;
  color: var(--text-secondary) !important;
}


.custom-prompts-wrapper :deep(*[class*="title"]) {
  color: var(--text-primary) !important;
}

.custom-prompts-wrapper :deep(*[class*="description"]) {
  color: var(--text-secondary) !important;
}

/* 强制所有文字元素使用主题颜色 */
.custom-prompts-wrapper :deep(div) {
  color: var(--text-primary) !important;
}

.custom-prompts-wrapper :deep(span) {
  color: var(--text-primary) !important;
}

.custom-prompts-wrapper :deep(p) {
  color: var(--text-secondary) !important;
}

.custom-prompts-wrapper :deep(h1),
.custom-prompts-wrapper :deep(h2),
.custom-prompts-wrapper :deep(h3),
.custom-prompts-wrapper :deep(h4),
.custom-prompts-wrapper :deep(h5),
.custom-prompts-wrapper :deep(h6) {
  color: var(--text-primary) !important;
}

.custom-prompts-wrapper :deep(svg) {
  color: inherit !important;
}

</style>
