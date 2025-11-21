# HoverAction 组件使用文档

HoverAction 是一个灵活的 AI 助手交互组件，支持两种使用方式：带插槽内容（悬停模式）和不带插槽（默认按钮）。

## 功能特性

- 🎯 **两种使用方式**：悬停显示浮动按钮 或 独立按钮
- 🎨 **极简 API**：根据是否有插槽内容自动判断模式
- 🖱️ **可拖拽弹窗**：模态框支持拖拽移动
- 💾 **唯一标识**：支持通过 id 区分不同的 AI 助手实例
- 📱 **iframe 集成**：内置 iframe 展示 AI 助手界面
- ♿ **无障碍支持**：完整的 ARIA 标签支持

## 快速开始

### 方式 1：悬停模式（提供插槽内容）

当你提供插槽内容时，鼠标悬停会显示浮动的 AI 图标按钮：

```vue
<template>
  <HoverAction :ai="aiConfig">
    <p>鼠标悬停在这段文字上会显示 AI 助手图标</p>
  </HoverAction>
</template>

<script setup>
const aiConfig = {
  token: 'your-auth-token',
  askContent: '请分析这段文本内容',
  id: 'text-analyzer-1', // 可选的唯一标识
};
</script>
```

### 方式 2：独立按钮（不提供插槽）

当不提供插槽内容时，会显示一个默认的 AI 助手按钮：

```vue
<template>
  <HoverAction :ai="aiConfig" />
</template>

<script setup>
const aiConfig = {
  token: 'your-auth-token',
  askContent: '我需要 AI 帮助',
  id: 'standalone-assistant',
};
</script>
```

## 基础用法

### 使用场景 1：悬停模式（提供插槽内容）

鼠标悬停在内容上时，显示浮动的 AI 图标按钮。

```vue
<template>
  <HoverAction :ai="aiConfig">
    <p>这是一段需要 AI 分析的文本内容</p>
  </HoverAction>
</template>

<script setup>
import HoverAction from '@/components/hover-action/hover-action.vue';

const aiConfig = {
  token: 'your-auth-token',
  askContent: '请分析这段文本的主要观点和情感倾向',
  id: 'text-analysis-1', // 可选：用于区分不同的 AI 助手实例
};
</script>
```

**适用场景**：

- 文本段落的智能分析
- 表格单元格的快速操作
- 卡片内容的智能解读
- 图片/文件的智能识别

### 使用场景 2：独立按钮（不提供插槽）

不提供插槽内容时，显示默认的 AI 助手按钮。

```vue
<template>
  <!-- 工具栏中的 AI 助手入口 -->
  <div class="toolbar">
    <button>保存</button>
    <button>导出</button>
    <HoverAction :ai="toolbarAiConfig" />
  </div>
</template>

<script setup>
const toolbarAiConfig = {
  token: 'your-auth-token',
  askContent: '帮我总结当前页面的内容',
  id: 'toolbar-assistant',
};
</script>
```

**适用场景**：

- 工具栏中的 AI 功能入口
- 页面右下角的浮动助手
- 表单旁边的智能填充按钮

## API 文档

### Props

| 属性名      | 类型            | 默认值     | 说明                                         |
| ----------- | --------------- | ---------- | -------------------------------------------- |
| `ai`        | `AIConfig`      | **必填**   | AI 配置对象，详见下方说明                    |
| `size`      | `number`        | `26`       | 浮动图标大小（像素），仅悬停模式生效         |
| `offset`    | `number`        | `4`        | 浮动图标与内容的距离（像素），仅悬停模式生效 |
| `iconClass` | `string`        | `''`       | 浮动图标的额外 CSS 类，仅悬停模式生效        |
| `iconStyle` | `CSSProperties` | `{}`       | 浮动图标的内联样式，仅悬停模式生效           |
| `zIndex`    | `number`        | `30`       | 浮动图标的 z-index，仅悬停模式生效           |
| `ariaLabel` | `string`        | `'Ask AI'` | 无障碍标签                                   |

### AI 配置对象（AIConfig）

`ai` prop 是一个配置对象，包含以下字段：

```typescript
interface AIConfig {
  // 必填：用户认证令牌
  token: string | null;

  // 必填：AI 助手的初始问题或上下文
  // 这个内容会作为用户的第一条消息发送给 AI
  askContent: string;

  // 可选：唯一标识符，用于区分不同的 AI 助手实例
  // 在同一页面有多个 AI 助手时，可以通过 id 进行追踪和区分
  id?: string | null;
}
```

