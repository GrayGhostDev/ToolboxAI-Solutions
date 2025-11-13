import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [
    react({
      // Explicit JSX runtime configuration for React 19
      jsxRuntime: 'automatic',
      // Disable Fast Refresh for production stability with React 19
      fastRefresh: false
    })
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
    },
    force: true
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
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          react: [
            'react',
            'react-dom',
            'react/jsx-runtime',
            'react/jsx-dev-runtime',
            'react-router-dom',
            'react-router',
            'react-redux',
            '@reduxjs/toolkit',
            '@remix-run/router',
          ],
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          mantine: [
            '@mantine/core',
            '@mantine/hooks',
            '@mantine/dates',
            '@mantine/charts',
            '@mantine/notifications',
            '@mantine/spotlight',
            '@mantine/tiptap',
          ],
        },
      },
    },
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
