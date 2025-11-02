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
      'zod',

      // Charts and visualization (fixes 504 errors)
      'recharts',
      'react-markdown',
      'remark-gfm',
      'react-chartjs-2',
      'chart.js',

      // 3D libraries
      'three',
      '@react-three/fiber',
      '@react-three/drei'
    ],
    exclude: [
      '@vite/client',
      '@vite/env',
      // Exclude any MUI packages to prevent resolution attempts
      '@mui/*',
      '@material-ui/*',
      '@emotion/*',
      // Exclude highlight.js to prevent pre-bundling issues with missing language files
      'highlight.js',
      'lowlight',
      // Exclude refractor to avoid default export issues
      'refractor',
      'refractor/core',
      // Exclude react-syntax-highlighter to prevent pre-bundling attempts that fail on refractor/core imports
      'react-syntax-highlighter',
      'react-syntax-highlighter/*'
    ],
    force: process.env.NODE_ENV === 'development',
    esbuildOptions: {
      define: { global: 'globalThis' },
      target: 'es2020'
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
      // Enhanced aliases for 2025
      '@assets': path.resolve(__dirname, './src/assets'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@config': path.resolve(__dirname, './src/config'),
      // Force react-syntax-highlighter to use CJS versions (better compatibility)
      'react-syntax-highlighter/dist/esm/prism': 'react-syntax-highlighter/dist/cjs/prism',
      'react-syntax-highlighter/dist/esm/prism-light': 'react-syntax-highlighter/dist/cjs/prism-light',
      'react-syntax-highlighter/dist/esm/prism-async-light': 'react-syntax-highlighter/dist/cjs/prism-async-light',
      'react-syntax-highlighter/dist/esm/light': 'react-syntax-highlighter/dist/cjs/light',
      'react-syntax-highlighter/dist/esm/light-async': 'react-syntax-highlighter/dist/cjs/light-async',
      // Force single instance of three.js to prevent multiple initialization errors
      // Point to root node_modules in workspace setup
      three: path.resolve(__dirname, '../../node_modules/three')
    },
    dedupe: [
      'react',
      'react-dom',
      'react-reconciler',
      'react-redux',
      '@mantine/core',
      '@mantine/hooks',
      'three',
      '@react-three/fiber',
      '@react-three/drei'
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
    // Configure HMR for all environments with improved error handling
    hmr: {
      // Use dynamic host detection for better compatibility
      host: 'localhost',
      port: 24678, // Use different port to avoid conflicts with main server
      clientPort: 24678,
      protocol: 'ws',
      overlay: process.env.DOCKER_ENV !== 'true', // Disable overlay only in Docker
      timeout: 30000, // Increased timeout for slower connections
      // Add error handling
      handleError: (error) => {
        console.warn('HMR WebSocket error (non-critical):', error.message);
        // Don't throw - allow app to continue working
      }
    },
    watch: {
      // Use polling in Docker for file watching
      usePolling: process.env.DOCKER_ENV === 'true',
      interval: 1000,
      // Ignore node_modules for better performance
      ignored: ['**/node_modules/**', '**/.git/**']
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
      '/api/ws': {
        target: (process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009').replace('http://', 'ws://'),
        ws: true,
        changeOrigin: true,
        // Rewrite to remove /api prefix for backend WebSocket endpoints
        rewrite: (path) => path.replace(/^\/api\/ws/, '/ws')
      },
      '/pusher': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      }
    }
  },

  // Enhanced build configuration for 2025 with performance focus - optimized for test performance
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production', // Only in dev for debugging
    minify: 'terser',
    target: 'es2022', // Updated for 2025 - better browser support
    chunkSizeWarningLimit: 200, // Even stricter limit for faster loading in tests

    // Performance-focused build settings
    cssCodeSplit: true,
    cssMinify: true,
    assetsInlineLimit: 2048, // Reduced from 4096 for faster initial load
    reportCompressedSize: false, // Disable for faster builds

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
        // Externalize refractor to avoid default export issues
        'refractor',
        'refractor/core',
        // Externalize all refractor language files
        /^refractor\/lang\/.*/
      ],

      // Enhanced module resolution
      plugins: [
        // Custom plugin to handle missing highlight.js language files and refractor/core
        {
          name: 'ignore-missing-highlight-langs',
          enforce: 'pre', // Run this plugin before others
          resolveId(id, importer) {
            // Externalize missing highlight.js language files that were removed in v11+
            if (id.includes('highlight.js/lib/languages/c-like') ||
                id.includes('highlight.js/lib/languages/htmlbars') ||
                id.includes('highlight.js/lib/languages/sql_more') ||
                id.includes('highlight.js/es/languages/c-like') ||
                id.includes('highlight.js/es/languages/htmlbars') ||
                id.includes('highlight.js/es/languages/sql_more')) {
              // Return as external to prevent bundling errors
              return { id, external: true };
            }
            // Handle refractor/core imports - refractor v4+ removed /core export
            if (id === 'refractor/core' || id === 'refractor/core.js') {
              return '\0virtual:refractor-core';
            }
            // Handle direct refractor imports - refractor doesn't have default export
            // Only intercept when imported from react-syntax-highlighter
            if (id === 'refractor' && importer && importer.includes('react-syntax-highlighter')) {
              return '\0virtual:refractor-main';
            }
            // Redirect problematic ESM imports to CJS versions
            if (id.includes('react-syntax-highlighter/dist/esm')) {
              return id.replace('/dist/esm/', '/dist/cjs/');
            }
            return null;
          },
          load(id) {
            // Provide empty module for externalized missing language files
            if (id.includes('highlight.js/lib/languages/c-like') ||
                id.includes('highlight.js/lib/languages/htmlbars') ||
                id.includes('highlight.js/lib/languages/sql_more') ||
                id.includes('highlight.js/es/languages/c-like') ||
                id.includes('highlight.js/es/languages/htmlbars') ||
                id.includes('highlight.js/es/languages/sql_more')) {
              return 'export default function() {}';
            }
            // Provide stub for refractor/core that mimics the old API
            if (id === '\0virtual:refractor-core') {
              const refractorPath = path.resolve(__dirname, 'node_modules/refractor/index.js');
              return `
                import { refractor } from '${refractorPath}';
                export default refractor;
              `;
            }
            // Provide default export wrapper for main refractor package
            if (id === '\0virtual:refractor-main') {
              const refractorPath = path.resolve(__dirname, 'node_modules/refractor/index.js');
              return `
                import { refractor } from '${refractorPath}';
                export default refractor;
                export * from '${refractorPath}';
              `;
            }
            return null;
          }
        }
      ],

      output: {
        // Enhanced manual chunks for better performance - optimized for sub-2-second initial load
        manualChunks: (id) => {
          // Critical path - load immediately (smallest chunks for fastest initial load)
          if (id.includes('react') && !id.includes('react-router') && !id.includes('react-redux') && !id.includes('react-dom')) {
            return 'critical-react';
          }
          if (id.includes('react-dom')) {
            return 'critical-react-dom';
          }
          if (id.includes('react-router')) {
            return 'essential-router';
          }

          // Essential UI - load with first interaction
          if (id.includes('@mantine/core')) {
            return 'essential-mantine-core';
          }
          if (id.includes('@mantine/hooks')) {
            return 'essential-mantine-hooks';
          }

          // State management - load after initial render
          if (id.includes('@reduxjs/toolkit') || id.includes('react-redux')) {
            return 'state-redux';
          }

          // Icons and extras - defer until needed
          if (id.includes('@tabler/icons-react')) {
            return 'defer-icons';
          }
          if (id.includes('@mantine/') && !id.includes('@mantine/core') && !id.includes('@mantine/hooks')) {
            return 'defer-mantine-extras';
          }

          // Heavy components - lazy load only when needed
          if (id.includes('recharts') || id.includes('chart.js') || id.includes('react-chartjs-2')) {
            return 'lazy-charts';
          }

          // 3D libraries - separate chunks for progressive loading
          if (id.includes('three') && !id.includes('@react-three')) {
            return 'lazy-three-core';
          }
          if (id.includes('@react-three/fiber')) {
            return 'lazy-three-fiber';
          }
          if (id.includes('@react-three/drei')) {
            return 'lazy-three-drei';
          }

          // Network layer - essential but can be deferred slightly
          if (id.includes('axios')) {
            return 'network-http';
          }
          if (id.includes('pusher-js')) {
            return 'network-pusher';
          }

          // Utilities - group by loading priority
          if (id.includes('date-fns') || id.includes('dayjs')) {
            return 'utils-dates';
          }
          if (id.includes('zod')) {
            return 'utils-validation';
          }
          if (id.includes('lodash')) {
            return 'utils-lodash';
          }

          // Development and monitoring - lowest priority
          if (id.includes('sentry') || id.includes('@sentry/')) {
            return 'dev-monitoring';
          }

          // Vendor fallback - split into smaller chunks
          if (id.includes('node_modules')) {
            // Create smaller vendor chunks based on package name hash
            const packageMatch = id.match(/node_modules\/([^\/]+)/);
            if (packageMatch) {
              const packageName = packageMatch[1];
              const hashCode = packageName.split('').reduce((a, b) => {
                a = ((a << 5) - a) + b.charCodeAt(0);
                return a & a;
              }, 0);
              return `vendor-${Math.abs(hashCode) % 4}`; // Split into 4 vendor chunks
            }
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

    // Asset handling
    assetsInclude: ['**/*.gltf', '**/*.glb', '**/*.hdr'],

    // Enable build watch in development
    watch: process.env.NODE_ENV === 'development' ? {} : null,

    // Manifest for asset tracking
    manifest: true,

    // SSR options (if needed in future)
    ssrManifest: false,

    // Enhanced module preload for better performance - prioritize critical chunks
    modulePreload: {
      polyfill: true,
      resolveDependencies: (filename, deps) => {
        // Prioritize loading order based on chunk names
        const criticalChunks = deps.filter(dep =>
          dep.includes('critical-') ||
          dep.includes('essential-') ||
          dep.includes('app.')
        );
        const deferredChunks = deps.filter(dep =>
          dep.includes('defer-') ||
          dep.includes('lazy-') ||
          dep.includes('vendor-')
        );

        // Load critical chunks first, then others
        return [...criticalChunks, ...deferredChunks];
      }
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

      // TEMPORARY: Thresholds disabled for baseline coverage generation (Phase 2 - Task 1.1)
      // Will be re-enabled after establishing baseline metrics
      // Original thresholds: 80% for all metrics, perFile: true, 100% for critical paths
      thresholds: {
        branches: 0,       // Disabled for baseline (was 80)
        functions: 0,      // Disabled for baseline (was 80)
        lines: 0,          // Disabled for baseline (was 80)
        statements: 0,     // Disabled for baseline (was 80)

        // Per-file thresholds disabled for baseline generation
        perFile: false,    // Changed from true

        // Auto-update threshold on improvement
        autoUpdate: false,

        // 100% coverage requirement for critical paths - COMMENTED OUT FOR BASELINE
        // '100': {
        //   branches: 100,
        //   functions: 100,
        //   lines: 100,
        //   statements: 100
        // }
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
    logOverride: {
      'this-is-undefined-in-esm': 'silent',
      // Silence warnings for missing highlight.js language files
      // These were removed in highlight.js v11+ but lowlight/react-syntax-highlighter still try to import them
      'Could not resolve "highlight.js/lib/languages/c-like"': 'silent',
      'Could not resolve "highlight.js/lib/languages/htmlbars"': 'silent',
      'Could not resolve "highlight.js/lib/languages/sql_more"': 'silent',
      'Could not resolve "highlight.js/es/languages/c-like"': 'silent',
      'Could not resolve "highlight.js/es/languages/htmlbars"': 'silent',
      'Could not resolve "highlight.js/es/languages/sql_more"': 'silent'
    },
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