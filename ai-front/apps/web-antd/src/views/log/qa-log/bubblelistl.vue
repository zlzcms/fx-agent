<script setup lang="ts">
import type { BubbleListProps } from 'ant-design-x-vue';

import type { ChatMessageItem } from '#/api';

import { computed, h, onMounted, onUnmounted, reactive, ref, watch } from 'vue';

import { createIconifyIcon } from '@vben/icons';

import { Spin as ASpin, Collapse, Tag } from 'ant-design-vue';
import { Bubble, ThoughtChain } from 'ant-design-x-vue';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

import { getChatLogPaginatedApi } from '#/api';
// Props 定义
interface Props {
  chatMessageItem: ChatMessageItem;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const userScrolled = ref<boolean>(true);
const scrollContainerStyle = computed(() => {
  return {
    flex: '1',
    overflowY: 'auto' as const,
    padding: '10px 15px',
  };
});

const messageStyle = computed(() => {
  return {
    flex: '1',
    overflowX: 'hidden' as const,
    width: '100%', // 确保宽度为100%
    height: '100%',
  };
});
// 对话角色定义
const roles: BubbleListProps['roles'] = {
  assistant: {
    placement: 'start',
    variant: 'borderless',
    styles: {
      content: {
        borderRadius: '16px',
      },
    },
  },
  user: {
    placement: 'end',
    variant: 'shadow',
    styles: {
      content: {
        border: '1px solid #efefef',
        'border-bottom-right-radius': '0px',
        'box-shadow': 'none',
        'background-color': '#fff',
      },
    },
  },
};
// Emits 定义
interface Emits {
  (e: 'update:userScrolled', value: boolean): void;
  (e: 'scroll'): void;
  (e: 'dataLoaded'): void;
}

// 响应式引用
const scrollContainerRef = ref<HTMLElement | null>(null);
const bubbleListRef = ref(null);
const showScrollToBottom = ref(false);

const messages = ref<any>([]);
// 转换消息格式以适应Bubble.List组件
const bubbleItems = computed<BubbleListProps['items']>(() => {
  // console.info('messages:', messages.value);
  return messages.value.map(({ id, message, role }: any) => {
    const processedContent = message;
    const roles = role === 'assistant' ? 'assistant' : 'user';
    return {
      key: id,
      loading: false,
      role: roles,
      content: processedContent,
    };
  });
});
const isLoading = ref<boolean>(false);
const loadChatMessages = async () => {
  const playload: any = {
    chat_id: props.chatMessageItem.chat_id,
    size: 6,
    start_message_id: props.chatMessageItem.id,
    filter_symbol: '<=' as const,
  };
  isLoading.value = true;
  const res = await getChatLogPaginatedApi(playload);
  const dataLen = res.items.length;
  // console.info('getChatLog:', res.items);
  const messagelist = res.items.map((msg, index) => {
    if (msg.role === 'user') {
      return {
        id: msg.id,
        message: h('div', { innerHTML: formatMessageContent(msg.content) }),
        role: msg.role,
      };
    } else {
      const isLast = dataLen === index + 1;
      if (msg.response_data) {
        const response_data = JSON.parse(msg.response_data);
        const assistantMessage = handleAssistantMessages(response_data, isLast);
        return {
          id: msg.id,
          message: assistantMessage,
          role: msg.role,
        };
      } else {
        return {};
      }
    }
  });
  // console.info('messagelist:', messagelist);
  isLoading.value = false;
  messages.value = messagelist;
  scrollToBottom();
  // 通知父组件数据加载完成
};

watch(
  props.chatMessageItem,
  (val) => {
    if (val) {
      loadChatMessages();
    }
  },
  {
    immediate: true,
  },
);

// 格式化消息内容
const formatMessageContent = (content: any): string => {
  if (!content) return '';

  // 如果是对象类型，尝试提取文本内容
  let textContent = content;
  if (typeof content === 'object' && content !== null) {
    // 如果有content属性
    if (content.content) {
      textContent = content.content;
    }
    // 如果有text属性
    else if (content.text) {
      textContent = content.text;
    }
    // 如果是VNode对象，尝试提取innerHTML
    else if (content.props && content.props.innerHTML) {
      return content.props.innerHTML;
    }
    // 其他情况，尝试转为JSON字符串
    else {
      try {
        textContent = JSON.stringify(content);
      } catch {
        textContent = String(content);
      }
    }
  }

  try {
    // 确保输入是字符串
    const stringContent = String(textContent);
    const html = marked.parse(stringContent, {
      breaks: true,
      gfm: true,
    });
    // 对生成的HTML进行二次处理，为表格添加滚动容器
    const processedHtml = processTableHtml(String(html));
    return DOMPurify.sanitize(processedHtml);
  } catch (error) {
    console.error('格式化消息内容失败:', error);
    return String(textContent);
  }
};
// 处理表格HTML，为表格添加滚动容器
const processTableHtml = (html: string): string => {
  // 使用正则表达式匹配表格
  const tableRegex = /<table[^>]*>[\s\S]*?<\/table>/gi;

  return html.replaceAll(tableRegex, (tableMatch) => {
    // 为每个表格添加包装div和唯一ID
    const tableId = `table-${Math.random().toString(36).slice(2, 11)}`;
    return `<div class="table-scroll-container" data-table-id="${tableId}">${tableMatch}</div>`;
  });
};

// 创建图标组件
const CheckCircleIcon = createIconifyIcon('ant-design:check-circle-outlined');
const InfoCircleIcon = createIconifyIcon('ant-design:info-circle-outlined');
const LoadingIcon = createIconifyIcon('ant-design:loading-outlined');
const ExclamationCircleIcon = createIconifyIcon('ant-design:exclamation-circle-outlined');

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'error': {
      return h(InfoCircleIcon);
    }
    case 'pending': {
      return h(LoadingIcon);
    }
    case 'success': {
      return h(CheckCircleIcon);
    }
    default: {
      return undefined;
    }
  }
};

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return ext;
}

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size}B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(2)}KB`;
  }
  if (size < 1024 * 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(2)}MB`;
  }
  if (size < 1024 * 1024 * 1024 * 1024) {
    return `${(size / 1024 / 1024 / 1024).toFixed(2)}GB`;
  }
  return `${(size / 1024 / 1024 / 1024 / 1024).toFixed(2)}TB`;
}
const HOST = import.meta.env.VITE_GLOB_API_URL;
const genFinalFileCard = (message: any, fileObj: { [x: string]: any }) => {
  const fileName = fileObj.url.split('/').pop();
  const fileType = getFileType(fileName);
  const fileUrl = HOST + fileObj.url;
  // console.info('genFinalFileCard-----------', fileUrl);
  const fileMessage = message;
  const filesize = fileObj.file_size;
  const bSize = formatFileSize(filesize);
  const getClickFun = (fileType: string) => {
    if (fileType === 'csv') {
      // return showCsvViewer
    }
    if (fileType === 'pdf') {
      // return showPdfViewer
    }
    if (fileType === 'md') {
      // return showMarkdownViewer
    }
    return () => {};
  };
  // 创建图标组件
  const FileExcelIcon = createIconifyIcon('ant-design:file-excel-outlined');
  const FilePdfIcon = createIconifyIcon('ant-design:file-pdf-outlined');
  const FileMarkdownIcon = createIconifyIcon('ant-design:file-markdown-outlined');
  const FileWordIcon = createIconifyIcon('ant-design:file-word-outlined');
  const FilePptIcon = createIconifyIcon('ant-design:file-ppt-outlined');
  const FileIcon = createIconifyIcon('ant-design:file-outlined');

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'csv': {
        return h(FileExcelIcon, { size: 24 });
      }
      case 'doc': {
        return h(FileWordIcon, { size: 24 });
      }
      case 'docx': {
        return h(FileWordIcon, { size: 24 });
      }
      case 'md': {
        return h(FileMarkdownIcon, { size: 24 });
      }
      case 'pdf': {
        return h(FilePdfIcon, { size: 24 });
      }
      case 'ppt': {
        return h(FilePptIcon, { size: 24 });
      }
      case 'xls': {
        return h(FileExcelIcon, { size: 24 });
      }
      case 'xlsx': {
        return h(FileExcelIcon, { size: 24 });
      }
      default: {
        return h(FileIcon, { size: 24 });
      }
    }
  };
  const func = getClickFun(fileType);
  const finalFileCard = h('div', { class: 'csv-document-card' }, [
    h('div', { class: 'file-card-header' }, fileMessage),
    h(
      'div',
      {
        class: 'file-card-content',
        onClick: () => func(),
      },
      [
        h('div', { class: `file-icon ${fileType}` }, [getFileIcon(fileType)]),
        h('div', { class: 'file-info' }, [
          h('div', { class: 'file-filename' }, fileName),
          h('div', { class: 'file-meta' }, bSize),
        ]),
        h('div', { class: 'file-action' }, [
          h('div', { class: 'view-icon' }, h(createIconifyIcon('ant-design:eye-outlined'))),
        ]),
      ],
    ),
  ]);

  return [finalFileCard, fileType, fileUrl];
};
// 处理消息列表中ai回答的message数据
const handleAssistantMessages = (response_data: Array<any>, isLast: boolean) => {
  let assistantMessage: any;
  // 思维过程信息
  const resultDatas: any[] = [];

  let markdownContent = '';
  let fullResponse = '';
  const steps: Array<{
    description: any;
    icon: any;
    key: string;
    status: 'error' | 'pending' | 'success';
    title: any;
  }> = reactive([]);
  const stepIndexRef = { value: 0 };

  for (const chunkData of response_data) {
    // 使用 switch 语句替代多个 if-else
    switch (chunkData.type) {
      case 'chat': {
        // 普通的chat类型对话
        fullResponse += chunkData.message;
        assistantMessage = h('div', {
          class: 'md-wrap',
          innerHTML: formatMessageContent(fullResponse),
        });
        break;
      }
      case 'error':
      case 'interrupted': {
        assistantMessage = handleErrorType(chunkData, steps, markdownContent);
        break;
      }
      case 'final': {
        assistantMessage = handleFinalType(chunkData, markdownContent, steps, isLast);
        break;
      }
      case 'log': {
        handleLogType(chunkData, resultDatas);
        break;
      }
      case 'md_info': {
        fullResponse += chunkData.message;
        // ai响应的markdown信息，开头信息一般是md_info
        markdownContent = fullResponse;
        // 检查是否已经有思维链，如果有则创建组合内容
        assistantMessage =
          steps.length > 0
            ? h('div', { class: 'combined-content' }, [
                // 显示markdown内容
                h('div', {
                  class: 'md-wrap',
                  innerHTML: formatMessageContent(fullResponse),
                }),
                // 显示思维链
                h(ThoughtChain, {
                  collapsible: true,
                  items: [...steps] as any,
                }),
              ])
            : h('div', {
                class: 'md-wrap',
                innerHTML: formatMessageContent(fullResponse),
              });
        break;
      }
      case 'step': {
        handleStepType(chunkData, steps, stepIndexRef, markdownContent);
        break;
      }
      default: {
        // 处理未知类型
        break;
      }
    }
  }

  // 思维过程信息处理
  const collapse = h(
    Collapse,
    {
      accordion: true,
      bordered: false,
      class: 'mt-2',
    },
    {
      default: () => [
        h(Collapse.Panel, { header: '展示思维过程', key: 'p1' }, { default: () => resultDatas }),
      ],
    },
  );
  assistantMessage = h('div', [assistantMessage, collapse]);

  return assistantMessage;
};

