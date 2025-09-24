// Comprehensive MUI patch script to fix all interop issues
const fs = require('fs');
const path = require('path');

// Define the interop functions inline
const interopDefaultFunction = `
// Patched: Define _interopRequireDefault inline to fix ESM/CommonJS issues
var _interopRequireDefault = function(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
};`;

const interopWildcardFunction = `
// Patched: Define _interopRequireWildcard inline to fix ESM/CommonJS issues
function _interopRequireWildcard(e, r) {
  if (!r && e && e.__esModule) return e;
  if (null === e || "object" != typeof e && "function" != typeof e) return { default: e };
  var t = _getRequireWildcardCache && _getRequireWildcardCache(r);
  if (t && t.has(e)) return t.get(e);
  var n = { __proto__: null }, a = Object.defineProperty && Object.getOwnPropertyDescriptor;
  for (var u in e) if ("default" !== u && Object.prototype.hasOwnProperty.call(e, u)) {
    var i = a ? Object.getOwnPropertyDescriptor(e, u) : null;
    i && (i.get || i.set) ? Object.defineProperty(n, u, i) : n[u] = e[u];
  }
  return n.default = e, t && t.set(e, n), n;
}
function _getRequireWildcardCache(e) {
  if ("function" != typeof WeakMap) return null;
  var r = new WeakMap(), t = new WeakMap();
  return (_getRequireWildcardCache = function (e) { return e ? t : r; })(e);
}`;

// List of known problematic MUI files
const muiFiles = [
  '../../node_modules/@mui/system/colorManipulator.js',
  '../../node_modules/@mui/system/createStyled.js',
  '../../node_modules/@mui/material/styles/createPalette.js',
  '../../node_modules/@mui/material/styles/styled.js',
  '../../node_modules/@mui/material/styles/createTheme.js',
  '../../node_modules/@mui/material/styles/createMixins.js',
  '../../node_modules/@mui/material/styles/createTypography.js',
  '../../node_modules/@mui/system/styleFunctionSx.js',
  '../../node_modules/@mui/system/createTheme.js',
  '../../node_modules/@mui/system/styled.js'
];

let patchCount = 0;
let errorCount = 0;

muiFiles.forEach(filePath => {
  const fullPath = path.resolve(__dirname, filePath);

  if (fs.existsSync(fullPath)) {
    try {
      let content = fs.readFileSync(fullPath, 'utf8');
      let modified = false;

      // Check if file needs patching for _interopRequireDefault
      if (content.includes('require("@babel/runtime/helpers/interopRequireDefault")')) {
        content = content.replace(
          /var _interopRequireDefault = require\("@babel\/runtime\/helpers\/interopRequireDefault"\);/,
          interopDefaultFunction
        );
        modified = true;
        console.log(`✅ Patched _interopRequireDefault in: ${path.basename(filePath)}`);
      } else if (content.includes('_interopRequireDefault') && !content.includes('function(obj)')) {
        // File uses _interopRequireDefault but doesn't define it
        const lines = content.split('\n');
        if (lines[0] === '"use strict";') {
          lines.splice(2, 0, interopDefaultFunction);
          content = lines.join('\n');
          modified = true;
          console.log(`✅ Added _interopRequireDefault to: ${path.basename(filePath)}`);
        }
      }

      // Check if file uses _interopRequireWildcard but doesn't define it properly
      if (content.includes('_interopRequireWildcard(') && !content.includes('function _interopRequireWildcard(e, r)')) {
        // Add wildcard function if it's missing
        const lines = content.split('\n');
        let insertIndex = 2;

        // Find where to insert (after _interopRequireDefault if it exists)
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('var _interopRequireDefault')) {
            insertIndex = i + 2;
            break;
          }
        }

        lines.splice(insertIndex, 0, interopWildcardFunction);
        content = lines.join('\n');
        modified = true;
        console.log(`✅ Added _interopRequireWildcard to: ${path.basename(filePath)}`);
      }

      if (modified) {
        fs.writeFileSync(fullPath, content, 'utf8');
        patchCount++;
      }

    } catch (error) {
      console.error(`❌ Error patching ${filePath}:`, error.message);
      errorCount++;
    }
  } else {
    console.log(`⏭️  File not found: ${filePath}`);
  }
});

console.log(`\n✅ Patched ${patchCount} files`);
if (errorCount > 0) {
  console.log(`❌ Failed to patch ${errorCount} files`);
}
console.log('Patch complete!');