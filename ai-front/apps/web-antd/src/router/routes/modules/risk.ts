import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    name: 'Risk',
    path: '/risk',
    meta: {
      title: $t('page.menu.risk'),
      icon: 'material-symbols:security',
      order: 4,
    },
    children: [
      {
        name: 'RiskCustomer',
        path: 'risk-customer',
        component: () => import('#/views/risk/risk-customer/index.vue'),
        meta: {
          title: $t('page.menu.riskCustomer'),
        },
      },
      {
        name: 'RiskEmployee',
        path: 'risk-employee',
        component: () => import('#/views/risk/risk-employee/index.vue'),
        meta: {
          title: $t('page.menu.riskEmployee'),
        },
      },
      {
        name: 'RiskAssistant',
        path: 'risk-assistant',
        component: () => import('#/views/risk/risk-assistants/index.vue'),
        meta: {
          title: $t('page.menu.riskSettings'),
        },
      },
      {
        name: 'RiskLevels',
        path: 'risk-levels',
        component: () => import('#/views/risk/risk-levels/index.vue'),
        meta: {
          title: $t('page.menu.riskLevels'),
        },
      },
      {
        name: 'RiskTagList',
        path: 'risk-tag-list',
        component: () => import('#/views/risk/risk-tags/index.vue'),
        meta: {
          title: $t('page.menu.riskTagList'),
        },
      },
      {
        name: 'RiskAssistantAdd',
        path: 'risk-assistant/add',
        component: () => import('#/views/risk/risk-assistants/form.vue'),
        meta: {
          title: $t('page.menu.riskAssistantAdd'),
          hideInMenu: true,
          activePath: '/risk/risk-assistant',
        },
      },
      {
        name: 'RiskAssistantEdit',
        path: 'risk-assistant/edit/:id',
        component: () => import('#/views/risk/risk-assistants/form.vue'),
        meta: {
          title: $t('page.menu.riskAssistantEdit'),
          hideInMenu: true,
          activePath: '/risk/risk-assistant',
        },
      },
    ],
  },
];

export default routes;
