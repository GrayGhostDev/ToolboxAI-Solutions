// MUI and CommonJS interop polyfills - Enhanced 2025 version
// This must load before any other modules

// Immediate execution to ensure availability
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

// Also set on globalThis for broader compatibility
globalThis._interopRequireDefault = window._interopRequireDefault;
globalThis._interopRequireWildcard = window._interopRequireWildcard;

(function() {
  'use strict';

  // Make sure functions persist
  {
    // Additional helpers for module compatibility
    window.__createBinding = window.__createBinding || function(o, m, k, k2) {
      if (k2 === undefined) k2 = k;
      Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
    };

    window.__exportStar = window.__exportStar || function(m, exports) {
      for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) exports[p] = m[p];
    };

    window.__values = window.__values || function(o) {
      var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
      if (m) return m.call(o);
      if (o && typeof o.length === "number") return {
        next: function() {
          if (o && i >= o.length) o = void 0;
          return { value: o && o[i++], done: !o };
        }
      };
      throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
    };

    // Webpack compatibility helpers
    window.__webpack_require__ = window.__webpack_require__ || function(id) {
      return window[id] || {};
    };

    // ES6 module helpers
    window.__esModule = true;

    // Support for different module systems
    if (typeof module !== 'undefined' && module.exports) {
      module.exports._interopRequireDefault = window._interopRequireDefault;
      module.exports._interopRequireWildcard = window._interopRequireWildcard;
    }
  }

  // Node.js environment support
  if (typeof global !== 'undefined') {
    global._interopRequireDefault = window._interopRequireDefault;
    global._interopRequireWildcard = window._interopRequireWildcard;
  }

  console.log('[Polyfills] Enhanced CommonJS interop helpers loaded successfully');
})();
