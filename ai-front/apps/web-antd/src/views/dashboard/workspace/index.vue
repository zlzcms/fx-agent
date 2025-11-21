<script lang="ts" setup>
import type {
  WorkbenchProjectItem,
  WorkbenchQuickNavItem,
  WorkbenchTodoItem,
  WorkbenchTrendItem,
} from '@vben/common-ui';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  AnalysisChartCard,
  WorkbenchHeader,
  WorkbenchProject,
  WorkbenchQuickNav,
  WorkbenchTodo,
  WorkbenchTrends,
} from '@vben/common-ui';
import { $t } from '@vben/locales';
import { preferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';
import { openWindow } from '@vben/utils';

import AnalyticsVisitsSource from '../analytics/analytics-visits-source.vue';

const userStore = useUserStore();

// 这是一个示例数据，实际项目中需要根据实际情况进行调整
// url 也可以是内部路由，在 navTo 方法中识别处理，进行内部跳转
// 例如：url: /dashboard/workspace
const projectItems: WorkbenchProjectItem[] = [
  {
    color: '',
    content: $t('views.dashboard.workspace.githubContent'),
    date: '2021-04-01',
    group: $t('views.dashboard.workspace.openSourceGroup'),
    icon: 'carbon:logo-github',
    title: 'Github',
    url: 'https://github.com',
  },
  {
    color: '#3fb27f',
    content: $t('views.dashboard.workspace.vueContent'),
    date: '2021-04-01',
    group: $t('views.dashboard.workspace.algorithmGroup'),
    icon: 'ion:logo-vue',
    title: 'Vue',
    url: 'https://vuejs.org',
  },
  {
    color: '#e18525',
    content: $t('views.dashboard.workspace.html5Content'),
    date: '2021-04-01',
    group: $t('views.dashboard.workspace.workGroup'),
    icon: 'ion:logo-html5',
    title: 'Html5',
    url: 'https://developer.mozilla.org/zh-CN/docs/Web/HTML',
  },
  {
    color: '#bf0c2c',
    content: $t('views.dashboard.workspace.angularContent'),
    date: '2021-04-01',
    group: 'UI',
    icon: 'ion:logo-angular',
    title: 'Angular',
    url: 'https://angular.io',
  },
  {
    color: '#00d8ff',
    content: $t('views.dashboard.workspace.reactContent'),
    date: '2021-04-01',
    group: $t('views.dashboard.workspace.techGroup'),
    icon: 'bx:bxl-react',
    title: 'React',
    url: 'https://reactjs.org',
  },
  {
    color: '#EBD94E',
    content: $t('views.dashboard.workspace.jsContent'),
    date: '2021-04-01',
    group: $t('views.dashboard.workspace.architectureGroup'),
    icon: 'ion:logo-javascript',
    title: 'Js',
    url: 'https://developer.mozilla.org/zh-CN/docs/Web/JavaScript',
  },
];

// 同样，这里的 url 也可以使用以 http 开头的外部链接
const quickNavItems: WorkbenchQuickNavItem[] = [
  {
    color: '#1fdaca',
    icon: 'ion:home-outline',
    title: $t('views.dashboard.workspace.home'),
    url: '/',
  },
  {
    color: '#bf0c2c',
    icon: 'ion:grid-outline',
    title: $t('views.dashboard.workspace.dashboard'),
    url: '/dashboard',
  },
  {
    color: '#e18525',
    icon: 'ion:layers-outline',
    title: $t('views.dashboard.workspace.components'),
    url: '/demos/features/icons',
  },
  {
    color: '#3fb27f',
    icon: 'ion:settings-outline',
    title: $t('views.dashboard.workspace.systemManagement'),
    url: '/demos/features/login-expired', // 这里的 URL 是示例，实际项目中需要根据实际情况进行调整
  },
  {
    color: '#4daf1bc9',
    icon: 'ion:key-outline',
    title: $t('views.dashboard.workspace.permissionManagement'),
    url: '/demos/access/page-control',
  },
  {
    color: '#00d8ff',
    icon: 'ion:bar-chart-outline',
    title: $t('views.dashboard.workspace.charts'),
    url: '/analytics',
  },
];

const todoItems = ref<WorkbenchTodoItem[]>([
  {
    completed: false,
    content: $t('views.dashboard.workspace.todo1Content'),
    date: '2024-07-30 11:00:00',
    title: $t('views.dashboard.workspace.todo1Title'),
  },
  {
    completed: true,
    content: $t('views.dashboard.workspace.todo2Content'),
    date: '2024-07-30 11:00:00',
    title: $t('views.dashboard.workspace.todo2Title'),
  },
  {
    completed: false,
    content: $t('views.dashboard.workspace.todo3Content'),
    date: '2024-07-30 11:00:00',
    title: $t('views.dashboard.workspace.todo3Title'),
  },
  {
    completed: false,
    content: $t('views.dashboard.workspace.todo4Content'),
    date: '2024-07-30 11:00:00',
    title: $t('views.dashboard.workspace.todo4Title'),
  },
  {
    completed: false,
    content: $t('views.dashboard.workspace.todo5Content'),
    date: '2024-07-30 11:00:00',
    title: $t('views.dashboard.workspace.todo5Title'),
  },
]);
const trendItems: WorkbenchTrendItem[] = [
  {
    avatar: 'svg:avatar-1',
    content: $t('views.dashboard.workspace.trend1Content'),
    date: $t('views.dashboard.workspace.justNow'),
    title: $t('views.dashboard.workspace.william'),
  },
  {
    avatar: 'svg:avatar-2',
    content: $t('views.dashboard.workspace.trend2Content'),
    date: $t('views.dashboard.workspace.oneHourAgo'),
    title: $t('views.dashboard.workspace.ivan'),
  },
  {
    avatar: 'svg:avatar-3',
    content: $t('views.dashboard.workspace.trend3Content'),
    date: $t('views.dashboard.workspace.oneDayAgo'),
    title: $t('views.dashboard.workspace.chris'),
  },
  {
    avatar: 'svg:avatar-4',
    content: $t('views.dashboard.workspace.trend4Content'),
    date: $t('views.dashboard.workspace.twoDaysAgo'),
    title: 'Vben',
  },
  {
    avatar: 'svg:avatar-1',
    content: $t('views.dashboard.workspace.trend5Content'),
    date: $t('views.dashboard.workspace.threeDaysAgo'),
    title: $t('views.dashboard.workspace.peter'),
  },
  {
    avatar: 'svg:avatar-2',
    content: $t('views.dashboard.workspace.trend6Content'),
    date: $t('views.dashboard.workspace.oneWeekAgo'),
    title: $t('views.dashboard.workspace.jack'),
  },
  {
    avatar: 'svg:avatar-3',
    content: $t('views.dashboard.workspace.trend7Content'),
    date: $t('views.dashboard.workspace.oneWeekAgo'),
    title: $t('views.dashboard.workspace.william'),
  },
  {
    avatar: 'svg:avatar-4',
    content: $t('views.dashboard.workspace.trend8Content'),
    date: '2021-04-01 20:00',
    title: $t('views.dashboard.workspace.william'),
  },
  {
    avatar: 'svg:avatar-4',
    content: $t('views.dashboard.workspace.trend9Content'),
    date: '2021-03-01 20:00',
    title: $t('views.dashboard.workspace.vben'),
  },
];

const router = useRouter();

// 这是一个示例方法，实际项目中需要根据实际情况进行调整
// This is a sample method, adjust according to the actual project requirements
function navTo(nav: WorkbenchProjectItem | WorkbenchQuickNavItem) {
  if (nav.url?.startsWith('http')) {
    openWindow(nav.url);
    return;
  }
  if (nav.url?.startsWith('/')) {
    router.push(nav.url).catch((error) => {
      console.error('Navigation failed:', error);
    });
  } else {
    console.warn(`Unknown URL for navigation item: ${nav.title} -> ${nav.url}`);
  }
}
</script>

<template>
  <div class="p-5">
    <WorkbenchHeader
      :avatar="userStore.userInfo?.avatar || preferences.app.defaultAvatar"
    >
      <template #title>
        {{ $t('views.dashboard.workspace.goodMorning') }}, {{ userStore.userInfo?.realName }}, {{ $t('views.dashboard.workspace.startYourWork') }}!
      </template>
      <template #description> {{ $t('views.dashboard.workspace.todayWeather') }} </template>
    </WorkbenchHeader>

    <div class="mt-5 flex flex-col lg:flex-row">
      <div class="mr-4 w-full lg:w-3/5">
        <WorkbenchProject :items="projectItems" title="项目" @click="navTo" />
        <WorkbenchTrends :items="trendItems" class="mt-5" title="最新动态" />
      </div>
      <div class="w-full lg:w-2/5">
        <WorkbenchQuickNav
          :items="quickNavItems"
          class="mt-5 lg:mt-0"
          title="快捷导航"
          @click="navTo"
        />
        <WorkbenchTodo :items="todoItems" class="mt-5" title="待办事项" />
        <AnalysisChartCard class="mt-5" title="访问来源">
          <AnalyticsVisitsSource />
        </AnalysisChartCard>
      </div>
    </div>
  </div>
</template>
