<template>
  <div class="login-container">
    <!-- 语言切换按钮 -->
    <div class="language-switch">
      <Dropdown :trigger="['click']" :placement="'bottomRight'">
        <Button type="text" class="language-btn">
          <GlobalOutlined />
        </Button>
        <template #overlay>
          <Menu @click="handleLanguageChange">
            <Menu.Item key="zh" :class="{ 'selected': locale === 'zh' }">
              中文
            </Menu.Item>
            <Menu.Item key="en" :class="{ 'selected': locale === 'en' }">
              English
            </Menu.Item>
          </Menu>
        </template>
      </Dropdown>
    </div>
    
    <div class="login-box">
      <!-- Welcome message -->
      <div class="welcome-section">
        <h2 class="welcome-title">{{ $t('login.welcome') }}</h2>
      </div>

      <!-- Form inputs -->
      <div class="form-section">
        <Form :model="loginForm" :rules="loginRules" ref="loginFormRef">
          <div class="form-content">
            <FormItem prop="username">
              <div class="field-label">
                <UserOutlined class="field-icon" />
                <span class="field-text">{{ $t('login.account') }}</span>
              </div>
              <Input
                v-model:value="loginForm.username"
                :placeholder="$t('login.usernamePlaceholder')"
                size="large"
                class="custom-input"
              />
            </FormItem>

            <FormItem prop="password">
              <div class="field-label">
                <LockOutlined class="field-icon" />
                <span class="field-text">{{ $t('login.password') }}</span>
                <a href="#" tabindex="-1" class="forgot-password">{{ $t('login.forgotPassword') }}</a>
              </div>
              <InputPassword
                v-model:value="loginForm.password"
                :placeholder="$t('login.passwordPlaceholder')"
                size="large"
                class="custom-input"
              />
            </FormItem>

            <FormItem prop="verification">
              <!-- Custom verification slider to solve visibility issues -->
              <div
                class="verification-container"
                :class="{ 'is-verified': isVerified }"
              >
                <!-- Track background -->
                <div class="verification-track">
                  <!-- Progress bar -->
                  <div
                    class="verification-bar"
                    :style="{ width: `${loginForm.verification}%` }"
                  >
                  
                </div>

                  <!-- Slider button - adjusted position calculation -->
                  <div
                    class="verification-button"
                    :style="{
                      left: `calc(${loginForm.verification}% - ${loginForm.verification >= 95 ? BUTTON_WIDTH + 'px' : '0px'})`
                    }"
                    @mousedown="startDrag"
                    @touchstart.prevent="startTouch"
                    :class="{ 'is-verified': isVerified }"
                  >
                    <template v-if="!isVerified">
                      <RightOutlined class="slider-icon" />
                    </template>
                    <template v-else>
                      <CheckOutlined class="slider-icon" />
                    </template>
                  </div>

                  <!-- Text overlay -->
                  <span class="verification-text" v-if="!isVerified">
                    {{ $t('login.sliderText') }}
                  </span>
                  <span class="verification-success" v-else>
                    <span style="color: #fff">{{ $t('login.verificationSuccess') }}</span>
                    <CheckOutlined /> 
                  </span>
                </div>
              </div>
            </FormItem>
          </div>
        </Form>
      </div>

      <!-- Login button -->
      <div class="button-section">
        <Button
          class="login-button primary-login"
          @click="handleLogin"
          :loading="loading"
          :disabled="!isVerified"
        >
          {{ $t('login.login') }}
        </Button>
        <Divider class="custom-divider">
          <span class="divider-text">{{ $t('login.dividerText') }}</span>
        </Divider>
        <Button
          class="login-button crm-login"
          @click="handleCrmLogin"
          :disabled="!isVerified"
        >
          <UserOutlined class="crm-icon" />
          {{ $t('login.crmLogin') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import type { FormInstance  } from 'ant-design-vue'
import type { RuleObject } from 'ant-design-vue/es/form/interface'
import {
  UserOutlined,
  LockOutlined,
  CheckOutlined,
  RightOutlined,
  GlobalOutlined
} from '@ant-design/icons-vue'
import { Button, Form, FormItem, Input, InputPassword, message, Divider, Dropdown, Menu } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
// 使用 store 中的设备检测
import { useStore } from 'vuex'

// removed dynamic inline styles for plain centered layout
// Use i18n
const { t, locale } = useI18n()
const router = useRouter()

// 语言切换功能 - 通过 store 保存到本地
const handleLanguageChange = ({ key }) => {
  // 通过 store 设置 locale，会自动保存到 localStorage
  store.dispatch('i18n/setLocale', key)
  // locale.value 会通过 store 的 watch 自动同步
}
const loginFormRef = ref<FormInstance | null>(null)
const loading = ref(false)
const isVerified = ref(false)
const isDragging = ref(false)
const isAnimating = ref(false)
const BUTTON_WIDTH = 38 // Button width in pixels
// Touch state
const isTouching = ref(false)




const store = useStore()

// Form data
const loginForm = reactive({
  username: '',
  password: '',
  verification: 0
})

// Form validation rules with i18n
const loginRules = reactive<Record<string, RuleObject[]>>({
  username: [
    {
      type: 'string',
      required: true,
      message: t('login.validation.usernameRequired'),
      trigger: 'blur'
    },
    {
      type: 'string',
      min: 3,
      max: 20,
      message: t('login.validation.usernameLength'),
      trigger: 'blur'
    }
  ],
  password: [
    {
      type: 'string',
      required: true,
      message: t('login.validation.passwordRequired'),
      trigger: 'blur'
    },
    { type: 'string', min: 6, message: t('login.validation.passwordLength'), trigger: 'blur' }
  ]
})

// Custom slider drag functionality
const startDrag = e => {
  if (isVerified.value || isAnimating.value) return

  isDragging.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)

  // Prevent default to stop text selection
  e.preventDefault()
}

const onDrag = e => {
  if (!isDragging.value || isVerified.value || isAnimating.value) return

  // Get track element and calculate position
  const track = document.querySelector('.verification-track')
  if (!track) return

  const trackRect = track.getBoundingClientRect()
  const trackWidth = trackRect.width
  const buttonWidth = BUTTON_WIDTH
  const offsetX = e.clientX - trackRect.left

  // Calculate percentage (clamped between 0 and 100)
  // Account for button width in the calculation
  const maxOffset = trackWidth - buttonWidth
  let percentage = Math.min(Math.max((offsetX / maxOffset) * 100, 0), 100)

  // Update verification value
  loginForm.verification = percentage

  // Check if verification is complete
  if (percentage >= 95) {
    loginForm.verification = 100
    isVerified.value = true
    message.success(t('login.verificationSuccess'))
    stopDrag()
  }
}

const stopDrag = () => {
  if (isDragging.value && !isVerified.value && !isAnimating.value) {
    animateSliderBack()
  }

  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// Touch support
const startTouch = (e) => {
  if (isVerified.value || isAnimating.value) return
  isTouching.value = true
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', stopTouch)
}

const onTouchMove = (e) => {
  if (!isTouching.value || isVerified.value || isAnimating.value) return
  const touch = e.touches && e.touches[0]
  if (!touch) return

  const track = document.querySelector('.verification-track')
  if (!track) return

  const trackRect = track.getBoundingClientRect()
  const trackWidth = trackRect.width
  const buttonWidth = BUTTON_WIDTH
  const offsetX = touch.clientX - trackRect.left

  const maxOffset = trackWidth - buttonWidth
  let percentage = Math.min(Math.max((offsetX / maxOffset) * 100, 0), 100)

  loginForm.verification = percentage

  if (percentage >= 95) {
    loginForm.verification = 100
    isVerified.value = true
    message.success(t('login.verificationSuccess'))
    stopTouch()
  }

  // prevent page scroll while sliding
  e.preventDefault()
}

const stopTouch = () => {
  if (isTouching.value && !isVerified.value && !isAnimating.value) {
    animateSliderBack()
  }
  isTouching.value = false
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', stopTouch)
}

// Clean up event listeners
onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', stopTouch)
})