// 辅助方法：处理步骤类型
const handleStepType = (
  chunkData: any,
  steps: Array<any>,
  stepIndexRef: { value: number },
  markdownContent: string,
) => {
  switch (chunkData.type_name) {
    case 'completion': {
      return handleCompletionStep(chunkData, steps, stepIndexRef.value, markdownContent);
    }
    case 'execute': {
      return handleExecuteStep(chunkData, steps, stepIndexRef.value, markdownContent);
    }
    case 'success': {
      return handleSuccessStep(chunkData, steps, stepIndexRef.value, markdownContent);
    }
    case 'title': {
      // 添加初始思维链步骤
      stepIndexRef.value = steps.length;
      steps.push({
        description: h('div', ''),
        icon: getStatusIcon('pending'),
        key: `step_${stepIndexRef.value}`,
        status: 'pending' as const,
        title: chunkData.message,
      });

      return createCombinedContent(markdownContent, steps);
    }
    default: {
      break;
    }
  }
};

// 辅助方法：创建组合内容
const createCombinedContent = (markdownContent: string, steps: Array<any>) => {
  return h('div', { class: 'combined-content' }, [
    // 如果有markdown内容，先显示
    h('div', {
      class: 'md-wrap',
      innerHTML: formatMessageContent(markdownContent),
    }),
    // 然后显示思维链
    h(ThoughtChain, {
      collapsible: true,
      items: [...steps] as any,
    }),
  ]);
};

