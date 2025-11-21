<template>
  <div class="settings-modal-overlay" @click="handleOverlayClick">
    <div class="settings-modal" @click.stop>
      <!-- 左侧菜单 -->
      <div class="settings-sidebar">
        <!-- Logo + 应用名称 -->
        <div class="sidebar-header">
          <div class="logo-container">
            <img :src="logo" draggable="false" alt="logo" class="logo">
            <span class="app-name">{{ $t('nav.appName') }}</span>
          </div>
          <!-- 移动端关闭按钮 -->
          <div v-if="isMobile" class="close-btn" @click="$emit('close')">
            <CloseOutlined />
          </div>
        </div>

        <!-- 菜单项 -->
        <div class="sidebar-menu">
          <!-- 桌面端菜单 -->
          <a-menu
            v-if="!isMobile"
            :selectedKeys="[activeMenu]"
            mode="vertical"
            class="desktop-menu"
            @click="handleMenuClick"
          >
            <a-menu-item v-for="item in menuItems" :key="item.key">
              <template #icon>
                <component :is="item.icon" />
              </template>
              {{ item.label }}
            </a-menu-item>
          </a-menu>

          <!-- 移动端菜单 -->
          <a-menu
            v-else
            :selectedKeys="[activeMenu]"
            mode="horizontal"
            class="mobile-menu"
            @click="handleMenuClick"
          >
            <a-menu-item v-for="item in menuItems" :key="item.key">
              <template #icon>
                <component :is="item.icon" />
              </template>
              {{ item.label }}
            </a-menu-item>
          </a-menu>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-content">
        <!-- 内容头部 - 移动端隐藏 -->
        <div v-if="!isMobile" class="content-header">
          <h2 class="content-title">{{ getActiveMenuTitle() }}</h2>
          <div class="close-btn" @click="$emit('close')">
            <CloseOutlined />
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="content-body">
          <!-- 账户设置 -->
          <div v-if="activeMenu === 'account'" class="content-section">
            <div class="account-info">
              <div class="info-item">
                <label>{{ $t('settings.username') }}</label>
                <span>{{ props.userInfo.username }}</span>
              </div>
              <div class="info-item">
                <label>{{ $t('settings.email') }}</label>
                <span>{{ props.userInfo.email }}</span>
              </div>
              <div class="info-item">
                <label>{{ $t('settings.lastLogin') }}</label>
                <span>{{
                  formatDateTime(props.userInfo.last_login_time)
                }}</span>
              </div>
            </div>
          </div>

          <!-- 系统设置 -->
          <div v-if="activeMenu === 'settings'" class="content-section">
            <h3>{{ $t('settings.systemSettings') }}</h3>
            <div class="settings-form">
              <div class="form-item">
                <label>{{ $t('settings.themeMode') }}</label>
                <div class="theme-selector">
                  <div
                    v-for="theme in themeOptions"
                    :key="theme.value"
                    :class="[
                      'theme-option',
                      { active: themeMode === theme.value }
                    ]"
                    @click="themeMode = theme.value"
                  >
                    <div
                      class="theme-icon"
                      :class="`theme-icon-${theme.icon}`"
                    ></div>
                    <span class="theme-label">{{ theme.label }}</span>
                    <div v-if="themeMode === theme.value" class="theme-check">
                      <CheckOutlined />
                    </div>
                  </div>
                </div>
              </div>
              <div class="form-item">
                <label>{{ $t('settings.language') }}</label>
                <select v-model="language" class="form-select">
                  <option value="zh">{{ $t('settings.languages.zh') }}</option>
                  <option value="en">{{ $t('settings.languages.en') }}</option>
                </select>
              </div>

              <!-- <div class="form-item">
                <label>{{ $t('settings.notifications') }}</label>
                <div class="checkbox-group">
                  <label class="checkbox-item">
                    <input type="checkbox" v-model="notifications.email" />
                    <span>{{ $t('settings.emailNotification') }}</span>
                  </label>
                  <label class="checkbox-item">
                    <input type="checkbox" v-model="notifications.push" />
                    <span>{{ $t('settings.pushNotification') }}</span>
                  </label>
                </div>
              </div> -->
            </div>
          </div>

          <!-- 我的订阅 -->
          <div v-if="activeMenu === 'subscriptions'" class="content-section">
            <div class="subscriptions-header">
              <div class="subscriptions-actions">
                <a-button
                  @click="fetchSubscriptions"
                  :disabled="subscriptionsLoading"
                >
                  {{ $t('common.refresh') }}
                </a-button>
              </div>
            </div>

            <div v-if="subscriptionsLoading" class="loading-state">
              <div class="loading-spinner"></div>
              <span>{{ $t('common.loading') }}</span>
            </div>

            <div v-else-if="subscriptions.length === 0" class="empty-state">
              <div class="empty-icon">📋</div>
              <p>{{ $t('settings.noSubscriptions') }}</p>
              <span class="empty-desc">{{ $t('settings.noSubscriptionsDesc') }}</span>
            </div>

            <div v-else class="table-wrap">
              <table class="subs-table">
                <thead>
                  <tr>
                    <th>{{ $t('settings.subscriptionTableHeaders.name') }}</th>
                    <th>{{ $t('settings.subscriptionTableHeaders.assistant') }}</th>
                    <th>{{ $t('settings.subscriptionTableHeaders.frequency') }}</th>
                    <th>{{ $t('settings.subscriptionTableHeaders.dataRange') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in subscriptions" :key="item.id">
                    <td class="subscription-name">{{ item.name }}</td>
                    <td class="subscription-type">
                      <span
                        class="type-badge"
                        :class="`type-${item.assistant_name}`"
                      >
                        {{ item.assistant_name }}
                      </span>
                    </td>
                    <td class="execution-frequency">
                      {{ formatExecutionFrequency(item) }}
                    </td>
                    <td class="assistant-id">
                      {{ item.setting_str }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  UserOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  CheckOutlined
} from '@ant-design/icons-vue'
import {
  Button as AButton,
  Menu as AMenu,
  MenuItem as AMenuItem
} from 'ant-design-vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'
import { getUserSubscriptions } from '@/api/subscription'
import logo from '@/assets/images/logo.png'

// Simple date formatter - replace with actual utility if needed
const formatDateTime = dateString => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 定义组件属性
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  initialMenu: {
    type: String,
    default: 'account'
  },
  userInfo: {
    type: Object,
    default: () => ({})
  }
})

