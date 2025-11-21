<template>
  <!-- 可悬浮菜单 -->
  <div :style="styles.menu"  @click.stop class="shadow-md">
    <div v-if="isMobile" class="menu-outline" @mouseleave="hideMenu" @click="hideMenu">
      <MenuOutlined />
    </div>
    <div class="menu-toggle-2"  @click.stop="toggleMenu" v-else>
      <Tooltip :title="$t('nav.dock')" @mouseleave="hideMenu">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          class="menu-icon lucide lucide-panel-left size-5 text-[var(--icon-secondary)]">
          <rect width="18" height="18" x="3" y="3" rx="2"></rect>
          <path d="M9 3v18"></path>
        </svg>
      </Tooltip>
    </div>
    <!-- 🌟 Logo -->
    <div :style="styles.logo">
      <img :src="logo" draggable="false" alt="logo" :style="styles['logo-img']">
      <span :style="styles['logo-span']" class="text-lg font-bold text-blue-600 p-2 rounded">{{ appName
        }}</span>
    </div>

    <!-- 🌟 添加会话 -->
    <Button type="link" :style="styles.addBtn" @click="onAddConversation" v-if="!isMobile">
      <template #icon>
        <PlusOutlined />
      </template>
      {{ $t('chat.newConversation') }}
    </Button>
    <!-- 类别： 全部 ，已订阅 -->
    <div :style="styles.category">
      <div :style="{ ...styles.categoryItem, ...(category === 'all' ? styles.activeCategoryItem : {}) }"
        @click="typeClick('all')">
        <span>{{ $t('chat.allChats') }}</span>
      </div>
      <div :style="{ ...styles.categoryItem, ...(category === 'subscribed' ? styles.activeCategoryItem : {}) }"
        @click="typeClick('subscribed')">
        <span>{{ $t('reports.assistantReports') }}</span>
      </div>
    </div>
    <!--订阅报告下的下拉菜单-->
    <div v-if="category === 'subscribed'" :style="styles.subscriptionContainer">
      <Dropdown :trigger="['click']" @open-change="onDropdownOpenChange">
        <div :style="styles.dropdownTrigger" class="dropdown-trigger">

          <span class="mr-2">{{ selectedSubscriptionType || $t('reports.allAssistants') }}</span>
          <FilterOutlined />
        </div>
        <template #overlay>
          <Menu @click="onSubscriptionMenuClick" :style="styles.dropdownMenu">
            <MenuItem v-for="item in subscriptionTypes" :key="item.key">
            <div :style="styles.menuItem">
              <span>{{ item.label }}</span>
            </div>
            </MenuItem>
          </Menu>
        </template>
      </Dropdown>
    </div>
    <!-- 🌟 会话列表或助理报告列表 -->
    <!-- 当选择"助理报告"时，替换会话列表为报告列表 -->
    <div v-if="category === 'subscribed'" :style="styles.conversations">
      <!-- 报告列表骨架屏 -->
      <div v-if="reportsLoading" class="reports-skeleton">
        <div v-for="i in 6" :key="i" class="report-skeleton-item">
          <Skeleton.Avatar :size="40" shape="square" />
          <div class="report-skeleton-content">
            <Skeleton :paragraph="{ rows: 2, width: ['85%', '60%'] }" :title="false" active />
          </div>
        </div>
      </div>
      <!-- 报告列表内容 -->
      <div v-else class="report-list">
        <div v-for="report in reports" :key="report.id" class="report-item" :class="[checkedReport ==report.id?'actived':'', !report.is_read?'unread':'']" @click="onReportClick(report)">
          <div class="icon-wrap">
            <FileDoneOutlined/>
            <div v-if="!report.is_read" class="unread-badge">1</div>
          </div>
          <div class="report-main ml-3">
            <div class="report-title">
             {{ report.title }}
            </div>
            <div class="report-meta">
            {{ report.type }}
            </div>
          </div>
          <div class="right">
            <div class="date"> {{ formatTime(report.created_time) }}</div>
            <menu>

            </menu>
          </div>
        </div>
        <div v-if="reports.length === 0" class="report-empty">{{ $t('reports.noMatchingReports') }}</div>
      </div>
    </div>
    <template v-else>
      <div v-if="conversationsLoading" :style="styles.conversations">
        <!-- 会话列表骨架屏 -->
        <div class="conversations-skeleton">
          <div v-for="(width, i) in ['90%', '70%', '85%', '60%', '95%', '75%']" :key="i"
            class="conversation-skeleton-item">
            <Skeleton.Avatar :size="32" />
            <div class="conversation-skeleton-content">
              <Skeleton :paragraph="{ rows: 1, width: [width] }" :title="false" active />
            </div>
          </div>
        </div>
      </div>
      <div v-else ref="conversationListWrapperRef" :style="styles.conversations" class="conversation-list-wrapper" @scroll="onConversationListScroll">
        <Conversations :menu="menuConfig" class="conversation-list" :items="conversationsItems"
          :active-key="activeKey" @active-change="onConversationClick" />
        <!-- 加载更多提示 -->
        <div v-if="conversationsLoadingMore" class="load-more-indicator">
          <Skeleton :paragraph="{ rows: 1, width: ['60%'] }" :title="false" active />
        </div>
        <div v-else-if="!conversationsHasMore && conversationsTotal > conversationsPageSize" class="load-more-end">
          {{ $t('chat.noMoreConversations') || '没有更多会话了' }}
        </div>
      </div>
    </template>
    <div :style="styles.settings">
      <div class="flex items-center justify-end h-full text-xl w-full gap-4 px-4">
        <div
          class="flex items-center justify-center rounded-md  p-2 bg-transparent hover:bg-gray-200 cursor-pointer transition-colors"
          @click="showSubscriptionsModal = true">
          <Tooltip :title="$t('nav.mySubscriptions')">
            <FieldTimeOutlined />
          </Tooltip>
        </div>
        <div
          class="flex items-center justify-center rounded-md  p-2 bg-transparent hover:bg-gray-200 cursor-pointer transition-colors"
          @click="showSettingsModal = true">
          <Tooltip :title="$t('nav.settings')">
            <SettingOutlined />
          </Tooltip>
        </div>
        <div class="flex items-center justify-center rounded-md p-2 bg-transparent hover:bg-gray-200"
          @click="handleLogout">
          <Tooltip :title="$t('nav.logout')">
            <LogoutOutlined class="text-orange-500 cursor-pointer" />
          </Tooltip>
        </div>
      </div>
    </div>

    <!-- 设置弹窗 -->
    <SettingsModal v-if="showSettingsModal || showSubscriptionsModal" :visible="showSettingsModal || showSubscriptionsModal"
      :initial-menu="showSubscriptionsModal ? 'subscriptions' : 'settings'" :userInfo="UserInfo" @close="closeModals" />
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref, onMounted, watch, defineExpose, nextTick, onUnmounted } from 'vue'
import { Button, Tooltip, Dropdown, Menu, MenuItem, Modal, Skeleton } from 'ant-design-vue'
import { MenuOutlined, PlusOutlined, FieldTimeOutlined, SettingOutlined, DeleteOutlined, LogoutOutlined, FileDoneOutlined, FilterOutlined } from '@ant-design/icons-vue'
import type { ConversationsProps } from 'ant-design-x-vue'
import { Conversations } from 'ant-design-x-vue'

