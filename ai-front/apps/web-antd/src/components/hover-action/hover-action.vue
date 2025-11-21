<script setup lang="ts">
import type { CSSProperties } from 'vue';

import { computed, onBeforeUnmount, ref, useSlots } from 'vue';

interface Props {
  /** Icon size in px */
  size?: number;
  /** Distance between wrapped element and icon (px) */
  offset?: number;
  /** Extra class on the floating icon */
  iconClass?: string;
  /** Inline style applied to the floating icon */
  iconStyle?: CSSProperties | {};
  /** z-index for the floating icon */
  zIndex?: number;
  /** Accessible label for the action button */
  ariaLabel?: string;
  /** AI config for iframe URL building */
  ai: {
    askContent: '' | string;
    id: null | string /** 唯一标识，用于区分不同的 AI 助手 */;
    token: null | string;
  };
}

const props = withDefaults(defineProps<Props>(), {
  size: 26,
  offset: 4,
  iconClass: '',
  iconStyle: () => ({}),
  zIndex: 30,
  ariaLabel: 'Ask AI',
  mode: 'auto',
});

const emit = defineEmits<{ click: [] }>();

const slots = useSlots();
const isModalOpen = ref(false);
const wrapperRef = ref<HTMLElement>();
const iconPosition = ref({ top: 0, left: 0 });

// 检测是否使用了自定义插槽内容（非默认内容）
const isHoveringMode = computed(() => {
  const slotContent = slots.default?.();
  if (slotContent) return true;
  return false;
});
const isHovering = ref(false);

// 拖拽相关状态
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const modalPosition = ref({ x: 0, y: 0 });
const modalRef = ref<HTMLElement>();

const wrapperClass = 'hover-action-wrapper';
const iframeSrc = computed(() => {
  const ai = props.ai;
  // const val = `https://client.ai1center.com?token=${encodeURIComponent(ai?.token || '')}&askContent=${encodeURIComponent(ai?.askContent || '')}`;
  const val = `http://localhost:5174?token=${encodeURIComponent(ai?.token || '')}&askContent=${encodeURIComponent(ai?.askContent || '')}`;
  return val;
});
const iconComputedStyle = computed<CSSProperties>(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  lineHeight: `${props.size}px`,
  position: 'fixed',
  top: `${iconPosition.value.top}px`,
  left: `${iconPosition.value.left}px`,
  transform: 'translate(-50%, -100%)',
  zIndex: 9999,
  ...props.iconStyle,
}));

function updateIconPosition() {
  if (wrapperRef.value) {
    const rect = wrapperRef.value.getBoundingClientRect();
    iconPosition.value = {
      top: rect.top - props.offset,
      left: rect.left + rect.width / 2,
    };
  }
}

function handleClick() {
  emit('click');
  isModalOpen.value = true;
  // 重置模态框位置到屏幕中心
  modalPosition.value = { x: 0, y: 0 };
}

// 拖拽开始
function handleDragStart(e: MouseEvent) {
  if (!modalRef.value) return;

  isDragging.value = true;

  // 获取模态框当前在屏幕上的实际位置
  const rect = modalRef.value.getBoundingClientRect();
  const currentX = rect.left;
  const currentY = rect.top;

  dragStart.value = {
    x: e.clientX - currentX,
    y: e.clientY - currentY,
  };

  // 阻止默认行为
  e.preventDefault();

  // 添加全局事件监听器
  document.addEventListener('mousemove', handleDragMove);
  document.addEventListener('mouseup', handleDragEnd);
}

// 拖拽移动
function handleDragMove(e: MouseEvent) {
  if (!isDragging.value) return;

  const newX = e.clientX - dragStart.value.x;
  const newY = e.clientY - dragStart.value.y;

  // 限制在视窗范围内
  const modalWidth = 320; // 模态框宽度
  const maxX = window.innerWidth - modalWidth;

  modalPosition.value = {
    x: Math.max(0, Math.min(newX, maxX)),
    y: Math.max(0, newY),
  };
}

// 拖拽结束
function handleDragEnd() {
  isDragging.value = false;

  // 移除全局事件监听器
  document.removeEventListener('mousemove', handleDragMove);
  document.removeEventListener('mouseup', handleDragEnd);
}
let hideTimer: number | undefined;

function onEnter() {
  // 如果是按钮模式，不显示浮动按钮
  if (!isHoveringMode.value) return;

  if (hideTimer) {
    window.clearTimeout(hideTimer);
    hideTimer = undefined;
  }
  isHovering.value = true;
  updateIconPosition();
}

function onLeaveWithDelay() {
  // 如果是按钮模式，不需要处理浮动按钮显隐
  if (!isHoveringMode.value) return;

  if (hideTimer) window.clearTimeout(hideTimer);
  hideTimer = window.setTimeout(() => {
    hideTimer = undefined;
    isHovering.value = false;
  }, 120);
}

// 计算模态框样式
const modalStyle = computed(() => {
  const isInitialPosition = modalPosition.value.x === 0 && modalPosition.value.y === 0;

  return isInitialPosition
    ? {
        // 初始位置：居中显示
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
      }
    : {
        // 拖拽后：使用绝对位置
        left: `${modalPosition.value.x}px`,
        top: `${modalPosition.value.y}px`,
        transform: 'none',
      };
});

onBeforeUnmount(() => {
  if (hideTimer) window.clearTimeout(hideTimer);
  // 清理拖拽事件监听器
  document.removeEventListener('mousemove', handleDragMove);
  document.removeEventListener('mouseup', handleDragEnd);
});
</script>

