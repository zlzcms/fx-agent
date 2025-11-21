import { computed } from 'vue'
import { theme } from 'ant-design-vue'

/**
 * Styles composable
 * Manages all computed styles for the chat interface
 */
export function useStyles(dependencies: {
  isMobile: any,
  showRightAgent: any,
  chatVisible: any,
  activeConversation: any
}) {
  const { token } = theme.useToken()

  // Justify alignment for chat container
  const justifyAlign = computed(() => {
    if (dependencies.isMobile.value) {
      return dependencies.activeConversation.value ? 'flex-start' : 'space-between'
    } else {
      return dependencies.activeConversation.value ? 'flex-start' : 'space-between'
    }
  })

  // Main styles object
  const styles = computed(() => {
    return {
      'layout': {
        'height': '100%',
        'width': '100%',
        'border-radius': `${token.value.borderRadius}px`,
        'display': 'flex',
        'background': `${token.value.colorBgContainer}`,
        'font-family': `AlibabaPuHuiTi, ${token.value.fontFamily}, sans-serif`,
      },
      'chat-container': {
        'height': '100%',
        'background-color': 'var(--bg-chat)',
        'width': dependencies.showRightAgent.value ? '50%' : '100%',
        'max-width': '100%',
        'box-sizing': 'border-box',
        'display': 'flex',
        'justify-content': justifyAlign.value,
        'flex-direction': 'column',
        'position': 'relative',
        'transition': 'margin-left 0.3s ease',
      },
      'head-title': {
        "max-width": "clamp(200px, 94vw, 800px)",
        'margin': '0 auto',
        'position': 'relative',
        'text-align': 'left',
        'display': 'flex',
        'padding': '15px 0 5px 0',
        'align-items': 'center',
        'justify-content': 'space-between',
        'font-size': '18px',
        'color': 'var(--text-primary)',
      },
      'rightAgent': {
        'width': dependencies.chatVisible.value ? '50%' : '100%',
        'max-width': '100%',
        'height': '100%',
        'border-left': '1px solid var(--border-agent)',
      },
      'scroll-container': {
        'flex': '1',
        'overflow-y': 'auto',
        'padding-top': '15px',
      },
      'messages': {
        'flex': '1',
        'overflow-x': 'hidden',
        'width': '100%',
      },
      'chat-style': {
        "max-width": "clamp(200px, 90vw, 768px)",
        'margin': '0 auto',
        'position': 'relative',
        'padding': dependencies.isMobile.value ? '0' : '0 25px',
      },
      'prompts-style': {
        'max-width': 'clamp(200px, 94vw, 768px)',
        'overflow-y': 'auto',
        'width': '100%',
        'margin': '0 auto',
        "padding":"10px",
        'position': 'relative',

      },
      'sender-style': {
        "max-width": "clamp(200px, 94vw, 768px)",
        'margin': '0 auto',
        'position': 'relative',
        'padding': dependencies.isMobile.value ? '0' : '0 10px',
      },
      'placeholder': {
        'padding-top': '32px',
        'text-align': 'left',
        'flex': 1,
      },
    } as const
  })

  // Speech icon styles
  const speechIconStyle = computed(() => ({
    color: 'var(--text-secondary)',
    fontSize: '16px',
    padding: '4px 8px',
    borderRadius: '4px',
    transition: 'all 0.2s',
    '&:hover': {
      backgroundColor: 'var(--hover-bg)',
      color: 'var(--primary-color)'
    }
  }))

  return {
    styles,
    speechIconStyle,
    justifyAlign
  }
}