// Docker-specific Vite configuration - Alternative configuration for Docker environment
// This config disables HMR WebSocket connections to avoid connection issues

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  // Development server configuration for Docker
  server: {
    port: 5179,
    host: '0.0.0.0',
    strictPort: true,
    open: false,
    cors: true,
    // Disable HMR WebSocket to avoid connection issues in Docker
    hmr: false,
    // Alternative: Use polling instead of WebSocket
    watch: {
      usePolling: true,
      interval: 1000,
      // Ignore node_modules and other large directories
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/build/**']
    },
    // Proxy configuration for backend services
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/dashboard': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/pusher': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      }
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
      '@assets': path.resolve(__dirname, './src/assets'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@config': path.resolve(__dirname, './src/config')
    }
  },

  // Enhanced optimizations for Docker with MUI compatibility
  optimizeDeps: {
    include: [
      'prop-types', // Critical for MUI
      'react/jsx-runtime',
      'react-dom/client',
      '@mui/material',
      '@mui/icons-material',
      '@emotion/react',
      '@emotion/styled',
      '@clerk/clerk-react',
      '@clerk/types',
      'pusher-js',
      'axios',
      'react-redux',
      '@reduxjs/toolkit'
    ],
    exclude: [
      // Exclude MUI system from pre-bundling to avoid interop issues
      '@mui/system',
      '@mui/material/styles'
    ],
    esbuildOptions: {
      target: 'es2022',
      define: {
        global: 'globalThis',
      }
    },
    force: true // Force re-optimization in Docker
  },

  // Environment configuration
  envPrefix: 'VITE_',
  envDir: '.',

  // Define Docker-specific constants
  define: {
    __DOCKER_ENV__: true,
    __HMR_DISABLED__: true
  }
})