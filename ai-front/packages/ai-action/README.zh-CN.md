# @maxpro/ai-action

<p align="center">
  <img src="https://img.shields.io/npm/v/@maxpro/ai-action" alt="npm version">
  <img src="https://img.shields.io/npm/dm/@maxpro/ai-action" alt="npm downloads">
  <img src="https://img.shields.io/npm/l/@maxpro/ai-action" alt="license">
  <img src="https://img.shields.io/badge/vue-3.x-brightgreen" alt="vue 3">
</p>

一个灵活的 Vue 3 AI 助手交互组件，支持悬停显示浮动按钮和可拖拽模态框。适用于为应用中的任何元素添加上下文 AI 帮助。

[English](./README.md) | 简体中文

## ✨ 功能特性

- 🎯 **双模式支持**：悬停模式（浮动按钮）或独立按钮模式
- 🎨 **极简 API**：根据插槽使用情况自动判断模式
- 🖱️ **可拖拽弹窗**：模态框支持拖拽移动
- 💾 **唯一标识**：支持通过 ID 追踪不同的 AI 助手实例
- 📱 **iframe 集成**：内置 iframe 展示 AI 助手界面
- ♿ **无障碍支持**：完整的 ARIA 标签支持
- 🎭 **TypeScript**：使用 TypeScript 编写，提供完整类型定义
- 🚀 **零配置**：开箱即用，提供合理的默认值

## 📦 安装

```bash
npm install @maxpro/ai-action
```

```bash
yarn add @maxpro/ai-action
```

```bash
pnpm add @maxpro/ai-action
```

## 🚀 快速开始

### 全局注册

```typescript
// main.ts
import { createApp } from 'vue';
import App from './App.vue';
import AiAction from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const app = createApp(App);
app.component('AiAction', AiAction);
app.mount('#app');
```

### 局部注册

```vue
<script setup lang="ts">
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const aiConfig = {
  token: 'your-auth-token',
  askContent: '请分析这段文本',
  id: 'text-analyzer',
};
</script>

<template>
  <AiAction :ai="aiConfig">
    <p>鼠标悬停在这段文字上会显示 AI 助手图标</p>
  </AiAction>
</template>
```

## 📖 使用方式

### 方式 1：悬停模式（提供插槽内容）

当提供插槽内容时，鼠标悬停会显示浮动的 AI 图标按钮：

```vue
<template>
  <AiAction :ai="aiConfig">
    <p>鼠标悬停在这段文字上会显示 AI 助手</p>
  </AiAction>
</template>

<script setup>
import { AiAction } from '@maxpro/ai-action';

const aiConfig = {
  token: 'your-auth-token',
  askContent: '请分析这段文本内容',
  id: 'text-analyzer-1',
};
</script>
```

**适用场景：**

- 文本段落分析
- 表格单元格快速操作
- 卡片内容智能解读
- 图片/文件识别

### 方式 2：独立按钮（不提供插槽内容）

当不提供插槽内容时，显示默认的 AI 助手按钮：

```vue
<template>
  <!-- 不提供插槽内容 = 独立按钮 -->
  <AiAction :ai="aiConfig" />
</template>

<script setup>
const aiConfig = {
  token: 'your-auth-token',
  askContent: '我需要 AI 帮助',
  id: 'standalone-assistant',
};
</script>
```

**适用场景：**

- 工具栏 AI 功能入口
- 页面右下角浮动助手
- 表单旁边的智能填充按钮

## 🎛️ API

### Props

| 属性        | 类型            | 默认值                           | 说明                                         |
| ----------- | --------------- | -------------------------------- | -------------------------------------------- |
| `ai`        | `AIConfig`      | **必填**                         | AI 配置对象（见下方说明）                    |
| `size`      | `number`        | `26`                             | 浮动图标大小（像素），仅悬停模式生效         |
| `offset`    | `number`        | `4`                              | 浮动图标与内容的距离（像素），仅悬停模式生效 |
| `iconClass` | `string`        | `''`                             | 浮动图标的额外 CSS 类，仅悬停模式生效        |
| `iconStyle` | `CSSProperties` | `{}`                             | 浮动图标的内联样式，仅悬停模式生效           |
| `zIndex`    | `number`        | `30`                             | 浮动图标的 z-index，仅悬停模式生效           |
| `ariaLabel` | `string`        | `'Ask AI'`                       | 无障碍标签                                   |
| `baseUrl`   | `string`        | `'https://client.ai1center.com'` | AI 助手 iframe 的基础 URL                    |

### AI 配置对象（AIConfig）

`ai` prop 是一个配置对象：

```typescript
interface AIConfig {
  // 必填：用户认证令牌
  token: string | null;

  // 必填：AI 助手的初始问题或上下文
  askContent: string;

  // 可选：唯一标识符，用于追踪
  id?: string | null;
}
```

| 字段         | 类型             | 必填 | 说明                      | 示例                         |
| ------------ | ---------------- | ---- | ------------------------- | ---------------------------- |
| `token`      | `string \| null` | ✅   | 用户认证令牌              | `'eyJhbGci...'`              |
| `askContent` | `string`         | ✅   | AI 助手的初始提问或上下文 | `'请分析这段代码的性能问题'` |
| `id`         | `string \| null` | ❌   | 唯一标识符，用于追踪实例  | `'code-reviewer-1'`          |

### 插槽

