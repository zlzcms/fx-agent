export default {
  // Common
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    close: 'Close',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    loading: 'Loading...',
    search: 'Search',
    clear: 'Clear',
    submit: 'Submit',
    reset: 'Reset',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    finish: 'Finish',
    ok: 'OK',
    yes: 'Yes',
    no: 'No',
    refresh: 'Refresh'
  },

  // Login Page
  login: {
    welcome: 'Welcome Login',
    account: 'Account',
    password: 'Password',
    usernamePlaceholder: 'Please enter registered account',
    passwordPlaceholder: 'Please enter password',
    forgotPassword: 'Forgot Password',
    sliderText: 'Hold the slider and drag to the right',
    verificationSuccess: 'Verification successful',
    pleaseVerify: 'Please complete verification first',
    login: 'Sign In',
    crmLogin: 'CRM Account Login',
    dividerText: 'Or login through the follow',
    loginSuccess: 'Login successful',
    loginFailed: 'Login failed',
    validation: {
      usernameRequired: 'Please enter your username',
      usernameLength: 'Username must be between 3-20 characters',
      passwordRequired: 'Please enter your password',
      passwordLength: 'Password must be at least 6 characters'
    }
  },

  // Chat Assistant
  chat: {
    newConversation: 'New Conversation',
    allChats: 'All Chats',
    assistantReports: 'Assistant Reports',
    allAssistants: 'All Assistants',
    noReports: 'No matching assistant reports',
    aiGeneratedContent: ' AI Summary - Verify',
    assistantThinking: 'Assistant is thinking...',
    attachments: 'Attachments',
    uploadFiles: 'Upload files',
    uploadDescription: 'Click or drag files to this area to upload',
    dropFile: 'Drop file here',
    placeholder: 'Please send a message to ask',
    report: "Report",
    web: "Web",
    welcome: {
      title: "Welcome to the Chat Assistant",
      description: "I will leverage AI capabilities to help you address risk control issues in your work."
    },
    modes: {
      auto: 'Auto',
      agent: 'Agent',
      chat: 'Chat'
    }
  },

  // Navigation and Menu
  nav: {
    dock: 'Dock',
    mySubscriptions: 'My Subscriptions',
    settings: 'Settings',
    logout: 'Logout',
    appName: 'AI Assistant',
    appTitle: 'AI Assistant'
  },

  // Logout Confirmation
  logoutConfirmation: {
    title: 'Confirm Logout',
    content: 'Are you sure you want to logout? You will need to login again after logging out.',
    okText: 'Confirm',
    cancelText: 'Cancel'
  },

  // Settings Modal
  settings: {
    title: 'Settings',
    account: 'Account',
    subscriptions: 'Subscriptions',
    systemSettings: 'System Settings',
    username: 'Username',
    email: 'Email',
    lastLogin: 'Last Login',
    themeMode: 'Theme Mode',
    language: 'Language',
    notifications: 'Message Notifications',
    emailNotification: 'Email Notifications',
    pushNotification: 'Push Notifications',
    noSubscriptions: 'No subscriptions',
    noSubscriptionsDesc: 'You haven\'t created any subscriptions yet',
    subscriptionTableHeaders: {
      name: 'Name',
      assistant: 'Assistant',
      frequency: 'Execution Frequency',
      dataRange: 'Data Range'
    },
    executionFrequency: {
      daily: 'Daily',
      weekly: 'Weekly',
      monthly: 'Monthly',
      hours: 'Every {hours} hour(s)',
      everyDay: 'Every day',
      weekdays: {
        monday: 'Monday',
        tuesday: 'Tuesday',
        wednesday: 'Wednesday',
        thursday: 'Thursday',
        friday: 'Friday',
        saturday: 'Saturday',
        sunday: 'Sunday',
        一: 'Monday',
        二: 'Tuesday',
        三: 'Wednesday',
        四: 'Thursday',
        五: 'Friday',
        六: 'Saturday',
        日: 'Sunday'
      }
    },
    themes: {
      light: 'Light',
      dark: 'Dark',
      system: 'System'
    },
    languages: {
      zh: 'Chinese',
      en: 'English'
    }
  },

  // Document Viewer
  viewer: {
    pdfFiles: 'PDF Files',
    uploadPdf: 'Upload PDF',
    noFileSelected: 'No file selected',
    loadingDocument: 'Loading document...',
    documentLoadError: 'Failed to load document',
    fullscreen: 'Fullscreen',
    exitFullscreen: 'Exit Fullscreen'
  },

  // Reports
  reports: {
    riskDaily: 'TA001 Risk Daily Report',
    financeQuarterly: 'Q2 Financial Quarterly Analysis',
    newsDaily: 'Daily News Brief',
    riskWeekly: 'TA002 Risk Weekly Report',
    riskAssistant: 'Risk Assistant',
    financeAssistant: 'Finance Assistant',
    newsAssistant: 'News Assistant',
    customerAnalysis: 'Customer Trading Data Analysis Report',
    allAssistants: 'All Assistants',
    assistantReports: 'Assistant Reports',
    noMatchingReports: 'No matching assistant reports'
  },

  // Error Messages
  errors: {
    networkError: 'Network error, please try again',
    serverError: 'Server error, please try again later',
    unauthorized: 'Unauthorized access',
    forbidden: 'Access denied',
    notFound: 'Resource not found',
    validationError: 'Validation error',
    unknownError: 'Unknown error occurred'
  },

  // Success Messages
  success: {
    saved: 'Saved successfully',
    deleted: 'Deleted successfully',
    updated: 'Updated successfully',
    uploaded: 'Uploaded successfully'
  },

  // Document Viewer Actions
  docViewer: {
    download: 'Download',
    downloadMarkdown: 'Download Markdown',
    downloadPdf: 'Download PDF',
    shrink: 'Shrink',
    expand: 'Expand',
    close: 'Close',
    loading: 'Loading...',
    loadingDocument: 'Loading document...',
    loadFailed: 'Load failed',
    unknownError: 'Unknown error',
    markdownDocument: 'Markdown Document',
    pdfDocument: 'PDF Document',
    csvData: 'CSV Data',
    csvFile: 'CSV File',
    csvDocument: 'CSV Data',
    search: 'Search...',
    totalRows: 'Total {count} rows',
    noData: 'No data',
    column: 'Column',
    unsupportedSourceType: 'Unsupported source type',
    pdfLoadFailed: 'PDF load failed',
    csvParseError: 'CSV parse error',
    csvParseErrorEmpty: 'CSV file is empty',
    csvParseErrorFormat: 'CSV file format error',
    htmlDocument: 'HTML Document',
    htmlLoadFailed: 'HTML load failed'
  },

  // Workspace
  workspace: {
    title: 'Workspace',
    aiWorking: 'AI Assistant is working....',
    realtime: 'Real-time',
    loadingFile: 'Loading...',
    loadFailed: 'Load failed'
  },

  // Confirm Dialogs
  confirmDialog: {
    deleteConversation: 'Confirm Delete Conversation',
    deleteConversationContent: 'Are you sure you want to delete this conversation? This action cannot be undone.',
    confirmDelete: 'Confirm Delete',
    cancel: 'Cancel',
    deleteSuccess: 'Deleted successfully',
    deleteFailed: 'Delete failed'
  },

  // Modes
  modes: {
    auto: 'Auto',
    agent: 'Agent',
    chat: 'Chat'
  },

  // Thinking Status
  thinking: {
    processing: 'Assistant is thinking...',
    analyzing: 'Analyzing...',
    generating: 'Generating...'
  },

  // Message Related
  messages: {
    scrollToBottom: 'Scroll to bottom',
    newMessage: 'New message',
    sending: 'Sending...',
    sendFailed: 'Send failed',
    retry: 'Retry',
    copy: 'Copy',
    copySuccess: 'Copied successfully',
    delete: 'Delete'
  }
}
