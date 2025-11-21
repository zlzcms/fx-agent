# 在 Monorepo 中使用 ai-action

本指南介绍如何在 `apps/web-antd` 中使用 `@maxpro/ai-action` 组件。

## 📦 安装依赖

### 1. 依赖已添加

在 `apps/web-antd/package.json` 中已经添加了依赖：

```json
{
  "dependencies": {
    "@maxpro/ai-action": "workspace:*"
  }
}
```

### 2. 安装依赖

在项目根目录运行：

```bash
pnpm install
```

## 🚀 使用方法

### 方式 1：局部引入（推荐）

在需要使用的 Vue 组件中：

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
  <div>
    <h1>示例页面</h1>

    <!-- 悬停模式 -->
    <AiAction :ai="aiConfig">
      <p>鼠标悬停在这段文字上会显示 AI 助手图标</p>
    </AiAction>

    <!-- 独立按钮模式 -->
    <AiAction :ai="aiConfig" />
  </div>
</template>
```

### 方式 2：全局注册

如果需要在多个页面使用，可以全局注册。

在 `apps/web-antd/src/main.ts` 中：

```typescript
import { createApp } from 'vue';
import App from './App.vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const app = createApp(App);

// 全局注册组件
app.component('AiAction', AiAction);

app.mount('#app');
```

然后在任何组件中直接使用：

```vue
<template>
  <AiAction :ai="{ token: 'xxx', askContent: '帮助', id: '1' }">
    <p>内容</p>
  </AiAction>
</template>
```

## 📚 完整示例

### 示例 1：在表格中使用

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const authToken = ref('your-auth-token');
const users = ref([
  { id: 1, name: 'Alice', email: 'alice@example.com', status: 'Active' },
  { id: 2, name: 'Bob', email: 'bob@example.com', status: 'Inactive' },
]);
</script>

<template>
  <a-table :dataSource="users" :columns="columns">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'name'">
        <AiAction
          :ai="{
            token: authToken,
            askContent: `分析用户 ${record.name} 的行为数据`,
            id: `user-${record.id}`,
          }"
        >
          {{ record.name }}
        </AiAction>
      </template>
    </template>
  </a-table>
</template>
```

### 示例 2：在工具栏中使用

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const authToken = ref('your-auth-token');
</script>

<template>
  <div class="toolbar">
    <a-button type="primary">保存</a-button>
    <a-button>导出</a-button>

    <!-- AI 助手按钮 -->
    <AiAction
      :ai="{
        token: authToken,
        askContent: '帮我总结当前页面的内容',
        id: 'toolbar-assistant',
      }"
    />
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  padding: 16px;
}
</style>
```

### 示例 3：自定义 AI 服务端点

```vue
<script setup lang="ts">
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const aiConfig = {
  token: 'your-token',
  askContent: '请帮我分析',
  id: 'custom-endpoint',
};
</script>

<template>
  <!-- 使用自定义 AI 服务 URL -->
  <AiAction :ai="aiConfig" base-url="https://your-custom-ai-service.com">
    <p>使用自定义 AI 端点</p>
  </AiAction>
</template>
```

### 示例 4：监听点击事件

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const clickCount = ref(0);
const aiConfig = ref({
  token: 'your-token',
  askContent: '初始问题',
  id: 'event-tracker',
});

function handleAiClick() {
  clickCount.value++;
  aiConfig.value.askContent = `问题 #${clickCount.value}`;
  console.log('AI 助手即将打开');
}
</script>

<template>
  <div>
    <p>点击次数: {{ clickCount }}</p>
    <AiAction :ai="aiConfig" @click="handleAiClick">
      <p>点击 AI 按钮</p>
    </AiAction>
  </div>
</template>
```

## 🎨 与 Ant Design Vue 集成

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';
import { message } from 'ant-design-vue';

const authToken = ref('your-token');

function handleAiOpen() {
  message.info('AI 助手已打开');
}
</script>

<template>
  <a-card title="用户信息">
    <a-descriptions>
      <a-descriptions-item label="用户名">
        <AiAction
          :ai="{
            token: authToken,
            askContent: '分析此用户的详细信息',
            id: 'user-detail',
          }"
          @click="handleAiOpen"
        >
          张三
        </AiAction>
      </a-descriptions-item>
      <a-descriptions-item label="邮箱"> zhangsan@example.com </a-descriptions-item>
    </a-descriptions>
  </a-card>
</template>
```

## 📝 Props 说明

| 属性        | 类型       | 默认值                           | 说明                             |
| ----------- | ---------- | -------------------------------- | -------------------------------- |
| `ai`        | `AIConfig` | **必填**                         | AI 配置对象                      |
| `baseUrl`   | `string`   | `'https://client.ai1center.com'` | AI 服务的基础 URL                |
| `size`      | `number`   | `26`                             | 浮动图标大小（悬停模式）         |
| `offset`    | `number`   | `4`                              | 浮动图标与内容的距离（悬停模式） |
| `ariaLabel` | `string`   | `'Ask AI'`                       | 无障碍标签                       |

### AIConfig 类型

```typescript
interface AIConfig {
  token: string | null; // 认证令牌
  askContent: string; // AI 提问内容
  id?: string | null; // 唯一标识符
}
```

## 🔧 TypeScript 支持

```typescript
import type { AiActionProps, AIConfig } from '@maxpro/ai-action';

const config: AIConfig = {
  token: 'your-token',
  askContent: '请分析',
  id: 'unique-id',
};
```

## 💡 最佳实践

1. **使用唯一 ID**：为每个 AI 助手实例提供唯一的 `id`，便于追踪和分析
2. **明确的上下文**：在 `askContent` 中提供清晰、具体的问题或上下文
3. **响应式设计**：移动端考虑使用独立按钮模式而不是悬停模式
4. **错误处理**：监听 `click` 事件进行日志记录和错误处理

## 🐛 故障排除

### 样式不生效

确保导入了 CSS 文件：

```typescript
import '@maxpro/ai-action/dist/ai-action.css';
```

### 组件未注册

确保已安装依赖：

```bash
pnpm install
```

### TypeScript 类型错误

确保 TypeScript 可以识别工作区依赖。如果有问题，可以在 `tsconfig.json` 中添加：

```json
{
  "compilerOptions": {
    "paths": {
      "@maxpro/ai-action": ["../packages/ai-action/src"]
    }
  }
}
```

## 📖 更多文档

- [完整 API 文档](./README.md)
- [中文文档](./README.zh-CN.md)
- [发布指南](./PUBLISH.md)

---

Happy coding! 🎉
