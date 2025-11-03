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
  plugins: [react(), reorderModulePreloadsPlugin()],

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
      '@tabler/icons-react'
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
      '@tabler/icons-react',
      'three',
      '@react-three/fiber',
      '@react-three/drei'
    ]
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: 'terser',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Ensure proper module format
        format: 'es',
        // Control chunk loading order with priority hints
        experimentalMinChunkSize: 100000,
        // Manually separate vendor code with proper loading order
        manualChunks(id) {
          // Bundle React and core deps into vendor chunk
          if (id.includes('node_modules')) {
            // React core - HIGHEST PRIORITY (loads first)
            if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/react-redux/') ||
                id.includes('\\react\\') || id.includes('\\react-dom\\') || id.includes('\\react-redux\\')) {
              return 'vendor-react';
            }
            // Mantine UI - depends on React
            if (id.includes('@mantine')) {
              return 'vendor-mantine';
            }
            // Tabler icons - depends on React
            if (id.includes('@tabler/icons')) {
              return 'vendor-icons';
            }
            // React-Three-Fiber - MUST load AFTER React (uses React hooks)
            // Check this BEFORE checking for 'three' to avoid bundling with Three.js core
            if (id.includes('@react-three/fiber') || id.includes('@react-three/drei')) {
              return 'vendor-react-three';
            }
            // Three.js core library (no React dependencies)
            if (id.includes('/three/') || id.includes('\\three\\')) {
              return 'vendor-three';
            }
            // Everything else
            return 'vendor-other';
          }
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
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
