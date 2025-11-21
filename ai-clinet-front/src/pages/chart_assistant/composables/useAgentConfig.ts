import {  h, nextTick, VNode } from 'vue'
import { useXAgent, XStream } from 'ant-design-x-vue'
import { Tag, Collapse, Spin } from 'ant-design-vue'
import axios from 'axios'

import { useMessageUtils } from './useMessageUtils'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  FileSearchOutlined
} from '@ant-design/icons-vue'
import { ThoughtChain } from 'ant-design-x-vue'
/**
 * Agent configuration and stream processing composable
 * Handles agent setup, stream processing, and chat management
 */
const HOST = import.meta.env.VITE_API_HOST
const { formatMessageContent,getStatusIcon,genFinalFileCard } = useMessageUtils()
export function useAgentConfig(dependencies: {
  isMobile: any,
  agentRequestLoading: any,
  setMessages: any,
  activeConversation: any,
  modelValue: any,
  bubbleListlRef: any,
  createNewConversation: (message: string) => Promise<void>,
  onWorkSpaceShow: (options: { source: string }) => void,
  resultFormat: any,
  showCsvViewer: Function,
  showPdfViewer: Function,
  showMarkdownViewer: Function,
  showHtmlViewer: Function,
  store?: any
}) {

  const { isMobile,onWorkSpaceShow,showCsvViewer,showMarkdownViewer,showPdfViewer,showHtmlViewer } = dependencies
  // Create stream processing helpers
  const createStreamProcessingHelpers = () => {
    const createStreamState = () => ({
      markdownContent: '',
      fullResponse: '',
      finalErrorMessages: '',
      steps: [],
      currentStepIndex: 0,
      resultDatas: [],
      isStreaming: false
    })

    const manageLoadingMessage = () => {
      const loadingMessageId = `loading_${Date.now()}`
      const loadingStartTime = Date.now()
      const loadingMessages = 'Assistant is thinking...'
      
      const addLoadingMessage = () => {
        dependencies.setMessages(prev => [...prev, {
          id: loadingMessageId,
          message: loadingMessages,
          status: 'custom_loading'
        }])
        dependencies.bubbleListlRef.value?.scrollToBottom()
      }
      
      const removeLoadingMessage = (force = false) => {
        if (force || Date.now() - loadingStartTime >= 500) {
          dependencies.setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId))
        }
      }
      
      const updateLoadingMessageToError = () => {
        dependencies.setMessages(prev => prev.map(msg => 
          msg.id === loadingMessageId 
            ? { ...msg, message: '请求失败，请重试', status: 'error' } 
            : msg
        ))
      }
      
      return { addLoadingMessage, removeLoadingMessage, updateLoadingMessageToError }
    }

    const createCombinedContent = (markdownContent, steps, additionalContent = []) => {
      const content = [
        markdownContent ? h('div', { class: "md-wrap", innerHTML: formatMessageContent(markdownContent) }) : null,
        steps.length ? h(ThoughtChain, {
          size: 'small',
          items: [...steps],
          collapsible: true
        }) : null,
        ...additionalContent
      ].filter(Boolean)
      
      return h('div', { class: 'combined-content' }, content)
    }

    // Helper to add loading indicator at the bottom of content
    const addLoadingToContent = (content) => {
      const loadingIndicator = h('div', {
        class: 'stream-loading-indicator',
        style: {
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          marginTop: '4px',
          marginBottom: '4px',
          color: '#8c8c8c',
          fontSize: '13px',
          minHeight: '20px', // 固定高度，避免抖动
          lineHeight: '20px'
        }
      }, [
        h(Spin, {
          size: 'small',
          indicator: h(LoadingOutlined, { 
            style: { fontSize: '14px' },
            spin: true 
          })
        }),
        h('span', '思考中...')
      ])

      // If content is empty string or null/undefined
      if (!content || content === '') {
        return h('div', { class: 'combined-content' }, [loadingIndicator])
      }

      // If content is already a VNode with children
      if (content && content.type === 'div' && content.children) {
        const children = Array.isArray(content.children) ? content.children : [content.children]
        return h('div', { class: content.props?.class || 'combined-content' }, [...children, loadingIndicator])
      }
      
      // If content is a simple VNode
      return h('div', { class: 'combined-content' }, [content, loadingIndicator])
    }

    return { createStreamState, manageLoadingMessage, createCombinedContent, addLoadingToContent }
  }

  // Process stream response
  const processStreamResponse = async (response: Response, state: any, helpers: any, loadingManager: any) => {
    const chat_reps_id = `chat_reps_id_${Date.now()}`
    let loadingTimeout: ReturnType<typeof setTimeout> | null = null
    
    try {
      if (!response.body) return
      
      const stream = XStream({ readableStream: response.body })
      
      // Track if stream is still processing
      state.isStreaming = true
      
      // Initialize empty message (without loading indicator initially)
      dependencies.setMessages(prev => [...prev, {
        id: chat_reps_id,
        message: '',
        status: 'success',
        role: 'assistant'
      }])

      // Process each chunk
      for await (const chunk of stream) {
        // Clear any pending loading timeout
        if (loadingTimeout) {
          clearTimeout(loadingTimeout)
          loadingTimeout = null
        }
        
        // Remove loading before processing chunk (AI is not thinking, it's processing)
        removeLoadingFromMessage(chat_reps_id)
        
        const chunkData = JSON.parse(chunk.data)
        await processChunk(chunkData, state, helpers, chat_reps_id, loadingManager)
        
        // Add loading after processing chunk with delay (AI is thinking about next chunk)
        if (state.isStreaming) {
          loadingTimeout = setTimeout(() => {
            if (state.isStreaming) {
              addLoadingToMessage(chat_reps_id, helpers)
            }
          }, 450) // 450ms delay before showing loading
        }
        
        dependencies.bubbleListlRef.value?.scrollToBottom()
      }
      
      // Mark streaming as complete
      state.isStreaming = false
      if (loadingTimeout) {
        clearTimeout(loadingTimeout)
      }
      removeLoadingFromMessage(chat_reps_id)
      loadingManager.removeLoadingMessage(true)
      
    } catch (streamError) {
      // Clear timeout on error
      if (loadingTimeout) {
        clearTimeout(loadingTimeout)
        loadingTimeout = null
      }
      if (streamError.name !== 'AbortError') {
        throw streamError
      }
    } finally {
      // Ensure streaming is marked as complete
      state.isStreaming = false
      // Clear any remaining timeout
      if (loadingTimeout) {
        clearTimeout(loadingTimeout)
      }
      
      // Add thinking process if has results
      if (state.resultDatas.length > 0) {
        const collapse = h(Collapse, {
          accordion: true,
          bordered: false,
          class: 'mt-2'
        }, {
          default: () => [
            h(Collapse.Panel, {
              key: 'p1', 
              header: '展示思维过程'
            }, {
              default: () => state.resultDatas
            })
          ]
        })
        console.info("添加思维过程")
        dependencies.setMessages(prev => prev.map((msg) =>{
            if (msg.id === chat_reps_id) {
              // 移除loading indicator并添加collapse
              let existingContent = msg.message
              
              // 如果message有children，过滤掉loading indicator
              if (existingContent?.children && Array.isArray(existingContent.children)) {
                const contentWithoutLoading = existingContent.children.filter(child => 
                  !child?.props?.class?.includes('stream-loading-indicator')
                )
                existingContent = h('div', { class: 'combined-content' }, contentWithoutLoading)
              }
              
              // 添加collapse到内容中
              let message: VNode
              if (existingContent?.children && Array.isArray(existingContent.children)) {
                message = h('div', { class: 'combined-content' }, [...existingContent.children, collapse])
              } else {
                message = h('div', { class: 'combined-content' }, [existingContent, collapse])
              }
              return {
                ...msg,
                message: message
              }
            } else {
              return msg
            }
          }
        ))
      } else {
        // 如果没有思维过程，也要移除loading indicator
        dependencies.setMessages(prev => prev.map((msg) =>{
          if (msg.id === chat_reps_id && msg.message?.children && Array.isArray(msg.message.children)) {
            const contentWithoutLoading = msg.message.children.filter(child => 
              !child?.props?.class?.includes('stream-loading-indicator')
            )
            if (contentWithoutLoading.length !== msg.message.children.length) {
              return {
                ...msg,
                message: h('div', { class: msg.message.props?.class || 'combined-content' }, contentWithoutLoading)
              }
            }
          }
          return msg
        }))
      }
      dependencies.bubbleListlRef.value?.scrollToBottom()
    }
  }

