/**
 * ============================================
 * API CONFIGURATION
 * ============================================
 * Centralized API configuration with environment-based URLs
 * Updated: 2025-11-02
 * ============================================
 */

// Get API URL from environment
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8009';

const WS_URL = import.meta.env.VITE_WS_URL ||
               'ws://localhost:8009';

const CDN_URL = import.meta.env.VITE_CDN_URL || '';

/**
 * API Configuration
 */
export const apiConfig = {
  baseURL: API_URL,
  wsURL: WS_URL,
  cdnURL: CDN_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
};

/**
 * API Endpoints
 */
export const endpoints = {
  // Authentication
  auth: {
    login: `${API_URL}/api/v1/auth/login`,
    logout: `${API_URL}/api/v1/auth/logout`,
    refresh: `${API_URL}/api/v1/auth/refresh`,
    me: `${API_URL}/api/v1/auth/me`,
  },

  // Users
  users: {
    list: `${API_URL}/api/v1/users`,
    detail: (id: string) => `${API_URL}/api/v1/users/${id}`,
    create: `${API_URL}/api/v1/users`,
    update: (id: string) => `${API_URL}/api/v1/users/${id}`,
    delete: (id: string) => `${API_URL}/api/v1/users/${id}`,
  },

  // Courses
  courses: {
    list: `${API_URL}/api/v1/courses`,
    detail: (id: string) => `${API_URL}/api/v1/courses/${id}`,
    create: `${API_URL}/api/v1/courses`,
    update: (id: string) => `${API_URL}/api/v1/courses/${id}`,
    delete: (id: string) => `${API_URL}/api/v1/courses/${id}`,
  },

  // Analytics
  analytics: {
    dashboard: `${API_URL}/api/v1/analytics/dashboard`,
    users: `${API_URL}/api/v1/analytics/users`,
    courses: `${API_URL}/api/v1/analytics/courses`,
  },

  // Health
  health: `${API_URL}/health`,

  // WebSocket
  ws: {
    connect: `${WS_URL}/ws`,
    notifications: `${WS_URL}/ws/notifications`,
  },
};

/**
 * Get full asset URL with CDN support
 */
export const getAssetUrl = (path: string): string => {
  if (CDN_URL) {
    return `${CDN_URL}${path.startsWith('/') ? path : `/${path}`}`;
  }
  return path;
};

/**
 * Check if API is available
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(endpoints.health, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return response.ok;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};

export default apiConfig;

