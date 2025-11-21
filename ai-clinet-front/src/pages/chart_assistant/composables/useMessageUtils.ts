import { h } from 'vue'
import {
  CheckCircleOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined,
  FileWordOutlined,
  FilePptOutlined,
  FileOutlined,
} from '@ant-design/icons-vue'
import { ThoughtChain } from 'ant-design-x-vue'
import { Tag, Collapse } from 'ant-design-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { getFileType, formatFileSize } from '@/utils'

/**
 * Message utilities composable
 * Handles message formatting, status icons, and file processing
 */
export function useMessageUtils() {
  const HOST = import.meta.env.VITE_API_HOST

  // Format message content with markdown support
  const formatMessageContent = (content: any): string => {
    if (!content) return ''
    
    let textContent = content;
    if (typeof content === 'object' && content !== null) {
      if (content.content) {
        textContent = content.content;
      } else if (content.text) {
        textContent = content.text;
      } else if (content.props && content.props.innerHTML) {
        return content.props.innerHTML;
      } else {
        try {
          textContent = JSON.stringify(content);
        } catch (e) {
          textContent = String(content);
        }
      }
    }
    
    try {
      const stringContent = String(textContent);
      const html = marked(stringContent, {
        breaks: true,
        gfm: true,
        headerIds: true,
        mangle: false
      });
      
      const processedHtml = processTableHtml(html);
      return DOMPurify.sanitize(processedHtml);
    } catch (e) {
      console.error('格式化消息内容失败:', e);
      return String(textContent);
    }
  }

  // Process table HTML to add scroll containers
  const processTableHtml = (html: string): string => {
    const tableRegex = /<table[^>]*>[\s\S]*?<\/table>/gi;
    
    return html.replace(tableRegex, (tableMatch) => {
      const tableId = `table-${Math.random().toString(36).substr(2, 9)}`;
      return `<div class="table-scroll-container" data-table-id="${tableId}">${tableMatch}</div>`;
    });
  }

  // Get status icon based on status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return h(CheckCircleOutlined);
      case 'error':
        return h(InfoCircleOutlined);
      case 'pending':
        return h(LoadingOutlined);
      default:
        return undefined;
    }
  }

  // Get file icon based on file type
  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'csv':
        return h(FileExcelOutlined)
      case 'pdf':
        return h(FilePdfOutlined, { size: 24 })
      case 'md':
        return h(FileMarkdownOutlined, { size: 24 })
      case 'xls':
      case 'xlsx':
        return h(FileExcelOutlined, { size: 24 })
      case 'doc':
      case 'docx':
        return h(FileWordOutlined, { size: 24 })
      case 'ppt':
      case 'pptx':
        return h(FilePptOutlined, { size: 24 })
      default:
        return h(FileOutlined, { size: 24 })
    }
  }

  // Generate final file card component
  const genFinalFileCard = (message: string, fileObj: any, onFileClick: (type: string, url: string) => void) => {
    const fileName = fileObj.url.split('/').pop()
    const fileType = getFileType(fileName)
    const fileUrl = HOST + fileObj.url
    const fileSize = formatFileSize(fileObj.file_size)

    const finalFileCard = h('div', { class: 'csv-document-card' }, [
      h('div', { class: 'file-card-header' }, message),
      h('div', { 
        class: 'file-card-content',
        onClick: () => onFileClick(fileType, fileUrl)
      }, [
        h('div', { class: `file-icon ${fileType}` }, [getFileIcon(fileType)]),
        h('div', { class: 'file-info' }, [
          h('div', { class: 'file-filename' }, fileName),
          h('div', { class: 'file-meta' }, fileSize)
        ]),
        h('div', { class: 'file-action' }, [
          h('div', { class: 'view-icon' }, h(EyeOutlined))
        ])
      ])
    ]);

    return [finalFileCard, fileType, fileUrl]
  }

  // Create combined content with markdown and thought chain
  const createCombinedContent = (markdownContent: string, steps: any[], additionalContent?: any[]) => {
    const content = [
      markdownContent ? h('div', { class: "md-wrap", innerHTML: formatMessageContent(markdownContent) }) : null,
      steps.length ? h(ThoughtChain, {
        size: 'small',
        items: [...steps],
        collapsible: true
      }) : null,
      ...(additionalContent || [])
    ].filter(Boolean)
    
    return h('div', { class: 'combined-content' }, content)
  }

  // Create success tag
  const createSuccessTag = (text: string = 'AI Assistant 已完成当前任务') => {
    return h(Tag, { color: 'success' }, {
      icon: () => h(CheckCircleOutlined),
      default: () => text
    })
  }

  // Create warning tag
  const createWarningTag = (text: string) => {
    return h(Tag, { color: 'warning' }, {
      icon: () => h(ExclamationCircleOutlined),
      default: () => text
    })
  }

  // Create thinking process collapse
  const createThinkingProcessCollapse = (resultDatas: any[]) => {
    return h(Collapse, {
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
  }

  return {
    formatMessageContent,
    processTableHtml,
    getStatusIcon,
    getFileIcon,
    genFinalFileCard,
    createCombinedContent,
    createSuccessTag,
    createWarningTag,
    createThinkingProcessCollapse
  }
}