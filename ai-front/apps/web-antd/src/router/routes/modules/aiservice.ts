import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'AIService',
    path: '/ai-service',
    meta: {
      title: $t('page.menu.aiService'),
      icon: 'material-symbols:robot-2',
      order: 3,
    },
    children: [
      {
        name: 'mcp',
        path: 'mcp',
        component: () => import('#/views/ai/mcp/index.vue'),
        meta: {
          title: $t('page.menu.mcp'),
        },
      },
      {
        name: 'ShortcutCommand',
        path: 'shortcut-command',
        component: () => import('#/views/un-implement.vue'),
        meta: {
          title: $t('page.menu.ShortcutCommand'),
        },
      },
      {
        name: 'SchedulerManage',
        path: 'scheduler-manage',
        component: () => import('#/views/scheduler/manage/index.vue'),
        meta: {
          title: $t('page.menu.schedulerManage'),
          // icon: 'ix:scheduler',
        },
      },
      {
        name: 'SchedulerRecord',
        path: 'scheduler-record',
        component: () => import('#/views/scheduler/record/index.vue'),
        meta: {
          title: $t('page.menu.schedulerRecord'),
          // icon: 'ix:scheduler',
        },
      },
    ],
  },
];

export default routes;
