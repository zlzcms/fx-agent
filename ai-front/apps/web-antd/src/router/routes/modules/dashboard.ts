/**
 * @Author: zhujinlong
 * @Date:   2025-06-07 18:18:33
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-12 10:10:35
 */
import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: $t('page.dashboard.title'),
    },
    name: 'Analytics',
    path: '/analytics',
    component: () => import('#/views/dashboard/analytics/index.vue'),
    // {
    //   name: 'Workspace',
    //   path: '/workspace',
    //   component: () => import('#/views/dashboard/workspace/index.vue'),
    //   meta: {
    //     icon: 'carbon:workspace',
    //     title: $t('page.dashboard.workspace'),
    //   },
    // },
  },
];

export default routes;
