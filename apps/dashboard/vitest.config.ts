import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    // Debug-specific configuration
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',

    // Debug settings
    testTimeout: 30000,
    hookTimeout: 30000,
    teardownTimeout: 30000,

    // Debug output
    reporter: ['verbose', 'html', 'json'],
    outputFile: {
      html: './test-reports/debug-report.html',
      json: './test-reports/debug-report.json',
    },

    // Debug coverage
    coverage: {
      enabled: true,
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      reportsDirectory: './test-reports/coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/test/**/*',
        'src/**/*.d.ts',
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
    },

    // Debug parallel execution
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },

    // Debug isolation
    isolate: true,

    // Debug logging
    logHeapUsage: true,
    passWithNoTests: true,

    // Debug specific test patterns
    include: ['src/**/*.{test,spec}.{ts,tsx}', 'src/**/*.debug.{ts,tsx}'],

    // Debug exclude patterns
    exclude: ['node_modules/**', 'dist/**', 'build/**', '**/*.d.ts'],
  },

  // Debug resolve configuration
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

  // Debug server configuration
  server: {
    port: 5179,
    host: '127.0.0.1',
    strictPort: true,
  },
});
