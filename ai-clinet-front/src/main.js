/**
 * @Author: zhujinlong
 * @Date:   2025-05-16 20:56:59
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-05-17 10:22:16
 */
import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import router from './router'
import './assets/styles/global.less'
// 导入Tailwind CSS
import './assets/styles/tailwind.css'
// 导入测试组件以触发 Tailwind 样式生成
// import TailwindTest from './components/TailwindTest.vue'
import { createI18n } from 'vue-i18n'
import zh from './assets/i18n/zh.js'
import en from './assets/i18n/en.js'
import './utils/requests'
// 判断是否为PC端
function isPC() {
  return (
    /Windows|Macintosh|Linux/i.test(navigator.userAgent) &&
    !/Mobile|Android|iPhone|iPad/i.test(navigator.userAgent)
  )
}

if (isPC()) {
  document.body.classList.add('pc')
} else {
  document.body.classList.add('mobile')
}

// 初始化主题类（避免首次加载时的闪烁）
const savedTheme = localStorage.getItem('themeMode')
if (
  savedTheme === 'dark' ||
  (!savedTheme &&
    window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches)
) {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.add('light')
}

const messages = {
  zh,
  en
}

// 支持的语种列表
const SUPPORTED_LOCALES = ['zh', 'en']
const DEFAULT_LOCALE = 'zh'

// 验证 locale 是否有效
const validateLocale = (locale) => {
  return SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE
}

// 从 localStorage 安全获取 locale
const getInitialLocale = () => {
  try {
    const storedLocale = localStorage.getItem('app_locale')
    return validateLocale(storedLocale)
  } catch (error) {
    console.warn('Failed to read locale from localStorage:', error)
    return DEFAULT_LOCALE
  }
}

const initialLocale = getInitialLocale()

const i18n = createI18n({
  locale: initialLocale,
  legacy: false,
  fallbackLocale: DEFAULT_LOCALE,
  messages,
  // 添加以下配置以关闭警告
  silentTranslationWarn: false, // 开启翻译缺失警告，便于开发调试
  silentFallbackWarn: true, // 关闭回退语言警告
  missingWarn: false, // 在生产环境关闭缺失翻译警告
  fallbackWarn: false // 在生产环境关闭回退警告
})

const app = createApp(App)
app.use(store)
app.use(router)
app.use(i18n)

// Sync locale between store and vue-i18n
// 确保 store 和 i18n 使用相同的初始 locale
if (store.state.i18n.locale !== initialLocale) {
  store.commit('i18n/SET_LOCALE', initialLocale)
}

// 监听 store 中的 locale 变化，同步到 vue-i18n
store.watch(
  (state) => state.i18n.locale,
  (newLocale) => {
    const validatedLocale = validateLocale(newLocale)
    if (i18n.global.locale.value !== validatedLocale) {
      i18n.global.locale.value = validatedLocale
    }
    // Update document title based on language
    try {
      const title = i18n.global.t('nav.appTitle')
      const titleElement = document.getElementById('app-title')
      if (titleElement) {
        titleElement.textContent = title
      }
      document.title = title
    } catch (error) {
      console.warn('Failed to update document title:', error)
    }
  },
  { immediate: true }
)

// 注意：vue-i18n 的 locale 应该通过 store 来修改，确保同步

const originalWarn = console.warn
console.warn = function (...args) {
  if (typeof args[0] === 'string' && args[0].includes('v-html')) {
    // 忽略包含 v-html 的警告
    return
  }
  // originalWarn.apply(console, args);
}

// 添加环境变量测试代码
console.log('当前环境:', import.meta.env.MODE)
console.log('API地址:', import.meta.env.VITE_API_HOST)
console.log('应用标题:', import.meta.env.VITE_APP_TITLE)

app.mount('#app')

// 移除首次加载的 Loading 效果
const appLoading = document.getElementById('app-loading')
if (appLoading) {
  // 添加淡出动画
  appLoading.classList.add('fade-out')
  
  // 等待动画完成后移除元素
  setTimeout(() => {
    appLoading.remove()
  }, 500)
}
