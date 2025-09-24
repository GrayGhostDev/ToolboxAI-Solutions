import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import * as path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment optimized for 2025 standards
    environment: 'happy-dom', // 40-60% faster than jsdom with React 19 support
    globals: true, // Enable Vitest globals for jest-like experience

    // Setup and configuration
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/cypress/**',
      '**/.{idea,git,cache,output,temp}/**',
      '**/e2e/**', // Exclude Playwright e2e tests
    ],

    // Timeouts optimized for happy-dom performance
    testTimeout: 5000,
    hookTimeout: 5000,
    teardownTimeout: 1000,

    // Reporters and output
    reporters: ['default', 'verbose'],
    outputFile: {
      junit: './test-results/junit.xml',
      json: './test-results/results.json',
    },

    // Performance optimizations for 2025
    isolate: false, // Disable isolation for better performance
    pool: 'forks', // Use forks for better worker management
    poolOptions: {
      forks: {
        singleFork: true, // Single fork for consistency
      },
    },

    // Coverage configuration with v8 (fastest)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'coverage/**',
        'dist/**',
        '**/[.]**',
        'packages/*/test{,s}/**',
        '**/*.d.ts',
        '**/virtual:*',
        '**/__x00__*',
        '**/\x00*',
        'cypress/**',
        'test{,s}/**',
        'test{,-*}.{js,cjs,mjs,ts,tsx,jsx}',
        '**/*{.,-}test.{js,cjs,mjs,ts,tsx,jsx}',
        '**/*{.,-}spec.{js,cjs,mjs,ts,tsx,jsx}',
        '**/tests/**',
        '**/__tests__/**',
        '**/*.config.*',
        '**/vite.config.*',
        '**/vitest.config.*',
        '**/playwright.config.*',
        '**/.storybook/**',
        '**/storybook-static/**',
        '**/e2e/**',
        '**/src/test/**', // Exclude test utilities
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
      all: true,
      clean: true,
    },

    // Watch mode configuration
    watch: {
      ignore: ['**/node_modules/**', '**/dist/**', '**/coverage/**'],
    },

    // Silent mode for cleaner output
    silent: false,
    passWithNoTests: true,

    // Mock handling
    clearMocks: true,
    restoreMocks: true,
    unstubEnvs: true,
    unstubGlobals: true,
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
      '@test': path.resolve(__dirname, './src/test'),
    },
  },

  // Optimize dependency scanning for faster startup
  optimizeDeps: {
    include: [
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event',
      'vitest',
    ],
  },
});