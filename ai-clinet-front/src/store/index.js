/**
 * @Author: zhujinlong
 * @Date:   2025-05-16 21:02:40
 * @Last Modified by:   zhujinbin
 * @Last Modified time: 2025-08-05
 */
import { createStore } from 'vuex'
import auth from './modules/auth'
import chat from './modules/chat'
import device from './modules/device'
import i18n from './modules/i18n'

export default createStore({
  modules: {
    auth,
    chat,
    device,
    i18n
  }
})
