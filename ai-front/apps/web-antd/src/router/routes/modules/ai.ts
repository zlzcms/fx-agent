/**
 * @Author: zhujinlong
 * @Date:   2025-06-11 14:19:42
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-21 17:43:30
 */
import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'AI',
    path: '/ai',
    meta: {
      title: $t('page.menu.ai'), // AI管理
      icon: 'material-symbols:robot-2',
      order: 2,
    },
    children: [
      {
        name: 'AIAssistants',
        path: 'assistants',
        component: () => import('#/views/ai/assistants/index.vue'),
        meta: {
          title: $t('page.menu.aiAssistants'), // 助理管理
        },
      },
      {
        name: 'AISubscription',
        path: 'subscription',
        component: () => import('#/views/ai/subscription/index.vue'),

        meta: {
          title: $t('page.menu.aiSubscription'), // 助理订阅
        },
      },
      {
        name: 'AIAssistantReports',
        path: 'reports',
        component: () => import('#/views/ai/reports/index.vue'),
        meta: {
          title: $t('page.menu.aiAssistantReports'),
        },
      },
      // {
      //   name: 'AITemplates',
      //   path: 'templates',
      //   component: () => import('#/views/ai/templates/index.vue'),
      //   meta: {
      //     title: $t('page.menu.aiTemplates'), // 模板管理
      //   },
      // },

      {
        name: 'AIAssistantAdd',
        path: 'assistants/add',
        component: () => import('#/views/ai/assistants/form.vue'),
        meta: {
          title: $t('page.menu.aiAssistantAdd'), // 添加AI助手
          hideInMenu: true,
          activePath: '/ai/assistants',
          keepAlive: false,
        },
      },
      {
        name: 'AIAssistantEdit',
        path: 'assistants/edit/:id',
        component: () => import('#/views/ai/assistants/form.vue'),
        meta: {
          title: $t('page.menu.aiAssistantEdit'), // 编辑AI助手
          hideInMenu: true,
          activePath: '/ai/assistants',
          keepAlive: false,
        },
      },
    ],
  },
];

export default routes;
