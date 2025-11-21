import type { CSSProperties } from 'vue';

/**
 * AI configuration object
 */
export interface AIConfig {
  /** Initial question or context for the AI assistant */
  askContent: string;
  /** Unique identifier to distinguish different AI assistant instances */
  id?: null | string;
  /** Authentication token for AI service */
  token: null | string;
}

/**
 * AiAction component props
 */
export interface Props {
  /** AI configuration object */
  ai: AIConfig;
  /** Accessible label for the action button */
  ariaLabel?: string;
  /** Base URL for the AI assistant iframe (customizable) */
  baseUrl?: string;
  /** Extra CSS class for the floating icon */
  iconClass?: string;
  /** Inline style applied to the floating icon */
  iconStyle?: CSSProperties | Record<string, any>;
  /** Distance between wrapped element and icon (pixels) */
  offset?: number;
  /** Icon size in pixels */
  size?: number;
  /** z-index for the floating icon */
  zIndex?: number;
}

/**
 * Component events
 */
export interface Emits {
  /** Emitted when the AI button is clicked (before modal opens) */
  click: [];
}