import { getAiAssistants,getUserReports,markReadReport } from '@/api/subscription'
import logo from '@/assets/images/logo.png'
import { getChats, deleteChat } from '@/api/chat'
import store from '@/store'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SettingsModal from './settings-modal.vue'


const router = useRouter()
const { t } = useI18n()
// 内部状态变量
const internalConversations = ref<{ id: string, title: string }[]>([])
const internalActiveConversation = ref<{ id: string, title: string } | null>(null)
const appName = ref('AI Assistant')
const category = ref('all')
const conversationsLoading = ref(true) // 会话列表加载状态
const reportsLoading = ref(false) // 报告列表加载状态
// 分页相关状态
const conversationsPage = ref(1) // 当前页码
const conversationsPageSize = ref(40) // 每页数量
const conversationsHasMore = ref(true) // 是否还有更多数据
const conversationsLoadingMore = ref(false) // 是否正在加载更多
const conversationsTotal = ref(0) // 总数据量
// 弹窗状态
const showSettingsModal = ref(false)
const showSubscriptionsModal = ref(false)
// 会话列表容器引用
const conversationListWrapperRef = ref<HTMLElement | null>(null)

// 助理报告 - 模拟数据
type ReportItem = {
  id: string
  title: string
  type: string
  fileUrl: string
  created_time: string
  is_read: boolean
}
const typeClick = (type: string) => {
  category.value = type
  if(type === 'subscribed'){
    getAIAssistantReportListApi()
  }
}


