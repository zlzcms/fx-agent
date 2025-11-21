import { defineConfig } from 'vite'
import path from 'path'

// 独立打包 src/embed.js 为 IIFE 脚本，供外部站点直接 <script> 引用
export default defineConfig({
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/embed.js'),
      name: 'AiassistantEmbed',
      formats: ['iife'],
      fileName: () => 'embed.min.js'
    },
    outDir: 'dist-embed',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      // embed.js 是纯浏览器运行，不需要外部依赖
      external: [],
      output: {
        // 避免生成额外的 chunks，确保单文件输出
        inlineDynamicImports: true
      }
    }
  }
})


