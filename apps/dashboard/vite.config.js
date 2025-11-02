import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],

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
      '@reduxjs/toolkit'
    ],
    exclude: ['@vite/client', '@vite/env']
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
      // Fix refractor module resolution for react-syntax-highlighter
      'refractor': path.resolve(__dirname, '../../node_modules/refractor'),
      'refractor/core': path.resolve(__dirname, '../../node_modules/refractor/core.js'),
      // Force single instance of three.js
      'three': path.resolve(__dirname, '../../node_modules/three')
    },
    // Prevent multiple React instances
    dedupe: [
      'react',
      'react-dom',
      'react-redux',
      '@mantine/core',
      '@mantine/hooks',
      'three'
    ]
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: 'terser',
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 5179,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
