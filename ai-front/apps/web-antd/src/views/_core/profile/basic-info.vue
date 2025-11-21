<script setup lang="ts">
import type { SysUpdateUserAvatarParams, SysUpdateUserNicknameParams } from '#/api';

import { computed, onMounted } from 'vue';

import { useVbenModal } from '@vben/common-ui';
import { preferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';

import { useVbenForm } from '#/adapter/form';
import { updateSysUserAvatarApi, updateSysUserNicknameApi } from '#/api';
import { useAuthStore } from '#/store';

import { avatarSchema, nicknameSchema } from './data';

const authStore = useAuthStore();
const userStore = useUserStore();

// 处理部门显示：兼容字符串和对象
const deptName = computed(() => {
  const dept = userStore.userInfo?.dept;
  if (!dept) return '';
  return typeof dept === 'string' ? dept : (dept as any)?.name || '';
});

// 处理角色显示：兼容字符串数组和对象数组
const roleNames = computed(() => {
  const roles = userStore.userInfo?.roles;
  if (!roles?.length) return [];
  return typeof roles[0] === 'string'
    ? (roles as string[])
    : (roles as any[]).map((role) => role?.name).filter(Boolean);
});

// 页面加载时刷新用户信息
onMounted(() => {
  authStore.fetchUserInfo();
});

const [AvatarForm, avatarFormApi] = useVbenForm({
  layout: 'vertical',
  showDefaultActions: false,
  schema: avatarSchema,
});

const [avatarModal, avatarModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await avatarFormApi.validate();
    if (valid) {
      avatarModalApi.lock();
      try {
        await updateSysUserAvatarApi(await avatarFormApi.getValues<SysUpdateUserAvatarParams>());
        await avatarModalApi.close();
        await authStore.fetchUserInfo();
      } finally {
        avatarModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      avatarFormApi.resetForm();
      const data = avatarModalApi.getData();
      if (data) avatarFormApi.setValues(data);
    }
  },
});

const [NicknameForm, nicknameFormApi] = useVbenForm({
  layout: 'vertical',
  showDefaultActions: false,
  schema: nicknameSchema,
});

const [nicknameModal, nicknameModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await nicknameFormApi.validate();
    if (valid) {
      nicknameModalApi.lock();
      try {
        await updateSysUserNicknameApi(
          await nicknameFormApi.getValues<SysUpdateUserNicknameParams>(),
        );
        await nicknameModalApi.close();
        await authStore.fetchUserInfo();
      } finally {
        nicknameModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      nicknameFormApi.resetForm();
      const data = nicknameModalApi.getData();
      if (data) nicknameFormApi.setValues(data);
    }
  },
});
</script>

<template>
  <a-card
    class="mr-3"
    title="基本信息"
    :head-style="{
      borderBottom: 'none',
    }"
  >
    <div class="mb-8 mt-2 text-center">
      <a-tooltip>
        <template #title>点击上传头像</template>
        <a-avatar
          class="cursor-pointer"
          :size="128"
          :src="userStore.userInfo?.avatar || preferences.app.defaultAvatar"
          @click="avatarModalApi.setData(null).open()"
        />
      </a-tooltip>
      <p class="mt-5 text-lg">
        {{ userStore.userInfo?.nickname }}
        <a-button type="ghost" size="small" @click="nicknameModalApi.setData(null).open()">
          <span class="icon-[cuida--edit-outline]"></span>
        </a-button>
      </p>
      <div class="mt-3 flex items-center justify-center gap-2">
        <span class="icon-[ix--id-filled]" style="width: 1.2em; height: 1.2em"></span>
        <p class="text-sm text-gray-500">{{ userStore.userInfo?.id }}</p>
      </div>
    </div>
    <a-descriptions class="ml-6" :column="1">
      <a-descriptions-item label="用户名">
        {{ userStore.userInfo?.username }}
      </a-descriptions-item>
      <a-descriptions-item label="手机">
        {{ userStore.userInfo?.phone || '暂无' }}
      </a-descriptions-item>
      <a-descriptions-item label="邮箱">
        {{ userStore.userInfo?.email }}
      </a-descriptions-item>
      <a-descriptions-item label="部门">
        <a-tag v-if="deptName" color="green">{{ deptName }}</a-tag>
        <span v-else>未绑定</span>
      </a-descriptions-item>
      <a-descriptions-item label="角色">
        <template v-if="roleNames.length > 0">
          <a-tag
            v-for="roleName in roleNames"
            :key="roleName"
            color="purple"
            class="whitespace-nowrap"
          >
            {{ roleName }}
          </a-tag>
        </template>
        <span v-else>未分配</span>
      </a-descriptions-item>
    </a-descriptions>
    <template #actions> 最后登录时间：{{ userStore.userInfo?.last_login_time }} </template>
  </a-card>
  <avatarModal title="更新头像">
    <AvatarForm />
  </avatarModal>
  <nicknameModal title="更新昵称">
    <NicknameForm />
  </nicknameModal>
</template>