// 定义组件事件
const emit = defineEmits(['close'])

// 获取 store 和 i18n
const store = useStore()
const { t } = useI18n()
const isMobile = computed(() => store.getters['device/isMobile'])

// 从store获取主题模式并双向绑定
const themeMode = computed({
  get: () => store.getters['device/themeMode'],
  set: value => store.dispatch('device/setThemeMode', value)
})

// 主题选项配置
const themeOptions = computed(() => [
  {
    value: 'light',
    label: t('settings.themes.light'),
    icon: 'sun'
  },
  {
    value: 'dark',
    label: t('settings.themes.dark'),
    icon: 'moon'
  },
  {
    value: 'auto',
    label: t('settings.themes.system'),
    icon: 'auto'
  }
])

// 菜单项配置
const menuItems = computed(() => [
  {
    key: 'account',
    label: t('settings.account'),
    icon: UserOutlined
  },
  {
    key: 'settings',
    label: t('settings.systemSettings'),
    icon: SettingOutlined
  },
  {
    key: 'subscriptions',
    label: t('settings.subscriptions'),
    icon: ClockCircleOutlined
  }
])

// 当前激活的菜单
const activeMenu = ref(props.initialMenu)

// 语言设置 - 从store获取并双向绑定
const language = computed({
  get: () => store.getters['i18n/currentLocale'],
  set: value => {
    store.dispatch('i18n/setLocale', value)
  }
})
const notifications = ref({
  email: true,
  push: false
})

// 我的订阅数据
const subscriptions = ref([])
const subscriptionsLoading = ref(false)

// 格式化执行频率显示
const formatExecutionFrequency = subscription => {
  const {
    execution_frequency,
    execution_time,
    execution_weekday,
    execution_day
  } = subscription

  const time = execution_time || '09:00'
  const day = execution_day || '1'
  const weekday = execution_weekday || '一'

  switch (execution_frequency) {
    case 'daily':
      return `${t('settings.executionFrequency.daily')} ${time}`
    case 'weekly': {
      const weekdayText = t(`settings.executionFrequency.weekdays.${weekday}`, weekday)
      return `${t('settings.executionFrequency.weekly')}${weekdayText} ${time}`
    }
    case 'monthly':
      return `${t('settings.executionFrequency.monthly')}${day}号 ${time}`
    case 'hours': {
      const hours = subscription.execution_hours || 1
      return t('settings.executionFrequency.hours', { hours: hours })
    }
    default:
      return execution_frequency
  }
}

// 获取订阅列表
const fetchSubscriptions = async () => {
  try {
    subscriptionsLoading.value = true
    const response = await getUserSubscriptions()
    console.info('response: ', response)
    subscriptions.value = response.data.data.items || []
  } catch (error) {
    console.error('获取订阅列表失败:', error)
    // 这里可以添加错误提示
  } finally {
    subscriptionsLoading.value = false
  }
}

// 获取当前激活菜单的标题
const getActiveMenuTitle = () => {
  const activeItem = menuItems.value.find(item => item.key === activeMenu.value)
  return activeItem ? activeItem.label : ''
}