#### 字段详细说明

| 字段         | 类型             | 必填 | 说明                                                                                                             | 示例                                                                                            |
| ------------ | ---------------- | ---- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `token`      | `string \| null` | ✅   | 用户认证令牌，用于 AI 服务的身份验证                                                                             | `'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'`                                                     |
| `askContent` | `string`         | ✅   | AI 助手的初始提问内容或上下文信息<br/>• 可以是一个具体的问题<br/>• 可以是需要分析的内容<br/>• 可以包含上下文信息 | `'请分析这段代码的性能问题'`<br/>`'帮我总结以下文档内容：...'`<br/>`'根据用户反馈生成改进建议'` |
| `id`         | `string \| null` | ❌   | 唯一标识符，用于区分不同的 AI 助手实例<br/>• 便于日志追踪<br/>• 便于数据分析<br/>• 便于区分不同场景的使用        | `'user-analysis-assistant'`<br/>`'code-reviewer-1'`<br/>`'doc-summarizer'`                      |

#### 配置示例

```vue
<script setup>
// 基础配置
const basicConfig = {
  token: 'your-auth-token',
  askContent: '请帮我分析这段文本',
};

// 带 ID 的配置（推荐）
const configWithId = {
  token: 'your-auth-token',
  askContent: '分析用户行为数据',
  id: 'user-behavior-analyst',
};

// 动态内容配置
const dynamicConfig = computed(() => ({
  token: userStore.token,
  askContent: `请分析以下数据：\n${JSON.stringify(currentData.value, null, 2)}`,
  id: `data-analyst-${currentData.value.id}`,
}));

// 表格场景配置
const getTableRowConfig = (row) => ({
  token: authToken.value,
  askContent: `分析用户 ${row.name} 的详细信息：
    - 注册时间：${row.registerDate}
    - 活跃度：${row.activityScore}
    - 消费金额：${row.totalSpent}`,
  id: `user-row-${row.id}`,
});
</script>
```

### Slots

| 插槽名    | 说明                                                                                               | 示例                         |
| --------- | -------------------------------------------------------------------------------------------------- | ---------------------------- |
| `default` | 默认插槽<br/>• **有内容**：悬停模式，鼠标悬停显示浮动按钮<br/>• **无内容**：显示默认的 AI 助手按钮 | 文本、表格单元格、卡片内容等 |
| `icon`    | 自定义浮动按钮的图标样式（仅悬停模式生效）                                                         | 自定义 SVG 图标、图片等      |

### Events

| 事件名  | 参数 | 说明                               |
| ------- | ---- | ---------------------------------- |
| `click` | -    | 点击 AI 按钮时触发（在打开弹窗前） |

## 完整示例

### 示例 1：表格中使用（悬停模式）

```vue
<template>
  <table>
    <tbody>
      <tr v-for="item in dataList" :key="item.id">
        <td>
          <HoverAction
            :ai="{
              token: userToken,
              askContent: `分析用户 ${item.name} 的行为数据和活跃度`,
              id: `user-analysis-${item.id}`,
            }"
          >
            {{ item.name }}
          </HoverAction>
        </td>
        <td>{{ item.email }}</td>
        <td>{{ item.status }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import HoverAction from '@/components/hover-action/hover-action.vue';
import { ref } from 'vue';

const userToken = 'your-auth-token';
const dataList = ref([
  { id: 1, name: 'Alice', email: 'alice@example.com', status: 'Active' },
  { id: 2, name: 'Bob', email: 'bob@example.com', status: 'Inactive' },
]);
</script>
```

### 示例 2：工具栏中使用（独立按钮）

```vue
<template>
  <div class="toolbar">
    <button>保存</button>
    <button>导出</button>

    <!-- AI 助手按钮 - 不提供插槽内容 -->
    <HoverAction
      :ai="{
        token: userToken,
        askContent: '帮我分析并总结当前文档的主要内容',
        id: 'document-summarizer',
      }"
    />
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #f5f5f5;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  color: #6366f1;
  background: white;
  border: 1px solid #e0e7ff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-btn:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
}
</style>
```

### 示例 3：自定义浮动图标（悬停模式）

