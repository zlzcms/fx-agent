import type { App } from 'vue';

import AiAction from './ai-action.vue';

// 类型导出
export type { Props as AiActionProps } from './types';

// 组件导出
export { AiAction };
export default AiAction;

// 支持 Vue.use() 安装
export const install = (app: App): void => {
  app.component('AiAction', AiAction);
};

// Auto-install when vue is found (for CDN usage)
declare global {
  interface Window {
    Vue?: App;
  }
}

if (typeof window !== 'undefined' && window.Vue) {
  install(window.Vue);
}