// // 根据选择的助理类型过滤
// const filteredReports = computed(() => {
//   if (selectedSubscriptionType.value && selectedSubscriptionType.value !== '所有助理') {
//     return reports.value.filter(r => r.type === selectedSubscriptionType.value)
//   }
//   return reports.value
// })

// Props
const props = defineProps({
  menuVisible: {
    type: Boolean,
    default: true
  },
  menuVisibleFlag: {
    type: Boolean,
    default: false
  },
  isMobile: {
    type: Boolean,
    default: false
  },

  activeConversation: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['add-conversation', 'conversation-click', 'hide-menu', 'toggle-menu', 'conversations-updated', 'active-conversation-updated', 'open-report'])

// 计算样式
const styles = computed(() => {
  return {
    'menu': {
      'background': 'var(--bg-tertiary)',
      'width': '280px',
      'height': '100%',
      'display': 'flex',
      'flex-direction': 'column',
      'position': props.menuVisibleFlag ? 'fixed' : 'static',
      'border-radius': props.menuVisibleFlag ? '10px' : '0',
      'border': props.menuVisibleFlag ? '1px solid var(--border-color)' : 'none',
      'box-shadow': props.menuVisibleFlag ? '0 0 2px var(--shadow-color)' : 'none',
      'left': props.menuVisible ? '0' : '-283px',
      'top': '0',
      'z-index': '1000',
      'transition': 'left 0.3s ease',
      'border-right': '1px solid var(--border-agent)'
    },
    'settings':{
      'height': '60px',
      'border-top': '1px solid var(--border-color)'
    },
    'category': {
      'display': 'flex',
      'flex-direction': 'row',
      'justify-content': 'flex-start',
      'padding': '10px 8px 5px 8px',
    },
    'categoryItem': {
      'display': 'flex',
      'flex-direction': 'row',
      'justify-content': 'space-between',
      'padding': '4px 12px',
      'border-radius': '15px',
      'border': '1px solid var(--border-color)',
      'background-color': 'var(--bg-tertiary)',
      'margin': '0 4px',
      'cursor': 'pointer',
      'transition': 'background-color 0.3s ease',
      'color': 'var(--text-secondary)',
      'font-size': '13px',
      'font-family': '-apple-system, "system-ui", "Segoe UI Variable Display", "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol',
      '&:hover': {
        'background-color': '#11111111',
        'color': '#ffffff',
      }
    },
    'activeCategoryItem': {
      'background-color': 'var(--active-bg2)',
      'color': 'var(--text-primary)',
    },

    'conversations': {
      'padding': '0 8px',
      'flex': 1,
      'overflow-y': 'auto',
      'margin': '5px 0px',
      'position': 'relative',
    },
    'logo': {
      'display': 'flex',
      'height': '52px',
      'align-items': 'center',
      'justify-content': 'start',
      'padding': '0 24px',
      'box-sizing': 'border-box',
    },
    'logo-img': {
      width: '24px',
      height: '26px',
      display: 'inline-block',
      marginTop: '5px'
    },
    'logo-span': {
      'display': 'inline-block',
      'font-weight': 'bold',
      'color': 'var(--text-primary)',
      'font-size': '16px',
    },
    'addBtn': {
      background: 'var(--bg-primary)',
      width: 'calc(100% - 24px)',
      margin: '0 12px 0px 12px',
      height: '40px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    },
    'subscriptionContainer': {
      margin: '10px 12px',
    },
    'dropdownTrigger': {
      display: 'inline-flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '6px 10px',
      backgroundColor: 'var(--bg-tertiary)',
      borderRadius: '5px',
      cursor: 'pointer',
      fontSize: '12px',
      color: 'var(--text-primary)',
      whiteSpace: 'nowrap',
    },
    'dropdownMenu': {
      fontSize: '12px',
      minWidth: 'fit-content',
    },
    'menuItem': {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%',
      minWidth: 'fit-content',
    },
    'checkIcon': {
      color: '#333',
      marginLeft: '10px',
    },
  }
})

const menuConfig: ConversationsProps['menu'] = (conversation) => ({
  items: [

    {
      label: t('common.delete'),
      key: 'delete',
      icon: h(DeleteOutlined),
    },
  ],
  onClick: async (menuInfo) => {
    if (menuInfo.key == 'delete') {
      // 显示删除确认弹窗
      Modal.confirm({
        title: t('confirmDialog.deleteConversation'),
        content: t('confirmDialog.deleteConversationContent'),
        okText: t('confirmDialog.confirmDelete'),
        cancelText: t('confirmDialog.cancel'),
        okType: 'danger',
        async onOk() {
          try {
            conversationsLoading.value = true
            const res = await deleteChat(conversation.key)
            if (res.data.status) {
              const chat_id = localStorage.getItem('store_chat_id');
              if (chat_id == conversation.key) {
                onAddConversation(undefined)
              }
              // 重置分页状态并重新加载第一页
              conversationsPage.value = 1
              conversationsHasMore.value = true
              const fetchedConversations = await loadConversationList(1, false)
              internalConversations.value = fetchedConversations;
            }
            console.info("DeleteOutlined:", res)
          } catch (error) {
            console.error('删除会话失败:', error);
          } finally {
            conversationsLoading.value = false
          }
        },
        onCancel() {
          console.log('用户取消删除会话');
        }
      });
    }
    console.info("DeleteOutlined:", menuInfo, conversation)
    // messageApi.info(`Click ${conversation.key} - ${menuInfo.key}`); // Removed contextHolder
  },
});
// 计算属性
const conversationsItems = computed(() => {
  // 优先使用内部状态，如果没有则使用props
  const conversationsToUse = internalConversations.value

  if (conversationsToUse.length === 0) {
    return [
      {
        key: 'new',
        label: 'New Conversation',
      }
    ]
  }

  return conversationsToUse.map(conv => ({
    key: conv.id,
    label: conv.title || `Chat ${conv.id}`,
  }))
})

const activeKey = computed(() => {
  const activeConversationToUse = internalActiveConversation.value || props.activeConversation
  return activeConversationToUse?.id || 'new'
})

const loadConversationList = async (page: number = 1, append: boolean = false) => {
  try {
    if (append) {
      conversationsLoadingMore.value = true
    }
    const chatsResponse = await getChats({ page, size: conversationsPageSize.value });
    const responseData = chatsResponse.data
    
    // 处理分页响应数据
    let items = []
    let total = 0
    let hasMore = false
    
    // 检查响应数据结构：可能是分页对象或数组
    if (responseData && typeof responseData === 'object') {
      if (Array.isArray(responseData)) {
        // 兼容旧格式：直接返回数组
        items = responseData
        total = responseData.length
        hasMore = false
      } else if (responseData.items) {
        // 新格式：分页对象
        items = responseData.items || []
        total = responseData.total || 0
        hasMore = responseData.page < responseData.total_pages
      } else {
        items = []
        total = 0
        hasMore = false
      }
    }
    
    const fetchedConversations = items.map((chat: any) => ({
      id: chat.id,
      title: chat.title || `Chat ${chat.id}`
    }))
    
    if (append) {
      // 追加模式：将新数据追加到现有列表
      internalConversations.value = [...internalConversations.value, ...fetchedConversations]
    } else {
      // 替换模式：替换整个列表
      internalConversations.value = fetchedConversations
    }
    
    // 更新分页状态
    conversationsPage.value = page
    conversationsTotal.value = total
    conversationsHasMore.value = hasMore
    
    // 数据加载后重新设置滚动监听
    if (append) {
      nextTick(() => {
        setupScrollObserver()
      })
    }
    
    return fetchedConversations
  } finally {
    if (append) {
      conversationsLoadingMore.value = false
    }
  }
}

// 加载更多会话
const loadMoreConversations = async () => {
  if (conversationsLoadingMore.value || !conversationsHasMore.value) {
    return
  }
  const nextPage = conversationsPage.value + 1
  await loadConversationList(nextPage, true)
}
// 初始化聊天
const initChat = async () => {

  if(loadAskContent()){
    // 
    return
  }
  try {
    conversationsLoading.value = true
    // 从localStorage获取会话ID
    const storedChatId = localStorage.getItem('store_chat_id');
    // 获取会话列表
    const fetchedConversations = await loadConversationList()
    internalConversations.value = fetchedConversations;

    console.info("found storedChatId: ", storedChatId)
    // 设置当前会话
    if (storedChatId) {
      const found = fetchedConversations.find(conv => conv.id === storedChatId);
      console.info("found storedChatId: ", found)
      if (found) {
        internalActiveConversation.value = found;
        emit('active-conversation-updated', found);
        emit('conversation-click', internalActiveConversation.value);
      }else{
        internalActiveConversation.value = fetchedConversations[0]
        emit('conversation-click', internalActiveConversation.value);
      }
    }else{
      internalActiveConversation.value = fetchedConversations[0]
      emit('conversation-click', internalActiveConversation.value);
    }

    // 如果没有当前会话或者会话没有消息，创建一个新会话
    if (!internalActiveConversation.value || internalConversations.value.length === 0) {
      // 创建新会话
      onAddConversation(undefined);
    }
  } catch (error) {
    console.error('初始化聊天失败:', error);

  } finally {
    conversationsLoading.value = false
  }
}
// 加载助理及助理报告列表
const loadAssistantsAndReports = async () => { 
  
  await getAIAssistantListApi()
  // await getAIAssistantReportListApi()
  
}
const subscriptionTypeIdMapName = ref<{ [key: string]: string }>({})
const getAIAssistantListApi = async () => {
  const res = await  getAiAssistants()
  res.data.data.forEach(assistant => {
     subscriptionTypes.push({
      label: assistant.name,
      key: assistant.id
     })
     subscriptionTypeIdMapName.value[assistant.id] = assistant.name
  });
  console.info("getAiAssistantListApi:" , res)
}
const reports = ref<ReportItem[]>([])
const getAIAssistantReportListApi = async () => {
  try {
    reportsLoading.value = true
    const params = {
      assistant_id: selectedSubscriptionId.value === 'all' ? null : selectedSubscriptionId.value,
      page: 1,
      size: 20,
    }
    const res = await getUserReports(params)
    reports.value = res.data.data.items.map((it)=>{
      const assistant_name =  subscriptionTypeIdMapName.value[it.assistant_id]
      const subscription_name = it.subscription_name
      const report_result = JSON.parse(it.report_result)
      return {
        id: it.id,
        title: subscription_name?subscription_name:assistant_name,
        type: assistant_name,
        assistant_id: it.assistant_id,
        is_read: it.is_read,
        created_time: it.created_time,
        // fileUrl: report_result.file.url,
        report_result: report_result
      }
    })
  } catch (error) {
    console.error('获取报告列表失败:', error)
  } finally {
    reportsLoading.value = false
  }
}
// 方法
const hideMenu = () => {
  emit('hide-menu')
}

const toggleMenu = () => {
  emit('toggle-menu')
}

const onAddConversation = (askContent: string | undefined) => {
  emit('hide-menu')
  // 排除 PointerEvent 对象，只处理字符串类型
  const content = typeof askContent === 'string' ? askContent : undefined
  console.info("onAddConversation: ", content)
  emit('add-conversation', content)
}

const onConversationClick = (key: string) => {
  // 如果是新建会话
  if (key === 'new') {
    internalActiveConversation.value = null;
  } else {
    // 查找对应的会话并设置为当前会话
    const found = internalConversations.value.find(conv => conv.id === key);
    if (found) {
      internalActiveConversation.value = found;
    }
  }

  emit('conversation-click', internalActiveConversation.value)
}

// 会话列表滚动事件处理
const onConversationListScroll = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target) return
  
  // 计算是否滚动到底部（距离底部50px时触发加载）
  const scrollTop = target.scrollTop
  const scrollHeight = target.scrollHeight
  const clientHeight = target.clientHeight
  const distanceToBottom = scrollHeight - scrollTop - clientHeight
  
  // 当距离底部小于50px时，触发加载更多
  if (distanceToBottom < 50 && conversationsHasMore.value && !conversationsLoadingMore.value) {
    loadMoreConversations()
  }
}

