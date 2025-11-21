# @maxpro/ai-action

<p align="center">
  <img src="https://img.shields.io/npm/v/@maxpro/ai-action" alt="npm version">
  <img src="https://img.shields.io/npm/dm/@maxpro/ai-action" alt="npm downloads">
  <img src="https://img.shields.io/npm/l/@maxpro/ai-action" alt="license">
  <img src="https://img.shields.io/badge/vue-3.x-brightgreen" alt="vue 3">
</p>

A flexible Vue 3 component for AI assistant integration with hover interaction and draggable modal. Perfect for adding contextual AI help to any element in your application.

## ✨ Features

- 🎯 **Dual Modes**: Hover mode with floating button OR standalone button mode
- 🎨 **Simple API**: Automatically detects mode based on slot usage
- 🖱️ **Draggable Modal**: Modal window supports drag and drop
- 💾 **Unique IDs**: Track different AI assistant instances
- 📱 **iframe Integration**: Built-in iframe for AI interface
- ♿ **Accessibility**: Full ARIA label support
- 🎭 **TypeScript**: Written in TypeScript with full type definitions
- 🚀 **Zero Config**: Works out of the box with sensible defaults

## 📦 Installation

```bash
npm install @maxpro/ai-action
```

```bash
yarn add @maxpro/ai-action
```

```bash
pnpm add @maxpro/ai-action
```

## 🚀 Quick Start

### Global Registration

```typescript
// main.ts
import { createApp } from 'vue';
import App from './App.vue';
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const app = createApp(App);
app.component('AiAction', AiAction);
app.mount('#app');
```

### Local Registration

```vue
<script setup lang="ts">
import { AiAction } from '@maxpro/ai-action';
import '@maxpro/ai-action/dist/ai-action.css';

const aiConfig = {
  token: 'your-auth-token',
  askContent: 'Please analyze this text',
  id: 'text-analyzer',
};
</script>

<template>
  <AiAction :ai="aiConfig">
    <p>Hover over this text to see the AI assistant icon</p>
  </AiAction>
</template>
```

## 📖 Usage

### Mode 1: Hover Mode (with slot content)

When you provide slot content, hovering shows a floating AI icon button:

```vue
<template>
  <AiAction :ai="aiConfig">
    <p>Hover over this text to see the AI assistant</p>
  </AiAction>
</template>

<script setup>
import { AiAction } from '@maxpro/ai-action';

const aiConfig = {
  token: 'your-auth-token',
  askContent: 'Please analyze this text content',
  id: 'text-analyzer-1',
};
</script>
```

**Use cases:**

- Text paragraph analysis
- Table cell quick actions
- Card content interpretation
- Image/file recognition

### Mode 2: Standalone Button (no slot content)

When no slot content is provided, displays a default AI assistant button:

```vue
<template>
  <!-- No slot content = standalone button -->
  <AiAction :ai="aiConfig" />
</template>

<script setup>
const aiConfig = {
  token: 'your-auth-token',
  askContent: 'I need AI assistance',
  id: 'standalone-assistant',
};
</script>
```

**Use cases:**

- Toolbar AI feature entry
- Floating assistant in page corner
- Smart fill button next to forms

## 🎛️ API

### Props

| Prop        | Type            | Default                          | Description                                                   |
| ----------- | --------------- | -------------------------------- | ------------------------------------------------------------- |
| `ai`        | `AIConfig`      | **Required**                     | AI configuration object (see below)                           |
| `size`      | `number`        | `26`                             | Floating icon size in pixels (hover mode only)                |
| `offset`    | `number`        | `4`                              | Distance between element and icon in pixels (hover mode only) |
| `iconClass` | `string`        | `''`                             | Extra CSS class for floating icon (hover mode only)           |
| `iconStyle` | `CSSProperties` | `{}`                             | Inline styles for floating icon (hover mode only)             |
| `zIndex`    | `number`        | `30`                             | z-index for floating icon (hover mode only)                   |
| `ariaLabel` | `string`        | `'Ask AI'`                       | Accessibility label                                           |
| `baseUrl`   | `string`        | `'https://client.ai1center.com'` | Base URL for AI assistant iframe                              |

### AI Configuration (AIConfig)

The `ai` prop is a configuration object:

```typescript
interface AIConfig {
  // Required: User authentication token
  token: string | null;

  // Required: Initial question or context for AI
  askContent: string;

  // Optional: Unique identifier for tracking
  id?: string | null;
}
```

