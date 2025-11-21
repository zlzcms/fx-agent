/**
 * @Author: zhujinlong
 * @Date:   2025-05-16 21:01:26
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-05-20 09:28:09
 */
import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'
import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../pages/chart_assistant/index.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/login.vue')
  },
  {
    path: '/pdf-viewer',
    name: 'PdfViewer',
    component: () => import('../pages/PdfViewerPage.vue')
  },

  // 通配符路由 - 匹配所有未定义的路径
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const unauthenticatedRoutes = [
  '/login',
  '/pdf-viewer',
  '/step-demo',
  '/workspace-demo'
]
// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  // 1) Handle token from query and bootstrap session
  const urlToken = to.query && to.query.token
  if (urlToken) {

    try {
      // Persist token immediately
      store.commit('auth/setAuth', {
        token: urlToken,
        refreshToken: null,
        user: null
      })

      // Fetch user info with the fresh token
      const userResponse = await axios.get('/home/auth/me', {
        headers: { Authorization: `Bearer ${urlToken}` }
      })
      store.commit('auth/updateUser', userResponse.data)
      const channel = to.query.channel
      const locale = to.query.locale
      // 是否自动发送，默认自动发送
      const autoSend = to.query.autoSend === 'false' ? false : true
      store.commit('auth/setAutoSend', autoSend)
      if (locale) {
        // 验证并设置 locale，确保与 i18n 同步
        // store.dispatch 会返回验证后的 locale（在 actions 中已设置）
        console.info("set route locale: ", locale)
        const vLocale = locale.split('-')[0].split('_')[0]
        store.dispatch('i18n/setLocale', vLocale).then((validatedLocale) => {
          // 如果 locale 无效，会回退到默认值
          if (validatedLocale !== vLocale) {
            console.warn(`Invalid locale: ${vLocale}, using default: ${validatedLocale}`)
          }
        })
      }
      if(channel){
        // 如果有channelType,则存储store_channel
        store.commit('auth/setChannel', channel)
      }else{
        store.commit('auth/clearChannel')
      }

    } catch (e) {
      // If anything goes wrong, clear auth to keep state consistent
      store.commit('auth/clearAuth')
    } finally {
      // Always redirect to root as requested, removing token from URL
      const askContent = to.query && to.query.askContent
      return next({ path: '/', replace: true, query: { askContent: askContent } })
    }
  }

  // This is a simple implementation. In a real app, you would check
  // a token in localStorage/sessionStorage or use a proper auth system
  const isAuthenticated = localStorage.getItem('user')

  // If route is login and user is already authenticated
  if (to.path === '/login' && isAuthenticated) {
    next('/')
  }
  // If route requires auth and user is not authenticated
  else if (!unauthenticatedRoutes.includes(to.path) && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