// 辅助方法：处理执行步骤
const handleExecuteStep = (
  chunkData: any,
  steps: Array<any>,
  currentStepIndex: number,
  markdownContent: string,
) => {
  const message = chunkData.message;
  const step = steps[currentStepIndex];
  if (!step) return;

  // execute-ele
  if (chunkData.file) {
    const fileUrl = HOST + chunkData.file.url;
    // 创建可点击的VNode
    const clickableMessage = h(
      'div',
      {
        class: 'execute-ele mb-2',
        onClick: () => {
          // showWorkSpace({ source: fileUrl }); // 注释掉未定义的函数
          console.warn('showWorkSpace function not implemented', fileUrl);
        },
      },
      message,
    );
    // 在现有VNode中添加新的子VNode
    const currentChildren = step.description.children || [];
    step.description = h(
      'div',
      [
        ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
        clickableMessage,
      ].filter(Boolean),
    );
  } else {
    // 在现有VNode中添加文本内容
    const currentChildren = step.description.children || [];
    step.description = h(
      'div',
      {
        style: {
          marginTop: '5px',
        },
      },
      [
        ...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]),
        h('div', { class: 'execute-ele-none mb-2' }, message),
      ].filter(Boolean),
    );
  }
  step.status = 'pending';
  step.icon = getStatusIcon('pending');

  return createCombinedContent(markdownContent, steps);
};