| 插槽名    | 说明                             | 示例                       |
| --------- | -------------------------------- | -------------------------- |
| `default` | 主内容（提供内容则触发悬停模式） | 文本、表格单元格、卡片内容 |
| `icon`    | 自定义浮动图标（仅悬停模式生效） | 自定义 SVG、图片           |

### 事件

| 事件名  | 参数 | 说明                               |
| ------- | ---- | ---------------------------------- |
| `click` | -    | 点击 AI 按钮时触发（在打开弹窗前） |

## 📚 示例

### 示例 1：表格中使用（悬停模式）

```vue
<template>
  <table>
    <tbody>
      <tr v-for="user in users" :key="user.id">
        <td>
          <AiAction
            :ai="{
              token: authToken,
              askContent: `分析用户 ${user.name} 的行为和活跃度`,
              id: `user-${user.id}`,
            }"
          >
            {{ user.name }}
          </AiAction>
        </td>
        <td>{{ user.email }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { AiAction } from '@maxpro/ai-action';

const authToken = 'your-token';
const users = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' },
];
</script>
```

### 示例 2：工具栏中使用（独立按钮）

```vue
<template>
  <div class="toolbar">
    <button>保存</button>
    <button>导出</button>

    <!-- AI 助手按钮 -->
    <AiAction
      :ai="{
        token: authToken,
        askContent: '帮我总结这份文档',
        id: 'toolbar-ai',
      }"
    />
  </div>
</template>
```

### 示例 3：自定义浮动图标

```vue
<template>
  <AiAction :ai="aiConfig" :size="32" :offset="8">
    <template #icon>
      <img src="/custom-ai-icon.png" alt="AI" />
    </template>

    <pre><code>{{ codeContent }}</code></pre>
  </AiAction>
</template>
```

### 示例 4：监听点击事件

```vue
<template>
  <AiAction :ai="aiConfig" @click="handleClick">
    <p>点击分析</p>
  </AiAction>
</template>

<script setup>
import { ref } from 'vue';

const aiConfig = ref({
  token: 'your-token',
  askContent: '初始问题',
  id: 'tracker',
});

function handleClick() {
  console.log('AI 助手即将打开');
  // 更新上下文或追踪分析
  aiConfig.value.askContent = '根据上下文更新的问题';
}
</script>
```

### 示例 5：自定义基础 URL

```vue
<template>
  <AiAction :ai="aiConfig" base-url="https://your-custom-ai.com">
    <p>自定义 AI 端点</p>
  </AiAction>
</template>
```

## 🎨 样式定制

### 自定义模态框样式

```vue
<style>
/* 自定义模态框标题栏 */
:deep(.ha-modal__header) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 自定义关闭按钮 */
:deep(.ha-modal__close) {
  color: white;
}

/* 自定义模态框尺寸 */
:deep(.ha-modal) {
  width: 400px;
  height: 700px;
}
</style>
```

## 🌟 最佳实践

### 1. 选择合适的模式

- **悬停模式**（提供插槽）：AI 作为内容的辅助功能
- **独立按钮**（不提供插槽）：AI 作为独立功能入口

### 2. 提供清晰的上下文

```vue
<!-- ❌ 不好：过于模糊 -->
<AiAction :ai="{ token, askContent: '分析' }">
  <p>内容</p>
</AiAction>

<!-- ✅ 好：具体明确 -->
<AiAction
  :ai="{
    token,
    askContent: '分析这段用户反馈的情感倾向和关键问题点',
    id: 'feedback-analyzer',
  }"
>
  <p>用户反馈内容...</p>
</AiAction>
```

### 3. 使用 ID 进行追踪（推荐）

```vue
<!-- ✅ 推荐：带 ID -->
<AiAction
  :ai="{
    token,
    askContent: '分析数据',
    id: 'user-data-analyzer',
  }"
>
  {{ userData }}
</AiAction>
```

### 4. 移动端响应式

```vue
<template>
  <!-- 桌面端：悬停模式 -->
  <AiAction v-if="!isMobile" :ai="aiConfig">
    <div>悬停分析</div>
  </AiAction>

  <!-- 移动端：独立按钮 -->
  <AiAction v-else :ai="aiConfig" />
</template>
```

## 📱 模态框功能

### 可拖拽模态框

模态框支持拖拽：

- 点击并按住标题栏
- 拖动到任意位置
- 自动限制在视窗范围内

### 默认尺寸

- 宽度：320px
- 高度：600px

## 🔧 TypeScript 支持

完整的 TypeScript 支持和类型导出：

```typescript
import type { AiActionProps, AIConfig } from '@maxpro/ai-action';

const config: AIConfig = {
  token: 'token',
  askContent: 'question',
  id: 'unique-id',
};
```

## 🌐 浏览器兼容性

- ✅ Chrome/Edge (最新版)
- ✅ Firefox (最新版)
- ✅ Safari (最新版)
- ❌ IE11 (不支持)

## 📄 开源协议

MIT License - 详见 [LICENSE](./LICENSE)

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📮 支持

- 📧 邮箱：support@ai1center.com
- 🐛 问题反馈：[GitHub Issues](https://github.com/your-org/ai-action/issues)
- 📖 文档：[完整文档](https://github.com/your-org/ai-action#readme)

## 🙏 致谢

由 MaxPro 团队用 ❤️ 构建

---

**关键词**：vue3, ai, 助手, 悬停, 操作, 组件, 可拖拽, 模态框, typescript
