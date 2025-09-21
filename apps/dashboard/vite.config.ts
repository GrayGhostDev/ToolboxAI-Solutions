import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Check for local node_modules first, then workspace
const muiIconsPath = fs.existsSync(path.resolve(__dirname, 'node_modules/@mui/icons-material'))
  ? path.resolve(__dirname, 'node_modules/@mui/icons-material')
  : path.resolve(__dirname, '../../node_modules/@mui/icons-material')

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Module optimization for faster dev server startup
  optimizeDeps: {
    include: [
      // Core dependencies that should be pre-bundled
      '@mui/material',
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
      '@emotion/styled',
      '@emotion/react',
      'react-redux',
      '@reduxjs/toolkit',
      '@reduxjs/toolkit/query',
      'pusher-js',
      'axios',
      'date-fns',
      'zod',
      // Performance libraries
      'react-window',
      'web-vitals',
      // Three.js libraries - pre-bundle to avoid reconciler issues
      'three',
      '@react-three/fiber',
      '@react-three/drei',
      'react-reconciler',
      // Charts and their dependencies
      'recharts',
      'lodash',
      'lodash/get',
      'lodash/isNil',
      'lodash/isFunction',
      'chart.js',
      'react-chartjs-2'
    ],
    exclude: [
      '@vite/client',
      '@vite/env'
    ],
    esbuildOptions: {
      target: 'es2020',
      // Enable tree shaking for better performance
      treeShaking: true,
      // Minify deps in dev for smaller bundle
      minify: false,
      // Use more aggressive optimization
      drop: ['console', 'debugger']
    },
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
    },
    dedupe: ['@mui/icons-material', '@mui/material', 'react', 'react-dom', 'react-reconciler'],
  },

  // Development server configuration
  server: {
    port: 5179,
    host: '0.0.0.0', // Allow external connections (needed for Docker)
    strictPort: true,
    open: false,
    cors: true,
    hmr: {
      overlay: true,
      clientPort: 5179
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

  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    target: 'es2020',
    chunkSizeWarningLimit: 500, // Reduced from 800 to enforce smaller chunks

    // Enhanced Terser options for better minification
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.warn'],
        passes: 3, // Increased passes for better compression
        unsafe: true,
        unsafe_comps: true,
        unsafe_math: true,
        unsafe_proto: true,
        dead_code: true,
        keep_infinity: true,
        reduce_vars: true,
        sequences: true,
        conditionals: true,
        comparisons: true,
        evaluate: true,
        booleans: true,
        loops: true,
        unused: true,
        hoist_funs: true,
        hoist_props: true,
        hoist_vars: true,
        if_return: true,
        inline: true,
        join_vars: true,
        cascade: true,
        collapse_vars: true,
        reduce_funcs: true,
        warnings: false,
        negate_iife: true,
        pure_getters: true,
        pure_new: true,
        keep_fargs: false,
        keep_fnames: false
      },
      mangle: {
        safari10: true,
        properties: {
          regex: /^_/
        }
      },
      format: {
        comments: false,
        ascii_only: true
      }
    },

    // Rollup configuration
    rollupOptions: {
      output: {
        // Enhanced manual chunks for optimal code splitting
        manualChunks: (id) => {
          // Core React ecosystem - split for better caching
          if (id.includes('react/') && !id.includes('react-router') && !id.includes('react-redux')) {
            return 'vendor-react-core';
          }
          if (id.includes('react-dom')) {
            return 'vendor-react-dom';
          }
          if (id.includes('react-router')) {
            return 'vendor-react-router';
          }

          // State management - separate from React
          if (id.includes('@reduxjs/toolkit') || id.includes('react-redux')) {
            return 'vendor-redux';
          }

          // UI Framework - granular chunks for better caching
          if (id.includes('@mui/material/styles') || id.includes('@mui/system')) {
            return 'vendor-mui-system';
          }
          if (id.includes('@mui/material') && (id.includes('Button') || id.includes('TextField') || id.includes('Typography') || id.includes('Box') || id.includes('Stack'))) {
            return 'vendor-mui-core';
          }
          if (id.includes('@mui/material') && (id.includes('Table') || id.includes('Grid') || id.includes('Card') || id.includes('Paper'))) {
            return 'vendor-mui-layout';
          }
          if (id.includes('@mui/material') && (id.includes('Dialog') || id.includes('Drawer') || id.includes('Menu') || id.includes('Popover'))) {
            return 'vendor-mui-navigation';
          }
          if (id.includes('@mui/material')) {
            return 'vendor-mui-components';
          }
          if (id.includes('@mui/icons-material')) {
            return 'vendor-mui-icons';
          }
          if (id.includes('@emotion')) {
            return 'vendor-emotion';
          }

          // Charts and visualization - separate by library type
          if (id.includes('recharts')) {
            return 'vendor-charts-recharts';
          }
          if (id.includes('chart.js') || id.includes('react-chartjs-2')) {
            return 'vendor-charts-chartjs';
          }

          // 3D and Three.js - split by functionality for lazy loading
          if (id.includes('three/build/three.module.js')) {
            return 'vendor-3d-core';
          }
          if (id.includes('three/') && id.includes('loaders')) {
            return 'vendor-3d-loaders';
          }
          if (id.includes('@react-three/fiber')) {
            return 'vendor-3d-fiber';
          }
          if (id.includes('@react-three/drei')) {
            return 'vendor-3d-drei';
          }
          if (id.includes('three')) {
            return 'vendor-3d-utils';
          }

          // Communication and real-time
          if (id.includes('pusher-js')) {
            return 'vendor-realtime-pusher';
          }
          if (id.includes('axios')) {
            return 'vendor-http';
          }

          // Utilities - split by usage frequency
          if (id.includes('date-fns')) {
            return 'vendor-date';
          }
          if (id.includes('zod')) {
            return 'vendor-validation';
          }
          if (id.includes('lodash')) {
            return 'vendor-lodash';
          }

          // Internationalization
          if (id.includes('i18next') || id.includes('react-i18next')) {
            return 'vendor-i18n';
          }

          // Chat and markdown - feature-specific
          if (id.includes('react-chat-elements')) {
            return 'vendor-chat';
          }
          if (id.includes('react-markdown') || id.includes('react-syntax-highlighter')) {
            return 'vendor-markdown';
          }

          // Animation libraries
          if (id.includes('framer-motion')) {
            return 'vendor-animation';
          }

          // Performance monitoring
          if (id.includes('react-window') || id.includes('web-vitals')) {
            return 'vendor-performance';
          }

          // GraphQL
          if (id.includes('@apollo/client') || id.includes('graphql')) {
            return 'vendor-graphql';
          }

          // Small utilities that can be grouped
          if (id.includes('node_modules') && (
            id.includes('classnames') ||
            id.includes('clsx') ||
            id.includes('prop-types') ||
            id.includes('react-is') ||
            id.includes('scheduler') ||
            id.includes('object-assign') ||
            id.includes('loose-envify')
          )) {
            return 'vendor-utils-small';
          }

          // Everything else from node_modules
          if (id.includes('node_modules')) {
            return 'vendor-misc';
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

      // External dependencies for CDN optimization (optional)
      external: [
        // Uncomment to load from CDN in production
        // 'react',
        // 'react-dom'
      ],

      // Tree shaking configuration
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false
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
    modulePreload: {
      polyfill: true
    }
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