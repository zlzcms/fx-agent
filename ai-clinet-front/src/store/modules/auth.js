import axios from 'axios'

const state = {
  token: localStorage.getItem('access_token') || null,
  refreshToken: localStorage.getItem('refresh_token') || null,
  user: JSON.parse(localStorage.getItem('user')) || null,
  channel:  null,
  autoSend:  true
}

const getters = {
  isAuthenticated: state => !!state.token,
  currentUser: state => state.user,
  channel: state => state.channel,
  autoSend: state => state.autoSend
}

const actions = {
  async register({ commit }, credentials) {
    try {
      console.log('发送注册请求：', credentials)
      const response = await axios.post('/home/auth/register', credentials)
      console.log('注册响应：', response.data)
      return true
    } catch (error) {
      console.error('注册错误：', error.response?.data || error.message)
      throw error
    }
  },

  async login({ commit }, credentials) {
    try {
      // 创建表单数据格式，OAuth2需要
      const formData = {
        username: credentials.username,
        password: credentials.password
      }

      console.log('发送登录请求：', { username: credentials.username })
      const response = await axios.post('/home/auth/login', formData)
      console.log('登录响应：', response.data)

      const { access_token, refresh_token, user } = response.data.data
      console.log('access_token', access_token)
      // 保存Token，而不立即获取用户信息
      await commit('setAuth', {
        token: access_token,
        refreshToken: refresh_token,
        user: user // 先设置为null
      })

      // 等待一小段时间，确保Token生效
      await new Promise(resolve => setTimeout(resolve, 1000))

      try {
        console.log('获取用户信息：', access_token + '...')
        // 获取用户信息
        const userResponse = await axios.get('/home/auth/me', {
          headers: { Authorization: `Bearer ${access_token}` }
        })
        console.log('用户信息响应：', userResponse.data)

        // 更新用户信息
        commit('updateUser', userResponse.data)
      } catch (userError) {
        console.error(
          '获取用户信息失败：',
          userError.response?.data || userError.message
        )
        // 即使获取用户信息失败，也不影响登录状态
      }

      return true
    } catch (error) {
      console.error('登录错误：', error.response?.data || error.message)
      throw error
    }
  },

  async refreshToken({ commit, state }) {
    try {
      console.log('刷新Token：', state.refreshToken?.substring(0, 15) + '...')
      const response = await axios.post('/home/auth/refresh-token', {
        refresh_token: state.refreshToken
      })
      console.log('刷新Token响应：', response.data)

      const { access_token, refresh_token, access_token_expire_time } = response.data.data
      commit('updateTokens', {
        token: access_token,
        refreshToken: refresh_token
      })
      return true
    } catch (error) {
      console.error('刷新Token错误：', error.response?.data || error.message)
      commit('clearAuth')
      throw error
    }
  },

  async logout({ commit }) {
    console.log('用户登出')
    axios.post('/home/auth/logout')
    commit('clearAuth')
    return true
  }
}

const mutations = {
  setAuth(state, { token, refreshToken, user }) {
    state.token = token
    state.refreshToken = refreshToken
    state.user = user

    localStorage.setItem('access_token', token)
    localStorage.setItem('refresh_token', refreshToken)
    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    }
  },

  updateUser(state, user) {
    state.user = user
    localStorage.setItem('user', JSON.stringify(user))
  },

  updateTokens(state, { token, refreshToken }) {
    state.token = token
    state.refreshToken = refreshToken

    localStorage.setItem('access_token', token)
    localStorage.setItem('refresh_token', refreshToken)
  },

  clearAuth(state) {
    state.token = null
    state.refreshToken = null
    state.user = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },

  setChannel(state, channel) {
    state.channel = channel
  },
  clearChannel(state) {
    state.channel = null
  },
  setAutoSend(state, autoSend) {
    state.autoSend = autoSend

  },

}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