// 使用 Intersection Observer 作为备用方案（更可靠）
let intersectionObserver: IntersectionObserver | null = null

const setupScrollObserver = () => {
  if (typeof window === 'undefined' || !window.IntersectionObserver) return
  
  // 清理旧的 observer
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
  
  nextTick(() => {
    if (!conversationListWrapperRef.value) return
    
    // 创建一个哨兵元素用于检测是否到达底部
    const sentinel = document.createElement('div')
    sentinel.style.height = '1px'
    sentinel.style.visibility = 'hidden'
    sentinel.className = 'scroll-sentinel'
    
    // 将哨兵元素插入到列表底部
    const wrapper = conversationListWrapperRef.value
    const existingSentinel = wrapper.querySelector('.scroll-sentinel')
    if (existingSentinel) {
      existingSentinel.remove()
    }
    wrapper.appendChild(sentinel)
    
    // 创建 Intersection Observer
    intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && conversationsHasMore.value && !conversationsLoadingMore.value) {
            loadMoreConversations()
          }
        })
      },
      {
        root: wrapper,
        rootMargin: '0px',
        threshold: 0.1,
      }
    )
    
    intersectionObserver.observe(sentinel)
  })
}

// 订阅报告下拉菜单状态
const subscriptionDropdownOpen = ref(false);
const selectedSubscriptionType = ref<string>(t('reports.allAssistants'));
const selectedSubscriptionId = ref<string>('all');
const subscriptionTypes = [
  { key: 'all', label: t('reports.allAssistants') },

];