// Helper function to remove loading indicator from a message
const removeLoadingFromMessage = (messageId) => {
  dependencies.setMessages(prev => prev.map(msg => {
    if (msg.id === messageId) {
      // Check if message has children
      if (msg.message?.children && Array.isArray(msg.message.children)) {
        const contentWithoutLoading = msg.message.children.filter(child => 
          !child?.props?.class?.includes('stream-loading-indicator')
        )
        
        // Only update if loading was actually removed
        if (contentWithoutLoading.length !== msg.message.children.length) {
          // If no content left after removing loading, set to empty string
          if (contentWithoutLoading.length === 0) {
            return { ...msg, message: '' }
          }
          return {
            ...msg,
            message: h('div', { class: msg.message.props?.class || 'combined-content' }, contentWithoutLoading)
          }
        }
      }
    }
    return msg
  }))
}

// Helper function to add loading indicator to a message
const addLoadingToMessage = (messageId, helpers) => {
  if (!helpers || typeof helpers.addLoadingToContent !== 'function') return
  
  dependencies.setMessages(prev => prev.map(msg => {
    if (msg.id === messageId) {
      // Check if loading already exists
      if (msg.message?.children && Array.isArray(msg.message.children)) {
        const hasLoading = msg.message.children.some(child => 
          child?.props?.class?.includes('stream-loading-indicator')
        )
        if (hasLoading) {
          return msg // Already has loading, don't add again
        }
      }
      
      // Add loading to the message
      return {
        ...msg,
        message: helpers.addLoadingToContent(msg.message)
      }
    }
    return msg
  }))
}

