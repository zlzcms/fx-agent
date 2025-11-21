
import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'AISetting',
    path: '/ai-setting',
    meta: {
      title: 'AI设置', //   AI设置
      icon: 'material-symbols:robot-2',
      order: 5,
    },
    children: [

      {
        name: 'AIModels',
        path: 'models',
        component: () => import('#/views/ai/models/index.vue'),
        meta: {
          title: $t('page.menu.aiModels'), // AI模型
        },
      },
      {
        name: 'AIDatasources',
        path: 'datasources',
        meta: {
          title: $t('page.menu.aiDatasources'),// 数据源
        },
        component: () => import('#/views/ai/datasources/list/index.vue'),
      },

      {
        name: 'AITemplates',
        path: 'templates',
        component: () => import('#/views/ai/templates/index.vue'),//助理模版
        meta: {
          title: '助理模版', //$t('page.menu.aiTemplates'),
        },
      },

      {
        name: 'AIAssistantTypes',
        path: 'assistant-types',
        component: () => import('#/views/ai/assistant-types/index.vue'),
        meta: {
          title: $t('page.menu.aiAssistantTypes'), // 助手类型
        },
      },
    ],
  },
];

export default routes;
