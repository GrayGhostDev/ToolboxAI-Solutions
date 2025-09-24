// MUI Interop Layer - Must be imported before any MUI components
// This ensures interop functions are available when MUI modules load

// Define interop functions globally
if (typeof window !== 'undefined') {
  window._interopRequireDefault = function(obj) {
    return obj && obj.__esModule ? obj : { default: obj };
  };

  window._interopRequireWildcard = function(obj) {
    if (obj && obj.__esModule) {
      return obj;
    }
    if (obj === null || (typeof obj !== "object" && typeof obj !== "function")) {
      return { default: obj };
    }
    var cache = {};
    if (obj != null) {
      for (var key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
          cache[key] = obj[key];
        }
      }
    }
    cache.default = obj;
    return cache;
  };

  // Also define on globalThis
  globalThis._interopRequireDefault = window._interopRequireDefault;
  globalThis._interopRequireWildcard = window._interopRequireWildcard;
}

// Export to ensure module is evaluated
export const muiInteropInitialized = true;