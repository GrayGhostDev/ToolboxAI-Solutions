import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react()
  ],

  // Optimization for production Mantine integration
  optimizeDeps: {
    include: [
      // Core React ecosystem
      'react',
      'react-dom',
      'react/jsx-runtime',
      'react/jsx-dev-runtime',

      // Mantine UI Framework
      '@mantine/core',
      '@mantine/hooks',
      '@mantine/form',
      '@mantine/notifications',
      '@mantine/dates',
      '@mantine/charts',
      '@mantine/spotlight',
      '@mantine/tiptap',
      '@tabler/icons-react',

      // State management
      'react-redux',
      '@reduxjs/toolkit',

      // Communication libraries
      'pusher-js',
      'axios',

      // Essential utilities
      'date-fns',
      'dayjs',
      'zod'
    ],
    exclude: [
      '@vite/client',
      '@vite/env',
      // Exclude any MUI packages to prevent resolution attempts
      '@mui/*',
      '@material-ui/*',
      '@emotion/*'
    ]
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
      'react',
      'react-dom',
      'react-reconciler',
      'react-redux',
      '@mantine/core',
      '@mantine/hooks'
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
    // Configure HMR for Docker environment
    hmr: process.env.DOCKER_ENV === 'true' ? {
      // Docker HMR configuration
      clientPort: 5179,
      host: 'localhost',
      protocol: 'ws',
      port: 5179,
      overlay: false // Disable overlay in Docker to prevent connection errors
    } : {
      // Local development HMR
      overlay: true,
      clientPort: 5179,
      host: 'localhost',
      port: 5179,
      protocol: 'ws'
    },
    watch: {
      // Use polling in Docker for file watching
      usePolling: process.env.DOCKER_ENV === 'true',
      interval: 1000
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

    // Coverage configuration - 2025 standards (>80% all metrics)
    coverage: {
      enabled: process.env.COVERAGE === 'true',
      provider: 'v8', // V8 provider for accurate coverage

      // Multiple reporters for different use cases
      reporter: [
        'text',           // Console output
        'text-summary',   // Brief summary
        'json',           // Machine-readable format
        'json-summary',   // Summary in JSON
        'html',           // Interactive HTML report
        'lcov',           // For CI/CD integration
        'cobertura'       // For CI/CD integration (Jenkins, Azure DevOps)
      ],

      reportsDirectory: './coverage',

      // Files to include in coverage
      include: [
        'src/**/*.{ts,tsx}',
        'src/**/*.{js,jsx}'
      ],

      // Files to exclude from coverage
      exclude: [
        // Dependencies and build artifacts
        'node_modules/**',
        'dist/**',
        'coverage/**',
        'build/**',
        '.storybook/**',

        // Test files
        'src/**/*.{test,spec}.{ts,tsx,js,jsx}',
        'src/test/**/*',
        'src/__tests__/**/*',
        'src/**/__tests__/**/*',

        // Type definitions
        'src/**/*.d.ts',
        'src/types/**/*',
        'src/vite-env.d.ts',

        // Config files
        '**/*.config.*',
        '.eslintrc.*',
        'postcss.config.*',

        // Mock data and fixtures
        '**/mockData.*',
        '**/fixtures/**',

        // Stories and examples
        '**/*.stories.{ts,tsx,js,jsx}',

        // Entry points (already tested through integration)
        'src/main.tsx',
        'src/App.tsx',

        // Constants and static data
        'src/constants/**',
        'src/config/constants.ts'
      ],

      // Enforce >80% coverage thresholds (2025 standards)
      thresholds: {
        branches: 80,      // Branch coverage (if/else, switch)
        functions: 80,     // Function coverage
        lines: 80,         // Line coverage
        statements: 80,    // Statement coverage

        // Per-file thresholds (stricter)
        perFile: true,

        // Auto-update threshold on improvement
        autoUpdate: false,

        // 100% coverage requirement for critical paths
        '100': {
          branches: 100,
          functions: 100,
          lines: 100,
          statements: 100
        }
      },

      // Include all source files, even if not tested
      all: true,

      // Clean coverage results before running
      clean: true,
      cleanOnRerun: true,

      // Don't skip files with 100% coverage
      skipFull: false,

      // Additional V8 options
      allowExternal: false,

      // Source map support for accurate line mapping
      sourceMap: true,

      // Report uncovered lines/functions
      reportOnFailure: true,

      // Watermarks for visual indicators
      watermarks: {
        statements: [80, 95],
        branches: [80, 95],
        functions: [80, 95],
        lines: [80, 95]
      }
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

  // ESBuild configuration (will be replaced with SWC WASM)
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
});