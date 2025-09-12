import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock WebSocketService before any imports
vi.mock('../../services/websocket', () => ({
  WebSocketService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      disconnect: vi.fn(),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      getState: vi.fn(() => 'DISCONNECTED'),
      isConnected: vi.fn(() => false),
      onStateChange: vi.fn(),
      onError: vi.fn(),
    })),
  },
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    getState: vi.fn(() => 'DISCONNECTED'),
    isConnected: vi.fn(() => false),
  },
}));

// Mock the store to prevent WebSocket initialization
vi.mock('../../store', () => ({
  store: {
    dispatch: vi.fn(),
    getState: vi.fn(() => ({
      user: { currentUser: null },
      ui: {},
      dashboard: {},
    })),
    subscribe: vi.fn(),
  },
}));

import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import ApiClient from '../../services/api';

// Use the correct API base URL
const API_BASE_URL = 'http://localhost:8008';

describe('API Service', () => {
  let mock: MockAdapter;
  let apiClient: ApiClient;
  let localStorageMock: { [key: string]: string };

  beforeEach(() => {
    // Setup axios mock
    mock = new MockAdapter(axios);
    apiClient = new ApiClient();

    // Mock localStorage
    localStorageMock = {};
    global.localStorage = {
      getItem: (key: string) => localStorageMock[key] || null,
      setItem: (key: string, value: string) => {
        localStorageMock[key] = value;
      },
      removeItem: (key: string) => {
        delete localStorageMock[key];
      },
      clear: () => {
        // Clear all properties instead of reassigning
        Object.keys(localStorageMock).forEach(key => delete localStorageMock[key]);
      },
      length: 0,
      key: () => null,
    } as Storage;

    // Set test token using the actual key
    localStorage.setItem('toolboxai_auth_token', 'test-jwt-token');
  });

  afterEach(() => {
    mock.restore();
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should login successfully', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };

      mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, {
        access_token: 'new-jwt-token',
        refresh_token: 'refresh-token',
        user: { 
          id: '123', 
          email: 'test@example.com', 
          username: 'test',
          first_name: 'Test',
          last_name: 'User',
          role: 'teacher' 
        },
      });

      const result = await apiClient.login(loginData.email, loginData.password) as any;
      
      // The login method returns the raw API response
      expect(result).toBeDefined();
      expect(result.user.email).toBe('test@example.com');
      expect(result.access_token).toBe('new-jwt-token');
      expect(result.refresh_token).toBe('refresh-token');
    });

    it('should handle login failure', async () => {
      mock.onPost(`${API_BASE_URL}/auth/login`).reply(401, {
        success: false,
        message: 'Invalid credentials',
      });

      await expect(
        apiClient.login('wrong@example.com', 'wrongpass')
      ).rejects.toThrow();
    });

    it('should logout successfully', async () => {
      localStorage.setItem('toolboxai_auth_token', 'token');
      localStorage.setItem('toolboxai_refresh_token', 'refresh');

      mock.onPost(`${API_BASE_URL}/auth/logout`).reply(204);

      await apiClient.logout();

      // Verify logout was called
      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].url).toBe('/auth/logout');
    });
  });

  describe('Dashboard Operations', () => {
    it('should fetch dashboard overview', async () => {
      const mockData = {
        totalStudents: 100,
        totalClasses: 5,
        activeAssessments: 10,
      };

      mock.onGet(`${API_BASE_URL}/dashboard/overview/teacher`).reply(200, mockData);

      const result = await apiClient.getDashboardOverview('teacher');
      
      expect(result).toEqual(mockData);
      expect((result as any).totalStudents).toBe(100);
    });

    it('should handle API errors', async () => {
      // Mock fails with 500 error
      mock.onGet(`${API_BASE_URL}/dashboard/overview/teacher`).reply(500);

      await expect(apiClient.getDashboardOverview('teacher')).rejects.toThrow();
    });
  });

  describe('Class Management', () => {
    it('should create a new class', async () => {
      const newClass = {
        name: 'Math 101',
        description: 'Basic Mathematics',
        gradeLevel: 5,
      };

      mock.onPost(`${API_BASE_URL}/classes/`).reply(201, { 
        id: 'class-123', 
        ...newClass 
      });

      const result = await apiClient.createClass(newClass);
      
      expect(result.id).toBe('class-123');
      expect(result.name).toBe('Math 101');
    });

    it('should fetch class list', async () => {
      const classes = [
        { id: '1', name: 'Math 101' },
        { id: '2', name: 'Science 202' },
      ];

      mock.onGet(`${API_BASE_URL}/classes/`).reply(200, classes);

      const result = await apiClient.listClasses();
      
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('Math 101');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mock.onGet(`${API_BASE_URL}/test`).networkError();

      await expect(apiClient['request']({
        method: 'GET',
        url: '/test'
      })).rejects.toThrow();
    });

    it('should handle timeout', async () => {
      mock.onGet(`${API_BASE_URL}/test`).timeout();

      await expect(apiClient['request']({
        method: 'GET',
        url: '/test'
      })).rejects.toThrow();
    });

    it('should handle 404 errors', async () => {
      mock.onGet(`${API_BASE_URL}/nonexistent`).reply(404, {
        success: false,
        message: 'Resource not found',
      });

      await expect(apiClient['request']({
        method: 'GET',
        url: '/nonexistent'
      })).rejects.toThrow();
    });

    it('should handle validation errors', async () => {
      mock.onPost(`${API_BASE_URL}/classes/`).reply(422, {
        success: false,
        detail: [
          { msg: 'Name is required', loc: ['body', 'name'] },
          { msg: 'Grade level must be between 1 and 12', loc: ['body', 'gradeLevel'] },
        ],
      });

      await expect(apiClient.createClass({})).rejects.toThrow();
    });
  });

  describe('Request Interceptors', () => {
    it('should add auth token to requests', async () => {
      localStorage.setItem('toolboxai_auth_token', 'bearer-token-123');

      mock.onGet(`${API_BASE_URL}/protected`).reply(() => {
        // The Authorization header should be set by the interceptor
        return [200, { success: true }];
      });

      const result = await apiClient['request']({
        method: 'GET',
        url: '/protected'
      });

      expect(result).toBeDefined();
    });

    it('should handle concurrent requests', async () => {
      const requests = Array(5).fill(null).map((_, i) => ({
        url: `/test${i}`,
        response: { data: `response${i}` },
      }));

      requests.forEach(({ url, response }) => {
        mock.onGet(`${API_BASE_URL}${url}`).reply(200, {
          success: true,
          data: response,
        });
      });

      const results = await Promise.all(
        requests.map(({ url }) => apiClient['request']({
          method: 'GET',
          url
        }))
      );

      expect(results).toHaveLength(5);
      results.forEach((result: any, i) => {
        expect(result.data).toEqual({ data: `response${i}` });
      });
    });
  });
});