// Helper function to update message
const updateMessage = (messageId, content) => {
  dependencies.setMessages(prev => prev.map(msg => {
    if (msg.id === messageId) {
      return { ...msg, message: content }
    }
    return msg
  }))
}
// Process step chunks with different type_names
const processStepChunk = async (chunkData, state, helpers, chat_reps_id) => {
  const { createCombinedContent } = helpers
  
  switch (chunkData.type_name) {
    case 'title':
      state.currentStepIndex = state.steps.length
      state.steps.push({
        key: `step_${state.currentStepIndex}`,
        title: chunkData.message,
        description: h('div', ''),
        // status: 'pending',
        icon: getStatusIcon('pending')
      })
      
      await nextTick()
      updateMessage(chat_reps_id, createCombinedContent(state.markdownContent, state.steps))
      break
      
    case 'execute':
      const step = state.steps[state.currentStepIndex]
      const message = chunkData.message
      
      if (chunkData.file) {
        const fileUrl = HOST + chunkData.file.url
        if (!isMobile.value) {
          onWorkSpaceShow({ source: fileUrl })
        }
        
        const clickableMessage = h('div', {
          class: 'execute-ele mb-2',
          onClick: () => onWorkSpaceShow({ source: fileUrl }),
          style: {
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }
        }, [
          h(FileSearchOutlined, { style: { fontSize: '14px' } }),
          h('span', message)
        ])
        
        const currentChildren = step.description.children || []
        step.description = h('div', [
          ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
          clickableMessage
        ].filter(Boolean))
      } else {
        const currentChildren = step.description.children || []
        step.description = h('div', {
          style: { marginTop: '5px' }
        }, [
          ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
          h('div', { class: "execute-ele-none mb-2" }, message)
        ].filter(Boolean))
      }
      
      // step.status = 'pending'
      step.icon = getStatusIcon('pending')
      
      await nextTick()
      updateMessage(chat_reps_id, createCombinedContent(state.markdownContent, state.steps))
      break
      
    case 'completion':
      const completionStep = state.steps[state.currentStepIndex]
      const currentChildren = completionStep.description.children || []
      completionStep.description = h('div', [
        ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
        chunkData.message
      ].filter(Boolean))
      
      // completionStep.status = 'pending'
      completionStep.icon = getStatusIcon('pending')
      
      await nextTick()
      updateMessage(chat_reps_id, createCombinedContent(state.markdownContent, state.steps))
      break
      
    case 'success':
      const successStep = state.steps[state.currentStepIndex]
      const successChildren = successStep.description.children || []
      successStep.description = h('div', [
        ...(Array.isArray(successChildren) ? successChildren : [successChildren]),
        chunkData.message
      ].filter(Boolean))
      
      // successStep.status = 'success'
      successStep.icon = getStatusIcon('success')
      
      await nextTick()
      updateMessage(chat_reps_id, createCombinedContent(state.markdownContent, state.steps))
      break
  }
}

// Process error chunks
const processErrorChunk = (chunkData, state, helpers, chat_reps_id) => {
  if (state.steps.length) {
    const lastStep = state.steps[state.steps.length - 1]
    if (lastStep.status !== 'success') {
      // lastStep.status = 'error'
      lastStep.icon = getStatusIcon('error')
    }
  }
  
  const tagWarning = h(Tag, { color: 'warning' }, {
    icon: () => h(ExclamationCircleOutlined),
    default: () => chunkData.message
  })
  
  const content = helpers.createCombinedContent(state.markdownContent, state.steps, [
    h('div', [tagWarning])
  ])
  
  // Error stops streaming
  state.isStreaming = false
  updateMessage(chat_reps_id, content)
}

