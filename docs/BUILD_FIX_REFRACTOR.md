# Build Error Fix - Refractor Module Issue

**Date:** November 8, 2025  
**Error:** `Could not load refractor/lang/abap.js: ENOENT`  
**Status:** ✅ FIXED

---

## Problem

The build was failing with an error related to missing `refractor` language files:

```
[commonjs--resolver] Could not load /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/node_modules/refractor/lang/abap.js: ENOENT: no such file or directory
```

---

## Root Causes

1. **Missing Dependency:** `refractor` was not installed as a direct dependency, only used indirectly through `react-syntax-highlighter`
2. **Problematic Vite Plugin:** Custom `refractorImportPlugin` was trying to resolve module paths incorrectly
3. **Vite Config Issues:** Incorrectly configured external modules and aliases for refractor
4. **Cache Issues:** Vite cache was holding old configuration

---

## Solutions Applied

### 1. Installed Refractor Dependency
```bash
npm install refractor@^4.8.1 --save
```

### 2. Removed Problematic Plugin
Removed the custom `refractorImportPlugin()` function and its usage from `vite.config.js`

**Before:**
```javascript
// Plugin to rewrite refractor imports
function refractorImportPlugin() {
  return {
    name: 'refractor-import-rewrite',
    resolveId(id) { /* ... */ },
    load(id) { /* ... */ }
  };
}

export default defineConfig({
  plugins: [
    react({ /* ... */ }),
    refractorImportPlugin(), // ❌ Removed
    reorderModulePreloadsPlugin()
  ],
```

**After:**
```javascript
export default defineConfig({
  plugins: [
    react({ /* ... */ }),
    reorderModulePreloadsPlugin() // ✅ Only this plugin
  ],
```

### 3. Fixed Build Configuration

**Removed external configuration:**
```javascript
// Before
rollupOptions: {
  external: (id) => id === 'refractor' || id === 'refractor/core', // ❌ Removed
  output: { /* ... */ }
}

// After
rollupOptions: {
  output: { /* ... */ } // ✅ Let Vite handle it naturally
}
```

**Removed problematic aliases:**
```javascript
// Before
resolve: {
  alias: {
    'refractor': path.resolve(__dirname, '../../node_modules/refractor'), // ❌ Removed
    'refractor/core': path.resolve(__dirname, '../../node_modules/refractor/lib/core.js'), // ❌ Removed
  }
}

// After
resolve: {
  alias: {
    // Let Vite resolve refractor naturally ✅
  }
}
```

### 4. Updated Optimization Config

Added `refractor` and `react-syntax-highlighter` to exclude list:

```javascript
optimizeDeps: {
  include: [
    // ... other dependencies
  ],
  exclude: [
    '@vite/client',
    '@vite/env',
    'refractor', // ✅ Added
    'react-syntax-highlighter' // ✅ Added
  ],
}
```

### 5. Cleared Vite Cache
```bash
cd apps/dashboard
rm -rf node_modules/.vite node_modules/.vite-temp dist .vite
```

---

## Files Modified

1. **`apps/dashboard/vite.config.js`**
   - Removed `refractorImportPlugin` function
   - Removed plugin from plugins array
   - Removed external configuration for refractor
   - Removed refractor aliases
   - Added refractor to exclude list in optimizeDeps

2. **`package.json`** (root)
   - Added `refractor@^4.8.1` as a dependency

---

## Why This Fixes the Issue

1. **Direct Dependency:** Installing `refractor` directly ensures it's available in node_modules with all its language files

2. **Natural Resolution:** Removing custom resolution logic allows Vite to handle the module naturally using its built-in CommonJS support

3. **No External Exclusion:** Removing the `external` configuration allows Vite to bundle refractor properly instead of trying to load it at runtime

4. **Proper Optimization:** Excluding from `optimizeDeps` prevents pre-bundling issues with dynamic imports

---

## Testing

To verify the fix:

```bash
# Clean build
npm run dashboard:build

# Should complete successfully without refractor errors
```

---

## Related Dependencies

- `react-syntax-highlighter@^15.5.1` - Code syntax highlighting component
- `refractor@^4.8.1` - Language syntax highlighter (peer dependency)
- `prismjs@^1.30.0` - Syntax highlighting library

---

## Prevention

To prevent similar issues in the future:

1. **Check Peer Dependencies:** Always install peer dependencies explicitly
2. **Avoid Custom Resolution:** Use Vite's built-in module resolution when possible
3. **Test Builds:** Run production builds regularly to catch bundling issues early
4. **Clear Cache:** When config changes don't apply, clear Vite cache

---

## Additional Notes

- The issue only appeared during production builds, not in development mode
- Vite's dev server has different module loading behavior than production builds
- CommonJS modules like `refractor` need special handling in ESM-based bundlers

---

**Status:** ✅ Build now completes successfully

*Fix Applied: November 8, 2025*