// 辅助方法：处理完成步骤
const handleCompletionStep = (
  chunkData: any,
  steps: Array<any>,
  currentStepIndex: number,
  markdownContent: string,
) => {
  const message = chunkData.message;
  const step = steps[currentStepIndex];
  if (!step) return;

  // 在现有VNode中添加文本内容
  const currentChildren = step.description.children || [];
  step.description = h(
    'div',
    [...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]), message].filter(
      Boolean,
    ),
  );
  step.status = 'pending';
  step.icon = getStatusIcon('pending');

  return createCombinedContent(markdownContent, steps);
};

// 辅助方法：处理成功步骤
const handleSuccessStep = (
  chunkData: any,
  steps: Array<any>,
  currentStepIndex: number,
  markdownContent: string,
) => {
  const message = chunkData.message;
  const step = steps[currentStepIndex];
  if (!step) return;

  // 在现有VNode中添加文本内容
  const currentChildren = step.description.children || [];
  step.description = h(
    'div',
    [...(Array.isArray(currentChildren) ? currentChildren : [currentChildren]), message].filter(
      Boolean,
    ),
  );
  step.status = 'success';
  step.icon = getStatusIcon('success');

  return h(
    'div',
    { class: 'combined-content' },
    [
      // 如果有markdown内容，先显示
      markdownContent
        ? h('div', {
            class: 'md-wrap',
            innerHTML: formatMessageContent(markdownContent),
          })
        : null,
      // 然后显示思维链
      h(ThoughtChain, {
        collapsible: true,
        items: [...steps] as any,
      }),
    ].filter(Boolean),
  );
};

