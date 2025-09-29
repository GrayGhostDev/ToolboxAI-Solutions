/**
 * MSW (Mock Service Worker) Handlers
 *
 * Comprehensive API mock handlers for all dashboard endpoints
 */

import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import {
  createMockUser,
  createMockClass,
  createMockLesson,
  createMockAssessment,
  createMockDashboardData,
  createMockLeaderboardEntry,
  createMockMessage,
  createMockProgress,
  createMockBadge,
} from './mockData';

// Base API URL
const API_BASE = 'http://localhost:8008';

/**
 * Authentication Handlers
 */
const authHandlers = [
  // Login
  http.post(`${API_BASE}/api/v1/auth/login`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate validation
    if (!body.email || !body.password) {
      return HttpResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Simulate successful login
    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        user: createMockUser({
          email: body.email,
          role: 'teacher',
        }),
      });
    }

    // Simulate invalid credentials
    return HttpResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  // Register
  http.post(`${API_BASE}/api/v1/auth/register`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate validation
    if (!body.email || !body.password || !body.role) {
      return HttpResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Simulate email already exists
    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { error: 'Email already registered' },
        { status: 409 }
      );
    }

    // Simulate successful registration
    return HttpResponse.json({
      message: 'Registration successful',
      user: createMockUser({
        email: body.email,
        role: body.role,
        firstName: body.firstName,
        lastName: body.lastName,
      }),
    });
  }),

  // Password Reset Request
  http.post(`${API_BASE}/api/v1/auth/password-reset`, async ({ request }) => {
    const body = await request.json() as any;

    if (!body.email) {
      return HttpResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      message: 'Password reset email sent',
    });
  }),

  // Password Reset Confirm
  http.post(`${API_BASE}/api/v1/auth/password-reset/confirm`, async ({ request }) => {
    const body = await request.json() as any;

    if (!body.token || !body.password) {
      return HttpResponse.json(
        { error: 'Token and password are required' },
        { status: 400 }
      );
    }

    // Simulate invalid token
    if (body.token === 'invalid-token') {
      return HttpResponse.json(
        { error: 'Invalid or expired token' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      message: 'Password reset successful',
    });
  }),

  // Verify Token
  http.get(`${API_BASE}/api/v1/auth/verify`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      valid: true,
      user: createMockUser(),
    });
  }),
];

/**
 * Dashboard Handlers
 */
const dashboardHandlers = [
  // Dashboard Overview
  http.get(`${API_BASE}/api/v1/dashboard/overview`, () => {
    return HttpResponse.json(createMockDashboardData());
  }),

  // Dashboard Metrics
  http.get(`${API_BASE}/api/v1/dashboard/metrics`, ({ request }) => {
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || 'week';

    return HttpResponse.json({
      period,
      metrics: {
        activeUsers: 150,
        completionRate: 78.5,
        averageScore: 82.3,
        totalHours: 324,
      },
      trend: {
        users: '+12%',
        completion: '+5%',
        score: '+3%',
        hours: '+18%',
      },
    });
  }),
];

/**
 * Class Management Handlers
 */