<template>
  <!-- 按钮模式：直接点击触发器打开弹窗；悬停模式：鼠标移入显示浮动按钮 -->
  <span
    ref="wrapperRef"
    :class="[wrapperClass, { 'hover-action-wrapper--clickable': isHovering }]"
    @mouseenter="onEnter"
    @mouseleave="onLeaveWithDelay"
  >
    <slot>
      <!-- 如果没有提供默认插槽，显示默认 AI 图标按钮 -->
      <span
        data-ai-trigger="true"
        class="ai-action-btn"
        :aria-label="props.ariaLabel"
        @click="handleClick"
      >
        <svg
          t="1758781209716"
          viewBox="0 0 1024 1024"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          p-id="4666"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          width="20"
          height="20"
        >
          <path
            d="M432.64 184.832c-28.672 0-57.088 15.36-70.656 46.08L96.256 838.656l284.672-82.944c62.72-18.176 105.728-75.776 105.728-141.056l-218.112 68.096 126.72-290.304c14.08-32.512 60.16-32.512 74.24 0l153.344 350.72h-0.256c25.344 57.856 82.432 95.488 145.92 95.488h0.256L503.04 231.168c-13.312-30.976-41.984-46.336-70.4-46.336zM770.916 282.66a79.36 79.36 0 1 0 154.472-36.477 79.36 79.36 0 1 0-154.472 36.476zM792.064 386.048h112.384v453.12H792.064z"
            p-id="4667"
            fill="currentColor"
          />
        </svg>
      </span>
    </slot>
  </span>

  <!-- Teleport the icon to body to avoid overflow:hidden issues -->
  <!-- 只在悬停模式下显示浮动按钮 -->
  <teleport to="body">
    <button
      v-show="isHoveringMode && isHovering"
      type="button"
      class="hover-action__icon"
      :class="iconClass"
      :style="iconComputedStyle"
      :aria-label="props.ariaLabel"
      @click.stop="handleClick"
      @mouseenter="onEnter"
      @mouseleave="onLeaveWithDelay"
    >
      <slot name="icon">
        <!-- Inline SVG: Bold filled chat bubble + star (more visible) -->

        <svg
          t="1758781209716"
          viewBox="0 0 1024 1024"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          p-id="4666"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          style="width: 100%; height: 100%"
        >
          <path
            d="M432.64 184.832c-28.672 0-57.088 15.36-70.656 46.08L96.256 838.656l284.672-82.944c62.72-18.176 105.728-75.776 105.728-141.056l-218.112 68.096 126.72-290.304c14.08-32.512 60.16-32.512 74.24 0l153.344 350.72h-0.256c25.344 57.856 82.432 95.488 145.92 95.488h0.256L503.04 231.168c-13.312-30.976-41.984-46.336-70.4-46.336zM770.916 282.66a79.36 79.36 0 1 0 154.472-36.477 79.36 79.36 0 1 0-154.472 36.476zM792.064 386.048h112.384v453.12H792.064z"
            p-id="4667"
          />
        </svg>
      </slot>
    </button>
  </teleport>

  <!-- Centered Modal with iframe -->
  <teleport to="body">
    <div v-if="isModalOpen" ref="modalRef" class="ha-modal" :style="modalStyle">
      <div
        class="ha-modal__header"
        :class="{ 'ha-modal__header--dragging': isDragging }"
        @mousedown="handleDragStart"
      >
        <div class="ha-modal__title">AI Assistant</div>
        <button
          class="ha-modal__close"
          type="button"
          aria-label="close"
          @click="isModalOpen = false"
        >
          ✕
        </button>
      </div>
      <div class="ha-modal__body">
        <iframe class="ha-modal__iframe" :src="iframeSrc" frameborder="0"></iframe>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.hover-action-wrapper {
  position: relative;
  display: inline-block;
  vertical-align: middle;
}

.ai-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  color: #6366f1;
  cursor: pointer;
}

/* 按钮模式：添加可点击样式 */
.hover-action-wrapper--clickable {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.hover-action-wrapper--clickable:hover {
  opacity: 0.8;
}

/* 默认触发器按钮样式 */
.hover-action__default-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  color: #6366f1;
  cursor: pointer;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.hover-action__default-trigger:hover {
  color: #4f46e5;
  background: #e0e7ff;
  border-color: #a5b4fc;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
  transform: translateY(-1px);
}

.hover-action__default-trigger:active {
  box-shadow: 0 1px 2px rgb(0 0 0 / 10%);
  transform: translateY(0);
}

/* 浮动图标按钮样式（悬停模式） */
.hover-action__icon {
  position: absolute;
  top: 3px;
  left: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
  color: #fff;
  cursor: pointer;
  user-select: none;
  background-color: #fff;
  border: 1px solid rgb(0 0 0 / 8%);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
  transform: translate(-50%, -100%);
  transition: filter 0.15s ease-in-out;
}

.hover-action__icon:hover {
  filter: brightness(1.08);
}

/* Modal Styles */
.ha-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  width: 320px;
  height: 600px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #d3d3d3;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgb(0 0 0 / 19.6%);
  transform: translate(-50%, -50%);
}

.ha-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 12px;
  cursor: move;
  user-select: none;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.ha-modal__header:hover {
  background-color: #f8f9fa;
}

.ha-modal__header--dragging {
  cursor: grabbing;
  background-color: #e9ecef;
}

.ha-modal__title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.ha-modal__close {
  font-size: 18px;
  line-height: 1;
  color: #6b7280;
  cursor: pointer;
  background: transparent;
  border: none;
}

.ha-modal__body {
  flex: 1;
  background: #fafafa;
}

.ha-modal__iframe {
  width: 100%;
  height: 100%;
  border: 0;
}
</style>
