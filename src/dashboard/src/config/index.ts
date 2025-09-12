export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8008";
export const WS_URL = import.meta.env.VITE_WS_URL || "http://localhost:8008";

export const AUTH_TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || "toolboxai_auth_token";
export const AUTH_REFRESH_TOKEN_KEY = import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY || "toolboxai_refresh_token";

export const ROBLOX_API_URL = import.meta.env.VITE_ROBLOX_API_URL || "https://api.roblox.com";
export const ROBLOX_UNIVERSE_ID = import.meta.env.VITE_ROBLOX_UNIVERSE_ID || "";

export const GOOGLE_CLASSROOM_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLASSROOM_CLIENT_ID || "";
export const CANVAS_API_TOKEN = import.meta.env.VITE_CANVAS_API_TOKEN || "";

export const ENABLE_WEBSOCKET = import.meta.env.VITE_ENABLE_WEBSOCKET === "true";
export const ENABLE_GAMIFICATION = import.meta.env.VITE_ENABLE_GAMIFICATION !== "false";
export const ENABLE_ANALYTICS = import.meta.env.VITE_ENABLE_ANALYTICS !== "false";

export const COPPA_COMPLIANCE = import.meta.env.VITE_COPPA_COMPLIANCE !== "false";
export const FERPA_COMPLIANCE = import.meta.env.VITE_FERPA_COMPLIANCE !== "false";
export const GDPR_COMPLIANCE = import.meta.env.VITE_GDPR_COMPLIANCE !== "false";

export const DEBUG_MODE = import.meta.env.VITE_DEBUG_MODE === "true";
export const MOCK_API = import.meta.env.VITE_MOCK_API === "true";

// XP and Level Configuration
export const XP_CONFIG = {
  levelMultiplier: 100,
  maxLevel: 100,
  bonusXPMultiplier: 1.5,
  streakBonus: 10,
};

// Pagination defaults
export const PAGINATION = {
  defaultPageSize: 20,
  maxPageSize: 100,
};

// WebSocket reconnection settings
export const WS_CONFIG = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
};

// API request timeout
export const API_TIMEOUT = 30000;

// Supported languages
export const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Español" },
  { code: "fr", name: "Français" },
];

// Default language
export const DEFAULT_LANGUAGE = "en";