const classHandlers = [
  // List Classes
  http.get(`${API_BASE}/api/v1/classes`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    const classes = Array.from({ length: limit }, (_, i) =>
      createMockClass({
        id: `class-${page}-${i}`,
        name: `Class ${page}-${i + 1}`,
      })
    );

    return HttpResponse.json({
      data: classes,
      total: 50,
      page,
      limit,
    });
  }),

  // Get Class Details
  http.get(`${API_BASE}/api/v1/classes/:id`, ({ params }) => {
    const { id } = params;

    if (id === 'not-found') {
      return HttpResponse.json(
        { error: 'Class not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(
      createMockClass({
        id: id as string,
        name: `Class ${id}`,
        studentCount: 25,
      })
    );
  }),

  // Create Class
  http.post(`${API_BASE}/api/v1/classes`, async ({ request }) => {
    const body = await request.json() as any;

    if (!body.name || !body.subject) {
      return HttpResponse.json(
        { error: 'Name and subject are required' },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      createMockClass({
        ...body,
        id: `class-${Date.now()}`,
      }),
      { status: 201 }
    );
  }),

  // Update Class
  http.put(`${API_BASE}/api/v1/classes/:id`, async ({ params, request }) => {
    const { id } = params;
    const body = await request.json() as any;

    return HttpResponse.json(
      createMockClass({
        id: id as string,
        ...body,
      })
    );
  }),

  // Delete Class
  http.delete(`${API_BASE}/api/v1/classes/:id`, ({ params }) => {
    const { id } = params;

    if (id === 'protected') {
      return HttpResponse.json(
        { error: 'Cannot delete active class' },
        { status: 403 }
      );
    }

    return HttpResponse.json({
      message: 'Class deleted successfully',
    });
  }),
];

/**
 * Lesson Handlers
 */
const lessonHandlers = [
  // List Lessons
  http.get(`${API_BASE}/api/v1/lessons`, () => {
    const lessons = Array.from({ length: 10 }, (_, i) =>
      createMockLesson({
        id: `lesson-${i}`,
        title: `Lesson ${i + 1}`,
      })
    );

    return HttpResponse.json({
      data: lessons,
      total: 10,
    });
  }),

  // Generate AI Content
  http.post(`${API_BASE}/api/v1/lessons/generate`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate AI generation delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    return HttpResponse.json({
      content: `AI Generated content for ${body.topic}`,
      objectives: ['Objective 1', 'Objective 2'],
      materials: ['Material 1', 'Material 2'],
    });
  }),
];

/**
 * Assessment Handlers
 */
const assessmentHandlers = [
  // List Assessments
  http.get(`${API_BASE}/api/v1/assessments`, () => {
    const assessments = Array.from({ length: 5 }, (_, i) =>
      createMockAssessment({
        id: `assessment-${i}`,
        title: `Quiz ${i + 1}`,
      })
    );

    return HttpResponse.json({
      data: assessments,
      total: 5,
    });
  }),

  // Submit Assessment
  http.post(`${API_BASE}/api/v1/assessments/:id/submit`, async ({ params, request }) => {
    const { id } = params;
    const body = await request.json() as any;

    return HttpResponse.json({
      score: 85,
      passed: true,
      feedback: 'Great job!',
      correctAnswers: 8,
      totalQuestions: 10,
    });
  }),
];

/**
 * Gamification Handlers
 */
const gamificationHandlers = [
  // Get Leaderboard
  http.get(`${API_BASE}/api/v1/leaderboard`, ({ request }) => {
    const url = new URL(request.url);
    const type = url.searchParams.get('type') || 'class';

    const entries = Array.from({ length: 10 }, (_, i) =>
      createMockLeaderboardEntry({
        rank: i + 1,
        userId: `user-${i}`,
        displayName: `Student ${i + 1}`,
        xp: 1000 - (i * 50),
      })
    );

    return HttpResponse.json({
      type,
      entries,
      updatedAt: new Date().toISOString(),
    });
  }),

  // Get User Badges
  http.get(`${API_BASE}/api/v1/users/:id/badges`, ({ params }) => {
    const badges = Array.from({ length: 5 }, (_, i) =>
      createMockBadge({
        id: `badge-${i}`,
        name: `Badge ${i + 1}`,
      })
    );

    return HttpResponse.json({
      badges,
      total: 5,
      xpTotal: 500,
    });
  }),

  // Claim Reward
  http.post(`${API_BASE}/api/v1/rewards/:id/claim`, ({ params }) => {
    const { id } = params;

    if (id === 'already-claimed') {
      return HttpResponse.json(
        { error: 'Reward already claimed' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      message: 'Reward claimed successfully',
      xpAwarded: 100,
      newTotal: 1100,
    });
  }),
];

/**
 * Communication Handlers
 */
const communicationHandlers = [
  // List Messages
  http.get(`${API_BASE}/api/v1/messages`, ({ request }) => {
    const url = new URL(request.url);
    const folder = url.searchParams.get('folder') || 'inbox';

    const messages = Array.from({ length: 5 }, (_, i) =>
      createMockMessage({
        id: `message-${i}`,
        subject: `Message ${i + 1}`,
        read: i < 2,
      })
    );

    return HttpResponse.json({
      folder,
      messages,
      unreadCount: 3,
    });
  }),

  // Send Message
  http.post(`${API_BASE}/api/v1/messages`, async ({ request }) => {
    const body = await request.json() as any;

    if (!body.recipientId || !body.subject || !body.content) {
      return HttpResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      message: 'Message sent successfully',
      messageId: `message-${Date.now()}`,
    });
  }),
];

/**
 * Progress & Reports Handlers
 */
const progressHandlers = [
  // Get User Progress
  http.get(`${API_BASE}/api/v1/users/:id/progress`, ({ params, request }) => {
    const url = new URL(request.url);
    const subject = url.searchParams.get('subject');

    return HttpResponse.json({
      userId: params.id,
      subject,
      overallProgress: 75,
      completedLessons: 15,
      totalLessons: 20,
      averageScore: 82.5,
      timeSpent: 1200, // minutes
      streakDays: 7,
    });
  }),

  // Generate Report
  http.post(`${API_BASE}/api/v1/reports/generate`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 2000));

    return HttpResponse.json({
      reportId: `report-${Date.now()}`,
      status: 'completed',
      downloadUrl: `/api/v1/reports/download/report-${Date.now()}.pdf`,
    });
  }),
];

/**
 * Settings & Configuration Handlers
 */
