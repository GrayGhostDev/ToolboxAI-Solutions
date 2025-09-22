// Patch script to fix MUI CommonJS/ESM issues
const fs = require('fs');
const path = require('path');

// Define the interop function inline
const interopFunction = `
// Inline interop function to avoid require issues
function _interopRequireDefault(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
}
`;

// Files to patch
const filesToPatch = [
  '../node_modules/@mui/system/colorManipulator.js',
  '../node_modules/@mui/material/styles/createPalette.js'
];

filesToPatch.forEach(filePath => {
  const fullPath = path.resolve(__dirname, filePath);

  if (fs.existsSync(fullPath)) {
    let content = fs.readFileSync(fullPath, 'utf8');

    // Replace the require statement with inline function
    if (content.includes('var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");')) {
      content = content.replace(
        'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");',
        interopFunction
      );

      fs.writeFileSync(fullPath, content, 'utf8');
      console.log(`✅ Patched: ${filePath}`);
    } else if (content.includes('_interopRequireDefault') && !content.includes('function _interopRequireDefault')) {
      // Add the function at the top if it uses it but doesn't define it
      content = interopFunction + '\n' + content;
      fs.writeFileSync(fullPath, content, 'utf8');
      console.log(`✅ Added interop to: ${filePath}`);
    } else {
      console.log(`⏭️  Already patched or doesn't need patching: ${filePath}`);
    }
  } else {
    console.log(`❌ File not found: ${filePath}`);
  }
});

console.log('Patch complete!');