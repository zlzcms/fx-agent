import { h, reactive } from 'vue'
import { Collapse } from 'ant-design-vue'
import { useMessageUtils } from './useMessageUtils'
import { FileSearchOutlined } from '@ant-design/icons-vue'
/**
 * Message handler composable
 * Handles different types of message processing and content generation
 */
export function useMessageHandler() {
  const {
    formatMessageContent,
    createCombinedContent,
    getStatusIcon,
    createSuccessTag,
    createWarningTag,
    genFinalFileCard
  } = useMessageUtils()

  // Update step description helper
  const updateStepDescription = (step: any, newContent: any, options: { className?: string, clickHandler?: () => void } = {}) => {
    const currentChildren = step.description.children || []
    const contentElement = options.clickHandler 
      ? h('div', {
          class: options.className || 'execute-ele mb-2',
          onClick: options.clickHandler,
          style: {
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }
        }, [
          h(FileSearchOutlined, { style: { fontSize: '14px' } }),
          h('span', newContent)
        ])
      : h('div', { class: options.className || 'execute-ele-none mb-2' }, newContent)
    
    step.description = h('div', {
      style: options.className?.includes('none') ? { marginTop: '5px' } : {}
    }, [
      ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
      contentElement
    ].filter(Boolean))
  }

  // Handle chat type messages
  const handleChatType = (chunkData: any, state: any) => {
    state.fullResponse += chunkData.message
    state.markdownContent = state.fullResponse
    return h('div', { class: "md-wrap", innerHTML: formatMessageContent(state.markdownContent) })
  }

  // Handle markdown info type messages
  const handleMdInfoType = (chunkData: any, state: any) => {
    state.fullResponse += chunkData.message
    state.markdownContent = state.fullResponse
    
    return state.steps.length > 0 
      ? createCombinedContent(state.fullResponse, state.steps)
      : h('div', { class: "md-wrap", innerHTML: formatMessageContent(state.markdownContent) })
  }

  // Handle step type messages
  const handleStepType = (chunkData: any, state: any, onWorkSpaceShow: (options: { source: string }) => void) => {
    const { type_name, message } = chunkData
    const HOST = import.meta.env.VITE_API_HOST
    
    switch (type_name) {
      case 'title': {
        state.currentStepIndex = state.steps.length
        state.steps.push({
          key: `step_${state.currentStepIndex}`,
          title: message,
          description: h('div', ''),
          // status: 'pending',
          icon: getStatusIcon('pending')
        })
        return createCombinedContent(state.markdownContent, state.steps)
      }
      
      case 'execute': {
        const step = state.steps[state.currentStepIndex]
        if (chunkData.file) {
          const fileUrl:string = HOST + chunkData.file.url



          updateStepDescription(step, message, {
            className: 'execute-ele mb-2',
            clickHandler: () => onWorkSpaceShow({ source: fileUrl })
          })
        } else {
          updateStepDescription(step, message, { className: 'execute-ele-none mb-2' })
        }
        
        // step.status = 'pending'
        step.icon = getStatusIcon('pending')
        return createCombinedContent(state.markdownContent, state.steps)
      }
      
      case 'completion': {
        const step = state.steps[state.currentStepIndex]
        const currentChildren = step.description.children || []
        step.description = h('div', [
          ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
          message
        ].filter(Boolean))
        
        // step.status = 'pending'
        step.icon = getStatusIcon('pending')
        return createCombinedContent(state.markdownContent, state.steps)
      }
      
      case 'success': {
        const step = state.steps[state.currentStepIndex]
        const currentChildren = step.description.children || []
        step.description = h('div', [
          ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
          message
        ].filter(Boolean))
        
        // step.status = 'success'
        step.icon = getStatusIcon('success')
        return createCombinedContent(state.markdownContent, state.steps)
      }
      
      default:
        return null
    }
  }

  // Handle final type messages
  const handleFinalType = (chunkData: any, state: any, isLast: boolean, viewerHandlers: any) => {
    const { status, message, file } = chunkData
    
    if (status === 'success') {
      const successTag = createSuccessTag()
      
      let finalFileCard, fileType, fileUrl
      if (file) {
        const onFileClick = (type: string, url: string) => {
          const viewerMap = {
            csv: () => viewerHandlers.showCsvViewer?.(url),
            pdf: () => viewerHandlers.showPdfViewer?.(url),
            md: () => viewerHandlers.showMarkdownViewer?.(url),
            html: () => viewerHandlers.showHtmlViewer?.(url)
          }
          viewerMap[type]?.()
        }
        
        ;[finalFileCard, fileType, fileUrl] = genFinalFileCard(message, file, onFileClick)
        
        // Auto-open viewer if it's the last message
        if (isLast) {
          const viewerMap = {
            csv: () => viewerHandlers.showCsvViewer?.(fileUrl),
            pdf: () => viewerHandlers.showPdfViewer?.(fileUrl),
            md: () => viewerHandlers.showMarkdownViewer?.(fileUrl),
            html: () => viewerHandlers.showHtmlViewer?.(fileUrl)
          }
          viewerMap[fileType]?.()
        }
      }
      
      return createCombinedContent(state.markdownContent, state.steps, [
        finalFileCard,
        h('div', [successTag])
      ])
    }
    
    if (status === 'error') {
      state.finalErrorMessages += message
      return createCombinedContent(state.markdownContent, state.steps, [
        h('div', { class: "md-wrap", innerHTML: formatMessageContent(state.finalErrorMessages) })
      ])
    }
    
    return null
  }

  // Handle error and interrupted type messages
  const handleErrorType = (chunkData: any, state: any) => {
    if (state.steps.length) {
      const lastStep = state.steps[state.steps.length - 1]
      if (lastStep.status !== 'success') {
        // lastStep.status = 'error'
        lastStep.icon = getStatusIcon('error')
      }
    }
    
    const warningTag = createWarningTag(chunkData.message)
    
    return createCombinedContent(state.markdownContent, state.steps, [
      h('div', [warningTag])
    ])
  }

  // Handle log type messages
  const handleLogType = (chunkData: any, resultDatas: any[]) => {
    const { title: name, content } = chunkData
    
    let output
    if (Array.isArray(content)) {
      output = content.map(item => {
           const collapse = h(Collapse, {
            accordion: true,
            bordered: false,
            class: 'mt-2'
          }, {
            default: () => [
              h(Collapse.Panel, { key: 'p1', header: item.title }, {
                default: () =>  h('div', {
                  class: 'md-wrap thinking-process',
                  innerHTML: formatMessageContent(item.content)
                })
              })
            ]
          })
          return collapse
      })

    } else {
      output = content
    }
    
    // 意图识别,获取数据。。
    const collapse = h(Collapse, {
      accordion: true,
      bordered: false,
      class: 'mt-2'
    }, {
      default: () => [
        h(Collapse.Panel, { key: 'p1', header: name }, {
          default: () => output
        })
      ]
    })
    
    resultDatas.push(collapse)
  }

  // Main function to handle assistant messages
  const handleAssistantMessages = (
    response_data: Array<any>, 
    isLast: boolean, 
    onWorkSpaceShow: (options: { source: string }) => void,
    viewerHandlers?: any
  ) => {
    let assistantMessage: any = undefined
    const resultDatas: any[] = []
    
    // State object to centrally manage all states
    const state = {
      markdownContent: '',
      fullResponse: '',
      finalErrorMessages: '',
      steps: reactive([]) as Array<{
        key: string
        title: any
        description: any
        status: string
        icon: any
      }>,
      currentStepIndex: 0
    }
    
    // Use for...of instead of traditional for loop
    for (const chunkData of response_data) {
      const { type } = chunkData
      
      // Use switch statement instead of multiple if-else for better performance and readability
      switch (type) {
        case 'chat':
          assistantMessage = handleChatType(chunkData, state)
          break
          
        case 'md_info':
          assistantMessage = handleMdInfoType(chunkData, state)
          break
          
        case 'step':
          assistantMessage = handleStepType(chunkData, state, onWorkSpaceShow)
          break
          
        case 'final':
          assistantMessage = handleFinalType(chunkData, state, isLast, viewerHandlers || {})
          break
          
        case 'interrupted':
        case 'error':
          assistantMessage = handleErrorType(chunkData, state)
          break
          
        case 'log':
          handleLogType(chunkData, resultDatas)
          break
          
        default:
          // Handle unknown types to avoid silent failures
          console.warn(`Unknown chunk data type: ${type}`, chunkData)
          break
      }
    }
    
    // Add thinking process information
    if (resultDatas.length > 0) {
      const thinkingProcessCollapse = h(Collapse, {
        accordion: true,
        bordered: false,
        class: 'mt-2'
      }, {
        default: () => [
          h(Collapse.Panel, {
            key: 'thinking-process',
            header: '展示思维过程'
          }, {
            default: () => resultDatas
          })
        ]
      })
      
      assistantMessage = h('div', [assistantMessage, thinkingProcessCollapse])
    }
    
    return assistantMessage
  }

  return {
    handleAssistantMessages,
    handleChatType,
    handleMdInfoType,
    handleStepType,
    handleFinalType,
    handleErrorType,
    handleLogType,
    updateStepDescription
  }
}