<script setup lang="ts">
import type { ReportData } from './types';

import { onMounted, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';

import { Button as AButton, Card as ACard, Divider as ADivider } from 'ant-design-vue';
import MarkdownIt from 'markdown-it';

const props = defineProps<{
  report: ReportData;
}>();

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});
const reportDocument = ref<string>('');

const renderMarkdown = (content: string) => {
  if (!content) {
    return '<div class="text-gray-400 text-center py-8">暂无文档内容</div>';
  }
  return md.render(content);
};
const contentType = ref<string>('html');
const handleType = (type: string) => {
  contentType.value = type;
  // if(type === 'html') {
  //   reportDocument.value = props.report.report_result;
  // } else if(type === 'pdf') {
  //   reportDocument.value = props.report.report_result;
  // } else if(type === 'prompt') {
  //   reportDocument.value = props.report.ai_response
  // }
};

onMounted(() => {
  reportDocument.value =
    props.report.ai_response && props.report.ai_response.output
      ? props.report.ai_response.output
      : props.report.report_document || '';
});
</script>

<template>
  <div class="h-full flex flex-col">
    <ACard class="h-full flex flex-col">
      <div class="flex items-center justify-between mb-4">
        <div class="text-sm text-gray-500">共 {{ reportDocument.length }} 字</div>
        <div class="flex gap-2">
          <AButton size="small" @click="handleType('html')">
            <IconifyIcon icon="mdi:language-html5" class="mr-1" />
            <span>HTML</span>
          </AButton>
          <AButton size="small" @click="handleType('pdf')">
            <IconifyIcon icon="mdi:file-pdf-box" class="mr-1" />
            <span>PDF</span>
          </AButton>
        </div>
      </div>
      <ADivider class="my-3" />
      <div class="markdown-container flex-1">
        <div v-html="renderMarkdown(reportDocument)" class="markdown-body"></div>
      </div>
    </ACard>
  </div>
</template>

<style scoped>
.markdown-container {
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}

:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #24292e;
}

:deep(.ant-card-body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

:deep(.markdown-body h1) {
  padding-bottom: 0.3em;
  margin: 0.67em 0;
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-body h2) {
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-body h3) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-size: 1.25em;
}

:deep(.markdown-body code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgb(27 31 35 / 5%);
  border-radius: 3px;
}

:deep(.markdown-body pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}

:deep(.markdown-body blockquote) {
  padding: 0 1em;
  margin-left: 0;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
}

:deep(.markdown-body table) {
  width: 100%;
  margin-bottom: 16px;
  overflow: auto;
  border-collapse: collapse;
}

:deep(.markdown-body table th) {
  padding: 6px 13px;
  font-weight: 600;
  background-color: #f6f8fa;
  border: 1px solid #dfe2e5;
}

:deep(.markdown-body table td) {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}
</style>
