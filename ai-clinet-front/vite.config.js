/**
 * @Author: zhujinlong
 * @Date:   2025-05-16 20:56:59
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-05-17 15:51:46
 */
import { defineConfig, loadEnv } from 'vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import path from 'path'
import { AntDesignXVueResolver } from 'ant-design-x-vue/resolver';

import VueMacros from 'unplugin-vue-macros/vite'
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  // 根据当前工作目录中的 `mode` 加载 .env 文件
  // 设置第三个参数为 '' 来加载所有环境变量，而不管是否有 `VITE_` 前缀。
  const env = loadEnv(mode, process.cwd(), '')
  
  // 创建一个只包含VITE_开头的环境变量的对象
  const envPrefix = {};
  Object.keys(env).forEach(key => {
    if (key.startsWith('VITE_')) {
      envPrefix[key] = env[key];
    }
  });
  
  return {
    plugins: [
      VueMacros({
        plugins:{
          vue: vue(),
          vueJsx: vueJsx(),
        }
      }),
      Components({
        resolvers: [ElementPlusResolver(),AntDesignXVueResolver()],
      }),
    ],
    server: {
      host: '0.0.0.0',
      port: 5174
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    // 定义环境变量替换
    define: {
      'process.env': envPrefix
    }
  }
})
