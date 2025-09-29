// Node.js 22 LTS Features Configuration
import { WebSocket } from 'node:websocket';
import { test, describe } from 'node:test';
import { watch } from 'node:fs/promises';

/**
 * Node.js 22 LTS New Features
 * These features are now available natively without external dependencies
 */

// Native WebSocket Client (Stable in Node.js 22)
export const createWebSocketConnection = (url: string): WebSocket => {
  const ws = new WebSocket(url);

  ws.on('open', () => {
    console.log('WebSocket connection established');
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  return ws;
};

// Native Test Runner Configuration
export const testConfig = {
  // Enable TypeScript support in native test runner
  extensions: ['ts', 'tsx', 'js', 'jsx'],

  // Test file patterns
  patterns: [
    '**/*.test.ts',
    '**/*.spec.ts',
    '**/*.test.tsx',
    '**/*.spec.tsx'
  ],

  // Reporter options
  reporter: process.env.CI ? 'tap' : 'spec',

  // Concurrency
  concurrency: true,

  // Watch mode
  watch: process.env.NODE_ENV !== 'production'
};

// Native Watch Mode for Development
export const setupFileWatcher = async (directory: string, callback: (filename: string) => void) => {
  try {
    const watcher = watch(directory, { recursive: true });

    for await (const event of watcher) {
      if (event.filename) {
        callback(event.filename);
      }
    }
  } catch (error) {
    console.error('File watcher error:', error);
  }
};

// Performance improvements in Node.js 22
export const performanceConfig = {
  // V8 optimizations
  v8: {
    // Improved garbage collection
    exposeGC: process.env.NODE_ENV === 'development',

    // JIT compilation improvements
    useCodeCache: true,

    // Memory management
    maxOldSpaceSize: 4096, // MB
  },

  // Network optimizations
  network: {
    // HTTP/3 support (experimental)
    http3: process.env.ENABLE_HTTP3 === 'true',

    // Keep-alive improvements
    keepAliveTimeout: 65000,

    // Headers timeout
    headersTimeout: 65000,
  },

  // Worker threads improvements
  workers: {
    // Improved worker thread pool
    poolSize: process.env.WORKER_POOL_SIZE || 'auto',

    // SharedArrayBuffer support
    enableSharedArrayBuffer: true,
  }
};

// Environment-specific configurations
export const getNodeConfig = () => {
  const isProduction = process.env.NODE_ENV === 'production';

  return {
    // Enable source maps in production for better debugging
    enableSourceMaps: true,

    // Use native fetch (stable in Node.js 22)
    useNativeFetch: true,

    // Use native crypto.randomUUID()
    useNativeCrypto: true,

    // Permission model (new in Node.js 22)
    permissions: {
      fs: {
        read: isProduction ? ['./dist', './public'] : ['./'],
        write: isProduction ? ['./logs'] : ['./']
      },
      net: isProduction ? ['127.0.0.1', '::1'] : undefined
    },

    // ESM loader hooks
    loaders: {
      typescript: '@node-loader/typescript',
      importMaps: true
    }
  };
};

// Migrate from external packages to native features
export const migrationGuide = {
  // Replace 'ws' package with native WebSocket
  websocket: {
    before: "import WebSocket from 'ws';",
    after: "import { WebSocket } from 'node:websocket';",
  },

  // Replace 'node-fetch' with native fetch
  fetch: {
    before: "import fetch from 'node-fetch';",
    after: "// fetch is now globally available",
  },

  // Replace 'uuid' with native crypto
  uuid: {
    before: "import { v4 as uuidv4 } from 'uuid';",
    after: "import { randomUUID } from 'node:crypto';",
  },

  // Use native test runner instead of Jest/Mocha
  testing: {
    before: "import { describe, it, expect } from '@jest/globals';",
    after: "import { describe, it } from 'node:test'; import assert from 'node:assert';",
  }
};

export default {
  createWebSocketConnection,
  testConfig,
  setupFileWatcher,
  performanceConfig,
  getNodeConfig,
  migrationGuide
};
