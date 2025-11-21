import axios from 'axios'
import store from '@/store'
import router from '@/router'

// 设置API基础URL
// axios.defaults.baseURL = 'http://47.239.101.153:8000/api/v1';
const host = import.meta.env.VITE_API_HOST
console.log('host:', host)
axios.defaults.baseURL = `${host}/api/v1`

// 请求拦截器，添加认证令牌
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')

    // 添加调试日志，查看每个请求是否包含token
    console.log(`[请求] ${config.method.toUpperCase()} ${config.url}`)
    console.log(`[认证] Token存在: ${!!token}`)

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log(
        `[认证头] ${config.headers.Authorization.substring(0, 15)}...`
      )
    } else {
      console.warn(`[警告] 请求未携带认证令牌: ${config.url}`)
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器，处理令牌过期
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

axios.interceptors.response.use(
  response => {
    // 记录成功的响应
    console.log(
      `[响应成功] ${response.config.method.toUpperCase()} ${response.config.url}: ${response.status}`
    )
    return response
  },
  async error => {
    // 记录错误的响应
    console.error(
      `[响应错误] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${error.response?.status}`,
      error.response?.data
    )

    const originalRequest = error.config

    // 如果是 refresh-token 接口本身返回 401，直接跳转登录页
    if (
      error.response &&
      error.response.status === 401 &&
      originalRequest.url &&
      originalRequest.url.includes('/home/auth/refresh-token')
    ) {
      console.log('[令牌刷新] refresh-token接口返回401，直接跳转登录页')
      isRefreshing = false // 重置刷新状态
      processQueue(error) // 清空失败队列
      store.commit('auth/clearAuth')
      router.push('/login')
      return Promise.reject(error)
    }

    // 如果收到401响应且错误消息包含"已过期"，尝试刷新令牌
    if (
      error.response &&
      error.response.status === 401 &&
      error.response.data &&
      error.response.data.msg &&
      error.response.data.msg.includes('已过期') &&
      !originalRequest._retry
    ) {
      console.log('[令牌过期] 尝试刷新令牌')

      if (isRefreshing) {
        console.log('[令牌刷新] 已有刷新操作进行中，将请求加入队列')
        if(error.config.url.includes('/home/auth/refresh-token')) {
          store.commit('auth/clearAuth')
          router.push('/login')
          return Promise.reject(error)
        }
        // 如果当前正在刷新令牌，将请求添加到队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
            return axios(originalRequest)
          })
          .catch(err => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // 尝试使用刷新令牌获取新的访问令牌
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          console.error('[令牌刷新] 刷新令牌不存在')
          throw new Error('No refresh token available')
        }

        console.log('[令牌刷新] 发送刷新请求')
        const response = await axios.post('/home/auth/refresh-token', {
          refresh_token: refreshToken
        })

        console.log('[令牌刷新] 刷新成功', response.data)
        
        // 检查响应格式
        if (!response.data || !response.data.data) {
          console.error('[令牌刷新] 响应格式错误', response.data)
          throw new Error('刷新Token响应格式错误')
        }
        
        const { access_token, refresh_token } = response.data.data
        
        // 检查必要字段
        if (!access_token || !refresh_token) {
          console.error('[令牌刷新] 响应缺少必要字段', response.data.data)
          throw new Error('刷新Token响应缺少必要字段')
        }

        // 更新存储的令牌
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        store.commit('auth/updateTokens', {
          token: access_token,
          refreshToken: refresh_token
        })

        // 更新当前请求的Authorization头
        axios.defaults.headers.common['Authorization'] =
          `Bearer ${access_token}`
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`

        // 处理队列中的请求
        processQueue(null, access_token)

        // 重试原始请求
        console.log(
          `[令牌刷新] 重试原始请求: ${originalRequest.method.toUpperCase()} ${originalRequest.url}`
        )
        return axios(originalRequest)
      } catch (refreshError) {
        // 如果刷新令牌失败，处理队列并登出
        console.error('[令牌刷新] 刷新失败', refreshError)
        processQueue(refreshError)
        store.commit('auth/clearAuth')
        router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 对于其他401错误，登出并重定向到登录页面
    if (error.response && error.response.status === 401) {
      console.log('[认证失败] 401错误，执行登出')
      store.commit('auth/clearAuth')
      router.push('/login')
    }

    return Promise.reject(error)
  }
)
