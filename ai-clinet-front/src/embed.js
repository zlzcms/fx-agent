;(function () {
  const defaultConfig = {
    // 用户认证令牌 (User authentication token)
    token: '',
    
    // API 基础 URL (API base URL)
    baseUrl: '',
    
    // iframe 完整地址 (Full iframe URL)
    // 可直接指定完整聊天页面地址；若不填则尝试用 baseUrl + token 推断
    iframeSrc: '',
    
    // 按钮位置 (Button position)
    // 可选值: 'right' | 'left'
    position: 'right',
    
    // 层级 (Z-index for layering)
    // 默认值接近最大值，确保浮窗在最上层显示
    zIndex: 2147483000,
    
    // 按钮颜色 (Button background color)
    // 支持任何有效的 CSS 颜色值 (HEX, RGB, RGBA 等)
    buttonColor: '#1C64F2',
    
    // 按钮尺寸 (Button size in pixels)
    // 圆形按钮的宽度和高度
    buttonSize: 56,
    
    // 按钮距离底部的距离 (Button distance from bottom in pixels)
    buttonBottom: 20,
    
    // 按钮距离侧边的距离 (Button distance from side in pixels)
    // 根据 position 值，距离左侧或右侧的距离
    buttonSide: 20,
    
    // 聊天面板宽度 (Chat panel width in pixels)
    // 仅在桌面端生效，移动端自动全屏
    panelWidth: 480,
    
    // 聊天面板高度 (Chat panel height in viewport height)
    // 使用 vh 单位，80 表示占据 80% 的视口高度
    panelHeightVh: 80,

    // locale: 'zh','en' 语言
    locale: 'zh',
  }

  const cfg = Object.assign(
    {},
    defaultConfig,
    window.AiassistantChatbotConfig || {}
  )

  function computeIframeSrc() {
    const assistCfg = window.AiassistantChatbotConfig
    if (assistCfg.baseUrl && assistCfg.token) {
      // 这里是通用推断，若你的服务实际路径不同，请直接配置 iframeSrc
      return (
        assistCfg.baseUrl.replace(/\/+$/, '') +
        '/embed/chat?channel=embed&token=' +
        encodeURIComponent(assistCfg.token) +
        '&locale=' +
        encodeURIComponent(assistCfg.locale)+
        '&channel=' +
        encodeURIComponent(assistCfg.id)
      )
    }
    console.warn(
      '[ChatbotWidget] 未配置 iframeSrc，且无法根据 baseUrl + token 推断。'
    )
    return 'about:blank'
  }

  // 样式
  const style = document.createElement('style')
  style.textContent = `
    .cbw-hide { display: none !important; }
    .cbw-fixed { position: fixed; z-index: 99999 }
    .cbw-button {
      border-radius: 50%;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform .15s ease, box-shadow .15s ease;
      user-select: none;
    }
    .cbw-button:active { transform: scale(0.98); }
    .cbw-panel {
      width: ${cfg.panelWidth}px;
      max-width: calc(100vw - 24px);
      height: ${cfg.panelHeightVh}vh;
      max-height: 90vh;
      background: #fff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 16px 48px rgba(0,0,0,0.22);
      display: flex;
      flex-direction: column;
    }
    .cbw-header {
      height: 44px;
      background: #0b1220;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      font-size: 14px;
    }
    .cbw-close {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #fff;
    }
    .cbw-close:hover {
      background: rgba(255,255,255,0.12);
    }
    .cbw-iframe {
      border: 0;
      width: 100%;
      height: calc(100% - 44px);
      background: #fff;
    }
    .cbw-wrap {
      inset: 0;
      pointer-events: none; /* 只有面板和按钮能点 */
    }
    .cbw-panel, .cbw-button { pointer-events: auto; }

    /* 移动端：面板全屏化体验更好 */
    @media (max-width: 768px) {
      .cbw-panel {
        width: 100vw;
        height: 80vh;
        border-radius: 12px;
      }
    }
  `
  document.head.appendChild(style)

  // 根容器（占位，便于管理 zIndex）
  const root = document.createElement('div')
  root.className = 'cbw-fixed cbw-wrap'
  root.style.zIndex = String(cfg.zIndex)
  document.body.appendChild(root)

  // 悬浮按钮
  const button = document.createElement('div')
  button.id = 'custom-chatbot-bubble-button'
  button.className = 'cbw-fixed cbw-button'
  button.style.bottom = cfg.buttonBottom + 'px'
  if (cfg.position === 'left') {
    button.style.left = cfg.buttonSide + 'px'
  } else {
    button.style.right = cfg.buttonSide + 'px'
  }
  // 构建 logo 图片路径
  const logoUrl = cfg.baseUrl 
    ? cfg.baseUrl.replace(/\/+$/, '') + '/logo.png'
    : './logo.png'
  
  button.innerHTML = `
    <img src="${logoUrl}" alt="Chat" width="56" height="56" style="object-fit: contain;" />
  `
  document.body.appendChild(button)

  // 面板容器（默认隐藏）
  const panelHost = document.createElement('div')
  panelHost.className = 'cbw-fixed cbw-hide'
  panelHost.style.bottom = cfg.buttonBottom + cfg.buttonSize + 12 + 'px'
  if (cfg.position === 'left') {
    panelHost.style.left = cfg.buttonSide + 'px'
  } else {
    panelHost.style.right = cfg.buttonSide + 'px'
  }
  document.body.appendChild(panelHost)

  // 面板（懒创建，首次打开再加载 iframe）
  let panel = null
  let iframe = null
  let isOpen = false

  function createPanel() {
    if (panel) return
    panel = document.createElement('div')
    panel.className = 'cbw-panel'

    const header = document.createElement('div')
    header.className = 'cbw-header'
    header.innerHTML = `
      <div>Chat</div>
      <div class="cbw-close" aria-label="Close">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
    `

    iframe = document.createElement('iframe')
    iframe.className = 'cbw-iframe'
    iframe.allow = 'clipboard-write; microphone;'
    iframe.referrerPolicy = 'no-referrer'
    iframe.src = computeIframeSrc()

    header.querySelector('.cbw-close').addEventListener('click', close)
    panel.appendChild(header)
    panel.appendChild(iframe)
    panelHost.appendChild(panel)
  }

  function open() {
    if (isOpen) return
    createPanel()
    panelHost.classList.remove('cbw-hide')
    isOpen = true
  }

  function close() {
    if (!isOpen) return
    panelHost.classList.add('cbw-hide')
    isOpen = false
  }

  function toggle() {
    isOpen ? close() : open()
  }

  button.addEventListener('click', toggle)

  // 暴露 API
  window.ChatbotWidget = {
    open,
    close,
    toggle,
    isOpen: () => isOpen,
    setIframeSrc: src => {
      if (iframe) iframe.src = src
    }
  }
})()
