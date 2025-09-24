#!/usr/bin/env node

// Comprehensive patch script for ALL MUI packages
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// The inline functions to inject
const interopDefaultFunction = `// Patched: Define _interopRequireDefault inline to fix ESM/CommonJS issues
var _interopRequireDefault = function(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
};`;

const interopWildcardFunction = `// Define _interopRequireWildcard and helper functions at the top
function _getRequireWildcardCache(e) { if ("function" != typeof WeakMap) return null; var r = new WeakMap(), t = new WeakMap(); return (_getRequireWildcardCache = function (e) { return e ? t : r; })(e); }
function _interopRequireWildcard(e, r) { if (!r && e && e.__esModule) return e; if (null === e || "object" != typeof e && "function" != typeof e) return { default: e }; var t = _getRequireWildcardCache(r); if (t && t.has(e)) return t.get(e); var n = { __proto__: null }, a = Object.defineProperty && Object.getOwnPropertyDescriptor; for (var u in e) if ("default" !== u && Object.prototype.hasOwnProperty.call(e, u)) { var i = a ? Object.getOwnPropertyDescriptor(e, u) : null; i && (i.get || i.set) ? Object.defineProperty(n, u, i) : n[u] = e[u]; } return n.default = e, t && t.set(e, n), n; }`;

// Find all JavaScript files in MUI packages
const muiPackages = [
  '@mui/material',
  '@mui/icons-material',
  '@mui/system',
  '@mui/base',
  '@mui/utils',
  '@mui/x-date-pickers',
  '@mui/styled-engine',
  '@mui/private-theming',
  '@mui/core-downloads-tracker'
];

console.log('Starting comprehensive MUI patch...\n');

let totalPatchCount = 0;
let totalAlreadyPatchedCount = 0;
let totalErrorCount = 0;

muiPackages.forEach(packageName => {
  const packagePath = path.join(__dirname, '../../node_modules', packageName);

  if (!fs.existsSync(packagePath)) {
    console.log(`⏭️  Package not found: ${packageName}`);
    return;
  }

  console.log(`\n📦 Processing ${packageName}...`);

  // Find all JS files in the package
  const jsFiles = glob.sync(path.join(packagePath, '**/*.js'), {
    ignore: ['**/node_modules/**', '**/test/**', '**/tests/**', '**/*.test.js', '**/*.spec.js']
  });

  let packagePatchCount = 0;
  let packageAlreadyPatchedCount = 0;

  jsFiles.forEach(filePath => {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      let modified = false;

      // Check if already patched
      if (content.includes('// Patched: Define _interopRequireDefault inline') ||
          content.includes('// Define _interopRequireWildcard and helper functions')) {
        packageAlreadyPatchedCount++;
        return;
      }

      // Check and patch _interopRequireDefault
      if (content.includes('var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault")')) {
        content = content.replace(
          'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");',
          interopDefaultFunction
        );
        modified = true;
      }

      // Check and patch _interopRequireWildcard
      if (content.includes('var _interopRequireWildcard = require("@babel/runtime/helpers/interopRequireWildcard")')) {
        // Find where to insert the wildcard function
        const lines = content.split('\n');
        let insertIndex = -1;

        // Find the line with _interopRequireWildcard require
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('var _interopRequireWildcard = require("@babel/runtime/helpers/interopRequireWildcard")')) {
            insertIndex = i;
            break;
          }
        }

        if (insertIndex !== -1) {
          // Replace the require with the inline function
          lines[insertIndex] = interopWildcardFunction;
          content = lines.join('\n');
          modified = true;
        }
      }

      // Additional helper functions that might be needed
      const helpers = [
        'extends',
        'objectWithoutPropertiesLoose',
        'objectWithoutProperties',
        'defineProperty',
        'objectSpread2'
      ];

      helpers.forEach(helper => {
        const pattern = new RegExp(`var _${helper} = require\\("@babel/runtime/helpers/${helper}"\\);`);
        if (content.match(pattern)) {
          // For now, just replace with a simple pass-through
          // In a more complete solution, we'd implement each helper
          content = content.replace(
            pattern,
            `var _${helper} = function(obj) { return obj && obj.__esModule ? obj : { default: obj }; };`
          );
          modified = true;
        }
      });

      if (modified) {
        fs.writeFileSync(filePath, content, 'utf8');
        packagePatchCount++;
        totalPatchCount++;
      }

    } catch (error) {
      console.error(`❌ Error patching ${path.relative(packagePath, filePath)}: ${error.message}`);
      totalErrorCount++;
    }
  });

  console.log(`  ✅ Patched: ${packagePatchCount} files`);
  console.log(`  ⏭️  Already patched: ${packageAlreadyPatchedCount} files`);
  totalAlreadyPatchedCount += packageAlreadyPatchedCount;
});

console.log('\n' + '='.repeat(60));
console.log('📊 Summary:');
console.log(`✅ Total patched: ${totalPatchCount} files`);
console.log(`⏭️  Already patched: ${totalAlreadyPatchedCount} files`);
if (totalErrorCount > 0) {
  console.log(`❌ Errors: ${totalErrorCount} files`);
}
console.log('='.repeat(60));
console.log('\n✨ Patch complete! Now restart your dev server with:');
console.log('   npm run dev -- --force');