// Slow animation for spring-back
const animateSliderBack = () => {
  isAnimating.value = true
  const startValue = loginForm.verification
  const steps = 20 // More steps = slower animation
  const stepSize = startValue / steps
  const interval = 15 // milliseconds between steps

  let currentStep = 0

  const animate = () => {
    currentStep++
    if (currentStep <= steps) {
      loginForm.verification = startValue - stepSize * currentStep
      setTimeout(animate, interval)
    } else {
      loginForm.verification = 0
      isAnimating.value = false
    }
  }

  animate()
}

// Handle login submission
const handleCrmLogin = () => {
  message.info("敬请期待...")
}

const handleLogin = () => {
  if (!isVerified.value) {
    message.warning(t('login.pleaseVerify'))
    return
  }

  (loginFormRef.value as FormInstance | null)
    ?.validate()
    .then(async () => {
      loading.value = true

      try {
        // Use store action for login
        await store.dispatch('auth/login', {
          username: loginForm.username,
          password: loginForm.password
        })

        message.success(t('login.loginSuccess'))
        console.info('go to home page')
        router.push('/')
      } catch (error) {
        console.error('Login error:', error)
        message.error(error.response?.data?.message || t('login.loginFailed'))
      } finally {
        loading.value = false
      }
    })
    .catch(() => {
      return false
    })
}
</script>

<style scoped lang="less">
// Remove global style overrides and work with existing styles

.login-container {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background-color: #ffffff;
  z-index: 10;
  overflow: auto;
  padding-top: 30px;
}

