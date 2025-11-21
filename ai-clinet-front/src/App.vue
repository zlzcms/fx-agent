<script>
/**
 * @Author: zhujinlong
 * @Date:   2025-05-16 20:56:59
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-08-05
 */
import { onMounted, watch } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'App',
  setup() {
    const store = useStore()

    onMounted(() => {
      // 初始化设备检测
      store.dispatch('device/initDeviceDetection')
      // 初始化主题
      store.dispatch('device/initTheme')
    })

    // 监听主题变化并应用到DOM
    watch(
      () => store.getters['device/isDarkMode'],
      isDark => {
        if (isDark) {
          document.documentElement.classList.add('dark')
          document.documentElement.classList.remove('light')
        } else {
          document.documentElement.classList.add('light')
          document.documentElement.classList.remove('dark')
        }
      },
      { immediate: true }
    )
  }
}
</script>

<template>
  <router-view />
</template>

<style>
.slide-x-enter-active,
.slide-x-leave-active {
  transition: transform 0.4s cubic-bezier(0.55, 0, 0.1, 1);
  will-change: transform;
  position: absolute;
  width: 100%;
}
.slide-x-enter-from {
  transform: translateX(100%);
}
.slide-x-leave-to {
  transform: translateX(-100%);
}
.slide-x-enter-to,
.slide-x-leave-from {
  transform: translateX(0);
}
html,
body,
#app {
  height: 100%;
  overflow: hidden;
}
#app {
  position: relative;
  min-height: 100vh;
}
</style>