const onDropdownOpenChange = (open: boolean) => {
  subscriptionDropdownOpen.value = open;
};

const onSubscriptionMenuClick = ({ key }: { key: string | number }) => {
  const selectedItem = subscriptionTypes.find(item => item.key === key);
  if (selectedItem) {
    selectedSubscriptionType.value = selectedItem.label;
    selectedSubscriptionId.value = selectedItem.key;
  }
  getAIAssistantReportListApi()
};

const checkedReport = ref<string>('')
// 打开助理报告（由父组件处理右侧视图）
const onReportClick = async (report: ReportItem) => {
  checkedReport.value = report.id
  emit('open-report', report)
    // 如果报告未读，则标记为已读
  if (!report.is_read) {
    try {
      await markReadReport(report.id)
      // 更新本地状态
      const reportIndex = reports.value.findIndex(r => r.id === report.id)
      if (reportIndex !== -1) {
        reports.value[reportIndex].is_read = true
      }
    } catch (error) {
      console.error('标记报告为已读失败:', error)
    }
  }
}

// 处理退出登录
const handleLogout = () => {
  Modal.confirm({
    title: t('logoutConfirmation.title'),
    content: t('logoutConfirmation.content'),
    okText: t('logoutConfirmation.okText'),
    cancelText: t('logoutConfirmation.cancelText'),
    okType: 'danger',
    async onOk() {
      // 执行退出登录逻辑
      await store.dispatch('auth/logout');
      router.push('/login');
    },
    onCancel() {
      // 用户取消，不做任何操作
      console.log('用户取消退出登录');
    }
  });
};

