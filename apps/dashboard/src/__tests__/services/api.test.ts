/**
 * API Service Test
 * 
 * Example test file demonstrating how to test API services with
 * proper mocking and error handling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { 
  createMockUser,
  createMockClass,
  createMockLesson,
  createMockAssessment,
  createMockApiResponse,
  createMockError
} from '../../test/utils/mockData';

// Import the API service first
import { 
  apiClient,
  login,
  logout,
  getDashboardOverview,
  listClasses,
  listUsers,
  createLesson,
  updateLesson,
  deleteLesson,
  getAssessments,
  submitAssessment
} from '../../services/api';

// Create axios mock adapter on the apiClient's axios instance
const mockAxios = new MockAdapter(apiClient.client);

describe('API Service', () => {
  const API_BASE_URL = 'http://localhost:8008';
  
  beforeEach(() => {
    // Reset axios mock before each test
    mockAxios.reset();
    
    // Clear all mocks
    vi.clearAllMocks();
    
    // Mock localStorage
    global.localStorage.setItem('token', 'mock-token');
  });

  afterEach(() => {
    mockAxios.reset();
    localStorage.clear();
  });

  describe('Authentication', () => {
    it('should login successfully with valid credentials', async () => {
      const mockUser = createMockUser({ role: 'teacher' });
      const mockResponse = {
        user: mockUser,
        token: 'jwt-token',
        refreshToken: 'refresh-token'
      };

      mockAxios.onPost('/auth/login').reply(200, mockResponse);

      const result = await login('teacher@example.com', 'password123');

      expect(result).toEqual(mockResponse);
      expect(localStorage.getItem('token')).toBe('jwt-token');
    });

    it('should handle login failure with invalid credentials', async () => {
      mockAxios.onPost('/auth/login').reply(401, {
        error: 'Invalid credentials'
      });

      await expect(
        login('wrong@example.com', 'wrongpassword')
      ).rejects.toThrow();
    });

    it('should logout and clear stored data', async () => {
      mockAxios.onPost('/auth/logout').reply(200);

      await logout();

      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('should include auth token in requests', async () => {
      const token = 'Bearer mock-token';
      localStorage.setItem('token', 'mock-token');

      mockAxios.onGet('/users').reply((config) => {
        expect(config.headers?.Authorization).toBe(token);
        return [200, []];
      });

      await listUsers();
    });
  });

  describe('Dashboard API', () => {
    it('should fetch dashboard overview data', async () => {
      const mockData = {
        totalStudents: 150,
        totalClasses: 6,
        averageScore: 82.5,
        recentActivity: []
      };

      mockAxios.onGet('/dashboard/overview').reply(200, mockData);

      const result = await getDashboardOverview();

      expect(result).toEqual(mockData);
    });

    it('should handle dashboard API errors', async () => {
      mockAxios.onGet('/dashboard/overview').reply(500, {
        error: 'Internal server error'
      });

      await expect(getDashboardOverview()).rejects.toThrow();
    });
  });

  describe('Classes API', () => {
    it('should fetch list of classes', async () => {
      const mockClasses = [
        createMockClass({ id: '1', name: 'Math 101' }),
        createMockClass({ id: '2', name: 'Science 202' })
      ];

      mockAxios.onGet('/classes').reply(200, mockClasses);

      const result = await listClasses();

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('Math 101');
    });

    it('should filter classes by query parameters', async () => {
      const mockClasses = [
        createMockClass({ subject: 'Mathematics' })
      ];

      mockAxios.onGet('/classes', { 
        params: { subject: 'Mathematics' } 
      }).reply(200, mockClasses);

      const result = await listClasses({ subject: 'Mathematics' });

      expect(result).toHaveLength(1);
      expect(result[0].subject).toBe('Mathematics');
    });
  });

  describe('Lessons API', () => {
    it('should create a new lesson', async () => {
      const newLesson = createMockLesson({
        title: 'Introduction to Algebra',
        subject: 'Mathematics'
      });

      mockAxios.onPost('/lessons').reply(201, newLesson);

      const result = await createLesson(newLesson);

      expect(result).toEqual(newLesson);
      expect(result.title).toBe('Introduction to Algebra');
    });

    it('should update an existing lesson', async () => {
      const lessonId = 'lesson-123';
      const updates = { title: 'Updated Title' };
      const updatedLesson = createMockLesson({ 
        id: lessonId, 
        ...updates 
      });

      mockAxios.onPut(`/lessons/${lessonId}`).reply(200, updatedLesson);

      const result = await updateLesson(lessonId, updates);

      expect(result.title).toBe('Updated Title');
    });

    it('should delete a lesson', async () => {
      const lessonId = 'lesson-123';

      mockAxios.onDelete(`/lessons/${lessonId}`).reply(204);

      await expect(deleteLesson(lessonId)).resolves.not.toThrow();
    });
  });

  describe('Assessments API', () => {
    it('should fetch assessments for a class', async () => {
      const mockAssessments = [
        createMockAssessment({ title: 'Math Quiz 1' }),
        createMockAssessment({ title: 'Math Quiz 2' })
      ];

      mockAxios.onGet('/assessments').reply(200, mockAssessments);

      const result = await getAssessments();

      expect(result).toHaveLength(2);
      expect(result[0].title).toBe('Math Quiz 1');
    });

    it('should submit assessment answers', async () => {
      const assessmentId = 'assessment-123';
      const answers = {
        question1: 'answer1',
        question2: 'answer2'
      };
      const mockResult = {
        score: 85,
        passed: true,
        feedback: 'Good job!'
      };

      mockAxios.onPost(`/assessments/${assessmentId}/submit`)
        .reply(200, mockResult);

      const result = await submitAssessment(assessmentId, answers);

      expect(result.score).toBe(85);
      expect(result.passed).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockAxios.onGet('/classes').networkError();

      await expect(listClasses()).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      mockAxios.onGet('/classes').timeout();

      await expect(listClasses()).rejects.toThrow();
    });

    it('should retry failed requests with exponential backoff', async () => {
      let attemptCount = 0;
      
      mockAxios.onGet('/classes').reply(() => {
        attemptCount++;
        if (attemptCount < 3) {
          return [500, { error: 'Server error' }];
        }
        return [200, []];
      });

      // If your API client implements retry logic
      const result = await listClasses();
      
      expect(attemptCount).toBeGreaterThanOrEqual(1);
      expect(result).toEqual([]);
    });

    it('should handle 401 unauthorized and refresh token', async () => {
      // First request fails with 401
      mockAxios.onGet('/classes').replyOnce(401, {
        error: 'Token expired'
      });

      // Token refresh endpoint
      mockAxios.onPost('/auth/refresh').reply(200, {
        token: 'new-token',
        refreshToken: 'new-refresh-token'
      });

      // Retry original request with new token
      mockAxios.onGet('/classes').reply(200, []);

      const result = await listClasses();

      expect(result).toEqual([]);
      expect(localStorage.getItem('token')).toBe('new-token');
    });
  });

  describe('Request Interceptors', () => {
    it('should add default headers to requests', async () => {
      mockAxios.onGet('/users').reply((config) => {
        expect(config.headers?.['Content-Type']).toBe('application/json');
        expect(config.headers?.['X-Client-Version']).toBeDefined();
        return [200, []];
      });

      await listUsers();
    });

    it('should log requests in development mode', async () => {
      const consoleSpy = vi.spyOn(console, 'log');
      process.env.NODE_ENV = 'development';

      mockAxios.onGet('/users').reply(200, []);

      await listUsers();

      // If your API client logs in dev mode
      if (process.env.NODE_ENV === 'development') {
        expect(consoleSpy).toHaveBeenCalled();
      }

      consoleSpy.mockRestore();
    });
  });

  describe('Response Interceptors', () => {
    it('should transform response data', async () => {
      const rawData = {
        data: { users: [] },
        meta: { total: 0 }
      };

      mockAxios.onGet('/users').reply(200, rawData);

      const result = await listUsers();

      // If your API client transforms responses
      expect(Array.isArray(result)).toBe(true);
    });

    it('should handle rate limiting', async () => {
      mockAxios.onGet('/users').reply(429, {
        error: 'Rate limit exceeded',
        retryAfter: 60
      });

      await expect(listUsers()).rejects.toThrow();
    });
  });

  describe('Caching', () => {
    it('should cache GET requests', async () => {
      const mockData = [createMockClass()];
      
      // First request hits the API
      mockAxios.onGet('/classes').replyOnce(200, mockData);

      const result1 = await listClasses();
      const result2 = await listClasses(); // Should use cache

      expect(result1).toEqual(result2);
      expect(mockAxios.history.get.length).toBe(1); // Only one actual request
    });

    it('should invalidate cache on mutations', async () => {
      const mockData = [createMockClass()];
      
      mockAxios.onGet('/classes').reply(200, mockData);
      mockAxios.onPost('/classes').reply(201, createMockClass());

      await listClasses(); // Cache populated
      await createClass({}); // Should invalidate cache
      await listClasses(); // Should hit API again

      expect(mockAxios.history.get.length).toBe(2);
    });
  });
});

// Helper function for testing (add to your actual API if not present)
async function createClass(classData: any) {
  return apiClient.post('/classes', classData);
}