const settingsHandlers = [
  // Get User Settings
  http.get(`${API_BASE}/api/v1/users/:id/settings`, ({ params }) => {
    return HttpResponse.json({
      userId: params.id,
      theme: 'light',
      language: 'en',
      notifications: {
        email: true,
        push: true,
        sms: false,
      },
      privacy: {
        profileVisible: true,
        showProgress: true,
      },
    });
  }),

  // Update Settings
  http.put(`${API_BASE}/api/v1/users/:id/settings`, async ({ params, request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      message: 'Settings updated successfully',
      settings: body,
    });
  }),
];

/**
 * Roblox Integration Handlers
 */
const robloxHandlers = [
  // List Roblox Environments
  http.get(`${API_BASE}/api/v1/roblox/environments`, () => {
    return HttpResponse.json({
      environments: [
        {
          id: 'env-1',
          name: 'Math World',
          status: 'active',
          playerCount: 12,
          maxPlayers: 30,
        },
        {
          id: 'env-2',
          name: 'Science Lab',
          status: 'inactive',
          playerCount: 0,
          maxPlayers: 25,
        },
      ],
    });
  }),

  // Deploy Content to Roblox
  http.post(`${API_BASE}/api/v1/roblox/deploy`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate deployment
    await new Promise(resolve => setTimeout(resolve, 3000));

    return HttpResponse.json({
      message: 'Content deployed successfully',
      deploymentId: `deploy-${Date.now()}`,
      status: 'completed',
    });
  }),

  // Get Gameplay Session
  http.get(`${API_BASE}/api/v1/roblox/sessions/:id`, ({ params }) => {
    return HttpResponse.json({
      sessionId: params.id,
      startTime: new Date(Date.now() - 3600000).toISOString(),
      endTime: new Date().toISOString(),
      events: [
        { timestamp: '00:01:23', type: 'quest_started', data: { questId: 'q1' } },
        { timestamp: '00:05:45', type: 'checkpoint', data: { checkpoint: 1 } },
        { timestamp: '00:10:12', type: 'quest_completed', data: { questId: 'q1', xp: 100 } },
      ],
      metrics: {
        totalTime: 3600,
        questsCompleted: 3,
        xpEarned: 300,
        accuracy: 85,
      },
    });
  }),
];

/**
 * Compliance Handlers
 */
const complianceHandlers = [
  // Get Compliance Status
  http.get(`${API_BASE}/api/v1/compliance/status`, () => {
    return HttpResponse.json({
      coppa: {
        compliant: true,
        lastAudit: new Date().toISOString(),
      },
      ferpa: {
        compliant: true,
        lastAudit: new Date().toISOString(),
      },
      gdpr: {
        compliant: false,
        issues: ['Missing privacy policy update'],
      },
    });
  }),

  // Export User Data (GDPR)
  http.post(`${API_BASE}/api/v1/compliance/export-data`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      message: 'Data export initiated',
      exportId: `export-${Date.now()}`,
      estimatedTime: '5 minutes',
    });
  }),
];

/**
 * Integration Handlers
 */
const integrationHandlers = [
  // List Integrations
  http.get(`${API_BASE}/api/v1/integrations`, () => {
    return HttpResponse.json({
      integrations: [
        {
          id: 'google-classroom',
          name: 'Google Classroom',
          status: 'connected',
          lastSync: new Date().toISOString(),
        },
        {
          id: 'canvas',
          name: 'Canvas LMS',
          status: 'disconnected',
          lastSync: null,
        },
      ],
    });
  }),

  // Connect Integration
  http.post(`${API_BASE}/api/v1/integrations/:id/connect`, ({ params }) => {
    return HttpResponse.json({
      message: 'Integration connected successfully',
      integrationId: params.id,
      authUrl: `https://oauth.example.com/authorize?integration=${params.id}`,
    });
  }),
];

/**
 * Combine all handlers
 */
export const handlers = [
  ...authHandlers,
  ...dashboardHandlers,
  ...classHandlers,
  ...lessonHandlers,
  ...assessmentHandlers,
  ...gamificationHandlers,
  ...communicationHandlers,
  ...progressHandlers,
  ...settingsHandlers,
  ...robloxHandlers,
  ...complianceHandlers,
  ...integrationHandlers,
];

/**
 * Create and export the MSW server
 */
export const server = setupServer(...handlers);

/**
 * Helper function to add custom handlers for specific tests
 */
export function addCustomHandler(handler: any) {
  server.use(handler);
}

/**
 * Helper function to reset handlers to defaults
 */
export function resetHandlers() {
  server.resetHandlers();
}

/**
 * Helper function to simulate network errors
 */
export function simulateNetworkError(endpoint: string) {
  server.use(
    http.get(`${API_BASE}${endpoint}`, () => {
      return HttpResponse.error();
    }),
    http.post(`${API_BASE}${endpoint}`, () => {
      return HttpResponse.error();
    })
  );
}

/**
 * Helper function to simulate slow network
 */
export function simulateSlowNetwork(delayMs: number = 3000) {
  server.use(
    http.all('*', async ({ request }) => {
      await new Promise(resolve => setTimeout(resolve, delayMs));
      return HttpResponse.json({});
    })
  );
}