// 辅助方法：处理最终结果
const handleFinalType = (
  chunkData: any,
  markdownContent: string,
  steps: Array<any>,
  isLast: boolean,
) => {
  if (chunkData.status === 'success') {
    const tagSuccess = h(
      Tag,
      { color: 'success' },
      {
        default: () => 'AI Assistant 已完成当前任务',
        icon: () => h(CheckCircleIcon),
      },
    );
    const tagWrap = h('div', [tagSuccess]);
    let finalFileCard: any = null;
    let fileType: string = '';
    let fileUrl: string = '';
    if (chunkData.file) {
      // 走后端API逻辑
      [finalFileCard, fileType, fileUrl] = genFinalFileCard(chunkData.message, chunkData.file);
    }
    const assistantMessage = h(
      'div',
      { class: 'combined-content' },
      [
        // 如果有markdown内容，先显示
        markdownContent
          ? h('div', {
              class: 'md-wrap',
              innerHTML: formatMessageContent(markdownContent),
            })
          : null,
        // 然后显示思维链
        h(ThoughtChain, {
          collapsible: true,
          items: [...steps] as any,
        }),
        finalFileCard || null,
        tagWrap,
      ].filter(Boolean),
    );
    // 自动打开对应的查看器
    if (isLast) {
      if (fileType === 'csv') {
        // showCsvViewer(fileUrl);
        console.warn('showCsvViewer function not implemented', fileUrl);
      }
      if (fileType === 'pdf') {
        // showPdfViewer(fileUrl);
        console.warn('showPdfViewer function not implemented', fileUrl);
      }
      if (fileType === 'md') {
        // showMarkdownViewer(fileUrl);
        console.warn('showMarkdownViewer function not implemented', fileUrl);
      }
    }
    return assistantMessage;
  }

  if (chunkData.status === 'error') {
    // 流式输出message
    let finalErrorMessages = '';
    finalErrorMessages += chunkData.message;
    return h(
      'div',
      { class: 'combined-content' },
      [
        // 如果有markdown内容，先显示
        markdownContent
          ? h('div', {
              class: 'md-wrap',
              innerHTML: formatMessageContent(markdownContent),
            })
          : null,
        // 然后显示思维链
        h(ThoughtChain, {
          collapsible: true,
          items: [...steps] as any,
        }),
        h('div', {
          class: 'md-wrap',
          innerHTML: formatMessageContent(finalErrorMessages),
        }),
      ].filter(Boolean),
    );
  }
};

// 辅助方法：处理错误类型
const handleErrorType = (chunkData: any, steps: Array<any>, markdownContent: string) => {
  if (steps.length > 0) {
    const lastStep = steps[steps.length - 1];
    if (lastStep && lastStep.status !== 'success') {
      lastStep.status = 'error';
      lastStep.icon = getStatusIcon('error');
    }
  }
  const tagWarning = h(
    Tag,
    { color: 'warning' },
    {
      default: () => chunkData.message,
      icon: () => h(ExclamationCircleIcon),
    },
  );
  const tagWrap = h('div', [tagWarning]);
  return h(
    'div',
    { class: 'combined-content' },
    [
      // 如果有markdown内容，先显示
      markdownContent
        ? h('div', {
            class: 'md-wrap',
            innerHTML: formatMessageContent(markdownContent),
          })
        : null,
      // 然后显示思维链
      steps.length > 0
        ? h(ThoughtChain, {
            collapsible: true,
            items: [...steps] as any,
          })
        : null,
      tagWrap,
    ].filter(Boolean),
  );
};

