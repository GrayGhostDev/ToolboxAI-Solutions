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

  // Module optimization
  optimizeDeps: {
    include: [
      '@mui/material',
      '@mui/material/Unstable_Grid2',
      '@mui/material/Grid',
      '@mui/icons-material',
      '@emotion/styled',
      '@emotion/react',
      'react-redux',
      '@reduxjs/toolkit',
      'pusher-js',
      'recharts',
      'chart.js',
      'react-chartjs-2',
      'axios',
      'date-fns',
      'zod'
    ],
    exclude: ['@vite/client', '@vite/env'],
    esbuildOptions: {
      target: 'es2020',
    }
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
    dedupe: ['@mui/icons-material', '@mui/material', 'react', 'react-dom'],
  },

  // Development server configuration
  server: {
    port: 5179,
    host: '127.0.0.1',
    strictPort: true,
    open: false,
    cors: true,
    hmr: {
      overlay: true,
      clientPort: 5179
    },
    proxy: {
      // Proxy all backend API endpoints
      '/dashboard': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/realtime': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/lessons': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/classes': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/assessments': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/api': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
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
      '/ws': {
        target: 'ws://127.0.0.1:8009',
        ws: true,
        changeOrigin: true
      },
      '/socket.io': {
        target: 'ws://127.0.0.1:8009',
        ws: true,
        changeOrigin: true,
      },
      '/pusher': {
        target: 'http://127.0.0.1:8009',
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
    chunkSizeWarningLimit: 1000,

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

    // Rollup configuration
    rollupOptions: {
      output: {
        // Manual chunks for optimal code splitting
        manualChunks: {
          // Core React ecosystem
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],

          // State management
          'vendor-redux': ['@reduxjs/toolkit', 'react-redux'],

          // UI Framework
          'vendor-mui': ['@mui/material', '@mui/icons-material'],
          'vendor-emotion': ['@emotion/react', '@emotion/styled'],

          // Charts and visualization
          'vendor-charts': ['recharts', 'chart.js', 'react-chartjs-2'],

          // Utilities
          'vendor-utils': ['axios', 'date-fns', 'zod'],

          // Real-time communication
          'vendor-realtime': ['pusher-js', 'socket.io-client'],

          // Internationalization
          'vendor-i18n': ['i18next', 'react-i18next'],

          // Chat components
          'vendor-chat': ['react-chat-elements', 'react-markdown', 'react-syntax-highlighter'],
        },

        // Asset naming patterns for cache busting
        entryFileNames: (chunkInfo) => {
          return chunkInfo.name === 'index'
            ? 'assets/[name].[hash].js'
            : 'assets/[name].[hash].js';
        },
        chunkFileNames: (chunkInfo) => {
          // Use consistent naming for vendor chunks
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId : '';
          if (facadeModuleId.includes('node_modules')) {
            return 'assets/vendor/[name].[hash].js';
          }
          return 'assets/chunks/[name].[hash].js';
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
            return 'assets/styles/[name].[hash][extname]';
          }
          return 'assets/[name].[hash][extname]';
        }
      },

      // External dependencies (if needed for CDN)
      external: [],

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

    // Polyfill configuration
    polyfillModulePreload: true
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
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http://127.0.0.1:8008 ws://127.0.0.1:8008"
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

  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    __DEV__: process.env.NODE_ENV === 'development',
    __TEST__: process.env.NODE_ENV === 'test',
    __PROD__: process.env.NODE_ENV === 'production'
  }
})