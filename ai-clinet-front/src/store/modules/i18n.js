/**
 * i18n store module for language management
 */

// 支持的语种列表
const SUPPORTED_LOCALES = ['zh', 'en']
const DEFAULT_LOCALE = 'zh'

// 验证 locale 是否有效
const validateLocale = (locale) => {
  return SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE
}

// 从 localStorage 安全获取 locale
const getLocaleFromStorage = () => {
  try {
    const storedLocale = localStorage.getItem('app_locale')
    return validateLocale(storedLocale)
  } catch (error) {
    console.warn('Failed to read locale from localStorage:', error)
    return DEFAULT_LOCALE
  }
}

const state = {
  locale: getLocaleFromStorage(),
  availableLocales: [
    { code: 'zh', name: '中文' },
    { code: 'en', name: 'English' }
  ]
}

const mutations = {
  SET_LOCALE(state, locale) {
    const validatedLocale = validateLocale(locale)
    state.locale = validatedLocale
    try {
      localStorage.setItem('app_locale', validatedLocale)
    } catch (error) {
      console.warn('Failed to save locale to localStorage:', error)
    }
  }
}

const actions = {
  setLocale({ commit }, locale) {
    const validatedLocale = validateLocale(locale)
    commit('SET_LOCALE', validatedLocale)
    return validatedLocale
  }
}

const getters = {
  currentLocale: state => state.locale,
  availableLocales: state => state.availableLocales,
  isZh: state => state.locale === 'zh',
  isEn: state => state.locale === 'en',
  isValidLocale: state => (locale) => SUPPORTED_LOCALES.includes(locale)
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}