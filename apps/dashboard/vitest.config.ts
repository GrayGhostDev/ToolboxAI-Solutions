import react from '@vitejs/plugin-react';
import * as  path from 'path';
import { defineConfig } from 'vitest/config';

// Following official Vitest documentation best practices
// https://vitest.dev/guide/
export default defineConfig({
  plugins: [react()] as any,
  test: {
    // Environment configuration for React/DOM testing
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',

    // Timeout configuration
    testTimeout: 10000,
    hookTimeout: 10000,

    // Reporter configuration
    // Using built-in reporters that don't require additional dependencies
    reporters: ['verbose', 'json'],
    outputFile: {
      json: './test-reports/test-results.json',
    },

    // Coverage configuration
    // Note: Coverage requires @vitest/coverage-v8 or @vitest/coverage-istanbul
    // Run with: vitest run --coverage
    coverage: {
      enabled: false,  // Enable via CLI with --coverage flag
      provider: 'v8',  // Default provider, requires @vitest/coverage-v8
      reporter: ['text', 'json'],  // Removed 'html' as it requires @vitest/ui
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/**',
        'src/**/*.{test,spec}.{ts,tsx}',
        'src/test/**/*',
        'src/**/*.d.ts',
        'src/types/**/*',
      ],
    },

    // Execution strategy
    pool: 'forks',  // Better for DOM/Node.js compatibility
    isolate: true,  // Isolate tests for better reliability

    // Test patterns following Vitest conventions
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules/**', 'dist/**', 'build/**'],
  },

  // Resolve configuration for module aliases
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
  },

  // Development server configuration
  server: {
    port: 5179,
    host: '127.0.0.1',
    strictPort: true,
  },
});