```vue
<template>
  <HoverAction
    :ai="{ token: userToken, askContent: '分析这段代码' }"
    :size="32"
    :offset="8"
    icon-class="custom-icon"
  >
    <template #icon>
      <img src="/path/to/custom-ai-icon.png" alt="AI" />
    </template>

    <pre><code>{{ codeContent }}</code></pre>
  </HoverAction>
</template>

<script setup>
const userToken = 'your-token';
const codeContent = `function hello() {
  console.log('Hello World');
}`;
</script>

<style scoped>
.custom-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
}
</style>
```

### 示例 4：监听点击事件

```vue
<template>
  <HoverAction :ai="aiConfig" @click="handleAIClick">
    <p>点击查看 AI 分析</p>
  </HoverAction>
</template>

<script setup>
import { ref } from 'vue';

const aiConfig = ref({
  token: 'your-token',
  askContent: '初始问题',
  id: 'click-tracker',
});

function handleAIClick() {
  console.log('AI 助手即将打开');
  // 可以在这里执行一些逻辑，比如更新 askContent
  aiConfig.value.askContent = '根据当前上下文更新的问题';
  // 可以进行埋点统计
  trackEvent('ai_assistant_opened', { id: aiConfig.value.id });
}
</script>
```

### 示例 5：混合使用两种模式

```vue
<template>
  <div class="page">
    <!-- 表格内容：悬停模式（有插槽内容） -->
    <table>
      <tr v-for="item in list" :key="item.id">
        <td>
          <HoverAction
            :ai="{
              token,
              askContent: `分析 ${item.name} 的数据`,
              id: `table-row-${item.id}`,
            }"
          >
            {{ item.name }}
          </HoverAction>
        </td>
      </tr>
    </table>

    <!-- 工具栏按钮：独立按钮（无插槽内容） -->
    <div class="toolbar">
      <HoverAction
        :ai="{
          token,
          askContent: '帮我总结页面所有数据',
          id: 'page-summarizer',
        }"
      />
    </div>

    <!-- 浮动助手：独立按钮 -->
    <div class="floating-assistant">
      <HoverAction
        :ai="{
          token,
          askContent: '我需要帮助',
          id: 'floating-helper',
        }"
      />
    </div>
  </div>
</template>
```

## 弹窗功能

### 拖拽移动

弹窗支持拖拽移动：

- 点击并按住弹窗顶部的标题栏
- 拖动到任意位置
- 自动限制在视窗范围内

### 弹窗尺寸

默认尺寸：

- 宽度：320px
- 高度：600px

如需自定义尺寸，可以通过 CSS 变量或全局样式覆盖：

```css
/* 在你的全局样式文件中 */
.ha-modal {
  width: 400px !important;
  height: 700px !important;
}
```

## 最佳实践

### 1. 选择合适的使用方式

- **悬停模式**（有插槽内容）：当 AI 功能是作为内容的辅助功能时
  - 表格单元格、文本段落、卡片内容等
- **独立按钮**（无插槽内容）：当 AI 功能是独立的操作入口时
  - 工具栏、页面固定位置的助手等

### 2. 提供清晰详细的 askContent

```vue
<!-- ❌ 不好的做法：内容过于模糊 -->
<HoverAction :ai="{ token, askContent: '分析' }">
  <p>内容</p>
</HoverAction>

<!-- ✅ 好的做法：提供具体的上下文和要求 -->
<HoverAction
  :ai="{
    token,
    askContent: '请分析这段用户反馈的情感倾向、关键问题点和改进建议',
    id: 'feedback-analyzer',
  }"
>
  <p>用户反馈内容...</p>
</HoverAction>
```

### 3. 使用 id 进行追踪（推荐）

为每个 AI 助手实例提供唯一的 id，便于日志追踪和数据分析：

```vue
<!-- ✅ 推荐：带 ID -->
<HoverAction
  :ai="{
    token,
    askContent: '分析数据',
    id: 'user-data-analyzer',
  }"
>
  {{ userData }}
</HoverAction>

<!-- ⚠️ 可用但不推荐：无 ID -->
<HoverAction :ai="{ token, askContent: '分析数据' }">
  {{ userData }}
</HoverAction>
```

### 4. 响应式设计

移动端建议使用独立按钮模式，因为移动设备没有悬停交互：