// Process final chunks
const processFinalChunk = (chunkData, state, helpers, chat_reps_id) => {
  // Final chunk stops streaming
  state.isStreaming = false
  
  if (chunkData.status === 'success') {
    let finalFileCard, fileType, fileUrl
    if (chunkData.file) {
      const onFileClick = (type: string, url: string) => {
          const viewerMap = {
            csv: () => showCsvViewer(url),
            pdf: () => showPdfViewer(url),
            md: () => showMarkdownViewer(url),
            html: () => showHtmlViewer(url)
          }
          viewerMap[type]?.()
        }
      [finalFileCard, fileType, fileUrl] = genFinalFileCard(chunkData.message, chunkData.file,onFileClick)
    }
    
    const tagSuccess = h(Tag, { color: 'success' }, {
      icon: () => h(CheckCircleOutlined),
      default: () => 'AI Assistant 已完成当前任务'
    })
    
    const content = helpers.createCombinedContent(state.markdownContent, state.steps, [
      finalFileCard,
      h('div', [tagSuccess])
    ].filter(Boolean))
    
    updateMessage(chat_reps_id, content)
    
    // Auto-open viewers
    if (fileType === 'csv') showCsvViewer(fileUrl)
    if (fileType === 'pdf') showPdfViewer(fileUrl)
    if (fileType === 'md') showMarkdownViewer(fileUrl)
    
  } else if (chunkData.status === 'error') {
    state.finalErrorMessages += chunkData.message
    
    const content = helpers.createCombinedContent(state.markdownContent, state.steps, [
      h('div', { class: "md-wrap", innerHTML: formatMessageContent(state.finalErrorMessages) })
    ])
    
    updateMessage(chat_reps_id, content)
  }
}

// Process log chunks
const processLogChunk = (chunkData, state) => {
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
  
  state.resultDatas.push(collapse)
}
  // Process individual chunk
// Process individual chunk - extracted chunk processing logic
const processChunk = async (chunkData, state, helpers, chat_reps_id, loadingManager) => {
  const { createCombinedContent } = helpers
  
  switch (chunkData.type) {
    case 'chat':
      state.fullResponse += chunkData.message
      state.markdownContent = state.fullResponse
      if (state.fullResponse.trim().length > 0) {
        loadingManager.removeLoadingMessage()
      }
      
      const chatContent = h('div', { 
        class: "md-wrap", 
        innerHTML: formatMessageContent(state.fullResponse) 
      })
      updateMessage(chat_reps_id, chatContent)
      break
      
    case 'md_info':
      state.fullResponse += chunkData.message
      state.markdownContent = state.fullResponse
      if (state.fullResponse.trim().length > 0) {
        loadingManager.removeLoadingMessage()
      }
      
      const mdContent = state.steps.length > 0 
        ? createCombinedContent(state.markdownContent, state.steps)
        : h('div', { class: "md-wrap", innerHTML: formatMessageContent(state.fullResponse) })
      
      updateMessage(chat_reps_id, mdContent)
      break
      
    case 'step':
      await processStepChunk(chunkData, state, helpers, chat_reps_id)
      break
      
    case 'interrupted':
    case 'error':
      processErrorChunk(chunkData, state, helpers, chat_reps_id)
      break
      
    case 'final':
      processFinalChunk(chunkData, state, helpers, chat_reps_id)
      break
      
    case 'log':
      processLogChunk(chunkData, state)
      break
      
    default:
      console.warn(`Unknown chunk type: ${chunkData.type}`, chunkData)
  }
}

  // Create and configure the agent
  const [agent] = useXAgent({
    request: async ({ message, messages }, { onUpdate, onSuccess, onError, onStream }) => {
      dependencies.agentRequestLoading.value = true
      const helpers = createStreamProcessingHelpers()
      const state = helpers.createStreamState()
      const loadingManager = helpers.manageLoadingMessage()

      try {
        // Setup API request
        const baseURL = axios.defaults.baseURL || ''
        const url = `${baseURL}/home/chat/completion`
        const token = localStorage.getItem('access_token')
        const chat_id = localStorage.getItem('store_chat_id')
        
        if (chat_id === '' && message) {
          await dependencies.createNewConversation(message)
        }

        // Show loading message
        loadingManager.addLoadingMessage()
        // Get store from dependencies or use a fallback
        const store = dependencies.store || null
        const channel = store?.getters?.['auth/channel'] || null
        // Make API request
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            chat_id: dependencies.activeConversation.value?.id || null,
            message,
            action: dependencies.modelValue.value,
            result_format: dependencies.resultFormat.value,
            channel: channel || null
          }),
        })
        
        if (!response.ok) {
          loadingManager.updateLoadingMessageToError()
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        await processStreamResponse(response, state, helpers, loadingManager)
        
      } catch (error) {
        console.error('发送消息失败:', error)
        onError(error instanceof Error ? error : new Error('发送消息失败'))
      } finally {
       
        dependencies.bubbleListlRef.value?.scrollToBottom()
        dependencies.agentRequestLoading.value = false
      }
    }
  })

  return {
    agent,
    processStreamResponse,
    processChunk,
    createStreamProcessingHelpers
  }
}