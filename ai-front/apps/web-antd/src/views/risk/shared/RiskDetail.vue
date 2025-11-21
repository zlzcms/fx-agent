<script setup lang="ts">
import { computed, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';
import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';
import { useAccessStore } from '@vben/stores';

import { Button as AButton, Divider as ADivider, Spin as ASpin, message } from 'ant-design-vue';
import hljs from 'highlight.js';
import MarkdownIt from 'markdown-it';

import { getRiskReportDetailApi } from '#/api/risk';

import 'highlight.js/styles/github.css';

// 定义Props类型
interface Props {
  customerId?: string;
}

// 定义Modal数据类型
interface ModalData {
  customerId?: string;
}

// 定义Props
const props = defineProps<Props>();

// 创建markdown实例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string) => {
    if (lang && hljs.getLanguage && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`;
      } catch {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});

// 响应式数据
const loading = ref(false);
const error = ref('');
const reportItem = ref<any>(null);
const customerId = ref(props.customerId || '');
const data = ref<ModalData | undefined>(undefined);

// Modal配置
const [Modal, modalApi] = useVbenModal({
  onCancel() {
    modalApi.close();
  },
  onOpenChange(isOpen: boolean) {
    if (isOpen) {
      data.value = modalApi.getData<ModalData>();
      handleDataChange(data.value);
    }
  },
});

// 获取风险报告详情
const fetchReportDetail = async (id: string): Promise<void> => {
  if (!id) {
    error.value = $t('invalidCustomerId');
    return;
  }

  loading.value = true;
  error.value = '';
  reportItem.value = null;

  try {
    const reportDetail = await getRiskReportDetailApi(Number(id));
    reportItem.value = reportDetail;

    // 设置modal标题包含客户信息
    modalApi?.setState?.({
      title: `${$t('customerDetailTitle')}${reportDetail.id ? ` - ID: ${reportDetail.id}` : ''}`,
    });
  } catch (error_) {
    const errorMessage = error_ instanceof Error ? error_.message : $t('fetchDetailError');
    error.value = errorMessage;
    message.error(errorMessage);
  } finally {
    loading.value = false;
  }
};

// 监听modal传递的数据
const handleDataChange = (data: ModalData | undefined): void => {
  if (data?.customerId && data.customerId !== customerId.value) {
    customerId.value = data.customerId;
    fetchReportDetail(data.customerId);
  }
};

// 渲染Markdown内容
const renderedMarkdown = computed((): string => {
  if (!reportItem.value?.report_document) return '';

  try {
    // 尝试解析为JSON，如果失败则直接作为Markdown字符串处理
    const reportDocument = JSON.parse(reportItem.value.report_document);
    return md.render(reportDocument);
  } catch {
    // 如果JSON解析失败，直接作为Markdown字符串处理
    return md.render(reportItem.value.report_document);
  }
});

// 计算字数
const wordCount = computed((): number => {
  if (!reportItem.value?.report_document) return 0;

  try {
    // 尝试解析为JSON，如果失败则直接计算字符串长度
    const reportDocument = JSON.parse(reportItem.value.report_document);
    return reportDocument.length || 0;
  } catch {
    // 如果JSON解析失败，直接计算字符串长度
    return reportItem.value.report_document.length || 0;
  }
});

// 导出HTML
const exportHtml = (): void => {
  if (!reportItem.value?.report_document) {
    message.warning($t('noDataToExport'));
    return;
  }

  const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${$t('riskReport')}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1, h2, h3 { color: #333; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f5f5f5; }
    pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; }
  </style>
</head>
<body>
  ${renderedMarkdown.value}
</body>
</html>`;

  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `risk-report-${customerId.value}.html`;
  a.click();
  URL.revokeObjectURL(url);
};

// 导出PDF
const exportPdf = (): void => {
  if (!reportItem.value?.report_pdf_url) {
    message.warning($t('pdfNotAvailable') || 'PDF文件尚未生成，请稍后再试');
    return;
  }

  try {
    // 获取 API base URL
    const apiBaseUrl = import.meta.env.VITE_GLOB_API_URL || '';

    // 构建完整的 PDF URL
    let pdfUrl = reportItem.value.report_pdf_url;

    // 如果是相对路径，拼接 base URL
    if (pdfUrl.startsWith('/')) {
      // 移除 base URL 末尾的斜杠（如果有）
      const baseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
      pdfUrl = `${baseUrl}${pdfUrl}`;
    }

    // 获取认证 token
    const accessStore = useAccessStore();
    const token = accessStore.accessToken;

    // 使用 fetch 下载文件，确保携带认证信息
    fetch(pdfUrl, {
      method: 'GET',
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
      })
      .then((blob) => {
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `risk-report-${customerId.value || reportItem.value.id || 'report'}.pdf`;
        document.body.append(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        message.success($t('downloadSuccess') || 'PDF下载成功');
      })
      .catch((error) => {
        console.error('PDF下载失败:', error);
        // 如果 fetch 失败，尝试直接打开链接（可能是不需要认证的静态文件）
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.target = '_blank';
        link.download = `risk-report-${customerId.value || reportItem.value.id || 'report'}.pdf`;
        link.click();
        message.warning($t('pdfDownloadWarning') || '正在尝试下载PDF，如遇问题请检查网络连接');
      });
  } catch (error) {
    console.error('导出PDF时发生错误:', error);
    message.error($t('pdfExportError') || '导出PDF失败，请稍后重试');
  }
};
</script>

<template>
  <Modal class="w-[1200px]" :title="$t('customerDetailTitle')">
    <!-- 头部操作栏 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center text-muted-foreground text-lg font-medium">
        <IconifyIcon icon="mdi:text" class="mr-2" />
        {{ $t('totalWords', { count: wordCount }) }}
      </div>
      <div class="flex gap-3">
        <AButton
          type="primary"
          ghost
          size="small"
          :disabled="!reportItem"
          @click="exportHtml"
          class="flex items-center"
        >
          <IconifyIcon icon="mdi:language-html5" class="mr-1" />
          <div>{{ $t('html') }}</div>
        </AButton>
        <AButton
          type="primary"
          ghost
          size="small"
          :disabled="!reportItem"
          @click="exportPdf"
          class="flex items-center"
        >
          <IconifyIcon icon="mdi:file-pdf-box" class="mr-1" />
          <div>{{ $t('pdf') }}</div>
        </AButton>
      </div>
    </div>

    <ADivider class="my-4" />

    <!-- 内容区域 -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- 加载状态 -->
      <div v-if="loading" class="flex-center flex-1 min-h-[300px]">
        <ASpin size="large">
          <template #tip>
            <div class="mt-3 text-muted-foreground text-sm">
              {{ $t('loadingReport') }}
            </div>
          </template>
        </ASpin>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="flex-center flex-1 min-h-[300px]">
        <div class="text-center max-w-md">
          <IconifyIcon icon="mdi:alert-circle-outline" class="text-5xl text-destructive mb-4" />
          <div class="text-lg font-semibold text-foreground mb-2">
            {{ $t('loadError') }}
          </div>
          <div class="text-muted-foreground mb-5 leading-relaxed">
            {{ error }}
          </div>
          <AButton type="primary" @click="fetchReportDetail(customerId)" class="flex items-center">
            <IconifyIcon icon="mdi:refresh" class="mr-1" />
            {{ $t('retry') }}
          </AButton>
        </div>
      </div>

      <!-- 报告内容 -->
      <!-- eslint-disable vue/no-v-html -->
      <div v-else-if="reportItem?.report_document" class="flex flex-col flex-1 overflow-hidden">
        <div
          class="flex-1 overflow-y-auto px-1 prose prose-sm max-w-none"
          v-html="renderedMarkdown"
        ></div>
      </div>
      <!-- eslint-enable vue/no-v-html -->

      <!-- 空状态 -->
      <div v-else class="flex-center flex-1 min-h-[300px]">
        <div class="text-center max-w-md">
          <IconifyIcon
            icon="mdi:file-document-outline"
            class="text-6xl text-muted-foreground/50 mb-4"
          />
          <div class="text-lg font-semibold text-foreground mb-2">
            {{ $t('noData') }}
          </div>
          <div class="text-muted-foreground leading-relaxed">
            {{ $t('noDataDescription') }}
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
/* Markdown 内容样式 */
.prose :deep(h1) {
  @apply text-2xl font-semibold mt-6 mb-4 text-foreground border-b border-border pb-2;
}

.prose :deep(h2) {
  @apply text-xl font-semibold mt-5 mb-3 text-foreground;
}

.prose :deep(h3) {
  @apply text-lg font-semibold mt-4 mb-2 text-foreground;
}

.prose :deep(p) {
  @apply my-2 text-muted-foreground leading-relaxed;
}

.prose :deep(ul),
.prose :deep(ol) {
  @apply my-2 pl-6;
}

.prose :deep(li) {
  @apply my-1 text-muted-foreground;
}

.prose :deep(blockquote) {
  @apply border-l-4 border-primary pl-4 my-4 bg-muted/50 p-3 rounded-r;
}

.prose :deep(code) {
  @apply bg-muted px-1 py-0.5 rounded text-sm font-mono;
}

.prose :deep(pre) {
  @apply bg-muted p-4 rounded-md overflow-x-auto my-4;
}

.prose :deep(pre code) {
  @apply bg-transparent p-0;
}

.prose :deep(table) {
  @apply border-collapse w-full my-4;
}

.prose :deep(th),
.prose :deep(td) {
  @apply border border-border px-3 py-2 text-left;
}

.prose :deep(th) {
  @apply bg-muted font-semibold;
}

.prose :deep(a) {
  @apply text-primary hover:text-primary/80 no-underline hover:underline;
}

.prose :deep(img) {
  @apply max-w-full h-auto rounded-md my-4;
}

.prose :deep(hr) {
  @apply border-0 border-t border-border my-6;
}

/* 滚动条样式 */
.prose::-webkit-scrollbar {
  @apply w-1.5;
}

.prose::-webkit-scrollbar-track {
  @apply bg-muted rounded;
}

.prose::-webkit-scrollbar-thumb {
  @apply bg-muted-foreground/30 rounded hover:bg-muted-foreground/50;
}
</style>
