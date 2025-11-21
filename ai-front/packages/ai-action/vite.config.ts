import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'AiAction',
      formats: ['es', 'umd'],
      fileName: (format) => `ai-action.${format}.js`,
    },
    rollupOptions: {
      // Make sure to externalize deps that shouldn't be bundled
      external: ['vue'],
      output: {
        // Provide global variables to use in the UMD build
        // for externalized deps
        globals: {
          vue: 'Vue',
        },
        // Export CSS separately
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'style.css') return 'ai-action.css';
          return assetInfo.name || 'asset';
        },
      },
    },
    // Generate source maps
    sourcemap: true,
    // Clear output directory before build
    emptyOutDir: true,
  },
});
