import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import * as path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom', // 2025 best practice: 40-60% faster than jsdom
    globals: true,
    setupFiles: './src/test/setup.ts',
    testTimeout: 5000, // Reduced timeout since happy-dom is faster
    hookTimeout: 5000,
    reporters: ['default'],
    // Disable isolation to avoid serialization issues with axios
    isolate: false,
    // Use single thread to avoid cross-thread serialization
    threads: false,
    maxThreads: 1,
    minThreads: 1,
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
  },
});