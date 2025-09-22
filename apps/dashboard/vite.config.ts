import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'
import { muiInteropFix } from './vite-plugin-mui-fix.js'

// Enhanced interop helper for MUI compatibility (2025)
// This is a more robust approach that ensures interop functions are available globally
const interopHelper = `
  // Critical: Define interop functions globally BEFORE any modules load
  (function() {
    'use strict';

    // Make interop functions available globally for MUI
    if (typeof window !== 'undefined') {
      // Primary interop function - MUI needs this
      window._interopRequireDefault = function(obj) {
        return obj && obj.__esModule ? obj : { default: obj };
      };

      // Make it available on globalThis too for better compatibility
      globalThis._interopRequireDefault = window._interopRequireDefault;

      // Additional interop helpers
      window._interopRequireWildcard = function(obj) {
        if (obj && obj.__esModule) return obj;
        if (obj === null || (typeof obj !== "object" && typeof obj !== "function")) {
          return { default: obj };
        }
        var cache = {};
        if (obj != null) {
          for (var key in obj) {
            if (Object.prototype.hasOwnProperty.call(obj, key)) {
              cache[key] = obj[key];
            }
          }
        }
        cache.default = obj;
        return cache;
      };

      // Make sure modules can find these functions
      window.__createBinding = window.__createBinding || function(o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
      };

      // Webpack compatibility shim for some modules
      window.__webpack_require__ = window.__webpack_require__ || function(id) {
        return window[id] || {};
      };

      console.log('[Vite] MUI interop helpers injected successfully');
    }
  })();
`

