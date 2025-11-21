export default {
  // 通用
  common: {
    confirm: '确认',
    cancel: '取消',
    close: '关闭',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    loading: '加载中...',
    search: '搜索',
    clear: '清除',
    submit: '提交',
    reset: '重置',
    back: '返回',
    next: '下一步',
    previous: '上一步',
    finish: '完成',
    ok: '确定',
    yes: '是',
    no: '否',
    refresh: '刷新',
    
  },

  // 登录页面
  login: {
    welcome: '欢迎登录',
    account: '账户',
    password: '密码',
    usernamePlaceholder: '请输入注册账户',
    passwordPlaceholder: '请输入密码',
    forgotPassword: '忘记密码',
    sliderText: '请按住滑块，拖动到最右边',
    verificationSuccess: '验证通过',
    pleaseVerify: '请先完成验证',
    login: '登录',
    crmLogin: 'CRM账户登录',
    dividerText: '或通过以下方式登录',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',
    validation: {
      usernameRequired: '请输入用户名',
      usernameLength: '用户名长度应为3-20个字符',
      passwordRequired: '请输入密码',
      passwordLength: '密码至少6个字符'
    }
  },

  // 聊天助理
  chat: {
    newConversation: '新建对话',
    allChats: '全部',
    assistantReports: '助理报告',
    allAssistants: '所有助理',
    noReports: '暂无匹配的助理报告',
    aiGeneratedContent: 'AI总结生成，请甄别',
    assistantThinking: '助理正在思考...',
    attachments: '附件',
    uploadFiles: '上传文件',
    uploadDescription: '点击或拖拽文件到此区域上传',
    dropFile: '将文件拖拽到此处',
    placeholder: '请发送消息提问',
    report: "报告",
    web: "网页",
    welcome: {
      title: "欢迎，我是您的AI助手",
      description: "我将利用人工智能技术帮助您解决工作中的各种问题。"
    },
    modes: {
      auto: '自动',
      agent: '代理',
      chat: '聊天'
    }
  },

  // 导航和菜单
  nav: {
    dock: '停靠',
    mySubscriptions: '我的订阅',
    settings: '设置',
    logout: '退出登录',
    appName: 'AI助手',
    appTitle: 'AI助手'
  },

  // 退出确认弹窗
  logoutConfirmation: {
    title: '确认退出登录',
    content: '确定要退出登录吗？退出后需要重新登录。',
    okText: '确定',
    cancelText: '取消'
  },

  // 设置弹窗
  settings: {
    title: '设置',
    account: '账户',
    subscriptions: '订阅',
    systemSettings: '系统设置',
    username: '用户名',
    email: '邮箱',
    lastLogin: '最后登录',
    themeMode: '主题模式',
    language: '语言',
    notifications: '消息提醒',
    emailNotification: '邮件提醒',
    pushNotification: '推送提醒',
    noSubscriptions: '暂无订阅',
    noSubscriptionsDesc: '您还没有创建任何订阅',
    subscriptionTableHeaders: {
      name: '名称',
      assistant: '助理',
      frequency: '执行周期',
      dataRange: '数据范围'
    },
    executionFrequency: {
      daily: '每日',
      weekly: '每周',
      monthly: '每月',
      hours: '每{hours}小时',
      everyDay: '每日',
      weekdays: {
        monday: '周一',
        tuesday: '周二',
        wednesday: '周三',
        thursday: '周四',
        friday: '周五',
        saturday: '周六',
        sunday: '周日',
        一: '一',
        二: '二',
        三: '三',
        四: '四',
        五: '五',
        六: '六',
        日: '日'
      }
    },
    themes: {
      light: '浅色',
      dark: '深色',
      system: '跟随系统'
    },
    languages: {
      zh: '中文',
      en: 'English'
    }
  },

  // 文档查看器
  viewer: {
    pdfFiles: 'PDF文件',
    uploadPdf: '上传PDF',
    noFileSelected: '未选择文件',
    loadingDocument: '正在加载文档...',
    documentLoadError: '文档加载失败',
    fullscreen: '全屏',
    exitFullscreen: '退出全屏'
  },

  // 报告
  reports: {
    riskDaily: 'TA001 风控日报',
    financeQuarterly: 'Q2 财务季度分析',
    newsDaily: '今日要闻简报',
    riskWeekly: 'TA002 风控周报',
    riskAssistant: '风控助理',
    financeAssistant: '财务助理',
    newsAssistant: '新闻助理',
    customerAnalysis: '客户交易数据分析报告',
    allAssistants: '所有助理',
    assistantReports: '助理报告',
    noMatchingReports: '暂无匹配的助理报告'
  },

  // 错误信息
  errors: {
    networkError: '网络错误，请重试',
    serverError: '服务器错误，请稍后重试',
    unauthorized: '未授权访问',
    forbidden: '访问被拒绝',
    notFound: '资源未找到',
    validationError: '验证错误',
    unknownError: '发生未知错误'
  },

  // 成功信息
  success: {
    saved: '保存成功',
    deleted: '删除成功',
    updated: '更新成功',
    uploaded: '上传成功'
  },

  // 文档查看器操作
  docViewer: {
    download: '下载',
    downloadMarkdown: 'Markdown',
    downloadPdf: 'PDF',
    shrink: '缩小',
    expand: '放大',
    close: '关闭',
    loading: '加载中...',
    loadingDocument: '正在加载文档...',
    loadFailed: '加载失败',
    unknownError: '未知错误',
    markdownDocument: 'Markdown文档',
    pdfDocument: 'PDF文档',
    csvData: 'CSV数据',
    csvFile: 'CSV文件',
    csvDocument: 'CSV数据',
    search: '搜索...',
    totalRows: '共 {count} 行数据',
    noData: '暂无数据',
    column: '列',
    unsupportedSourceType: '不支持的源类型',
    pdfLoadFailed: 'PDF加载失败',
    csvParseError: 'CSV解析错误',
    csvParseErrorEmpty: 'CSV文件为空',
    csvParseErrorFormat: 'CSV文件格式错误',
    htmlDocument: 'HTML文档',
    htmlLoadFailed: 'HTML加载失败'
  },

  // 工作空间
  workspace: {
    title: '工作空间',
    aiWorking: 'AI Assistant 正在工作....',
    realtime: '实时',
    loadingFile: '加载中...',
    loadFailed: '加载失败'
  },

  // 确认对话框
  confirmDialog: {
    deleteConversation: '确认删除会话',
    deleteConversationContent: '确定要删除这个会话吗？删除后无法恢复。',
    confirmDelete: '确定删除',
    cancel: '取消',
    deleteSuccess: '删除成功',
    deleteFailed: '删除失败'
  },

  // 模式
  modes: {
    auto: '自动',
    agent: '代理',
    chat: '聊天'
  },

  // 思考状态
  thinking: {
    processing: '助理正在思考...',
    analyzing: '分析中...',
    generating: '生成中...'
  },

  // 消息相关
  messages: {
    scrollToBottom: '滚动到底部',
    newMessage: '新消息',
    sending: '发送中...',
    sendFailed: '发送失败',
    retry: '重试',
    copy: '复制',
    copySuccess: '复制成功',
    delete: '删除'
  }
}
