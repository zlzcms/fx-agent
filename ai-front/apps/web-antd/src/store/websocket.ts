// stores/websocket.ts
import { computed, ref } from 'vue';

import { useAccessStore } from '@vben/stores';

import { defineStore } from 'pinia';
import { io, Socket } from 'socket.io-client';

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref<null | Socket>(null);
  const isConnected = ref(false);
  const reconnectAttempts = ref(0);

  // 定义事件清理信息的类型
  interface EventCleanupInfo {
    event: string;
    callback: (data: any) => void;
    cleanup: () => void;
  }

  const eventCleanupFunctions = ref<EventCleanupInfo[]>([]);

  // 连接配置常量
  const WS_URL = import.meta.env.VITE_GLOB_API_URL;
  const WS_PATH = '/ws/socket.io';

  // 连接配置参数
  const WS_CONFIG = {
    autoConnect: true,
    path: WS_PATH,
    reconnection: true,
    reconnectionAttempts: 3,
    reconnectionDelay: 1000,
    transports: ['websocket'],
  };

  /**
   * 建立 WebSocket 连接
   * @returns {boolean} 连接是否成功
   */
  const connect = () => {
    const accessStore = useAccessStore();

    // 检查登录状态
    if (!accessStore.accessToken) {
      console.warn('用户未登录或登录已过期，无法建立 WebSocket 连接');
      return false;
    }

    // 检查是否已连接
    if (isConnected.value) {
      return true;
    }

    // 如果有 socket 实例但未连接，尝试连接
    if (socket.value && !isConnected.value) {
      socket.value.connect();
      return true;
    }

    try {
      // 创建 Socket 连接，携带认证信息，连接到默认命名空间
      socket.value = io(WS_URL, {
        ...WS_CONFIG,
        auth: {
          session_uuid: accessStore.accessSessionUuid,
          token: accessStore.accessToken,
        },
      });

      // 注册核心事件监听器
      registerCoreEvents();
      return true;
    } catch (error) {
      console.error('WebSocket 连接失败:', error);
      return false;
    }
  };

  /**
   * 注册核心事件监听器
   */
  const registerCoreEvents = () => {
    if (!socket.value) return;

    socket.value.on('connect', () => {
      // console.log('WebSocket 连接成功');
      isConnected.value = true;
      reconnectAttempts.value = 0;
    });

    socket.value.on('connect_error', (error) => {
      console.error('WebSocket 连接错误:', error);
      handleConnectionError(error);
    });

    socket.value.on('disconnect', (reason) => {
      // console.log('WebSocket 已断开:', reason);
      isConnected.value = false;

      if (reason !== 'io client disconnect') {
        handleReconnection();
      }
    });
  };

  /**
   * 处理连接错误
   */
  const handleConnectionError = async (error: any) => {
    const accessStore = useAccessStore();

    // 检查是否是认证相关错误
    // 包括：401错误、Token过期、连接被拒绝等
    const isAuthError =
      error?.description?.includes('401') ||
      error?.message?.includes('Token 已过期') ||
      error?.message?.includes('401') ||
      error?.message?.includes('Connection rejected by server') ||
      error?.data?.message?.includes('Token 已过期');

    if (isAuthError) {
      console.warn('WebSocket 认证失败，可能是 Token 已过期，跳转到登录页面');
      console.error('详细错误信息:', error);

      // 立即断开 WebSocket 连接
      disconnect();

      // 停止所有重连尝试
      reconnectAttempts.value = WS_CONFIG.reconnectionAttempts; // 设置为最大值，防止继续重连

      // 导入 useAuthStore 来处理登出逻辑
      const { useAuthStore } = await import('#/store/auth');
      const authStore = useAuthStore();

      // 清除 access store 中的 token 和 session
      accessStore.setAccessToken(null);
      accessStore.setAccessSessionUuid(null);
      accessStore.setRefreshToken(null);

      // 调用 logout 方法，传递 false 参数防止在 logout 中再次触发 WebSocket 连接
      await authStore.logout(false);

      // 强制跳转到登录页
      window.location.href = '/auth/login';
      return;
    }

    if (!accessStore.accessToken) {
      disconnect();
    }
  };

  /**
   * 处理重连机制
   */
  const handleReconnection = () => {
    if (reconnectAttempts.value >= WS_CONFIG.reconnectionAttempts) {
      console.error('已达到最大重连次数，停止重连');
      return;
    }

    reconnectAttempts.value++;
    setTimeout(() => {
      connect();
    }, WS_CONFIG.reconnectionDelay);
  };

  /**
   * 发送消息
   * @param event 事件名称
   * @param data 发送的数据
   */
  const emit = (event: string, data?: any): boolean => {
    connect();
    try {
      socket.value?.emit(event, data);
      return true;
    } catch (error) {
      console.error('发送消息失败:', error);
      return false;
    }
  };

  /**
   * 监听事件
   * @param event 事件名称
   * @param callback 回调函数
   */
  const on = (event: string, callback: (data: any) => void) => {
    connect();

    // 检查是否已经存在相同的事件监听器
    const existingCleanup = eventCleanupFunctions.value.find(
      (cleanup) => cleanup.event === event && cleanup.callback === callback,
    );

    if (existingCleanup) {
      console.warn(`Event listener for '${event}' already exists, skipping duplicate registration`);
      return existingCleanup.cleanup;
    }

    socket.value?.on(event, callback);

    // 保存清理函数和相关信息
    const cleanup = () => {
      socket.value?.off(event, callback);
    };

    const cleanupInfo = {
      event,
      callback,
      cleanup,
    };

    eventCleanupFunctions.value.push(cleanupInfo);
    return cleanup; // 返回清理函数，便于手动清理
  };

  /**
   * 移除事件监听
   * @param event 事件名称
   * @param callback 可选，特定回调函数
   */
  const off = (event: string, callback?: any) => {
    if (!socket.value) return;

    if (callback) {
      // 移除特定的事件监听器
      socket.value.off(event, callback);

      // 从清理函数列表中移除
      const index = eventCleanupFunctions.value.findIndex(
        (cleanup) => cleanup.event === event && cleanup.callback === callback,
      );
      if (index !== -1) {
        eventCleanupFunctions.value.splice(index, 1);
      }
    } else {
      // 移除所有该事件的监听器
      socket.value.off(event);

      // 从清理函数列表中移除所有该事件的监听器
      eventCleanupFunctions.value = eventCleanupFunctions.value.filter(
        (cleanup) => cleanup.event !== event,
      );
    }
  };

  /**
   * 清理所有注册的事件监听
   */
  const cleanupEvents = () => {
    eventCleanupFunctions.value.forEach((cleanupInfo) => {
      cleanupInfo.cleanup();
    });
    eventCleanupFunctions.value = [];
  };

  /**
   * 断开 WebSocket 连接
   */
  const disconnect = () => {
    if (socket.value) {
      cleanupEvents();
      socket.value.disconnect();
      socket.value = null;
      isConnected.value = false;
    }
  };

  // 连接状态计算属性
  const connectionStatus = computed(() => {
    if (!socket.value) return 'disconnected';
    return isConnected.value ? 'connected' : 'connecting';
  });

  function $reset() {
    disconnect();
  }

  return {
    $reset,
    socket,
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    emit,
    on,
    off,
    cleanupEvents,
  };
});
