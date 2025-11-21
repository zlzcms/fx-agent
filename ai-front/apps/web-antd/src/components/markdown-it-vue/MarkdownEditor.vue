<script setup lang="ts">
import type { DocumentConfigItem, MarkdownEditorEmits, MarkdownEditorProps } from './types';

import { computed, nextTick, onMounted, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { Button, Select } from 'ant-design-vue';
// @ts-ignore
import hljs from 'highlight.js';
// Import markdown-it and plugins
// @ts-ignore
import MarkdownIt from 'markdown-it';

import { DOCUMENT_TEMPLATE_KEYS, getDefaultTemplates } from './types';

// 导入代码高亮样式
import 'highlight.js/styles/github-dark.css';

// Props和Emits定义
const props = withDefaults(defineProps<MarkdownEditorProps>(), {
  placeholder: $t('page.components.markdownEditor.enterMarkdownContent'),
  height: '500px',
  readonly: false,
});

const emit = defineEmits<MarkdownEditorEmits>();

// 初始化 markdown-it - 完整配置
const md = new MarkdownIt({
  html: true, // 启用HTML标签
  xhtmlOut: true, // 使用 '/' 来闭合单标签 (<br />)
  breaks: true, // 将段落里的 '\n' 转换为 <br>
  linkify: true, // 将类似URL的文本自动转换为链接
  typographer: true, // 启用一些语言中性的替换 + 引号美化
  quotes: `""''`,
  // 代码高亮配置
  // @ts-ignore
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`;
      } catch {}
    }
    // @ts-ignore
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});

// 响应式数据
const textareaRef = ref<HTMLTextAreaElement>();
const previewRef = ref<HTMLDivElement>();
const viewMode = ref<'edit' | 'preview' | 'split'>('split');

// 本地配置数据
const localConfig = ref<DocumentConfigItem>({
  template: 'standard',
  content: '',
});

// 计算属性
const editorHeight = computed(() => {
  if (typeof props.height === 'number') {
    return `${props.height}px`;
  }
  return props.height;
});

// 动态生成模板选项
const documentTemplateOptions = computed(() => {
  return DOCUMENT_TEMPLATE_KEYS.map((option) => ({
    label: $t(option.labelKey),
    value: option.value,
  }));
});

// 动态生成默认模板内容
const defaultTemplates = computed(() => {
  // 默认使用英文模板，可以根据需要调整
  return getDefaultTemplates('en');
});

// 使用 markdown-it 渲染 Markdown 内容
const renderedMarkdown = computed(() => {
  // 确保content是字符串类型
  const content = typeof localConfig.value.content === 'string' ? localConfig.value.content : '';

  if (!content.trim()) {
    return `<div class="text-gray-400 text-center py-8">${$t('page.components.markdownEditor.noContent')}</div>`;
  }

  try {
    return md.render(content);
  } catch (error) {
    console.error($t('page.components.markdownEditor.renderError'), error);
    return `<div class="text-red-400 text-center py-8">${$t('page.components.markdownEditor.renderErrorMsg')}</div>`;
  }
});

// 监听props变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      // 确保content是字符串类型
      const safeValue = {
        template: newValue.template || 'standard',
        content: typeof newValue.content === 'string' ? newValue.content : '',
      };
      localConfig.value = { ...safeValue };
    }
  },
  { immediate: true, deep: true },
);

// 处理模板变化
function handleTemplateChange(template: any) {
  localConfig.value.template = template;

  // 确保content是字符串类型
  const currentContent =
    typeof localConfig.value.content === 'string' ? localConfig.value.content : '';

  // 如果内容为空或者是默认模板内容，则使用新模板的默认内容
  const trimmedContent = currentContent.trim();
  const isDefaultContent = Object.values(defaultTemplates.value).some(
    (tmpl) => tmpl.trim() === trimmedContent,
  );

  if (!trimmedContent || isDefaultContent) {
    localConfig.value.content =
      defaultTemplates.value[template as keyof typeof defaultTemplates.value] || '';
  }

  handleConfigChange();
}

// 处理配置变化
function handleConfigChange() {
  emit('update:modelValue', { ...localConfig.value });
  emit('change', { ...localConfig.value });
}

// 处理内容变化
function handleContentChange() {
  handleConfigChange();
}

// 处理编辑器滚动同步
function handleEditorScroll() {
  if (viewMode.value === 'split' && textareaRef.value && previewRef.value) {
    const textarea = textareaRef.value;
    const preview = previewRef.value;

    const scrollPercentage = textarea.scrollTop / (textarea.scrollHeight - textarea.clientHeight);
    const previewScrollTop = scrollPercentage * (preview.scrollHeight - preview.clientHeight);

    preview.scrollTop = previewScrollTop;
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 如果没有初始值或content不是字符串，使用默认模板
  if (!props.modelValue?.content || typeof props.modelValue.content !== 'string') {
    localConfig.value.content = defaultTemplates.value.standard;
    nextTick(() => {
      handleConfigChange();
    });
  }
});
</script>

<template>
  <div class="markdown-editor-wrapper">
    <div class="markdown-editor">
      <!-- 配置选项 -->
      <div class="editor-config mb-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- 文档模板选择 -->
          <div class="config-item">
            <div class="flex items-center">
              <label class="text-sm font-medium text-gray-700 mr-4 whitespace-nowrap">
                <span class="text-red-500">*</span
                >{{ $t('page.components.markdownEditor.documentTemplate') }}
              </label>
              <Select
                v-model:value="localConfig.template"
                :options="documentTemplateOptions"
                :placeholder="$t('page.components.markdownEditor.selectTemplate')"
                @change="handleTemplateChange"
                class="w-full"
                :required="true"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Markdown编辑器 -->
      <div class="editor-container">
        <div class="editor-header flex items-center justify-between p-3 bg-gray-50 border-b">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-medium text-gray-700">{{
              $t('page.components.markdownEditor.markdownEditor')
            }}</span>
            <div class="flex items-center space-x-2">
              <Button
                size="small"
                :type="viewMode === 'edit' ? 'primary' : 'default'"
                @click="viewMode = 'edit'"
              >
                {{ $t('page.components.markdownEditor.edit') }}
              </Button>
              <Button
                size="small"
                :type="viewMode === 'preview' ? 'primary' : 'default'"
                @click="viewMode = 'preview'"
              >
                {{ $t('page.components.markdownEditor.preview') }}
              </Button>
              <Button
                size="small"
                :type="viewMode === 'split' ? 'primary' : 'default'"
                @click="viewMode = 'split'"
              >
                {{ $t('page.components.markdownEditor.split') }}
              </Button>
            </div>
          </div>
          <div class="text-xs text-gray-500">
            {{ $t('page.components.markdownEditor.markdownSupport') }}
          </div>
        </div>

        <div class="editor-body" :style="{ height: editorHeight }">
          <!-- 编辑模式 -->
          <div v-if="viewMode === 'edit'" class="h-full">
            <textarea
              ref="textareaRef"
              v-model="localConfig.content"
              :placeholder="placeholder"
              class="w-full h-full p-4 border-0 resize-none focus:outline-none font-mono text-sm leading-relaxed"
              @input="handleContentChange"
              @scroll="handleEditorScroll"
            ></textarea>
          </div>

          <!-- 预览模式 -->
          <!-- eslint-disable vue/no-v-html -->
          <div v-else-if="viewMode === 'preview'" class="h-full overflow-auto">
            <div
              ref="previewRef"
              class="p-4 prose prose-sm max-w-none"
              v-html="renderedMarkdown"
            ></div>
          </div>
          <!-- eslint-enable vue/no-v-html -->

          <!-- 分屏模式 -->
          <div v-else class="h-full flex">
            <div class="flex-1 border-r">
              <textarea
                ref="textareaRef"
                v-model="localConfig.content"
                :placeholder="placeholder"
                class="w-full h-full p-4 border-0 resize-none focus:outline-none font-mono text-sm leading-relaxed"
                @input="handleContentChange"
                @scroll="handleEditorScroll"
              ></textarea>
            </div>
            <div class="flex-1 overflow-auto">
              <!-- eslint-disable vue/no-v-html -->
              <div
                ref="previewRef"
                class="p-4 prose prose-sm max-w-none"
                v-html="renderedMarkdown"
              ></div>
              <!-- eslint-enable vue/no-v-html -->
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 响应式设计 */
@media (max-width: 768px) {
  .editor-body .flex {
    @apply flex-col;
  }

  .editor-body .flex > div {
    @apply flex-none;

    height: 50%;
  }

  .editor-body .border-r {
    @apply border-r-0 border-b;
  }
}

.markdown-editor {
  @apply w-full;
}

.editor-container {
  @apply border border-gray-200 rounded-lg overflow-hidden;
}

.editor-body {
  @apply relative;
}

/* 编辑器样式 */
.editor-body textarea {
  font-family: Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace;
  line-height: 1.6;
  tab-size: 2;
}

.editor-body textarea:focus {
  @apply outline-none;
}

/* 预览区域样式 */
:deep(.prose) {
  @apply text-gray-800;
}

:deep(.prose h1) {
  @apply text-2xl font-bold text-gray-900 mt-6 mb-4 pb-2 border-b border-gray-200;
}

:deep(.prose h2) {
  @apply text-xl font-semibold text-gray-900 mt-5 mb-3;
}

:deep(.prose h3) {
  @apply text-lg font-medium text-gray-900 mt-4 mb-2;
}

:deep(.prose p) {
  @apply mb-3 leading-relaxed;
}

:deep(.prose ul, .prose ol) {
  @apply mb-3 pl-6;
}

:deep(.prose li) {
  @apply mb-1;
}

:deep(.prose blockquote) {
  @apply border-l-4 border-blue-200 pl-4 italic text-gray-600 my-4;
}

:deep(.prose code) {
  @apply bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-red-600;
}

:deep(.prose pre) {
  @apply bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4;
}

:deep(.prose pre code) {
  @apply bg-transparent text-gray-100 p-0;
}

:deep(.prose table) {
  @apply w-full border-collapse border border-gray-300 my-4;
}

:deep(.prose th, .prose td) {
  @apply border border-gray-300 px-3 py-2 text-left;
}

:deep(.prose th) {
  @apply bg-gray-50 font-semibold;
}

:deep(.prose a) {
  @apply text-blue-600 hover:text-blue-800 underline;
}

/* 代码高亮样式 */
:deep(.hljs) {
  @apply text-sm;

  color: #e2e8f0 !important;
  background: #2d3748 !important;
}

/* 表情符号样式 */
:deep(.emoji) {
  @apply inline-block text-lg;
}

/* 图片样式 */
:deep(.prose img) {
  @apply max-w-full h-auto rounded-lg shadow-sm;
}

/* 分割线样式 */
:deep(.prose hr) {
  @apply border-0 border-t border-gray-300 my-6;
}

/* 任务列表样式 */
:deep(.prose .task-list-item) {
  @apply list-none;
}

:deep(.prose .task-list-item input) {
  @apply mr-2;
}

/* 配置项样式 */
.config-item {
  @apply space-y-2;
}

.config-item label {
  @apply block text-sm font-medium text-gray-700;
}
</style>
