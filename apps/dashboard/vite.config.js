import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Custom plugin to handle missing refractor/lang imports in both dev and build
    {
      name: 'ignore-refractor-langs',
      enforce: 'pre',
      resolveId(id) {
        const cleanId = id.split('?')[0];

        // Intercept refractor/lang imports that don't exist in refractor v5
        if (cleanId.startsWith('refractor/lang/') || cleanId.includes('/refractor/lang/')) {
          return '\0virtual:refractor-lang-stub';
        }
        return null;
      },
      load(id) {
        // Provide empty stub for refractor language imports
        if (id === '\0virtual:refractor-lang-stub') {
          return 'export default function() {}';
        }
        return null;
      }
    }
  ],

  // Optimization for production Mantine integration
  optimizeDeps: {
    esbuildOptions: {
      plugins: [
        {
          name: 'stub-refractor-langs',
          setup(build) {
            // Intercept all refractor/lang/* imports and redirect to stub
            build.onResolve({ filter: /^refractor\/lang\// }, () => {
              return {
                path: path.resolve(__dirname, 'src/utils/refractor-lang-stub.js'),
                external: false
              };
            });
          }
        }
      ]
    },
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
    // Configure HMR for all environments
    hmr: {
      // Use dynamic host detection for better compatibility
      host: 'localhost',
      port: 24678, // Use different port to avoid conflicts with main server
      clientPort: 24678,
      protocol: 'ws',
      overlay: process.env.DOCKER_ENV !== 'true', // Disable overlay only in Docker
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
    chunkSizeWarningLimit: 1500, // Increased to accommodate large libraries like Three.js (1.2MB)

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
      ],

      // Enhanced module resolution
      plugins: [
        // Custom plugin to handle missing language files
        {
          name: 'ignore-missing-langs',
          enforce: 'pre', // Run this plugin before others
          resolveId(id) {
            // Strip query strings from id for checking
            const cleanId = id.split('?')[0];

            // Externalize missing highlight.js language files that were removed in v11+
            if (cleanId.includes('highlight.js/lib/languages/c-like') ||
                cleanId.includes('highlight.js/lib/languages/htmlbars') ||
                cleanId.includes('highlight.js/lib/languages/sql_more') ||
                cleanId.includes('highlight.js/es/languages/c-like') ||
                cleanId.includes('highlight.js/es/languages/htmlbars') ||
                cleanId.includes('highlight.js/es/languages/sql_more')) {
              // Return as external to prevent bundling errors
              return { id: cleanId, external: true };
            }

            // Externalize all refractor/lang imports - these don't exist in refractor v5
            // refractor v4+ uses different structure, v5 has all languages in main export
            if (cleanId.startsWith('refractor/lang/') || cleanId.includes('refractor/lang/')) {
              // Return a virtual module ID that we'll handle in load()
              return '\0virtual:refractor-lang-stub';
            }

            return null;
          },
          load(id) {
            // Strip query strings from id for checking
            const cleanId = id.split('?')[0];

            // Provide empty module for externalized missing language files
            if (cleanId.includes('highlight.js/lib/languages/c-like') ||
                cleanId.includes('highlight.js/lib/languages/htmlbars') ||
                cleanId.includes('highlight.js/lib/languages/sql_more') ||
                cleanId.includes('highlight.js/es/languages/c-like') ||
                cleanId.includes('highlight.js/es/languages/htmlbars') ||
                cleanId.includes('highlight.js/es/languages/sql_more')) {
              return 'export default function() {}';
            }

            // Provide stub for refractor language imports
            if (id === '\0virtual:refractor-lang-stub') {
              return 'export default function() {}';
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