```vue
<template>
  <!-- 桌面端：悬停模式 -->
  <HoverAction v-if="!isMobile" :ai="aiConfig">
    <div>悬停分析</div>
  </HoverAction>

  <!-- 移动端：独立按钮 -->
  <HoverAction v-else :ai="aiConfig" />
</template>

<script setup>
import { ref, onMounted } from 'vue';

const isMobile = ref(false);
const aiConfig = {
  token: 'your-token',
  askContent: '分析内容',
  id: 'responsive-assistant',
};

onMounted(() => {
  isMobile.value = window.innerWidth < 768;
});
</script>
```

### 5. 无障碍支持

提供有意义的 aria-label：

```vue
<HoverAction
  aria-label="使用 AI 分析客户评论并生成改进建议"
  :ai="{ token, askContent: '分析客户评论', id: 'review-analyzer' }"
>
  <div>客户评论内容</div>
</HoverAction>
```

## 样式定制

### 自定义默认触发器样式

```vue
<template>
  <HoverAction mode="button" :ai="aiConfig" class="custom-trigger" />
</template>

<style>
.custom-trigger .hover-action__default-trigger {
  padding: 10px 20px;
  color: #10b981;
  background: #d1fae5;
  border-color: #6ee7b7;
}

.custom-trigger .hover-action__default-trigger:hover {
  background: #a7f3d0;
  border-color: #34d399;
}
</style>
```

### 自定义模态框样式

```vue
<style>
/* 修改模态框标题栏颜色 */
:deep(.ha-modal__header) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 修改关闭按钮颜色 */
:deep(.ha-modal__close) {
  color: white;
}
</style>
```

## 常见问题

### Q: 如何选择使用悬停模式还是独立按钮？

- **悬停模式**（提供插槽内容）：当 AI 是内容的辅助功能时
- **独立按钮**（不提供插槽）：当 AI 是独立功能入口时

```vue
<!-- 悬停模式：分析已有内容 -->
<HoverAction :ai="{ token, askContent: '分析', id: 'hover-1' }">
  <p>现有内容</p>
</HoverAction>

<!-- 独立按钮：独立功能入口 -->
<HoverAction :ai="{ token, askContent: '通用助手', id: 'button-1' }" />
```

### Q: 如何动态更新 askContent？

使用响应式对象：

```vue
<script setup>
import { ref, computed } from 'vue';

const selectedData = ref({ name: 'Alice', age: 25 });

const aiConfig = computed(() => ({
  token: 'your-token',
  askContent: `分析用户数据：${JSON.stringify(selectedData.value)}`,
  id: `user-${selectedData.value.name}`,
}));
</script>

<template>
  <HoverAction :ai="aiConfig">
    <div>{{ selectedData.name }}</div>
  </HoverAction>
</template>
```

### Q: id 字段是必须的吗？

不是必须的，但强烈推荐使用，便于：

- 日志追踪和问题定位
- 用户行为数据分析
- 区分不同场景的 AI 使用

```vue
<!-- ✅ 推荐：提供 ID -->
<HoverAction :ai="{ token, askContent: '...', id: 'unique-id' }" />

<!-- ⚠️ 可用但不推荐 -->
<HoverAction :ai="{ token, askContent: '...' }" />
```

### Q: 如何根据权限控制显示？

使用 `v-if` 或 `v-show`：

```vue
<HoverAction v-if="hasAIPermission" :ai="{ token, askContent: '...', id: 'protected-ai' }">
  <div>受保护的内容</div>
</HoverAction>
```

### Q: 能否在一个页面使用多个 HoverAction？

可以！建议为每个实例提供不同的 id：

```vue
<HoverAction :ai="{ token, askContent: '分析A', id: 'analyzer-a' }">
  <div>内容 A</div>
</HoverAction>

<HoverAction :ai="{ token, askContent: '分析B', id: 'analyzer-b' }">
  <div>内容 B</div>
</HoverAction>

<HoverAction :ai="{ token, askContent: '通用助手', id: 'general-assistant' }" />
```

### Q: 移动端如何使用？

移动端没有悬停交互，建议使用独立按钮模式：

```vue
<HoverAction v-if="isMobile" :ai="{ token, askContent: '帮助', id: 'mobile-assistant' }" />

<HoverAction v-else :ai="{ token, askContent: '分析', id: 'desktop-assistant' }">
  <div>桌面端内容（可悬停）</div>
</HoverAction>
```

## 浏览器兼容性

- Chrome/Edge: ✅ 完全支持
- Firefox: ✅ 完全支持
- Safari: ✅ 完全支持
- IE11: ❌ 不支持

## License

MIT
