/**
 * @Author: zhujinlong
 * @Date:   2025-06-16 20:21:50
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-16 20:30:48
 */
/**
 * Markdown编辑器组件
 */

export { default as MarkdownEditor } from './MarkdownEditor.vue';

export type { DocumentConfigItem, MarkdownEditorEmits, MarkdownEditorProps } from './types';

export {
  DEFAULT_TEMPLATES_EN,
  DEFAULT_TEMPLATES_ZH,
  DOCUMENT_TEMPLATE_KEYS,
  getDefaultTemplates,
} from './types';
