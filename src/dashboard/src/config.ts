/**
 * Configuration for ToolboxAI Dashboard
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8008';
export const API_TIMEOUT = 30000; // 30 seconds

// WebSocket Configuration
export const ENABLE_WEBSOCKET = true; // Socket.io server now integrated
export const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8008';
export const WS_RECONNECT_INTERVAL = 5000;
export const WS_MAX_RECONNECT_ATTEMPTS = 3;

// WebSocket Config object for backward compatibility
export const WS_CONFIG = {
  url: WS_URL,
  reconnectInterval: WS_RECONNECT_INTERVAL,
  maxReconnectAttempts: WS_MAX_RECONNECT_ATTEMPTS,
  enabled: ENABLE_WEBSOCKET,
  heartbeatInterval: 30000, // 30 seconds
  messageTimeout: 10000, // 10 seconds
};

// Debug Configuration
export const DEBUG_MODE = import.meta.env.DEV;

// Feature Flags
export const FEATURES = {
  REAL_TIME_UPDATES: false, // Disabled until Socket.io server is configured
  AI_CONTENT_GENERATION: true,
  GAMIFICATION: true,
  ROBLOX_INTEGRATION: true,
  ANALYTICS: true,
};

// Polling Configuration (fallback for when WebSocket is disabled)
export const POLLING_INTERVAL = 30000; // 30 seconds
export const ENABLE_POLLING = false; // Disable polling to prevent duplicate requests

// Authentication
export const AUTH_TOKEN_KEY = 'auth_token';
export const AUTH_REFRESH_TOKEN_KEY = 'auth_refresh_token';
export const AUTH_REFRESH_INTERVAL = 3600000; // 1 hour

// UI Configuration
export const NOTIFICATION_DURATION = 5000; // 5 seconds
export const TABLE_PAGE_SIZE = 10;
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// Language Configuration
export const DEFAULT_LANGUAGE = 'en';
export const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
];

// COPPA Compliance Configuration
export const COPPA_COMPLIANCE = {
  enabled: true,
  minAge: 13,
  requireParentalConsent: true,
  dataRetentionDays: 90,
  features: {
    restrictedDataCollection: true,
    parentalDashboard: true,
    ageVerification: true,
    contentFiltering: true,
  },
};

export default {
  API_BASE_URL,
  API_TIMEOUT,
  ENABLE_WEBSOCKET,
  WS_URL,
  WS_RECONNECT_INTERVAL,
  WS_MAX_RECONNECT_ATTEMPTS,
  WS_CONFIG,
  DEBUG_MODE,
  FEATURES,
  POLLING_INTERVAL,
  ENABLE_POLLING,
  AUTH_TOKEN_KEY,
  AUTH_REFRESH_TOKEN_KEY,
  AUTH_REFRESH_INTERVAL,
  NOTIFICATION_DURATION,
  TABLE_PAGE_SIZE,
  MAX_FILE_SIZE,
  DEFAULT_LANGUAGE,
  LANGUAGES,
  COPPA_COMPLIANCE,
};