// 处理菜单点击
const handleMenuClick = ({ key }) => {
  activeMenu.value = key
}

// 处理遮罩层点击
const handleOverlayClick = () => {
  emit('close')
}

// 组件挂载时获取订阅数据
onMounted(() => {
  fetchSubscriptions()
})
</script>

<style lang="scss">
/* 主题相关CSS变量 - 使用全局作用域 */
:root {
  --modal-bg-primary: #fafafa;
  --modal-bg-secondary: #ffffff;
  --modal-text-primary: #262626;
  --modal-text-secondary: #595959;
  --modal-text-tertiary: #8c8c8c;
  --modal-border-color: #e8e8e8;
  --modal-border-light: #f0f0f0;
  --modal-hover-bg: #f5f5f5;
  --modal-primary-color: #1890ff;
  --modal-primary-hover-bg: #e6f7ff;
  --modal-success-bg: #f6ffed;
  --modal-success-color: #52c41a;
}

/* 深色主题下的变量覆盖 */
:root.dark {
  --modal-bg-primary: #2d2d2d;
  --modal-bg-secondary: #3d3d3d;
  --modal-text-primary: #ffffff;
  --modal-text-secondary: #cccccc;
  --modal-text-tertiary: #aaaaaa;
  --modal-border-color: #404040;
  --modal-border-light: #555555;
  --modal-hover-bg: #454545;
  --modal-primary-color: #40a9ff;
  --modal-primary-hover-bg: rgba(64, 169, 255, 0.1);
  --modal-success-bg: rgba(82, 196, 26, 0.1);
  --modal-success-color: #73d13d;
}
</style>

<style lang="scss" scoped>
.settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.settings-modal {
  display: flex;
  width: 900px;
  height: 600px;
  background: var(--modal-bg-secondary);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

/* 左侧边栏样式 */
.settings-sidebar {
  width: 200px;
  background: var(--modal-bg-primary);
  color: var(--modal-text-primary);
  padding: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--modal-border-color);
}

.sidebar-header {
  padding: 24px;
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  width: 24px;
  height: 26px;
  display: inline-block;
  margin-top: 5px;
}


.app-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--modal-text-primary);
}

.sidebar-menu {
  flex: 1;
  padding: 24px 0;
}

/* Ant Design 菜单样式覆盖 */
.desktop-menu {
  border: none;
  background: transparent;

  :deep(.ant-menu-item) {
    color: var(--modal-text-secondary);

    &.ant-menu-item-selected {
      color: var(--modal-primary-color);
      background-color: var(--modal-primary-hover-bg);
    }

    &:hover {
      color: var(--modal-primary-color);
      background-color: var(--modal-primary-hover-bg);
    }

    .anticon {
      color: inherit;
    }
  }
}

.mobile-menu {
  border: none;
  background: transparent;

  :deep(.ant-menu-item) {
    color: var(--modal-text-secondary);

    &.ant-menu-item-selected {
      color: var(--modal-primary-color);
      background-color: var(--modal-primary-hover-bg);
    }

    &:hover {
      color: var(--modal-primary-color);
      background-color: var(--modal-primary-hover-bg);
    }

    .anticon {
      color: inherit;
    }
  }
}

/* 右侧内容样式 */
.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--modal-bg-primary);
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  border-bottom: 1px solid var(--modal-border-color);
}

.content-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--modal-text-primary);
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--modal-hover-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--modal-text-primary);

  &:hover {
    background: var(--modal-primary-hover-bg);
    color: var(--modal-primary-color);
  }
}

.content-body {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
}

.content-section {
  h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--modal-text-primary);
  }
}

/* 订阅页面头部 */
.subscriptions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;

  h3 {
    margin: 0;
  }
}

.subscriptions-actions {
  display: flex;
  gap: 8px;
}

.refresh-btn {
  padding: 8px 16px;
  background: var(--modal-primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    background: var(--modal-primary-hover-bg);
    color: var(--modal-primary-color);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--modal-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--modal-border-color);
  border-top: 3px solid var(--modal-primary-color);
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

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--modal-text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state p {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--modal-text-primary);
}

.empty-desc {
  font-size: 14px;
  color: var(--modal-text-tertiary);
}

/* 我的订阅表格样式 */
.table-wrap {
  background: var(--modal-bg-secondary);
  border-radius: 8px;
  overflow: hidden;
}

.subs-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.subs-table th:nth-child(1),
.subs-table td:nth-child(1) {
  width: 120px;
}

.subs-table th:nth-child(2),
.subs-table td:nth-child(2) {
  width: 120px;
}

.subs-table th:nth-child(3),
.subs-table td:nth-child(3) {
  width: 120px;
}

.subs-table th:nth-child(4),
.subs-table td:nth-child(4) {
  width: auto;
}