| Field        | Type             | Required | Description                              | Example                           |
| ------------ | ---------------- | -------- | ---------------------------------------- | --------------------------------- |
| `token`      | `string \| null` | ✅       | Authentication token for AI service      | `'eyJhbGci...'`                   |
| `askContent` | `string`         | ✅       | Initial prompt or context for AI         | `'Analyze this code performance'` |
| `id`         | `string \| null` | ❌       | Unique identifier for tracking instances | `'code-reviewer-1'`               |

### Slots

| Slot      | Description                                    | Example                  |
| --------- | ---------------------------------------------- | ------------------------ |
| `default` | Main content (triggers hover mode if provided) | Text, table cells, cards |
| `icon`    | Custom floating icon (hover mode only)         | Custom SVG, images       |

### Events

| Event   | Parameters | Description                                            |
| ------- | ---------- | ------------------------------------------------------ |
| `click` | -          | Emitted when AI button is clicked (before modal opens) |

## 📚 Examples

### Example 1: Table Usage (Hover Mode)

```vue
<template>
  <table>
    <tbody>
      <tr v-for="user in users" :key="user.id">
        <td>
          <AiAction
            :ai="{
              token: authToken,
              askContent: `Analyze user ${user.name}'s behavior and activity`,
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

### Example 2: Toolbar Usage (Standalone Button)

```vue
<template>
  <div class="toolbar">
    <button>Save</button>
    <button>Export</button>

    <!-- AI assistant button -->
    <AiAction
      :ai="{
        token: authToken,
        askContent: 'Help me summarize this document',
        id: 'toolbar-ai',
      }"
    />
  </div>
</template>
```

### Example 3: Custom Floating Icon

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

### Example 4: Event Handling

```vue
<template>
  <AiAction :ai="aiConfig" @click="handleClick">
    <p>Click to analyze</p>
  </AiAction>
</template>

<script setup>
import { ref } from 'vue';

const aiConfig = ref({
  token: 'your-token',
  askContent: 'Initial question',
  id: 'tracker',
});

function handleClick() {
  console.log('AI assistant opening');
  // Update context or track analytics
  aiConfig.value.askContent = 'Updated question based on context';
}
</script>
```

### Example 5: Custom Base URL

```vue
<template>
  <AiAction :ai="aiConfig" base-url="https://your-custom-ai.com">
    <p>Custom AI endpoint</p>
  </AiAction>
</template>
```

## 🎨 Styling

### Custom Modal Styles

```vue
<style>
/* Customize modal header */
:deep(.ha-modal__header) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Customize close button */
:deep(.ha-modal__close) {
  color: white;
}

/* Customize modal size */
:deep(.ha-modal) {
  width: 400px;
  height: 700px;
}
</style>
```

## 🌟 Best Practices

### 1. Choose the Right Mode

- **Hover Mode** (with slot): AI as auxiliary feature for existing content
- **Standalone Button** (no slot): AI as independent feature entry

### 2. Provide Clear Context

```vue
<!-- ❌ Bad: Too vague -->
<AiAction :ai="{ token, askContent: 'analyze' }">
  <p>Content</p>
</AiAction>

<!-- ✅ Good: Specific and clear -->
<AiAction
  :ai="{
    token,
    askContent: 'Analyze sentiment and key issues in this user feedback',
    id: 'feedback-analyzer',
  }"
>
  <p>User feedback content...</p>
</AiAction>
```

### 3. Use IDs for Tracking (Recommended)

```vue
<!-- ✅ Recommended: With ID -->
<AiAction
  :ai="{
    token,
    askContent: 'Analyze data',
    id: 'user-data-analyzer',
  }"
>
  {{ userData }}
</AiAction>
```

### 4. Mobile Responsiveness

```vue
<template>
  <!-- Desktop: Hover mode -->
  <AiAction v-if="!isMobile" :ai="aiConfig">
    <div>Hover to analyze</div>
  </AiAction>

  <!-- Mobile: Standalone button -->
  <AiAction v-else :ai="aiConfig" />
</template>
```

## 📱 Modal Features

### Draggable Modal

The modal supports drag-and-drop:

- Click and hold the title bar
- Drag to any position
- Auto-constrained within viewport

### Default Size

- Width: 320px
- Height: 600px

## 🔧 TypeScript Support

Full TypeScript support with exported types:

```typescript
import type { AiActionProps, AIConfig } from '@maxpro/ai-action';

const config: AIConfig = {
  token: 'token',
  askContent: 'question',
  id: 'unique-id',
};
```

## 🌐 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ❌ IE11 (not supported)

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📮 Support

- 📧 Email: support@ai1center.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/ai-action/issues)
- 📖 Docs: [Full Documentation](https://github.com/your-org/ai-action#readme)

## 🙏 Acknowledgments

Built with ❤️ by the MaxPro Team

---

**Keywords**: vue3, ai, assistant, hover, action, component, draggable, modal, typescript
