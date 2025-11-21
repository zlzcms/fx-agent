<script lang="ts" setup>
import type { BreadcrumbStyleType } from '@vben/types';

import type { IBreadcrumb } from '@vben-core/shadcn-ui';

import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { $t } from '@vben/locales';

import { VbenBreadcrumbView } from '@vben-core/shadcn-ui';

interface Props {
  hideWhenOnlyOne?: boolean;
  showHome?: boolean;
  showIcon?: boolean;
  type?: BreadcrumbStyleType;
}

const props = withDefaults(defineProps<Props>(), {
  showHome: false,
  showIcon: false,
  type: 'normal',
});

const route = useRoute();
const router = useRouter();

/**
 * 包装面包屑标题的国际化
 * 使用 sidebar.{routeName} 格式，如果找不到则尝试直接翻译 title
 */
function wrapperBreadcrumbLocale(routeName: string, originalTitle?: string): string {
  if (!routeName && !originalTitle) {
    return '';
  }

  // 优先使用 sidebar.{routeName} 格式
  if (routeName) {
    const i18nKey = `sidebar.${routeName}`;
    const translatedText = $t(i18nKey);

    // 如果翻译成功（不等于 key 本身），则返回翻译结果
    if (translatedText !== i18nKey) {
      return translatedText;
    }
  }

  // 如果 sidebar.{routeName} 找不到，尝试直接翻译 originalTitle（向后兼容）
  if (originalTitle) {
    return $t(originalTitle);
  }

  return routeName || '';
}

const breadcrumbs = computed((): IBreadcrumb[] => {
  const matched = route.matched;

  const resultBreadcrumb: IBreadcrumb[] = [];

  for (const match of matched) {
    const { meta, path, name } = match;
    const { hideChildrenInMenu, hideInBreadcrumb, icon, title } = meta || {};
    if (hideInBreadcrumb || hideChildrenInMenu || !path) {
      continue;
    }

    resultBreadcrumb.push({
      icon,
      path: path || route.path,
      title: wrapperBreadcrumbLocale(name as string, title as string),
    });
  }
  if (props.showHome) {
    resultBreadcrumb.unshift({
      icon: 'mdi:home-outline',
      isHome: true,
      path: '/',
    });
  }
  if (props.hideWhenOnlyOne && resultBreadcrumb.length === 1) {
    return [];
  }

  return resultBreadcrumb;
});

function handleSelect(path: string) {
  router.push(path);
}
</script>
<template>
  <VbenBreadcrumbView
    :breadcrumbs="breadcrumbs"
    :show-icon="showIcon"
    :style-type="type"
    class="ml-2"
    @select="handleSelect"
  />
</template>