// 辅助方法：处理日志类型
const handleLogType = (chunkData: any, resultDatas: any[]) => {
  const name = chunkData.title;
  const content = chunkData.content;
  const output = Array.isArray(content)
    ? content
        .map((item) => {
          return item.content &&
            (Object.prototype.toString.call(item.content) === '[object Object]' ||
              Object.prototype.toString.call(item.content) === '[object Array]')
            ? `**${item.title}** \n ${JSON.stringify(item.content)}`
            : `**${item.title}** \n ${item.content}`;
        })
        .join('\n')
    : content;

  const collapse = h(
    Collapse,
    {
      accordion: true,
      bordered: false,
      class: 'mt-2',
    },
    {
      default: () => [
        h(
          Collapse.Panel,
          { header: name, key: 'p1' },
          {
            default: () =>
              h('div', {
                class: 'md-wrap thinking-process',
                innerHTML: formatMessageContent(output),
              }),
          },
        ),
      ],
    },
  );
  resultDatas.push(collapse);
};

// 滚动到底部
const scrollToBottom = async (force = false) => {
  emit('dataLoaded');

  // 如果是强制滚动（比如用户点击滚动到底部按钮），重置用户滚动状态
  if (force) {
    userScrolled.value = false;
    // console.info('user force scroll to bottom and set userScrolled false');
  }
};

// 检查是否需要显示滚动到底部按钮
const checkScrollPosition = () => {
  const scrollContainer = scrollContainerRef.value;
  if (!scrollContainer) return;

  const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px的容差
  showScrollToBottom.value = !isAtBottom;
  // 如果用户滚动到底部，重置用户滚动状态
  if (isAtBottom) {
    userScrolled.value = false;
    // console.info('isAtBottom set userScrolled false!');
  }
};

// 在组件挂载时初始化
onMounted(() => {});

// 组件卸载时清理
onUnmounted(() => {
  // 移除滚动监听器
});

// 暴露方法给父组件
defineExpose({
  checkScrollPosition,
});
</script>

<template>
  <!-- 消息滚动区域 -->
  <div class="scroll-wrap" :style="scrollContainerStyle" ref="scrollContainerRef">
    <!-- 内容居中容器 -->
    <div class="flex h-60 justify-center" v-if="isLoading">
      <ASpin :spinning="isLoading" class="mt-10" />
    </div>
    <!-- 🌟 消息列表 -->
    <Bubble.List ref="bubbleListRef" :items="bubbleItems" :roles="roles" :style="messageStyle" />
    <!-- 浮动滚动到底部按钮 -->
    <div
      v-if="showScrollToBottom"
      class="scroll-to-bottom-btn"
      @click="scrollToBottom(true)"
      title="滚动到底部"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M7 13l5 5 5-5" />
        <path d="M7 6l5 5 5-5" />
      </svg>
    </div>
  </div>
</template>

<style lang="scss" scoped>
/* 浮动滚动到底部按钮样式 */
.scroll-to-bottom-btn {
  position: absolute;
  bottom: 120px;
  left: 50%;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  color: white;
  cursor: pointer;
  background: rgb(40 40 40 / 70%);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgb(0 0 0 / 20%);
  transform: translateX(-50%);
  transition: all 0.3s ease;
}

.scroll-to-bottom-btn:hover {
  background: rgb(0 0 0 / 80%);
  box-shadow: 0 4px 12px rgb(0 0 0 / 30%);
  transform: translateX(-50%) scale(1.1);
}

.scroll-to-bottom-btn svg {
  transition: transform 0.2s ease;
}

.scroll-to-bottom-btn:hover svg {
  transform: translateY(2px);
}