// Check for local node_modules first, then workspace
const muiIconsPath = fs.existsSync(path.resolve(__dirname, 'node_modules/@mui/icons-material'))
  ? path.resolve(__dirname, 'node_modules/@mui/icons-material')
  : path.resolve(__dirname, '../../node_modules/@mui/icons-material')

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    muiInteropFix(), // Add the MUI fix plugin first
    react(),
    {
      name: 'inject-interop-helper',
      transformIndexHtml(html) {
        return html.replace(
          '</head>',
          `<script>${interopHelper}</script></head>`
        )
      }
    }
  ],

  // Enhanced module optimization for 2025 best practices
  optimizeDeps: {
    // Force esbuild to treat MUI as ESM
    esbuildOptions: {
      target: 'es2020',
      define: {
        'global': 'globalThis'
      },
      // Inject interop helpers at build time for each module
      banner: {
        js: `
          // Critical: Define interop functions before any imports
          if (typeof globalThis !== 'undefined' && !globalThis._interopRequireDefault) {
            globalThis._interopRequireDefault = function(obj) {
              return obj && obj.__esModule ? obj : { default: obj };
            };
            globalThis._interopRequireWildcard = function(obj) {
              if (obj && obj.__esModule) return obj;
              if (obj === null || (typeof obj !== "object" && typeof obj !== "function")) return { default: obj };
              var cache = {}; if (obj != null) { for (var key in obj) { if (Object.prototype.hasOwnProperty.call(obj, key)) cache[key] = obj[key]; } } cache.default = obj; return cache;
            };
          }
          if (typeof window !== 'undefined') {
            window._interopRequireDefault = window._interopRequireDefault || globalThis._interopRequireDefault;
            window._interopRequireWildcard = window._interopRequireWildcard || globalThis._interopRequireWildcard;
          }
        `
      },
      // Enable tree shaking for better performance
      treeShaking: true,
      // Handle JSX transform
      jsx: 'automatic',
      // More conservative approach to dropping statements
      drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : []
    },
    include: [
      // Core React ecosystem
      'react/jsx-runtime',
      'react/jsx-dev-runtime',
      'react-dom/client',
      'prop-types',

      // UI Framework - MUI optimizations with specific modules
      '@mui/material',
      '@mui/material/styles',
      '@mui/material/styles/createTheme',
      '@mui/material/styles/createPalette',
      '@mui/system',
      '@mui/system/createStyled',
      '@mui/system/styled',
      '@mui/system/colorManipulator',
      '@mui/utils',
      '@mui/material/Unstable_Grid2',
      '@mui/material/Grid',
      '@mui/material/Box',
      '@mui/material/Typography',
      '@mui/material/Button',
      '@mui/material/Card',
      '@mui/material/CardContent',
      '@mui/icons-material/Add',
      '@mui/icons-material/Search',
      '@mui/icons-material/Refresh',
      // Don't include bare @babel/runtime as it has no main export
      '@babel/runtime/helpers/interopRequireDefault',
      '@babel/runtime/helpers/interopRequireWildcard',
      '@babel/runtime/helpers/extends',
      '@babel/runtime/helpers/objectWithoutPropertiesLoose',
      '@emotion/styled',
      '@emotion/react',
      '@emotion/cache',

      // Mantine UI Framework
      '@mantine/core',
      '@mantine/hooks',
      '@mantine/form',
      '@mantine/notifications',
      '@tabler/icons-react',
      
      // State management
      'react-redux',
      '@reduxjs/toolkit',
      '@reduxjs/toolkit/query',
      
      // Communication libraries
      'pusher-js',
      'axios',
      
      // Utilities
      'date-fns',
      'zod',

      // Clerk Authentication - Fixed optimization paths
      '@clerk/clerk-react',
      '@clerk/types',

      // Performance libraries
      'react-window',
      'web-vitals',
      
      // Three.js libraries - pre-bundle to avoid reconciler issues
      'three',
      '@react-three/fiber',
      '@react-three/drei',
      
      // Charts and their dependencies
      'recharts',
      'chart.js',
      'react-chartjs-2',
      
      // Syntax highlighting - fix ESM/CJS issues
      'react-syntax-highlighter',
      'react-syntax-highlighter/dist/cjs/styles/prism',
      
      // Markdown rendering
      'react-markdown'
    ],
    exclude: [
      '@vite/client',
      '@vite/env',
      // Exclude problematic packages that should be externalized
      'fsevents'
    ],
    // Add entries to ensure they're pre-bundled with interop support
    entries: [
      'src/main.tsx',
      '@mui/material/styles/colorManipulator',
      '@mui/system/colorManipulator'
    ],
    force: true // Force re-optimization to clear cached issues
  },

  // Path resolution
  resolve: {
  alias: {
  '@': path.resolve(__dirname, './src'),
  '@components': path.resolve(__dirname, './src/components'),
  '@store': path.resolve(__dirname, './src/store'),
  '@services': path.resolve(__dirname, './src/services'),
  '@hooks': path.resolve(__dirname, './src/hooks'),
  '@types': path.resolve(__dirname, './src/types'),
  '@utils': path.resolve(__dirname, './src/utils'),
  '@test': path.resolve(__dirname, './src/test'),
    // Enhanced aliases for 2025
    '@assets': path.resolve(__dirname, './src/assets'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@config': path.resolve(__dirname, './src/config')
    },
    dedupe: [
      '@mui/icons-material', 
      '@mui/material', 
      'react', 
      'react-dom', 
      'react-reconciler',
      // Additional dedupe for common conflicts
      '@emotion/react',
      '@emotion/styled',
      'react-redux'
    ],
    // Enhanced conditions for better module resolution
    conditions: ['import', 'module', 'browser', 'default'],
    mainFields: ['browser', 'module', 'main'],
    extensions: ['.tsx', '.ts', '.jsx', '.js', '.json', '.mjs']
  },

  // Development server configuration
  server: {
    port: 5179,
    host: '0.0.0.0', // Allow external connections (needed for Docker)
    strictPort: true,
    open: false,
    cors: true,
    // Disable HMR in Docker, use Pusher for realtime instead
    hmr: process.env.DOCKER_ENV === 'true' ? false : {
      overlay: true,
      clientPort: 5179,
      host: 'localhost',
      port: 5179,
      protocol: 'ws'
    },
    proxy: {
      // Use environment variable for proxy target, fallback to localhost for non-Docker development
      // In Docker, VITE_PROXY_TARGET will be set to http://fastapi-main:8009
      // For local development, it defaults to http://127.0.0.1:8009
      '/dashboard': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/realtime': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/lessons': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/classes': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/assessments': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false,
        // Don't rewrite the path - keep /api/v1/* as is for the backend
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      '/health': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: (process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009').replace('http://', 'ws://'),
        ws: true,
        changeOrigin: true
      },
      '/pusher': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      }
    }
  },

  // Enhanced build configuration for 2025
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    target: 'es2022', // Updated for 2025 - better browser support
    chunkSizeWarningLimit: 500, // Enforce smaller chunks for better caching

    // Terser options for better minification
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
        passes: 2
      },
      mangle: {
        safari10: true
      },
      format: {
        comments: false
      }
    },

    // Enhanced Rollup configuration for 2025
    rollupOptions: {
      // Handle problematic module resolution
      external: [
        // Uncomment to load from CDN in production
        // 'react',
        // 'react-dom'
      ],
      
      // Enhanced module resolution
      plugins: [
        // Custom plugin to handle react-syntax-highlighter ESM/CJS issues
        {
          name: 'resolve-syntax-highlighter',
          resolveId(id) {
            // Redirect problematic ESM imports to CJS versions
            if (id.includes('react-syntax-highlighter/dist/esm')) {
              return id.replace('/dist/esm/', '/dist/cjs/')
            }
            return null
          }
        }
      ],
      
      output: {
        // Simplified manual chunks for actual dependencies
        manualChunks: (id) => {
          // Core React ecosystem
          if (id.includes('react') && !id.includes('react-router') && !id.includes('react-redux')) {
            return 'vendor-react';
          }
          if (id.includes('react-router')) {
            return 'vendor-react-router';
          }

          // State management
          if (id.includes('@reduxjs/toolkit') || id.includes('react-redux')) {
            return 'vendor-redux';
          }

          // UI Framework - combine MUI packages
          if (id.includes('@mui/') || id.includes('@emotion/')) {
            return 'vendor-mui';
          }

          // Mantine UI Framework
          if (id.includes('@mantine/') || id.includes('@tabler/icons-react')) {
            return 'vendor-mantine';
          }

          // Charts and visualization
          if (id.includes('recharts') || id.includes('chart.js') || id.includes('react-chartjs-2')) {
            return 'vendor-charts';
          }

          // 3D libraries - only if actually used
          if (id.includes('three') || id.includes('@react-three/')) {
            return 'vendor-3d';
          }

          // HTTP and realtime
          if (id.includes('axios') || id.includes('pusher-js')) {
            return 'vendor-communication';
          }

          // Utilities
          if (id.includes('date-fns') || id.includes('lodash') || id.includes('zod')) {
            return 'vendor-utils';
          }

          // Large vendor packages
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },

        // Asset naming patterns for cache busting
        entryFileNames: 'assets/app/[name].[hash:8].js',
        chunkFileNames: (chunkInfo) => {
          // Use consistent naming for vendor chunks with cache optimization
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId : '';
          if (chunkInfo.name && chunkInfo.name.startsWith('vendor-')) {
            return 'assets/vendor/[name].[hash:8].js';
          }
          if (facadeModuleId.includes('node_modules')) {
            return 'assets/vendor/[name].[hash:8].js';
          }
          // Pages and components get separate folder for better organization
          if (chunkInfo.name && (chunkInfo.name.includes('pages') || chunkInfo.name.includes('components'))) {
            return 'assets/app/[name].[hash:8].js';
          }
          return 'assets/chunks/[name].[hash:8].js';
        },
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name?.split('.').pop() || '';
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return 'assets/images/[name].[hash][extname]';
          }
          if (/woff|woff2|eot|ttf|otf/i.test(extType)) {
            return 'assets/fonts/[name].[hash][extname]';
          }
          if (extType === 'css') {
            return 'assets/styles/[name].[hash:8][extname]';
          }
          return 'assets/[name].[hash:8][extname]';
        }
      },

      // Note: External dependencies moved to top-level external config

      // Enhanced tree shaking configuration for 2025
      treeshake: {
        moduleSideEffects: (id) => {
          // Preserve side effects for certain modules
          return id.includes('polyfill') || id.includes('global.css') || id.includes('reset.css')
        },
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false,
        preset: 'recommended'
      },

      // Input configuration
      input: {
        main: path.resolve(__dirname, 'index.html'),
      }
    },

    // CSS configuration
    cssCodeSplit: true,
    cssMinify: true,

    // Asset handling
    assetsInlineLimit: 4096, // 4kb
    assetsInclude: ['**/*.gltf', '**/*.glb', '**/*.hdr'],

    // Enable build watch in development
    watch: process.env.NODE_ENV === 'development' ? {} : null,

    // Manifest for asset tracking
    manifest: true,

    // SSR options (if needed in future)
    ssrManifest: false,

    // Report compressed size
    reportCompressedSize: true,

    // Module preload for better performance
    modulePreload: true
  },

  // Test configuration (consolidated from vitest.config.ts)
  test: {
    // Environment configuration for React/DOM testing
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',

    // Timeout configuration
    testTimeout: 10000,
    hookTimeout: 10000,

    // Reporter configuration
    reporters: process.env.CI
      ? ['verbose', 'json', 'junit']
      : ['verbose', 'json'],
    outputFile: {
      json: './test-reports/test-results.json',
      junit: './test-reports/junit.xml',
    },

    // Coverage configuration
    coverage: {
      enabled: process.env.COVERAGE === 'true',
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/**',
        'src/**/*.{test,spec}.{ts,tsx}',
        'src/test/**/*',
        'src/**/*.d.ts',
        'src/types/**/*',
        '**/*.config.*',
        '**/mockData.*',
        'dist/**',
        'coverage/**',
        '.eslintrc.*',
        'src/vite-env.d.ts'
      ],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      },
      all: true,
      clean: true,
      skipFull: false
    },

    // Execution strategy
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true
      }
    },
    isolate: true,
    passWithNoTests: false,

    // Test patterns
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules/**', 'dist/**', 'build/**', 'coverage/**'],

    // Watch configuration
    watchExclude: ['**/node_modules/**', '**/dist/**', '**/coverage/**'],

    // Cache configuration
    cache: {
      dir: 'node_modules/.vitest'
    },

    // Retry configuration for flaky tests
    retry: process.env.CI ? 2 : 0,

    // Benchmark configuration (if needed)
    benchmark: {
      include: ['**/*.bench.{ts,tsx}'],
      exclude: ['node_modules/**']
    }
  },

  // Preview server configuration (for production build preview)
  preview: {
    port: 4173,
    host: '127.0.0.1',
    strictPort: true,
    cors: true,
    headers: {
      'X-Frame-Options': 'DENY',
      'X-Content-Type-Options': 'nosniff',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http://127.0.0.1:8009 ws://127.0.0.1:8009"
    }
  },

  // CSS configuration
  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables" as *;`
      }
    },
    modules: {
      localsConvention: 'camelCaseOnly',
      generateScopedName: '[name]__[local]___[hash:base64:5]'
    }
  },

  // JSON configuration
  json: {
    namedExports: true,
    stringify: false
  },

  // ESBuild configuration
  esbuild: {
    logOverride: { 'this-is-undefined-in-esm': 'silent' },
    tsconfigRaw: {
      compilerOptions: {
        useDefineForClassFields: true
      }
    }
  },

  // Worker configuration
  worker: {
    format: 'es',
    plugins: () => []
  },

  // App type
  appType: 'spa',

  // Environment configuration
  envPrefix: 'VITE_',
  envDir: '.',

  // Log level
  logLevel: 'info',

  // Clear screen on start
  clearScreen: true,

  // Define global constants and enable dead code elimination
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    __DEV__: process.env.NODE_ENV === 'development',
    __TEST__: process.env.NODE_ENV === 'test',
    __PROD__: process.env.NODE_ENV === 'production',
    // Feature flags for tree shaking
    __ENABLE_PERFORMANCE_MONITORING__: JSON.stringify(process.env.NODE_ENV === 'development'),
    __ENABLE_DEBUG_TOOLS__: JSON.stringify(process.env.NODE_ENV === 'development')
  }
})