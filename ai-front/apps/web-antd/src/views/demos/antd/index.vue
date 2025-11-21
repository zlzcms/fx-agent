<script lang="ts" setup>
import { computed, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';

import { AiAction } from '@maxpro/ai-action';
import { marked } from 'marked';

// Simple readme content without complex markdown
const readmeContent = `
# AiAction 组件使用说明

## 概述

AiAction 是一个 Vue 3 AI 助手交互组件，已发布到 monorepo 的 packages 目录下。

**npm 包名**: @maxpro/ai-action

支持两种使用方式：
- **悬停模式**（提供插槽内容）：鼠标悬停时显示浮动的 AI 助手图标
- **独立按钮**（不提供插槽）：显示一个默认的 AI 助手按钮

点击后会打开一个可拖拽的模态框，展示 AI 助手的 iframe 界面。

## 功能特性

- 🎯 两种使用方式：悬停模式 或 独立按钮
- 🎨 极简 API：根据是否有插槽内容自动判断模式
- 🖱️ 可拖拽模态框：支持拖拽移动，自由调整位置
- 💾 唯一标识：支持通过 id 区分不同的 AI 助手实例
- 🎨 自定义样式：支持自定义图标大小、位置、样式等
- 📱 响应式设计：模态框位置自动限制在视窗范围内
- ♿ 无障碍支持：提供 ARIA 标签和键盘导航支持
- 🔧 可配置 URL：支持自定义 AI 服务端点
- 🎭 TypeScript：完整的类型定义支持

## 安装

在 monorepo 中，已在 apps/web-antd/package.json 添加依赖：
"dependencies": { "@maxpro/ai-action": "workspace:*" }

运行 pnpm install 安装依赖。

## AI 配置对象（重要）

ai 参数是一个配置对象，包含以下字段：

interface AIConfig {
  token: string | null;      // 必填：用户认证令牌
  askContent: string;        // 必填：AI 助手的初始问题或上下文
  id?: string | null;        // 可选：唯一标识符（强烈推荐）
  locale?: string;           // 可选：语言设置，支持 'zh' | 'en'，默认为 'zh'
}

查看下方示例了解如何使用。

## Props 属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| ai | AIConfig | 必填 | AI 配置对象，详见上方说明 |
| baseUrl | string | '' | AI 服务的基础 URL |
| size | number | 26 | 浮动图标大小（像素），仅悬停模式生效 |
| offset | number | 4 | 浮动图标与内容的距离（像素），仅悬停模式生效 |
| iconClass | string | '' | 浮动图标的额外 CSS 类名 |
| iconStyle | CSSProperties | {} | 浮动图标的内联样式 |
| zIndex | number | 30 | 浮动图标的 z-index 层级 |
| ariaLabel | string | 'Ask AI' | 无障碍标签 |

**AIConfig.locale 参数说明：**
- **locale**: 可选，字符串类型，支持 'zh'（中文）或 'en'（英文）
- 默认值为 'zh'，如果不提供则使用默认值
- 该参数会传递给 iframe 中的 AI 助手界面，控制界面显示的语言

## 事件

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| click | 点击 AI 按钮时触发（在打开弹窗前） | 无 |

## 插槽

| 插槽名 | 说明 |
|--------|------|
| default | 默认插槽。有内容=悬停模式，无内容=独立按钮 |
| icon | 自定义浮动按钮图标（仅悬停模式生效） |

## 注意事项

1. **AI 配置**: token 和 askContent 是必填的，id 强烈推荐提供
2. **askContent**: 应提供清晰具体的问题或上下文，避免过于模糊
3. **id 字段**: 便于日志追踪、数据分析和区分不同场景
4. **iframe 安全**: 组件使用 iframe 加载 AI 服务，确保 token 安全
5. **性能考虑**: 模态框使用 Teleport 渲染到 body
6. **拖拽限制**: 模态框拖拽时会自动限制在视窗范围内
`;

// Script embedding content
const scriptEmbedContent = `
除了在 Vue 组件中使用外，还可以通过脚本嵌入的方式在任何网页中使用 AI 助手功能。

## 快速开始

将以下代码添加到网页的 \`<body>\` 标签末尾，即可在页面中显示 AI 助手浮动按钮。

## 配置说明

### 基础配置（必填）
- **token**: 用户认证令牌（必填）
- **baseUrl**: AI 服务的基础 URL（必填）

### 按钮样式配置
- **position**: 按钮位置，可选 \`'right'\`（右侧）或 \`'left'\`（左侧）
- **buttonColor**: 按钮背景颜色，支持任何 CSS 颜色值
- **buttonSize**: 按钮尺寸（像素），默认 56px
- **buttonBottom**: 按钮距离底部的距离（像素）
- **buttonSide**: 按钮距离侧边的距离（像素）

### 面板配置
- **panelWidth**: 聊天面板宽度（像素），仅桌面端生效，移动端自动全屏
- **panelHeightVh**: 聊天面板高度（视口高度百分比），如 80 表示占 80% 视口高度

### 高级配置
- **zIndex**: 浮窗层级，默认值很大以确保显示在最上层
- **id**: 唯一标识符，用于区分不同的 AI 助手实例
- **locale**: 语言设置，支持 'zh'（中文）或 'en'（英文），默认为 'zh'

## 完整示例代码
`;

// Script code to display - properly escaped
const scriptCode = `&lt;script&gt;
  window.AiassistantChatbotConfig = {
    // 基础配置
    token: '',                      // 用户认证令牌
    baseUrl: 'https://client.ai1center.com', // API 基础 URL

    // 按钮位置和样式
    position: 'right',              // 按钮位置: 'right' | 'left'
    buttonColor: '#1C64F2',         // 按钮颜色 (HEX/RGB/RGBA)
    buttonSize: 56,                 // 按钮尺寸 (px)
    buttonBottom: 20,               // 距离底部距离 (px)
    buttonSide: 20,                 // 距离侧边距离 (px)

    // 聊天面板配置
    panelWidth: 480,                // 面板宽度 (px，桌面端)
    panelHeightVh: 80,              // 面板高度 (vh，占视口百分比)

    // 高级配置
    zIndex: 2147483000,             // 层级 (确保浮窗在最上层)
    id: 'assistant-embed',           // 唯一标识符
    locale: 'zh',                    // 语言设置：'zh'（中文）或 'en'（英文），默认为 'zh' ，支持 zh_xx,zh-xx,en-xx,en_xx
  }
&lt;/script&gt;
&lt;script
  src="https://client.ai1center.com/embed.min.js"
  defer&gt;
&lt;/script&gt;`;

const accessStore = useAccessStore();
// Convert markdown to HTML
const readmeHtml = computed(() => {
  return marked.parse(readmeContent);
});

const scriptEmbedHtml = computed(() => {
  return marked.parse(scriptEmbedContent);
});
const locale = preferences.app.locale || 'zh';

// Demo configurations
const aiConfig = ref({
  token: accessStore.accessToken || 'null',
  askContent: '请帮我分析这段代码的性能瓶颈和优化建议',
  id: 'basic-demo',
  locale,
});

const customAiConfig = ref({
  token: accessStore.accessToken || 'null',
  askContent: '分析这个用户界面设计的可用性和视觉效果，提供改进建议',
  id: 'custom-style-demo',
  locale,
});

const dynamicContent = ref('这是动态内容，将作为AI分析的上下文');
const dynamicAiConfig = computed(() => ({
  token: accessStore.accessToken || 'null',
  askContent: `请详细分析以下内容的含义和潜在问题：\n\n${dynamicContent.value}`,
  id: `dynamic-demo-${Date.now()}`,
  locale,
}));

// 独立按钮示例配置
const standaloneAiConfig = ref({
  token: accessStore.accessToken || 'null',
  askContent: '我需要 AI 助手帮我解决问题',
  id: 'standalone-assistant',
  locale,
});

const handleClick = () => {
  // AI 助手被点击
};

const handleDynamicClick = () => {
  // 动态AI助手被点击
};

// Tab management
const activeTab = ref('component');

const setActiveTab = (tab: string) => {
  activeTab.value = tab;
};

// Code examples for display
const example1Code =
  `<` +
  `script setup>
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const aiConfig = {
  token: 'test-token-12345',
  askContent: '请帮我分析这段代码的性能瓶颈和优化建议',
  id: 'basic-demo',
  locale: 'zh'  // 可选：'zh' | 'en'，默认为 'zh'
};

const handleClick = () => {
  console.log('AI assistant opened');
};
<` +
  `/script>

<` +
  `template>
  <AiAction :ai="aiConfig" base-url="https://client.ai1center.com" @click="handleClick">
    <div class="p-4 bg-blue-100 rounded">
      <div class="font-semibold">鼠标悬停在这里</div>
      <div class="text-sm text-gray-600 mt-1">会显示 AI 助手图标</div>
    </div>
  </AiAction>
<` +
  `/template>`;

const example2Code =
  `<` +
  `script setup>
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const standaloneAiConfig = {
  token: 'standalone-token-xyz',
  askContent: '我需要 AI 助手帮我解决问题',
  id: 'standalone-assistant',
  locale: 'zh'  // 可选：'zh' | 'en'，默认为 'zh'
};
<` +
  `/script>

<` +
  `template>
  <div class="toolbar">
    <button class="px-4 py-2 bg-gray-200 rounded">保存</button>
    <button class="px-4 py-2 bg-gray-200 rounded">导出</button>
    <!-- 不提供插槽内容 = 独立按钮模式 -->
    <AiAction :ai="standaloneAiConfig" base-url="https://client.ai1center.com" />
  </div>
<` +
  `/template>`;

const example3Code =
  `<` +
  `script setup>
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const customAiConfig = {
  token: 'custom-token-67890',
  askContent: '分析这个用户界面设计的可用性和视觉效果',
  id: 'custom-style-demo',
  locale: 'zh'  // 可选：'zh' | 'en'，默认为 'zh'
};
<` +
  `/script>

<` +
  `template>
  <AiAction
    :ai="customAiConfig"
    base-url="https://client.ai1center.com"
    :size="32"
    :offset="8"
    icon-class="custom-ai-icon"
    :icon-style="{ backgroundColor: '#1890ff', color: 'white' }"
    :z-index="9999"
    aria-label="自定义样式的 AI 助手"
  >
    <div class="p-4 bg-green-100 rounded">
      <div class="font-semibold">自定义样式示例</div>
      <div class="text-sm text-gray-600 mt-1">图标更大、偏移更多、自定义颜色</div>
    </div>
  </AiAction>
<` +
  `/template>

<` +
  `style scoped>
.custom-ai-icon {
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}
<` +
  `/style>`;

const example4Code =
  `<` +
  `script setup>
import { computed, ref } from 'vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const dynamicContent = ref('这是动态内容，将作为AI分析的上下文');

// 使用 computed 动态生成配置
const dynamicAiConfig = computed(() => ({
  token: 'dynamic-token-abcde',
  askContent: \`请详细分析以下内容的含义和潜在问题：\\n\\n\${dynamicContent.value}\`,
  id: \`dynamic-demo-\${Date.now()}\`,
  locale: 'zh'  // 可选：'zh' | 'en'，默认为 'zh'
}));

const handleDynamicClick = () => {
  console.log('Dynamic AI clicked with content:', dynamicContent.value);
};
<` +
  `/script>

<` +
  `template>
  <div>
    <textarea
      v-model="dynamicContent"
      class="w-full p-2 border rounded"
      rows="3"
      placeholder="输入一些文本让 AI 分析..."
    />

    <AiAction :ai="dynamicAiConfig" base-url="https://client.ai1center.com" @click="handleDynamicClick">
      <div class="p-4 bg-purple-100 rounded">
        <div class="font-semibold">悬停查看 AI 分析</div>
        <div class="text-sm text-gray-600 mt-1">AI 会分析上面输入框的内容</div>
      </div>
    </AiAction>
  </div>
<` +
  `/template>`;

const showCode = ref<Record<string, boolean>>({
  example1: true,
  example2: true,
  example3: true,
  example4: true,
});

const toggleCode = (example: string) => {
  showCode.value[example] = !showCode.value[example];
};
</script>

<template>
  <Page title="AI Assistant Client " description="展示 AI Assistant Client 嵌入使用方法">
    <div class="mb-6 p-4 bg-white rounded-lg shadow">
      <h2 class="text-xl font-bold mb-4">使用方式</h2>
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8">
          <button
            @click="setActiveTab('component')"
            class="py-4 px-1 text-sm font-medium border-b-2"
            :class="
              activeTab === 'component'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            "
          >
            组件方式
          </button>
          <button
            @click="setActiveTab('script')"
            class="py-4 px-1 text-sm font-medium border-b-2"
            :class="
              activeTab === 'script'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            "
          >
            脚本嵌入
          </button>
        </nav>
      </div>

      <div v-if="activeTab === 'component'" class="pt-4">
        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <h2 class="text-xl font-bold mb-4">组件介绍</h2>
          <div class="prose max-w-none" v-html="readmeHtml"></div>
        </div>

        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">示例 1：悬停模式（基础用法）</h2>
            <button
              @click="toggleCode('example1')"
              class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              {{ showCode.example1 ? '隐藏代码' : '查看代码' }}
            </button>
          </div>
          <p class="text-gray-600 mb-3 text-sm">提供插槽内容，鼠标悬停时显示浮动的 AI 助手图标</p>

          <!-- 源码展示 -->
          <div
            v-if="showCode.example1"
            class="mb-4 bg-gray-900 text-white p-4 rounded-lg overflow-x-auto"
          >
            <pre class="text-sm"><code>{{ example1Code }}</code></pre>
          </div>

          <!-- 效果展示 -->
          <div class="flex flex-wrap gap-4">
            <AiAction :ai="aiConfig" base-url="https://client.ai1center.com" @click="handleClick">
              <div class="p-4 bg-blue-100 rounded">
                <div class="font-semibold">鼠标悬停在这里</div>
                <div class="text-sm text-gray-600 mt-1">会显示 AI 助手图标</div>
              </div>
            </AiAction>
          </div>
          <div class="mt-3 text-xs text-gray-500 bg-gray-50 p-3 rounded">
            <strong>配置：</strong> token: "test-token-12345", askContent:
            "请帮我分析这段代码的性能瓶颈和优化建议", id: "basic-demo", locale: "zh"
          </div>
        </div>

        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">示例 2：独立按钮模式</h2>
            <button
              @click="toggleCode('example2')"
              class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              {{ showCode.example2 ? '隐藏代码' : '查看代码' }}
            </button>
          </div>
          <p class="text-gray-600 mb-3 text-sm">不提供插槽内容，显示默认的 AI 助手按钮</p>

          <!-- 源码展示 -->
          <div
            v-if="showCode.example2"
            class="mb-4 bg-gray-900 text-white p-4 rounded-lg overflow-x-auto"
          >
            <pre class="text-sm"><code>{{ example2Code }}</code></pre>
          </div>

          <!-- 效果展示 -->
          <div class="flex flex-wrap gap-4 items-center">
            <span class="text-gray-600">工具栏示例：</span>
            <button class="px-4 py-2 bg-gray-200 rounded">保存</button>
            <button class="px-4 py-2 bg-gray-200 rounded">导出</button>
            <AiAction :ai="standaloneAiConfig" base-url="https://client.ai1center.com" />
          </div>
          <div class="mt-3 text-xs text-gray-500 bg-gray-50 p-3 rounded">
            <strong>配置：</strong> token: "standalone-token-xyz", askContent: "我需要 AI
            助手帮我解决问题", id: "standalone-assistant", locale: "zh"
          </div>
        </div>

        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">示例 3：自定义样式</h2>
            <button
              @click="toggleCode('example3')"
              class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              {{ showCode.example3 ? '隐藏代码' : '查看代码' }}
            </button>
          </div>
          <p class="text-gray-600 mb-3 text-sm">
            自定义浮动图标的大小、偏移和样式（仅悬停模式生效）
          </p>

          <!-- 源码展示 -->
          <div
            v-if="showCode.example3"
            class="mb-4 bg-gray-900 text-white p-4 rounded-lg overflow-x-auto"
          >
            <pre class="text-sm"><code>{{ example3Code }}</code></pre>
          </div>

          <!-- 效果展示 -->
          <div class="flex flex-wrap gap-4">
            <AiAction
              :ai="customAiConfig"
              base-url="https://client.ai1center.com"
              :size="32"
              :offset="8"
              icon-class="custom-ai-icon"
              :icon-style="{ backgroundColor: '#1890ff', color: 'white' }"
              :z-index="9999"
              aria-label="自定义样式的 AI 助手"
              @click="handleClick"
            >
              <div class="p-4 bg-green-100 rounded">
                <div class="font-semibold">自定义样式示例</div>
                <div class="text-sm text-gray-600 mt-1">图标更大、偏移更多、自定义颜色</div>
              </div>
            </AiAction>
          </div>
          <div class="mt-3 text-xs text-gray-500 bg-gray-50 p-3 rounded">
            <strong>配置：</strong> size: 32, offset: 8, iconStyle: { backgroundColor: '#1890ff' },
            id: "custom-style-demo", locale: "zh"
          </div>
        </div>

        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">示例 4：动态配置（推荐）</h2>
            <button
              @click="toggleCode('example4')"
              class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              {{ showCode.example4 ? '隐藏代码' : '查看代码' }}
            </button>
          </div>
          <p class="text-gray-600 mb-3 text-sm">
            使用 computed 动态生成 AI 配置，askContent 会根据输入内容实时更新
          </p>

          <!-- 源码展示 -->
          <div
            v-if="showCode.example4"
            class="mb-4 bg-gray-900 text-white p-4 rounded-lg overflow-x-auto"
          >
            <pre class="text-sm"><code>{{ example4Code }}</code></pre>
          </div>

          <!-- 效果展示 -->
          <div class="mb-4">
            <label class="block mb-2 font-medium">编辑要分析的内容:</label>
            <textarea
              v-model="dynamicContent"
              class="w-full p-2 border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              rows="3"
              placeholder="输入一些文本让 AI 分析..."
            ></textarea>
          </div>
          <div class="flex flex-wrap gap-4">
            <AiAction
              :ai="dynamicAiConfig"
              base-url="https://client.ai1center.com"
              @click="handleDynamicClick"
            >
              <div class="p-4 bg-purple-100 rounded">
                <div class="font-semibold">悬停查看 AI 分析</div>
                <div class="text-sm text-gray-600 mt-1">AI 会分析上面输入框的内容</div>
              </div>
            </AiAction>
          </div>
          <div class="mt-3 text-xs text-gray-500 bg-gray-50 p-3 rounded">
            <strong>动态 ID：</strong> "dynamic-demo-{timestamp}" - 每次更新都会生成新的 ID
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'script'" class="pt-4">
        <div class="mb-6 p-4 bg-white rounded-lg shadow">
          <h2 class="text-xl font-bold mb-4">脚本嵌入方式</h2>
          <div class="prose max-w-none" v-html="scriptEmbedHtml"></div>
          <div class="bg-gray-800 text-white p-4 rounded-lg mt-4">
            <pre><code v-html="scriptCode"></code></pre>
          </div>
        </div>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.custom-ai-icon {
  border-radius: 50%;
  box-shadow: 0 2px 8px rgb(24 144 255 / 30%);
}

/* Markdown styles */
:deep(.prose) {
  color: #374151;
}

:deep(.prose h2) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

:deep(.prose h3) {
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

:deep(.prose p) {
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  line-height: 1.75;
}

:deep(.prose ul) {
  padding-left: 1.5rem;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

:deep(.prose li) {
  margin-bottom: 0.25rem;
}

:deep(.prose code) {
  padding: 0.2em 0.4em;
  font-family:
    ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
  font-size: 0.875em;
  background-color: #f3f4f6;
  border-radius: 0.25rem;
}

:deep(.prose pre) {
  padding: 1rem;
  margin-top: 1rem;
  margin-bottom: 1rem;
  overflow-x: auto;
  background-color: #f3f4f6;
  border-radius: 0.5rem;
}

:deep(.prose pre code) {
  padding: 0;
  background-color: transparent;
}

:deep(.prose table) {
  width: 100%;
  margin-top: 1rem;
  margin-bottom: 1rem;
  border-collapse: collapse;
}

:deep(.prose th) {
  padding: 0.5rem;
  text-align: left;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
}

:deep(.prose td) {
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
}

:deep(.prose blockquote) {
  padding-left: 1rem;
  margin-top: 1rem;
  margin-bottom: 1rem;
  margin-left: 0;
  color: #6b7280;
  border-left: 4px solid #e5e7eb;
}
</style>
