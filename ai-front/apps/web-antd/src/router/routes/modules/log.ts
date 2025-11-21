import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'Log',
    path: '/log',
    meta: {
      title: $t('page.menu.log'),
      icon: 'carbon:cloud-logging',
      order: 3,
    },
    children: [
      {
        name: 'LoginLog',
        path: '/log/login',
        component: () => import('#/views/log/login/index.vue'),
        meta: {
          title: $t('page.menu.login'),
          icon: 'mdi:login',
        },
      },
      {
        name: 'OperaLog',
        path: '/log/opera',
        component: () => import('#/views/log/opera/index.vue'),
        meta: {
          title: $t('page.menu.opera'),
          icon: 'carbon:operations-record',
        },
      },
      {
        name: 'QALog',
        path: '/log/qa-log',
        component: () => import('#/views/log/qa-log/index.vue'),
        meta: {
          title: 'QA日志',
          icon: 'mdi:chat-question',
        },
      },
      {
        name: 'NoticeLog',
        path: '/log/notice-log',
        component: () => import('#/views/log/notice-log/index.vue'),
        meta: {
          title: '通知日志',
          icon: 'mdi:bell-outline',
        },
      },
    ],
  },
];

export default routes;
