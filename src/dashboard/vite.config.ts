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
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    testTimeout: 10000,
    hookTimeout: 10000,
    pool: 'forks', // Use forks instead of threads to avoid serialization issues
    isolate: true,
  },
  optimizeDeps: {
    include: [
      '@mui/material',
      '@mui/material/Unstable_Grid2',
      '@mui/material/Grid',
      '@emotion/styled',
      '@emotion/react',
      '@mui/icons-material',
    ],
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
    },
    dedupe: ['@mui/icons-material', '@mui/material', 'react', 'react-dom'],
  },
  server: {
    port: 5179,
    host: '127.0.0.1',
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8008',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://127.0.0.1:8008',
        ws: true,
        changeOrigin: true
      }
    }
  },
})