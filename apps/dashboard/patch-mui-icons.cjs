#!/usr/bin/env node

// Comprehensive patch script for MUI icons
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// The inline function to inject
const interopFunction = `// Patched: Define _interopRequireDefault inline to fix ESM/CommonJS issues
var _interopRequireDefault = function(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
};`;

// Find all MUI icon files
const iconFiles = glob.sync(path.join(__dirname, '../../node_modules/@mui/icons-material/*.js'));

console.log(`Found ${iconFiles.length} icon files to patch`);

let patchCount = 0;
let alreadyPatchedCount = 0;

iconFiles.forEach(filePath => {
  try {
    let content = fs.readFileSync(filePath, 'utf8');

    // Check if already patched
    if (content.includes('// Patched: Define _interopRequireDefault inline')) {
      alreadyPatchedCount++;
      return;
    }

    // Check if file uses _interopRequireDefault
    if (content.includes('var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault")')) {
      // Replace the require statement with inline function
      content = content.replace(
        'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");',
        interopFunction
      );

      fs.writeFileSync(filePath, content, 'utf8');
      patchCount++;
      console.log(`✅ Patched: ${path.basename(filePath)}`);
    }
  } catch (error) {
    console.error(`❌ Error patching ${path.basename(filePath)}: ${error.message}`);
  }
});

console.log(`\n✅ Patched ${patchCount} files`);
console.log(`⏭️  Already patched: ${alreadyPatchedCount} files`);
console.log(`📊 Total processed: ${iconFiles.length} files`);