// 关闭弹窗
const closeModals = () => {
  showSettingsModal.value = false;
  showSubscriptionsModal.value = false;
};

// 暴露给父组件的方法
const addNewConversation = (newConversation: { id: string; title: string }) => {
  // 将新会话添加到列表开头
  internalConversations.value.unshift(newConversation);
  // 设置为当前活跃会话
  internalActiveConversation.value = newConversation;
  // 触发事件通知父组件
  emit('conversations-updated', internalConversations.value);
  emit('active-conversation-updated', newConversation);
  console.log('通过父组件调用添加新会话:', newConversation);
}
const UserInfo = ref(undefined)
// 加载本地用户信息
const loadLocalUserInfo = () => {
  const userInfo = localStorage.getItem('user')
  const user = JSON.parse(userInfo)
  UserInfo.value = user
  console.info("userInfo: ", user.username)

}
const onDocClosed = ()=>{
  checkedReport.value = ''
}

// 时间格式化函数
const formatTime = (timeString: string) => {
  if (!timeString) return ''
  
  const now = new Date()
  const targetTime = new Date(timeString)
  
  // 获取今天的开始时间
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  
  // 获取本周的开始时间（周一）
  const weekStart = new Date(todayStart)
  const dayOfWeek = now.getDay()
  const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  weekStart.setDate(todayStart.getDate() - daysToMonday)
  
  // 判断是否为当天
  if (targetTime >= todayStart) {
    // 当天显示小时分钟
    return targetTime.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  }
  
  // 判断是否在本周内
  if (targetTime >= weekStart) {
    // 本周显示周几
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return weekDays[targetTime.getDay()]
  }
  
  // 其他情况显示日期
  return targetTime.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

// 暴露方法给父组件
defineExpose({
  addNewConversation,
  onDocClosed
})
const loadAskContent = () => {
  const urlParams = new URLSearchParams(window.location.search)
  const askContent = urlParams.get('askContent')
  if (askContent) {
    console.info("检测到askContent参数:", askContent)
    onAddConversation(askContent)
    return true
  }
  return false
}
// 组件挂载时初始化
onMounted(() => {
  initChat();
  loadAssistantsAndReports()
  loadLocalUserInfo()
  // 设置滚动监听
  nextTick(() => {
    setupScrollObserver()
  })
})

// 组件卸载时清理
onUnmounted(() => {
  if (intersectionObserver) {
    intersectionObserver.disconnect()
    intersectionObserver = null
  }
})

// 监听外部activeConversation的变化
watch(() => props.activeConversation, (newVal) => {
  if (newVal) {
    internalActiveConversation.value = newVal;
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.menu-outline {
  display: flex;
  align-items: center;
  padding: 10px 0 0 10px;
}

.menu-toggle-2 {
  padding: 15px 0 0 15px;
  cursor: pointer;
}

.menu-icon {
  color: var(--text-secondary);
  transition: all 0.3s ease;
  outline-style: none;
  outline: none;
  border: none;
}

.menu-toggle-2 .menu-icon:hover {
  background-color: var(--hover-bg);
  transform: scale(1.05);
  border-radius: 2px;
}

/* 菜单图标自动隐藏样式 */
:deep(.ant-conversations-item-active) {
  background-color: var(--hover-bg);
  &:not(:hover) .ant-conversations-menu-icon {
    visibility: hidden;
  }
  
}
:deep(.ant-conversations-item){
  .ant-conversations-label{
    color: var(--text-primary);
  }
  &:hover{
    background-color: var(--hover-bg) !important;
  }
}

/* 下拉菜单触发器hover效果 */
.dropdown-trigger {
  transition: all 0.3s ease;

  &:hover {
    background-color: var(--hover-bg) !important;
    color: var(--text-primary) !important;
  }
}



/* 自定义WebKit浏览器的滚动条样式 - 组件特定样式 */
:deep(.ant-design-x-vue-conversations) {

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

/* 会话列表骨架屏样式 */
.conversations-skeleton {
  padding: 8px 0;
}

.conversation-skeleton-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  gap: 12px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.conversation-skeleton-item:hover {
  background: var(--hover-bg);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.conversation-skeleton-content {
  flex: 1;
  min-width: 0;
}

/* 让skeleton的头像更圆润 */
.conversation-skeleton-item :deep(.ant-skeleton-avatar) {
  border-radius: 50%;
}

/* 调整skeleton文本的样式 */
.conversation-skeleton-item :deep(.ant-skeleton-paragraph) {
  margin-bottom: 0;
}

.conversation-skeleton-item :deep(.ant-skeleton-paragraph > li) {
  height: 16px;
  border-radius: 4px;
}
.conversation-list{

  :deep(.ant-conversations-item){
    height: 38px;
    min-height:38px;
  }
}

/* 报告列表骨架屏样式 */
.reports-skeleton {
  padding: 8px 0;
}

.report-skeleton-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  gap: 12px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.report-skeleton-item:hover {
  background: var(--hover-bg);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.report-skeleton-content {
  flex: 1;
  min-width: 0;
}

/* 让skeleton的图标更方正 */
.report-skeleton-item :deep(.ant-skeleton-avatar) {
  border-radius: 8px;
}

/* 调整skeleton文本的样式 */
.report-skeleton-item :deep(.ant-skeleton-paragraph) {
  margin-bottom: 0;
}

.report-skeleton-item :deep(.ant-skeleton-paragraph > li) {
  height: 16px;
  border-radius: 4px;
}

/* 助理报告列表样式 */
.report-list {
  padding: 0;
}

.report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  cursor: pointer;
  &.actived{
    background: var(--hover-bg);
  }
  &:hover{
    background: var(--hover-bg);
  }
  &.unread{
    background: var(--bg-table-header);
  }
  .icon-wrap{
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
    padding: 8px;
    border-radius: 15px;
    position: relative;
  }
  .report-main{
    flex: 1;
    .report-h{
      display: flex;
      align-items: center;
      justify-content: space-between;
      
    }
  }
  .right{
    width: 40px;
    .date{
        font-size: 12px;
        color: var(--text-tertiary); 
      }
  }
}

.report-title {
  font-size: 14px;
  color: var(--text-primary);
}

.report-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.report-action .report-link {
  font-size: 12px;
  color: var(--primary-color);
  text-decoration: none;
}

.report-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
  padding: 12px 0;
}

/* 未读标签样式 */
.unread-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background-color: #ff4d4f;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  border: 2px solid var(--bg-secondary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* 加载更多提示样式 */
.load-more-indicator {
  padding: 12px 16px;
  text-align: center;
}

.load-more-end {
  padding: 12px 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
}
</style>