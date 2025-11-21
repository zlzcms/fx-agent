/**
 * @Author: zhujinlong
 * @Date:   2025-08-05
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-08-05
 */

const state = {
  isMobile: false,
  screenWidth: 0,
  screenHeight: 0,
  // 默认主题模式：light - 浅色, dark - 深色, auto - 自动
  themeMode: 'light'
}

const getters = {
  isMobile: state => state.isMobile,
  screenWidth: state => state.screenWidth,
  screenHeight: state => state.screenHeight,
  isTablet: state => state.screenWidth >= 768 && state.screenWidth < 1024,
  isDesktop: state => state.screenWidth >= 1024,
  // 获取当前的主题模式
  themeMode: state => state.themeMode,
  // 判断是否为深色模式（考虑自动模式的情况）
  isDarkMode: state => {
    if (state.themeMode === 'auto') {
      // 检查用户系统偏好
      return (
        window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches
      )
    }
    return state.themeMode === 'dark'
  }
}

const actions = {
  initDeviceDetection({ commit }) {
    const updateDeviceInfo = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      const mobile = width < 768

      commit('setDeviceInfo', {
        isMobile: mobile,
        screenWidth: width,
        screenHeight: height
      })
    }

    // 初始化
    updateDeviceInfo()

    // 监听窗口大小变化
    window.addEventListener('resize', updateDeviceInfo)

    // 监听设备方向变化（移动端）
    if (window.orientation !== undefined) {
      window.addEventListener('orientationchange', updateDeviceInfo)
    }
  },

  // 初始化主题设置
  initTheme({ commit }) {
    // 从localStorage读取保存的主题设置
    const savedTheme = localStorage.getItem('themeMode')
    if (savedTheme) {
      commit('setThemeMode', savedTheme)
    } else {
      // 默认检查系统偏好
      const isDarkSystem =
        window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches
      commit('setThemeMode', isDarkSystem ? 'dark' : 'light')
    }
  },

  // 设置主题模式
  setThemeMode({ commit }, mode) {
    commit('setThemeMode', mode)
    // 保存到localStorage
    localStorage.setItem('themeMode', mode)
  }
}

const mutations = {
  setDeviceInfo(state, { isMobile, screenWidth, screenHeight }) {
    state.isMobile = isMobile
    state.screenWidth = screenWidth
    state.screenHeight = screenHeight
  },

  setThemeMode(state, mode) {
    state.themeMode = mode
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
