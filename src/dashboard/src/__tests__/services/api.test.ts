import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import ApiClient from '../../services/api';
import { API_BASE_URL } from '../../config';

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
        localStorageMock = {};
      },
      length: 0,
      key: () => null,
    } as Storage;

    // Set test token
    localStorage.setItem('auth_token', 'test-jwt-token');
  });

  afterEach(() => {
    mock.restore();
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should login successfully', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };
      const response = {
        success: true,
        data: {
          user: { id: '123', email: 'test@example.com', role: 'teacher' },
          token: 'new-jwt-token',
          refreshToken: 'refresh-token',
        },
      };

      mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, response);

      const result = await apiClient.login(loginData.email, loginData.password);
      
      expect(result.data.user.email).toBe('test@example.com');
      expect(localStorage.getItem('auth_token')).toBe('new-jwt-token');
      expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
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

    it('should refresh token when expired', async () => {
      localStorage.setItem('refresh_token', 'old-refresh-token');
      
      // First request fails with 401
      mock.onGet(`${API_BASE_URL}/users/me`).replyOnce(401);
      
      // Token refresh succeeds
      mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(200, {
        success: true,
        data: {
          token: 'new-jwt-token',
          refreshToken: 'new-refresh-token',
        },
      });
      
      // Retry original request succeeds
      mock.onGet(`${API_BASE_URL}/users/me`).reply(200, {
        success: true,
        data: { id: '123', email: 'test@example.com' },
      });

      const result = await apiClient.getCurrentUser();
      
      expect(result.data.email).toBe('test@example.com');
      expect(localStorage.getItem('auth_token')).toBe('new-jwt-token');
    });

    it('should logout and clear tokens', async () => {
      localStorage.setItem('auth_token', 'token');
      localStorage.setItem('refresh_token', 'refresh');

      mock.onPost(`${API_BASE_URL}/auth/logout`).reply(200);

      await apiClient.logout();

      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('Dashboard Operations', () => {
    it('should fetch dashboard overview', async () => {
      const mockData = {
        totalStudents: 100,
        totalClasses: 5,
        activeAssessments: 10,
      };

      mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(200, {
        success: true,
        data: mockData,
      });

      const result = await apiClient.getDashboardOverview();
      
      expect(result.data).toEqual(mockData);
      expect(result.data.totalStudents).toBe(100);
    });

    it('should handle API errors with retry', async () => {
      // First attempt fails with network error
      mock.onGet(`${API_BASE_URL}/dashboard/overview`).replyOnce(500);
      
      // Second attempt succeeds
      mock.onGet(`${API_BASE_URL}/dashboard/overview`).reply(200, {
        success: true,
        data: { totalStudents: 50 },
      });

      const result = await apiClient.getDashboardOverview();
      
      expect(result.data.totalStudents).toBe(50);
    });
  });

  describe('Class Management', () => {
    it('should create a new class', async () => {
      const newClass = {
        name: 'Math 101',
        description: 'Basic Mathematics',
        gradeLevel: 5,
      };

      mock.onPost(`${API_BASE_URL}/classes`).reply(201, {
        success: true,
        data: { id: 'class-123', ...newClass },
      });

      const result = await apiClient.createClass(newClass);
      
      expect(result.data.id).toBe('class-123');
      expect(result.data.name).toBe('Math 101');
    });

    it('should fetch class list', async () => {
      const classes = [
        { id: '1', name: 'Math 101' },
        { id: '2', name: 'Science 202' },
      ];

      mock.onGet(`${API_BASE_URL}/classes`).reply(200, {
        success: true,
        data: classes,
      });

      const result = await apiClient.getClasses();
      
      expect(result.data).toHaveLength(2);
      expect(result.data[0].name).toBe('Math 101');
    });

    it('should update class details', async () => {
      const classId = 'class-123';
      const updates = { name: 'Advanced Math' };

      mock.onPatch(`${API_BASE_URL}/classes/${classId}`).reply(200, {
        success: true,
        data: { id: classId, ...updates },
      });

      const result = await apiClient.updateClass(classId, updates);
      
      expect(result.data.name).toBe('Advanced Math');
    });

    it('should delete a class', async () => {
      const classId = 'class-123';

      mock.onDelete(`${API_BASE_URL}/classes/${classId}`).reply(204);

      await expect(apiClient.deleteClass(classId)).resolves.not.toThrow();
    });
  });

  describe('Roblox Integration', () => {
    it('should generate Roblox content', async () => {
      const request = {
        subject: 'Science',
        gradeLevel: 7,
        learningObjectives: ['Solar System', 'Planets'],
      };

      mock.onPost(`${API_BASE_URL}/roblox/generate`).reply(200, {
        success: true,
        data: {
          worldId: 'world-123',
          scripts: ['script1.lua', 'script2.lua'],
          status: 'completed',
        },
      });

      const result = await apiClient.generateRobloxContent(request);
      
      expect(result.data.worldId).toBe('world-123');
      expect(result.data.scripts).toHaveLength(2);
    });

    it('should sync Roblox progress', async () => {
      const progressData = {
        studentId: 'student-123',
        worldId: 'world-456',
        progress: 75,
        achievements: ['explorer', 'problem_solver'],
      };

      mock.onPost(`${API_BASE_URL}/roblox/progress`).reply(200, {
        success: true,
        data: { updated: true },
      });

      const result = await apiClient.syncRobloxProgress(progressData);
      
      expect(result.data.updated).toBe(true);
    });
  });

  describe('WebSocket Connection', () => {
    it('should establish WebSocket connection', async () => {
      const mockWebSocket = {
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
      };

      global.WebSocket = vi.fn(() => mockWebSocket) as any;

      const ws = apiClient.connectWebSocket();
      
      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8001')
      );
    });

    it('should handle WebSocket messages', async () => {
      const onMessage = vi.fn();
      const mockWebSocket = {
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, handler) => {
          if (event === 'message') {
            // Simulate incoming message
            setTimeout(() => {
              handler({ data: JSON.stringify({ type: 'update', payload: {} }) });
            }, 100);
          }
        }),
      };

      global.WebSocket = vi.fn(() => mockWebSocket) as any;

      apiClient.connectWebSocket(onMessage);
      
      await new Promise(resolve => setTimeout(resolve, 150));
      
      expect(onMessage).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mock.onGet(`${API_BASE_URL}/test`).networkError();

      await expect(apiClient.get('/test')).rejects.toThrow('Network Error');
    });

    it('should handle timeout', async () => {
      mock.onGet(`${API_BASE_URL}/test`).timeout();

      await expect(apiClient.get('/test')).rejects.toThrow();
    });

    it('should handle 404 errors', async () => {
      mock.onGet(`${API_BASE_URL}/nonexistent`).reply(404, {
        success: false,
        message: 'Resource not found',
      });

      await expect(apiClient.get('/nonexistent')).rejects.toThrow();
    });

    it('should handle validation errors', async () => {
      mock.onPost(`${API_BASE_URL}/classes`).reply(422, {
        success: false,
        errors: {
          name: ['Name is required'],
          gradeLevel: ['Grade level must be between 1 and 12'],
        },
      });

      await expect(apiClient.createClass({})).rejects.toThrow();
    });
  });

  describe('Request Interceptors', () => {
    it('should add auth token to requests', async () => {
      localStorage.setItem('auth_token', 'bearer-token-123');

      mock.onGet(`${API_BASE_URL}/protected`).reply(config => {
        expect(config.headers?.Authorization).toBe('Bearer bearer-token-123');
        return [200, { success: true }];
      });

      await apiClient.get('/protected');
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
        requests.map(({ url }) => apiClient.get(url))
      );

      expect(results).toHaveLength(5);
      results.forEach((result, i) => {
        expect(result.data.data).toEqual({ data: `response${i}` });
      });
    });
  });
});