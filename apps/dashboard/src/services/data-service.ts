/**
 * Unified Data Service Layer
 *
 * This service provides a single interface for all data operations,
 * automatically switching between mock data and real API based on environment.
 * It ensures that components don't need to know about the data source.
 */

import { AxiosResponse } from 'axios';
import { apiClient } from './api';
import * as mockData from './mock-data';
import {
  getDataSource,
  debugLog,
  getEnvironmentConfig,
  isMockMode,
  isApiMode
} from '../utils/environment';

// Type definitions for common data structures
export interface DataServiceResponse<T = any> {
  data: T;
  source: 'mock' | 'api';
  cached?: boolean;
  timestamp?: string;
}

// Cache for mock data to simulate persistence
const mockDataCache = new Map<string, any>();

// Cache configuration
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

class DataCache {
  private cache = new Map<string, CacheEntry<any>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes default

  set<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }
}

const dataCache = new DataCache();

// Retry configuration
interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
};

/**
 * Retry with exponential backoff
 */
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig
): Promise<T> {
  let lastError: any;
  let delay = config.initialDelay;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Don't retry on client errors (4xx)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }

      if (attempt < config.maxRetries) {
        debugLog(`Retry attempt ${attempt + 1}/${config.maxRetries} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay = Math.min(delay * config.backoffMultiplier, config.maxDelay);
      }
    }
  }

  throw lastError;
}

/**
 * DataService class that handles all data operations
 */
class DataService {
  private config = getEnvironmentConfig();
  private retryConfig: RetryConfig = defaultRetryConfig;

  /**
   * Generic request handler that routes to mock or API
   */
  private async request<T>(
    endpoint: string,
    options: {
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
      data?: any;
      params?: any;
      useMock?: boolean; // Force mock even in production
      useApi?: boolean;  // Force API even in development
    } = {}
  ): Promise<DataServiceResponse<T>> {
    const { method = 'GET', data, params, useMock, useApi } = options;

    // Determine data source
    let source: 'mock' | 'api';
    if (useMock) {
      source = 'mock';
    } else if (useApi) {
      source = 'api';
    } else {
      source = getDataSource();
    }

    debugLog(`Data request: ${method} ${endpoint} (source: ${source})`);

    try {
      if (source === 'mock') {
        return await this.handleMockRequest<T>(endpoint, method, data);
      } else {
        return await this.handleApiRequest<T>(endpoint, method, data, params);
      }
    } catch (error) {
      // If API fails in development, fallback to mock
      if (source === 'api' && this.config.environment === 'development') {
        debugLog(`API failed, falling back to mock for ${endpoint}`, error);
        return await this.handleMockRequest<T>(endpoint, method, data);
      }
      throw error;
    }
  }

  /**
   * Handle mock data requests
   */
  private async handleMockRequest<T>(
    endpoint: string,
    method: string,
    data?: any
  ): Promise<DataServiceResponse<T>> {
    // Simulate network delay
    await mockData.mockDelay(this.config.mockDelay);

    // Route to appropriate mock data based on endpoint
    const mockResponse = this.getMockDataForEndpoint(endpoint, method, data);

    return {
      data: mockResponse as T,
      source: 'mock',
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Handle real API requests
   */
  private async handleApiRequest<T>(
    endpoint: string,
    method: string,
    data?: any,
    params?: any
  ): Promise<DataServiceResponse<T>> {
    // For GET requests, check cache first
    const cacheKey = `${method}:${endpoint}:${JSON.stringify(params || {})}`;

    if (method === 'GET') {
      const cached = dataCache.get<T>(cacheKey);
      if (cached) {
        debugLog(`Cache hit for ${endpoint}`);
        return {
          data: cached,
          source: 'api',
          cached: true,
          timestamp: new Date().toISOString(),
        };
      }
    }

    // Make the API request with retry logic
    const makeRequest = async () => {
      const response = await (apiClient as any).client.request<T>({
        url: endpoint,
        method,
        data,
        params,
      });
      return response.data;
    };

    const responseData = await retryWithBackoff(makeRequest, this.retryConfig);

    // Cache successful GET requests
    if (method === 'GET') {
      dataCache.set(cacheKey, responseData);
    }

    // Clear related cache on mutations
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      // Clear cache for the resource type
      const resourcePath = endpoint.split('/').slice(0, -1).join('/');
      dataCache.delete(`GET:${resourcePath}:`);
    }

    return {
      data: responseData,
      source: 'api',
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Get mock data for a specific endpoint
   */
  private getMockDataForEndpoint(endpoint: string, method: string, data?: any): any {
    // Handle different endpoints
    if (endpoint.includes('/classes')) {
      return this.handleClassesMock(method, data);
    }
    if (endpoint.includes('/lessons')) {
      return this.handleLessonsMock(method, data);
    }
    if (endpoint.includes('/assessments')) {
      return this.handleAssessmentsMock(method, data);
    }
    if (endpoint.includes('/messages')) {
      return this.handleMessagesMock(method, data);
    }
    if (endpoint.includes('/dashboard/overview')) {
      return mockData.mockDashboardOverview;
    }
    if (endpoint.includes('/analytics/weekly_xp')) {
      return mockData.mockAnalytics.weeklyXP;
    }
    if (endpoint.includes('/analytics/subject_mastery')) {
      return mockData.mockAnalytics.subjectMastery;
    }
    if (endpoint.includes('/gamification/leaderboard')) {
      return mockData.mockGamification;
    }
    if (endpoint.includes('/compliance/status')) {
      return mockData.mockComplianceStatus;
    }
    if (endpoint.includes('/users')) {
      return this.handleUsersMock(method, data);
    }
    if (endpoint.includes('/schools')) {
      return this.handleSchoolsMock(method, data);
    }
    if (endpoint.includes('/admin')) {
      return this.handleAdminMock(endpoint, method, data);
    }

    // Default empty response
    return { success: true, message: 'Mock response' };
  }

  // Mock handlers for different resources
  private handleClassesMock(method: string, data?: any) {
    const cacheKey = 'classes';

    switch (method) {
      case 'GET':
        return mockDataCache.get(cacheKey) || mockData.mockClasses;
      case 'POST':
        const newClass = {
          id: `class-${Date.now()}`,
          ...data,
          students: data.students || 0,
          progress: data.progress || 0,
        };
        const classes = mockDataCache.get(cacheKey) || mockData.mockClasses;
        const updated = { ...classes, classes: [...classes.classes, newClass] };
        mockDataCache.set(cacheKey, updated);
        return newClass;
      case 'PUT':
      case 'PATCH':
        const classesForUpdate = mockDataCache.get(cacheKey) || mockData.mockClasses;
        const updatedClasses = classesForUpdate.classes.map((c: any) =>
          c.id === data.id ? { ...c, ...data } : c
        );
        const result = { ...classesForUpdate, classes: updatedClasses };
        mockDataCache.set(cacheKey, result);
        return data;
      case 'DELETE':
        const classesForDelete = mockDataCache.get(cacheKey) || mockData.mockClasses;
        const filtered = classesForDelete.classes.filter((c: any) => c.id !== data.id);
        mockDataCache.set(cacheKey, { ...classesForDelete, classes: filtered });
        return { success: true };
      default:
        return mockData.mockClasses;
    }
  }

  private handleLessonsMock(method: string, data?: any) {
    const cacheKey = 'lessons';

    switch (method) {
      case 'GET':
        return mockDataCache.get(cacheKey) || mockData.mockLessons;
      case 'POST':
        const newLesson = {
          id: `lesson-${Date.now()}`,
          ...data,
        };
        const lessons = mockDataCache.get(cacheKey) || mockData.mockLessons;
        const updated = { ...lessons, lessons: [...lessons.lessons, newLesson] };
        mockDataCache.set(cacheKey, updated);
        return newLesson;
      default:
        return mockData.mockLessons;
    }
  }

  private handleAssessmentsMock(method: string, data?: any) {
    if (method === 'GET') {
      return { assessments: mockData.mockAssessments, totalCount: mockData.mockAssessments.length };
    }
    if (method === 'POST' && data) {
      return {
        id: `assess-${Date.now()}`,
        ...data,
        status: 'submitted',
        score: Math.floor(Math.random() * 100),
      };
    }
    return mockData.mockAssessments;
  }

  private handleMessagesMock(method: string, data?: any) {
    if (method === 'GET') {
      return { messages: mockData.mockMessages, totalCount: mockData.mockMessages.length };
    }
    if (method === 'POST') {
      return {
        id: `msg-${Date.now()}`,
        ...data,
        timestamp: new Date().toISOString(),
        read: false,
      };
    }
    return mockData.mockMessages;
  }

  private handleUsersMock(method: string, data?: any) {
    const cacheKey = 'users';

    switch (method) {
      case 'GET':
        return mockDataCache.get(cacheKey) || mockData.mockUsers;
      case 'POST':
        const newUser = {
          id: Date.now(),
          ...data,
          is_active: true,
        };
        const users = mockDataCache.get(cacheKey) || mockData.mockUsers;
        const updated = { ...users, results: [...users.results, newUser] };
        mockDataCache.set(cacheKey, updated);
        return newUser;
      case 'PUT':
      case 'PATCH':
        const usersForUpdate = mockDataCache.get(cacheKey) || mockData.mockUsers;
        const updatedUsers = usersForUpdate.results.map((u: any) =>
          u.id === data.id ? { ...u, ...data } : u
        );
        const result = { ...usersForUpdate, results: updatedUsers };
        mockDataCache.set(cacheKey, result);
        return data;
      case 'DELETE':
        const usersForDelete = mockDataCache.get(cacheKey) || mockData.mockUsers;
        const filtered = usersForDelete.results.filter((u: any) => u.id !== data.id);
        mockDataCache.set(cacheKey, { ...usersForDelete, results: filtered });
        return { success: true };
      default:
        return mockData.mockUsers;
    }
  }

  private handleSchoolsMock(method: string, data?: any) {
    if (method === 'GET') {
      return mockData.mockSchools;
    }
    if (method === 'POST') {
      return {
        id: Date.now(),
        ...data,
      };
    }
    return mockData.mockSchools;
  }

  private handleAdminMock(endpoint: string, method: string, data?: any) {
    // Admin analytics
    if (endpoint.includes('/admin/analytics')) {
      return {
        totalUsers: 1250,
        activeUsers: 890,
        newUsersToday: 24,
        systemHealth: 98.5,
        apiLatency: 145,
        errorRate: 0.02,
        charts: mockData.mockAnalytics,
      };
    }

    // Admin system settings
    if (endpoint.includes('/admin/system')) {
      return {
        maintenanceMode: false,
        debugMode: true,
        maxUploadSize: 10485760,
        sessionTimeout: 3600,
        features: {
          pusher: true,
          roblox: true,
          ai: true,
        },
      };
    }

    // Admin activity logs
    if (endpoint.includes('/admin/logs')) {
      return {
        logs: [
          {
            id: 1,
            timestamp: new Date().toISOString(),
            user: 'admin@demo.com',
            action: 'LOGIN',
            details: 'Successful login',
            ip: '192.168.1.1',
          },
          {
            id: 2,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            user: 'teacher@demo.com',
            action: 'CREATE_CLASS',
            details: 'Created class "Advanced Programming"',
            ip: '192.168.1.2',
          },
        ],
        totalCount: 2,
      };
    }

    return { success: true };
  }

  // Public API methods that components will use
  // These methods delegate to the existing API client for consistency

  /**
   * Dashboard methods
   */
  async getDashboardOverview() {
    // Check if we should use mock or API
    const source = getDataSource();

    if (source === 'mock' || isMockMode()) {
      return this.handleMockRequest('/api/v1/dashboard/overview', 'GET');
    }

    // Use the existing API client method
    const response = await (apiClient as any).getDashboardOverview();
    return {
      data: response,
      source: 'api' as const,
      timestamp: new Date().toISOString(),
    };
  }

  async getAnalytics(type: 'weekly_xp' | 'subject_mastery' | 'compliance') {
    return this.request(`/api/v1/analytics/${type}`);
  }

  /**
   * Classes methods
   */
  async getClasses() {
    return this.request('/classes');
  }

  async createClass(data: any) {
    return this.request('/classes', { method: 'POST', data });
  }

  async updateClass(id: string, data: any) {
    return this.request(`/classes/${id}`, { method: 'PUT', data: { ...data, id } });
  }

  async deleteClass(id: string) {
    return this.request(`/classes/${id}`, { method: 'DELETE', data: { id } });
  }

  /**
   * Lessons methods
   */
  async getLessons() {
    return this.request('/lessons');
  }

  async createLesson(data: any) {
    return this.request('/lessons', { method: 'POST', data });
  }

  /**
   * Assessments methods
   */
  async getAssessments() {
    return this.request('/assessments');
  }

  async submitAssessment(id: string, data: any) {
    return this.request(`/assessments/${id}/submit`, { method: 'POST', data });
  }

  /**
   * Messages methods
   */
  async getMessages() {
    return this.request('/messages');
  }

  async sendMessage(data: any) {
    return this.request('/messages', { method: 'POST', data });
  }

  /**
   * User management methods
   */
  async getUsers(params?: any) {
    return this.request('/api/v1/users/', { params });
  }

  async createUser(data: any) {
    return this.request('/api/v1/users/', { method: 'POST', data });
  }

  async updateUser(id: number, data: any) {
    return this.request(`/api/v1/users/${id}`, { method: 'PUT', data });
  }

  async deleteUser(id: number) {
    return this.request(`/api/v1/users/${id}`, { method: 'DELETE' });
  }

  /**
   * Admin methods
   */
  async getAdminAnalytics() {
    return this.request('/api/v1/admin/analytics');
  }

  async getSystemSettings() {
    return this.request('/api/v1/admin/system');
  }

  async updateSystemSettings(data: any) {
    return this.request('/api/v1/admin/system', { method: 'PUT', data });
  }

  async getActivityLogs(params?: any) {
    return this.request('/api/v1/admin/logs', { params });
  }

  /**
   * Utility method to check current data source
   */
  getCurrentDataSource(): 'mock' | 'api' {
    return getDataSource();
  }

  /**
   * Force refresh cache (useful for testing)
   */
  clearCache() {
    mockDataCache.clear();
    debugLog('Mock data cache cleared');
  }
}

// Export singleton instance
export const dataService = new DataService();

// Export as default for convenience
export default dataService;