import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


// Plugin to enforce correct module loading order
function reorderModulePreloadsPlugin() {
  return {
    name: 'reorder-modulepreloads',
    transformIndexHtml(html) {
      // Extract all modulepreload links
      const preloadRegex = /<link\s+rel="modulepreload"[^>]*>/g;
      const preloads = html.match(preloadRegex) || [];

      // Sort preloads by the numbered prefix in the href
      const sorted = preloads.sort((a, b) => {
        const getNumber = (link) => {
          const match = link.match(/\/(\d+)-/);
          return match ? parseInt(match[1]) : 999;
        };
        return getNumber(a) - getNumber(b);
      });

      // Remove all existing preloads
      let newHtml = html.replace(preloadRegex, '');

      // Insert sorted preloads before the main script tag
      const scriptPos = newHtml.indexOf('<script type="module"');
      if (scriptPos > 0) {
        newHtml = newHtml.slice(0, scriptPos) +
                  sorted.join('\n    ') + '\n    ' +
                  newHtml.slice(scriptPos);
      }

      return newHtml;
    }
  };
}

export default defineConfig({
  plugins: [
    react({
      // Explicit JSX runtime configuration for React 19
      jsxRuntime: 'automatic',
      // Disable Fast Refresh for production stability with React 19
      fastRefresh: false
    }),
    reorderModulePreloadsPlugin()
  ],

  // Optimize dependencies for faster dev and prevent bundling issues
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
      'react/jsx-dev-runtime',
      '@mantine/core',
      '@mantine/hooks',
      'react-redux',
      '@reduxjs/toolkit',
      '@tabler/icons-react',
      '@sentry/react',
      '@sentry-internal/replay',
      '@sentry-internal/browser-utils'
    ],
    exclude: ['@vite/client', '@vite/env'],
    // Force ESNext target for modern builds
    esbuildOptions: {
      target: 'esnext',
      supported: {
        bigint: true
      }
    }
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@store': path.resolve(__dirname, './src/store'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      // Force single React instance from workspace root (CRITICAL for React 19)
      'react': path.resolve(__dirname, '../../node_modules/react'),
      'react-dom': path.resolve(__dirname, '../../node_modules/react-dom'),
      'react/jsx-runtime': path.resolve(__dirname, '../../node_modules/react/jsx-runtime'),
      'react/jsx-dev-runtime': path.resolve(__dirname, '../../node_modules/react/jsx-dev-runtime'),
      'react-dom/client': path.resolve(__dirname, '../../node_modules/react-dom/client'),
      // Force single instance of three.js
      'three': path.resolve(__dirname, '../../node_modules/three')
    },
    // Prevent multiple React instances
    dedupe: [
      'react',
      'react-dom',
      'react-redux',
      'react-router-dom',
      '@reduxjs/toolkit',
      '@remix-run/router',
      '@mantine/core',
      '@mantine/hooks',
      '@tabler/icons-react',
      'three',
      'framer-motion'
    ]
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: 'terser',
    chunkSizeWarningLimit: 1000,
    // Force ESNext target for modern builds
    target: 'esnext',
    // Enable module preload polyfill to ensure correct chunk loading order
    modulePreload: { polyfill: true },
    rollupOptions: {
      output: {
        // Ensure proper module format
        format: 'es',
        // Control chunk loading order with priority hints
        experimentalMinChunkSize: 100000,
        // Manually separate vendor code with proper loading order
        manualChunks(id) {
          // Only process node_modules
          if (!id.includes('node_modules')) {
            return undefined;
          }

          // React core - HIGHEST PRIORITY (loads first)
          // Check for exact package boundaries using path separators
          if (id.match(/node_modules[/\\]react[/\\]/) ||
              id.match(/node_modules[/\\]react-dom[/\\]/) ||
              id.match(/node_modules[/\\]react-redux[/\\]/) ||
              id.match(/node_modules[/\\]react-router[/\\]/) ||
              id.match(/node_modules[/\\]react-router-dom[/\\]/) ||
              id.match(/node_modules[/\\]@reduxjs[/\\]toolkit[/\\]/) ||
              id.match(/node_modules[/\\]@remix-run[/\\]router[/\\]/) ||
              id.match(/node_modules[/\\]use-sync-external-store[/\\]/) ||
              id.match(/node_modules[/\\]@sentry[/\\]/)) {
            return 'vendor-react';
          }

          // Framer-Motion - MUST load AFTER React (uses React hooks like useLayoutEffect)
          // CRITICAL: Check for exact package boundary to catch all framer-motion code
          if (id.match(/node_modules[/\\]framer-motion[/\\]/)) {
            return 'vendor-mantine';
          }

          // Mantine UI - depends on React
          if (id.match(/node_modules[/\\]@mantine[/\\]/)) {
            return 'vendor-mantine';
          }

          // Emotion libraries - required by framer-motion and Mantine
          if (id.match(/node_modules[/\\]@emotion[/\\]/)) {
            return 'vendor-mantine';
          }

          // Tabler icons - depends on React
          if (id.match(/node_modules[/\\]@tabler[/\\]icons[/\\]/)) {
            return 'vendor-icons';
          }

          // React-Three-Fiber - MUST load AFTER React (uses React hooks)
          if (id.match(/node_modules[/\\]@react-three[/\\](fiber|drei)[/\\]/)) {
            return 'vendor-react-three';
          }

          // Three.js core library (no React dependencies)
          if (id.match(/node_modules[/\\]three[/\\]/)) {
            return 'vendor-three';
          }

          // Everything else
          return 'vendor-other';
        },
        // Ensure React chunk has priority in loading
        chunkFileNames: (chunkInfo) => {
          // Prefix React chunk to load first alphabetically
          if (chunkInfo.name === 'vendor-react') {
            return 'assets/00-vendor-react-[hash].js';
          }
          if (chunkInfo.name === 'vendor-mantine') {
            return 'assets/01-vendor-mantine-[hash].js';
          }
          if (chunkInfo.name === 'vendor-icons') {
            return 'assets/02-vendor-icons-[hash].js';
          }
          // React-Three-Fiber must load AFTER React but BEFORE Three.js core
          if (chunkInfo.name === 'vendor-react-three') {
            return 'assets/03-vendor-react-three-[hash].js';
          }
          // Three.js core library
          if (chunkInfo.name === 'vendor-three') {
            return 'assets/04-vendor-three-[hash].js';
          }
          // All other vendors load last
          if (chunkInfo.name === 'vendor-other') {
            return 'assets/05-vendor-other-[hash].js';
          }
          return 'assets/[name]-[hash].js';
        }
      }
    }
  },
  server: {
    port: 5179,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path  // Keep /api prefix intact
      }
    }
  }
});
