import { defineConfig } from '@vben/vite-config';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      resolve: {
        alias: [
          {
            find: '@maxpro/ai-action',
            // 指向工作空间内的源码入口，避免依赖扫描解析 dist
            replacement: fileURLToPath(
              new URL('../../packages/ai-action/src/index.ts', import.meta.url),
            ),
          },
        ],
      },
      server: {
        proxy: {
          '/api/mcp': {
            changeOrigin: true,
            rewrite: (path: string) => path.replace(/^\/api\/mcp/, ''),
            // MCP 服务代理到端口 8009
            target: 'http://localhost:8009',
            ws: true,
          },
          '/api': {
            changeOrigin: true,
            rewrite: (path: string) => path.replace(/^\/api/, ''),
            // 修改代理目标地址为localhost:8000
            target: 'http://localhost:8000/api',
            ws: true,
          },
        },
      },
      // 开发环境配置
      define: {
        __DEV__: process.env.NODE_ENV !== 'production',
      },
      build: {
        // 优化构建性能
        target: 'es2020',
        minify: process.env.NODE_ENV === 'production' ? 'esbuild' : false,
        sourcemap: process.env.NODE_ENV !== 'production',
        // 代码分割优化
        rollupOptions: {
          output: {
            // 手动分包策略
            manualChunks: {
              // 将Vue相关库分包
              'vue-vendor': ['vue', 'vue-router', 'pinia'],
              // 将Ant Design Vue分包
              'antd-vendor': ['ant-design-vue', 'dayjs'],
              // 将工具库分包
              'utils-vendor': ['@vueuse/core'],
              // 将编辑器相关分包
              'editor-vendor': ['highlight.js', 'markdown-it', 'markdown-it-emoji'],
              // 将WebSocket相关分包
              'socket-vendor': ['socket.io-client'],
            },
            // 优化chunk文件名
            chunkFileNames: 'js/[name]-[hash].js',
            entryFileNames: 'js/[name]-[hash].js',
            assetFileNames: (assetInfo: any) => {
              const info = assetInfo.name!.split('.');
              const ext = info[info.length - 1];
              if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name!)) {
                return `media/[name]-[hash].${ext}`;
              }
              if (/\.(png|jpe?g|gif|svg)(\?.*)?$/.test(assetInfo.name!)) {
                return `img/[name]-[hash].${ext}`;
              }
              if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name!)) {
                return `fonts/[name]-[hash].${ext}`;
              }
              return `assets/[name]-[hash].${ext}`;
            },
          },
          // 忽略某些警告
          // onwarn(warning, warn) {
          //   if (warning.code === 'MODULE_LEVEL_DIRECTIVE') {
          //     return;
          //   }
          //   warn(warning);
          // },
        },
        // 调整chunk大小警告阈值
        chunkSizeWarningLimit: 1000,
        // 压缩配置 - 只在生产环境启用
        ...(process.env.NODE_ENV === 'production' && {
          terserOptions: {
            compress: {
              drop_console: true,
              drop_debugger: true,
            },
          },
        }),
      },
      // 优化依赖预构建
      optimizeDeps: {
        // 避免对工作空间内的本地包进行预构建扫描
        exclude: ['@maxpro/ai-action'],
        include: [
          'vue',
          'vue-router',
          'pinia',
          '@vueuse/core',
          'ant-design-vue',
          'dayjs',
          'socket.io-client',
        ],
      },
    },
  };
}) as any;
