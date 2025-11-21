/**
 * LuckySheet 动态加载工具
 * 按需加载 LuckySheet 及其依赖，避免在首屏加载 2MB+ 的资源
 */

// 加载状态管理
let isLoaded = false;
let isLoading = false;
let loadPromise = null;

// LuckySheet 依赖的资源 URL
const LUCKYSHEET_RESOURCES = {
  css: [
    'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/css/pluginsCss.css',
    'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/plugins.css',
    'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/css/luckysheet.css',
    'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/assets/iconfont/iconfont.css'
  ],
  js: [
    {
      src: 'https://code.jquery.com/jquery-3.7.1.min.js',
      check: () => window.jQuery !== undefined,
      name: 'jQuery'
    },
    {
      src: 'https://cdnjs.cloudflare.com/ajax/libs/jquery-mousewheel/3.1.13/jquery.mousewheel.min.js',
      check: () => window.jQuery && window.jQuery.fn.mousewheel !== undefined,
      name: 'jQuery Mousewheel'
    },
    {
      src: 'https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/luckysheet.umd.js',
      check: () => window.luckysheet !== undefined,
      name: 'LuckySheet'
    }
  ]
};

/**
 * 加载 CSS 文件
 * @param {string} href - CSS 文件 URL
 * @returns {Promise<void>}
 */
function loadCSS(href) {
  return new Promise((resolve, reject) => {
    // 检查是否已加载
    if (document.querySelector(`link[href="${href}"]`)) {
      console.log(`✅ CSS already loaded: ${href}`);
      resolve();
      return;
    }

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.onload = () => {
      console.log(`✅ CSS loaded: ${href}`);
      resolve();
    };
    link.onerror = () => {
      console.error(`❌ Failed to load CSS: ${href}`);
      reject(new Error(`Failed to load CSS: ${href}`));
    };
    document.head.appendChild(link);
  });
}

/**
 * 加载 JavaScript 文件
 * @param {Object} config - JS 配置对象
 * @param {string} config.src - JS 文件 URL
 * @param {Function} config.check - 检查是否已加载的函数
 * @param {string} config.name - 资源名称
 * @returns {Promise<void>}
 */
function loadScript(config) {
  const { src, check, name } = config;

  return new Promise((resolve, reject) => {
    // 检查是否已加载（通过全局变量检测）
    if (check && check()) {
      console.log(`✅ ${name} already loaded`);
      resolve();
      return;
    }

    // 检查是否已有 script 标签
    if (document.querySelector(`script[src="${src}"]`)) {
      // 等待脚本加载完成
      const checkInterval = setInterval(() => {
        if (check && check()) {
          clearInterval(checkInterval);
          console.log(`✅ ${name} loaded from existing script tag`);
          resolve();
        }
      }, 100);
      
      // 超时处理
      setTimeout(() => {
        clearInterval(checkInterval);
        reject(new Error(`Timeout waiting for ${name} to load`));
      }, 30000);
      return;
    }

    console.log(`⏳ Loading ${name}...`);
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => {
      // 等待一小段时间确保全局变量已设置
      setTimeout(() => {
        if (check && !check()) {
          console.warn(`⚠️ ${name} loaded but check failed`);
        }
        console.log(`✅ ${name} loaded successfully`);
        resolve();
      }, 50);
    };
    script.onerror = () => {
      console.error(`❌ Failed to load ${name}: ${src}`);
      reject(new Error(`Failed to load ${name}: ${src}`));
    };
    document.body.appendChild(script);
  });
}

/**
 * 加载所有 LuckySheet 依赖
 * 使用单例模式，确保只加载一次
 * 
 * @returns {Promise<void>}
 * 
 * @example
 * // 在组件中使用
 * import { loadLuckySheet } from '@/utils/luckysheet-loader';
 * 
 * export default {
 *   async mounted() {
 *     try {
 *       await loadLuckySheet();
 *       // 初始化 LuckySheet
 *       luckysheet.create({ ... });
 *     } catch (error) {
 *       console.error('Failed to load LuckySheet:', error);
 *     }
 *   }
 * }
 */
export async function loadLuckySheet() {
  // 如果已经加载完成，直接返回
  if (isLoaded) {
    console.log('✅ LuckySheet already loaded');
    return Promise.resolve();
  }

  // 如果正在加载中，返回同一个 Promise
  if (isLoading && loadPromise) {
    console.log('⏳ LuckySheet is loading, waiting...');
    return loadPromise;
  }

  isLoading = true;
  const startTime = Date.now();
  console.log('🚀 Starting to load LuckySheet and dependencies...');

  loadPromise = (async () => {
    try {
      // 1. 并行加载所有 CSS 文件（不阻塞后续操作）
      console.log('📦 Loading CSS files...');
      const cssPromises = LUCKYSHEET_RESOURCES.css.map(href => loadCSS(href));
      await Promise.all(cssPromises);
      console.log('✅ All CSS files loaded');

      // 2. 按顺序加载 JS 文件（有依赖关系，必须顺序加载）
      console.log('📦 Loading JavaScript files...');
      for (const jsConfig of LUCKYSHEET_RESOURCES.js) {
        await loadScript(jsConfig);
      }
      console.log('✅ All JavaScript files loaded');

      // 3. 验证 LuckySheet 是否可用
      if (typeof window.luckysheet === 'undefined') {
        throw new Error('LuckySheet object not found after loading');
      }

      isLoaded = true;
      const loadTime = Date.now() - startTime;
      console.log(`✅ LuckySheet loaded successfully in ${loadTime}ms`);
      
      return true;
    } catch (error) {
      isLoading = false;
      isLoaded = false;
      loadPromise = null;
      console.error('❌ Failed to load LuckySheet:', error);
      throw error;
    }
  })();

  return loadPromise;
}

/**
 * 检查 LuckySheet 是否已加载
 * @returns {boolean}
 */
export function isLuckySheetLoaded() {
  return isLoaded && typeof window.luckysheet !== 'undefined';
}

/**
 * 重置加载状态（用于测试或强制重新加载）
 * 注意：这不会卸载已加载的资源，只是重置状态标志
 */
export function resetLoadState() {
  console.warn('⚠️ Resetting LuckySheet load state');
  isLoaded = false;
  isLoading = false;
  loadPromise = null;
}

// 导出默认对象
export default {
  loadLuckySheet,
  isLuckySheetLoaded,
  resetLoadState
};