.subs-table th,
.subs-table td {
  padding: 12px 14px;
  background: var(--modal-bg-primary);
  text-align: left;
  font-size: 13px;
  color: var(--modal-text-primary);
  border-bottom: 1px solid var(--modal-border-light);
}

.subs-table thead th {
  background: var(--modal-bg-primary);
  border-bottom: 1px solid var(--modal-border-light);
  color: var(--modal-text-secondary);
  font-weight: 600;
}

.subs-table tbody tr {
  background: var(--modal-bg-primary);
}

.subs-table tbody tr:hover {
  background: var(--modal-hover-bg);
}

.subs-table .desc {
  color: var(--modal-text-secondary);
}

/* 订阅表格特定样式 */
.subscription-name {
  font-weight: 500;
  color: var(--modal-text-primary);
}

.subscription-type {
  .type-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;

    &.type-report {
      background: var(--modal-success-bg);
      color: var(--modal-success-color);
    }

    &.type-alert {
      background: rgba(255, 193, 7, 0.1);
      color: #fa8c16;
    }

    &.type-analysis {
      background: rgba(24, 144, 255, 0.1);
      color: var(--modal-primary-color);
    }
  }
}

.execution-frequency {
  color: var(--modal-text-secondary);
  font-size: 13px;
}

.assistant-id {
  font-family: monospace;
  font-size: 12px;
  color: var(--modal-text-tertiary);
}

/* 账户信息样式 */
.account-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--modal-bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--modal-border-light);

  label {
    font-weight: 500;
    color: var(--modal-text-secondary);
  }

  span {
    color: var(--modal-text-primary);
  }
}

/* 设置表单样式 */
.settings-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-weight: 500;
    color: var(--modal-text-secondary);
    font-size: 14px;
  }
}

.form-select {
  padding: 10px 12px;
  border: 1px solid var(--modal-border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--modal-bg-secondary);
  color: var(--modal-text-primary);
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: var(--modal-primary-color);
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
}

/* 主题选择器样式 */
.theme-selector {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  border: 2px solid var(--modal-border-color);
  border-radius: 8px;
  background: var(--modal-bg-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 80px;
  position: relative;

  &:hover {
    border-color: var(--modal-primary-color);
    background: var(--modal-primary-hover-bg);
  }

  &.active {
    border-color: var(--modal-primary-color);
    background: var(--modal-primary-hover-bg);

    .theme-icon {
      color: var(--modal-primary-color);
    }

    .theme-label {
      color: var(--modal-primary-color);
      font-weight: 600;
    }
  }
}

.theme-icon {
  font-size: 24px;
  color: var(--modal-text-secondary);
  margin-bottom: 8px;
  transition: color 0.3s ease;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 自定义主题图标 */
.theme-icon-sun::before {
  content: '☀️';
  font-size: 20px;
}

.theme-icon-moon::before {
  content: '🌙';
  font-size: 20px;
}

.theme-icon-auto::before {
  content: '🖥️';
  font-size: 18px;
}

.theme-label {
  font-size: 12px;
  color: var(--modal-text-secondary);
  text-align: center;
  transition: color 0.3s ease;
}

.theme-check {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 16px;
  height: 16px;
  background: var(--modal-primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;

  input[type='checkbox'] {
    width: 16px;
    height: 16px;
    accent-color: var(--modal-primary-color);
    background: var(--modal-bg-secondary);
    border: 1px solid var(--modal-border-color);
  }

  span {
    color: var(--modal-text-primary);
    font-size: 14px;
  }
}

/* 移动端标签页样式 */
.mobile-tabs {
  margin-bottom: 20px;

  :deep(.ant-tabs-nav) {
    margin-bottom: 16px;
  }

  :deep(.ant-tabs-tab) {
    padding: 8px 16px;
    margin: 0 4px;
    color: var(--modal-text-secondary);

    &:hover {
      color: var(--modal-primary-color);
    }

    &.ant-tabs-tab-active {
      background: var(--modal-primary-hover-bg);
      border-color: var(--modal-primary-color);

      .ant-tabs-tab-btn {
        color: var(--modal-primary-color);
      }
    }
  }
}

.tab-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.tab-icon {
  font-size: 16px;
  color: inherit;
}

.tab-text {
  font-size: 12px;
  font-weight: 500;
  color: inherit;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-modal {
    width: 95vw;
    height: 90vh;
    flex-direction: column;
  }

  .settings-sidebar {
    width: 100%;
    height: auto;
  }

  .sidebar-header {
    padding: 20px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .sidebar-menu {
    padding: 16px 0;
  }

  .menu-item {
    margin: 2px 12px;
    padding: 12px 16px;
  }

  .content-header {
    padding: 15px 24px;
  }

  .content-body {
    padding: 24px;
  }
}
</style>
