import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';

// Use the new typescript-eslint v8 config helper
export default tseslint.config(
  // Base JavaScript recommended rules
  js.configs.recommended,

  // TypeScript recommended rules
  ...tseslint.configs.recommended,

  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    languageOptions: {
      ecmaVersion: 2025, // Updated to 2025
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2025, // Updated to ES2025
        ...globals.node,
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        projectService: true, // Use projectService instead of project for better performance
        tsconfigRootDir: import.meta.dirname,
      },
    },
    settings: {
      react: {
        version: '19.1.0' // Explicitly set React 19
      }
    },
    plugins: {
      'react': reactPlugin,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // React 19 specific configurations
      'react/jsx-uses-react': 'off', // Not needed in React 19
      'react/react-in-jsx-scope': 'off', // Not needed with new JSX transform
      'react/prop-types': 'off', // TypeScript handles this

      // React Hooks rules
      ...reactHooks.configs.recommended.rules,

      // React Refresh (Vite HMR)
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // TypeScript rules for 2025
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_'
        },
      ],
      '@typescript-eslint/no-explicit-any': 'warn', // Changed to warn
      '@typescript-eslint/consistent-type-imports': [
        'warn',
        {
          prefer: 'type-imports',
          fixStyle: 'inline-type-imports'
        }
      ],

      // General rules
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'semi': ['error', 'always'],
      'quotes': ['error', 'single', { avoidEscape: true }],
      'no-undef': 'off', // TypeScript handles this
      'prefer-const': 'error',
      'no-debugger': 'error',
    },
  },

  // Test files configuration
  {
    files: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': 'off'
    }
  },

  {
    ignores: [
      'dist',
      'build',
      'node_modules',
      '*.config.js',
      '*.config.ts',
      'vite.config.ts',
      'backend/**',
      '**/venv/**',
      '**/.venv/**',
      '**/venv_clean/**',
      'coverage/**',
      '.coverage/**',
      '**/coverage/**'
    ],
  }
);
