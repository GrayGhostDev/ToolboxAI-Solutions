// In development with Vite, use empty baseURL to enable relative URLs through proxy
// This avoids CORS issues by routing all requests through the same origin
const isDevelopment = import.meta.env.DEV;
const rawApi = (import.meta.env.VITE_API_BASE_URL as string) || `http://127.0.0.1:8009`;

// Use empty string in development so axios uses relative URLs that go through Vite proxy
export const API_BASE_URL = isDevelopment
  ? ''
  : rawApi.replace(/\/+$/, '').replace(/\/api\/v1$/, '');

const rawWs = (import.meta.env.VITE_WS_URL as string) || `http://127.0.0.1:8009`;
export const WS_URL = rawWs.replace(/\/+$/, '');

// Pusher configuration (Channels)
export const PUSHER_KEY = (import.meta.env.VITE_PUSHER_KEY as string) || '';
export const PUSHER_CLUSTER = (import.meta.env.VITE_PUSHER_CLUSTER as string) || 'us2';
// In development, use relative URL for auth endpoint to go through proxy
export const PUSHER_AUTH_ENDPOINT = (import.meta.env.VITE_PUSHER_AUTH_ENDPOINT as string) ||
  (isDevelopment ? '/api/v1/pusher/auth' : `${rawApi}/api/v1/pusher/auth`);

export const AUTH_TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || "toolboxai_auth_token";
export const AUTH_REFRESH_TOKEN_KEY = import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY || "toolboxai_refresh_token";

export const ROBLOX_API_URL = import.meta.env.VITE_ROBLOX_API_URL || "https://api.roblox.com";
export const ROBLOX_UNIVERSE_ID = import.meta.env.VITE_ROBLOX_UNIVERSE_ID || "";

export const GOOGLE_CLASSROOM_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLASSROOM_CLIENT_ID || "";
export const CANVAS_API_TOKEN = import.meta.env.VITE_CANVAS_API_TOKEN || "";

export const ENABLE_WEBSOCKET = import.meta.env.VITE_ENABLE_WEBSOCKET === "true" || !!PUSHER_KEY;
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