:deep(.ant-design-x-vue-bubble-list) {
  /* 默认隐藏滚动条 */
  &::-webkit-scrollbar-thumb {
    background: transparent;
    transition: background 0.3s ease;

    /* 自定义滚动条长度 - 使用固定高度 */
  }

  /* 当容器悬浮时显示滚动条 */
  &:hover::-webkit-scrollbar-thumb {
    background: rgb(0 0 0 / 20%);
  }
}

.scroll-wrap {
  padding-bottom: 15px;
}

/** 用于控制markdown 内容生成后的间距  */
.scroll-wrap :deep(.ant-bubble-content ol) {
  padding-left: 25px;
}

.scroll-wrap :deep(.ant-bubble-content ul) {
  padding-left: 20px;
}

.scroll-wrap :deep(.ant-thought-chain-item-header) {
  margin-bottom: 0 !important;
}
</style>
<style lang="scss">
.combined-content .ant-tag {
  display: flex;
  align-items: center;
  width: fit-content;
}

.execute-ele {
  display: flex;
  width: fit-content;
  padding: 5px 15px;
  cursor: pointer;
  background-color: var(--bg-tertiary);
  border-radius: 15px;
}

.execute-ele-none {
  display: flex;
  width: fit-content;
  padding: 5px 15px;
  background-color: var(--bg-tertiary);
  border-radius: 15px;
}

/* 思维链和markdown内容组合样式 */
.combined-content {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .ant-thought-chain-item-desc {
    text-overflow: unset !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    white-space: pre-wrap !important;
  }

  .ant-thought-chain-item-icon {
    background-color: var(--bg-secondary) !important;
  }
}

/* 文档卡片样式 */
.csv-document-card {
  margin: 0 0 10px;
}

.file-card-header {
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.file-card-content {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.file-card-content:hover {
  background: var(--hover-bg);
  border-color: var(--border-color);
}

.file-icon {
  margin-right: 12px;
  font-size: 28px;

  &.md {
    color: #5375ff;
  }

  &.pdf {
    color: #b30000;
  }

  &.csv {
    color: #0bd900;
  }

  &.xls {
    color: #5375ff;
  }
}

.file-info {
  flex: 1;
}

.file-filename {
  margin-bottom: 4px;
  font-weight: 600;
  color: var(--text-primary);
}

.file-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.file-action {
  margin-left: 12px;
}

.view-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 14px;
  color: var(--primary-color);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 50%;
}

/* Markdown样式 */
.md-wrap {
  font-size: 14px;
  line-height: 1.6;
  line-height: 28px;
  color: var(--text-primary);
  word-spacing: 1px;

  ol,
  ul,
  menu {
    list-style: disc;
  }

  /* 表格滚动容器样式 */
  .table-scroll-container {
    max-height: 600px;

    /* 限制整个表格高度 */
    margin: 12px 0;
    overflow: auto;

    /* 横向滚动条在容器上 */
    border: 1px solid var(--border-light);
    border-radius: 4px;
  }

  /* 表格样式 */
  table {
    /* 原生表格布局，列宽随内容自适应 */
    display: table;
    display: block;
    width: max-content;

    /* 根据内容扩展，触发横向滚动 */

    margin: 0;

    /* 移除margin，由容器控制 */
    table-layout: auto;

    /* 列宽自适应内容 */
    border-collapse: collapse;

    tbody {
      box-sizing: content-box;

      /* 确保内边距不影响容器宽度计算 */
      padding-right: 12px;

      /* 预留纵向滚动条宽度（通常 12-16px） */
    }
  }

  /* Sticky 表头 */
  thead th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: #dfdfdf;
  }

  th,
  td {
    padding: 8px 12px;
    text-align: left;
    white-space: nowrap;

    /* 不换行，列宽随最长内容扩展 */
    border: 1px solid #f0f0f0;
  }

  th {
    position: sticky;
    font-weight: 600;
    white-space: nowrap;

    /* 头部不换行，利于根据内容自适应列宽 */
  }

  tr:nth-child(even) {
    background: var(--hover-bg);
  }
}
</style>
