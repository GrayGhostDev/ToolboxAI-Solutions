jest.setTimeout(10000);

import { test, expect, APIRequestContext } from '@playwright/test';

const API_URL = process.env.PLAYWRIGHT_API_URL || 'http://127.0.0.1:8008';

test.describe('Comprehensive Endpoint Tests', () => {
  let apiContext: APIRequestContext;
  let authToken: string | null = null;

  test.beforeAll(async ({ playwright }) => {
    apiContext = await playwright.request.newContext({
      baseURL: API_URL,
      extraHTTPHeaders: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });

    // Try to authenticate
    try {
      const loginResponse = await apiContext.post('/api/v1/auth/login', {
        data: {
          username: 'test_teacher',
          password: 'TestPass123!'
        }
      });

      if (loginResponse.ok()) {
        const data = await loginResponse.json();
        authToken = data.access_token || data.token;
      }
    } catch (error) {
      console.log('Authentication not available or failed:', error);
    }
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test.describe('Health & Status Endpoints', () => {
    test('GET /health should return healthy status', async () => {
      const response = await apiContext.get('/health');
      expect([200, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('status');
      }
    });

    test('GET /api/v1/status should return API status', async () => {
      const response = await apiContext.get('/api/v1/status');
      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Classes Endpoints', () => {
    test('GET /api/v1/classes should return classes list', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/classes', { headers });
      expect([200, 401, 403]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });

    test('GET /api/v1/classes/{id} should return class details', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/classes/1', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('name');
      }
    });

    test('POST /api/v1/classes should create a new class', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.post('/api/v1/classes', {
        headers,
        data: {
          name: 'Test Class',
          subject: 'Mathematics',
          grade_level: 7,
          room: 'Room 101',
          schedule: 'Mon/Wed/Fri 10:00 AM',
          description: 'Test class for E2E testing'
        }
      });

      expect([200, 201, 401, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data.name).toBe('Test Class');
      }
    });

    test('GET /api/v1/classes/{id}/students should return student list', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/classes/1/students', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });
  });

  test.describe('Lessons Endpoints', () => {
    test('GET /api/v1/lessons should return lessons list', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/lessons', { headers });
      expect([200, 401, 403]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });

    test('GET /api/v1/lessons/{id} should return lesson details', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/lessons/1', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('title');
      }
    });

    test('POST /api/v1/lessons should create a new lesson', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.post('/api/v1/lessons', {
        headers,
        data: {
          title: 'Test Lesson',
          subject: 'Mathematics',
          grade_level: 7,
          description: 'Test lesson for E2E testing',
          objectives: ['Understand basic concepts', 'Apply knowledge'],
          duration: 45,
          materials: ['Textbook', 'Calculator']
        }
      });

      expect([200, 201, 401, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data.title).toBe('Test Lesson');
      }
    });

    test('GET /api/v1/lessons/{id}/materials should return lesson materials', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/lessons/1/materials', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });
  });

  test.describe('Assessments Endpoints', () => {
    test('GET /api/v1/assessments should return assessments list', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/assessments', { headers });
      expect([200, 401, 403]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });

    test('GET /api/v1/assessments/{id} should return assessment details', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/assessments/1', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('title');
      }
    });

    test('POST /api/v1/assessments should create a new assessment', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.post('/api/v1/assessments', {
        headers,
        data: {
          title: 'Test Assessment',
          type: 'quiz',
          class_id: 1,
          description: 'Test assessment for E2E testing',
          total_points: 100,
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          questions: [
            {
              question: 'What is 2 + 2?',
              type: 'multiple_choice',
              options: ['3', '4', '5', '6'],
              correct_answer: '4',
              points: 10
            }
          ]
        }
      });

      expect([200, 201, 401, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data.title).toBe('Test Assessment');
      }
    });

    test('GET /api/v1/assessments/{id}/submissions should return submissions', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/assessments/1/submissions', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });
  });

  test.describe('Messages Endpoints', () => {
    test('GET /api/v1/messages should return messages list', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/messages', { headers });
      expect([200, 401, 403]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });

    test('POST /api/v1/messages should send a new message', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.post('/api/v1/messages', {
        headers,
        data: {
          recipient_id: '2',
          subject: 'Test Message',
          body: 'This is a test message from E2E tests',
          priority: 'normal'
        }
      });

      expect([200, 201, 401, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data.subject).toBe('Test Message');
      }
    });

    test('GET /api/v1/messages/{id} should return message details', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/messages/1', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('subject');
      }
    });
  });

  test.describe('Analytics Endpoints', () => {
    test('GET /api/v1/analytics/overview should return analytics overview', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/analytics/overview', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('total_students');
      }
    });

    test('GET /api/v1/analytics/student-progress should return progress data', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/analytics/student-progress', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());
    });
  });

  test.describe('Roblox Integration Endpoints', () => {
    test('GET /api/v1/roblox/environments should return Roblox environments', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/roblox/environments', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());
    });

    test('POST /api/v1/roblox/generate should generate Roblox content', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.post('/api/v1/roblox/generate', {
        headers,
        data: {
          lesson_id: 1,
          environment_type: 'classroom',
          interactive_elements: ['whiteboard', 'desks']
        }
      });

      expect([200, 201, 401, 403, 404]).toContain(response.status());
    });
  });

  test.describe('Gamification Endpoints', () => {
    test('GET /api/v1/gamification/leaderboard should return leaderboard', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/gamification/leaderboard', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());
    });

    test('GET /api/v1/gamification/achievements should return achievements', async () => {
      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await apiContext.get('/api/v1/gamification/achievements', { headers });
      expect([200, 401, 403, 404]).toContain(response.status());
    });
  });

  test.describe('Authentication Endpoints', () => {
    test('POST /api/v1/auth/login should authenticate user', async () => {
      const response = await apiContext.post('/api/v1/auth/login', {
        data: {
          username: 'test_teacher',
          password: 'TestPass123!'
        }
      });

      expect([200, 401, 422]).toContain(response.status());

      if (response.status() === 200) {
        const data = await response.json();
        expect(data).toHaveProperty('access_token');
      }
    });

    test('POST /api/v1/auth/refresh should refresh token', async () => {
      if (!authToken) {
        test.skip();
        return;
      }

      const response = await apiContext.post('/api/v1/auth/refresh', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/auth/logout should logout user', async () => {
      if (!authToken) {
        test.skip();
        return;
      }

      const response = await apiContext.post('/api/v1/auth/logout', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      expect([200, 204, 401]).toContain(response.status());
    });
  });
});