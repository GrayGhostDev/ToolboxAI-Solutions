// Vite plugin to fix MUI interop issues
export function muiInteropFix() {
  return {
    name: 'mui-interop-fix',
    enforce: 'pre',

    transform(code, id) {
      // Only process MUI files
      if (!id.includes('@mui/') || !id.includes('node_modules')) {
        return null;
      }

      // Replace _interopRequireDefault calls with a simpler pattern
      if (code.includes('_interopRequireDefault')) {
        // Define the function inline at the top of each module
        const fixedCode = `
// MUI Interop Fix - Define functions locally
const _interopRequireDefault = (obj) => obj && obj.__esModule ? obj : { default: obj };
const _interopRequireWildcard = (obj) => {
  if (obj && obj.__esModule) return obj;
  if (obj === null || (typeof obj !== "object" && typeof obj !== "function")) return { default: obj };
  var cache = {};
  if (obj != null) {
    for (var key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) cache[key] = obj[key];
    }
  }
  cache.default = obj;
  return cache;
};
${code}`;

        return {
          code: fixedCode,
          map: null
        };
      }

      return null;
    }
  };
}