/* 语言切换按钮 */
.language-switch {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 20;
}

.language-btn {
  border: none;
  background: transparent;
  font-size: 18px;
  color: #666;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  width: 34px;
}

.language-btn:hover {
  background-color: #f5f5f5;
  color: #1890ff;
}

.language-btn:focus {
  background-color: #f5f5f5;
  color: #1890ff;
}

/* 语言选择下拉菜单样式 */
:deep(.ant-dropdown-menu) {
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #f0f0f0;
}

:deep(.ant-dropdown-menu-item) {
  padding: 8px 16px;
  font-size: 14px;
  transition: all 0.3s ease;
}

:deep(.ant-dropdown-menu-item:hover) {
  background-color: #f5f5f5;
}

:deep(.ant-dropdown-menu-item.selected) {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 500;
}

:deep(.ant-dropdown-menu-item.selected::after) {
  content: '✓';
  float: right;
  color: #1890ff;
  font-weight: bold;
}
.login-box {
  width: 380px;
  padding: 24px 20px;
  background-color: #ffffff;
  border-radius: 0;
  box-shadow: none;
  position: relative;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-top: 40px;

  .welcome-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 24px 0;
    color: #333;
  }
}

.form-section {

  .form-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
  }

  :deep(.ant-form-item) {
    margin-bottom: 24px;
    width: 100%;
  }

  /* 字段标签样式 */
  .field-label {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    position: relative;
  }

  .field-icon {
    font-size: 16px;
    color: #999;
    margin-right: 8px;
  }

  .field-text {
    font-size: 14px;
    color: #333;
    font-weight: 500;
  }

  .forgot-password {
    position: absolute;
    right: 0;
    font-size: 14px;
    color: #1890ff;
    text-decoration: none;
  }

  .forgot-password:hover {
    color: #40a9ff;
  }

  :deep(.ant-input-affix-wrapper) {
    padding: 8px 12px;
    margin-bottom: 16px;
    height: 40px;
    box-sizing: border-box;
  }

  :deep(.ant-input) {
    line-height: 24px;
  }

  .custom-input {
    border-radius: 4px;
    border: 1px solid #d9d9d9;
  }

  .custom-input:focus {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }

  /* Verification slider */
  .verification-container {
    position: relative;
    width: 100%;
    box-sizing: border-box;
    transition: all 0.3s ease;
    margin-top: 10px;

    &.is-verified {
      .verification-track { background-color: #f6ffed; }
      .verification-bar { background-color: #52c41a; }
      .verification-button { background-color: #52c41a; border-color: #52c41a; color: white; }
    }

    .verification-track {
      position: relative;
      width: 100%;
      height: 40px;
      background-color: #f0f0f0;
      border-radius: 4px;
      overflow: hidden;
    }

    .verification-bar {
      position: absolute;
      height: 40px;
      left: 0;
      top: 0;
      background-color: #52c41a;
      border-right: 1px solid #52c41a;
    }

    .verification-button {
      position: absolute;
      width: 38px;
      height: 36px;
      top: 2px;
      background-color: #fff;
      border: 1px solid #d9d9d9;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
      border-radius: 2px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      user-select: none;
      z-index: 10;

      &.is-verified {
        background-color: #52c41a;
        border-color: #52c41a;

        .slider-icon {
          color: white;
        }
      }
    }

    .slider-icon {
      font-size: 18px;
      color: #666666;
    }

    .verification-text {
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      color: #8c8c8c;
      font-size: 14px;
      pointer-events: none;
      z-index: 5;
      width: 100%;
      text-align: center;
    }

    .verification-success {
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      color: #52c41a;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      pointer-events: none;
      z-index: 5;
      width: 100%;
    }
  }
}

.button-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  padding: 15px 0;
  
  .login-button {
    width: 100%;
    height: 40px;
    padding: 0;
    font-size: 16px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .primary-login {
    background-color: #1890ff;
    border-color: #1890ff;
    color: white;
  }

  .primary-login:hover {
    background-color: #40a9ff;
    border-color: #40a9ff;
  }

  .crm-login {
    background-color: white;
    border: 1px solid #d9d9d9;
    color: #333;
    font-weight: 600;
  }

  .crm-login:hover {
    border-color: #1890ff;
    color: #1890ff;
  }

  .crm-icon {
    margin-right: 8px;
    font-size: 16px;
    font-weight: 600;
    color: inherit;
  }

  .custom-divider {
    margin: 16px 0;
    color: #999;
  }

  .divider-text {
    font-size: 14px;
    color: #999;
    background: white;
    padding: 0 16px;
  }
}
</style>

<style>
/* Override global styles for login page */
body:has(.login-container) #app {
  width: 100% !important;
  margin: 0 !important;
  max-width: none !important;
  padding: 0 !important;
}
</style>
