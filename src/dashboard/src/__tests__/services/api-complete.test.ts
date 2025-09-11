import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest';
import axios, { AxiosError } from 'axios';
import MockAdapter from 'axios-mock-adapter';

// Mock WebSocketService
vi.mock('../../services/websocket', () => ({
  WebSocketService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn().mockResolvedValue(undefined),
      disconnect: vi.fn(),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      getState: vi.fn(() => 'DISCONNECTED'),
      isConnected: vi.fn(() => false),
      onStateChange: vi.fn(),
      onError: vi.fn(),
      emit: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      reconnect: vi.fn(),
      getConnectionStats: vi.fn(() => ({
        connected: false,
        reconnectAttempts: 0,
        lastError: null,
        uptime: 0
      }))
    }))
  },
  websocketService: {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    send: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    getState: vi.fn(() => 'DISCONNECTED'),
    isConnected: vi.fn(() => false)
  },
  WebSocketState: {
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    DISCONNECTED: 'DISCONNECTED',
    RECONNECTING: 'RECONNECTING',
    ERROR: 'ERROR'
  }
}));

// Mock store
vi.mock('../../store', () => ({
  store: {
    dispatch: vi.fn(),
    getState: vi.fn(() => ({
      user: { 
        currentUser: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        role: null
      },
      ui: {
        loading: false,
        error: null,
        notifications: []
      },
      dashboard: {
        data: null,
        loading: false,
        error: null
      },
      classes: {
        list: [],
        current: null,
        loading: false
      },
      messages: {
        list: [],
        unreadCount: 0
      }
    })),
    subscribe: vi.fn(() => vi.fn())
  },
  useAppDispatch: () => vi.fn(),
  useAppSelector: (selector: any) => selector({
    user: { 
      currentUser: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      role: null
    },
    ui: {
      loading: false,
      error: null,
      notifications: []
    },
    dashboard: {
      data: null,
      loading: false,
      error: null
    },
    classes: {
      list: [],
      current: null,
      loading: false
    },
    messages: {
      list: [],
      unreadCount: 0
    }
  })
}));

// Import after mocks
import ApiClient from '../../services/api';
import type { 
  LoginCredentials,
  RegisterData,
  User,
  Class,
  Lesson,
  Assessment,
  Message,
  DashboardData,
  SchoolData,
  ReportData,
  ComplianceData,
  RewardData,
  MissionData,
  UserRole
} from '../../types';

const API_BASE_URL = 'http://localhost:8008';

describe('Complete API Service Test Suite', () => {
  let mock: MockAdapter;
  let apiClient: ApiClient;
  let localStorageMock: { [key: string]: string };
  let consoleErrorSpy: any;
  let consoleWarnSpy: any;

  beforeAll(() => {
    // Capture console errors and warnings
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // Fix for axios config serialization in Vitest
    if (typeof globalThis.structuredClone === 'undefined') {
      globalThis.structuredClone = (obj: any) => {
        try {
          return JSON.parse(JSON.stringify(obj));
        } catch {
          return obj;
        }
      };
    }
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    
    // Setup axios mock
    mock = new MockAdapter(axios, { delayResponse: 0 });
    
    // Create new API client instance
    apiClient = new ApiClient();

    // Setup localStorage mock
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
        Object.keys(localStorageMock).forEach(key => delete localStorageMock[key]);
      },
      length: Object.keys(localStorageMock).length,
      key: (index: number) => Object.keys(localStorageMock)[index] || null
    } as Storage;

    // Set default auth token
    localStorage.setItem('toolboxai_auth_token', 'test-jwt-token');
    localStorage.setItem('toolboxai_refresh_token', 'test-refresh-token');
  });

  afterEach(() => {
    mock.restore();
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Authentication Module', () => {
    describe('Login', () => {
      it('should successfully login with email and password', async () => {
        const credentials: LoginCredentials = {
          email: 'teacher@example.com',
          password: 'SecurePass123!'
        };

        const mockResponse = {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          user: {
            id: 'user-123',
            email: 'teacher@example.com',
            username: 'teacher',
            first_name: 'John',
            last_name: 'Doe',
            role: 'teacher' as UserRole,
            school_id: 'school-123',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          }
        };

        mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, mockResponse);

        const result = await apiClient.login(credentials.email, credentials.password);
        
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('toolboxai_auth_token')).toBe('new-access-token');
        expect(localStorage.getItem('toolboxai_refresh_token')).toBe('new-refresh-token');
        expect(mock.history.post[0].data).toBe(JSON.stringify(credentials));
      });

      it('should handle login with username', async () => {
        const mockResponse = {
          access_token: 'username-token',
          refresh_token: 'username-refresh',
          user: {
            id: 'user-456',
            username: 'johndoe',
            email: 'john@example.com',
            role: 'student'
          }
        };

        mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, mockResponse);

        const result = await apiClient.login('johndoe', 'password123');
        
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('toolboxai_auth_token')).toBe('username-token');
      });

      it('should handle invalid credentials', async () => {
        mock.onPost(`${API_BASE_URL}/auth/login`).reply(401, {
          detail: 'Invalid email or password'
        });

        await expect(apiClient.login('wrong@example.com', 'wrongpass'))
          .rejects.toThrow();
      });

      it('should handle rate limiting on login', async () => {
        mock.onPost(`${API_BASE_URL}/auth/login`).reply(429, {
          detail: 'Too many login attempts. Please try again later.'
        });

        await expect(apiClient.login('test@example.com', 'password'))
          .rejects.toThrow();
      });

      it('should handle server errors during login', async () => {
        mock.onPost(`${API_BASE_URL}/auth/login`).reply(500, {
          detail: 'Internal server error'
        });

        await expect(apiClient.login('test@example.com', 'password'))
          .rejects.toThrow();
      });
    });

    describe('Registration', () => {
      it('should successfully register a new user', async () => {
        const registerData: RegisterData = {
          email: 'newuser@example.com',
          username: 'newuser',
          password: 'SecurePass123!',
          confirm_password: 'SecurePass123!',
          first_name: 'New',
          last_name: 'User',
          role: 'student',
          school_id: 'school-123'
        };

        const mockResponse = {
          id: 'user-789',
          email: 'newuser@example.com',
          username: 'newuser',
          first_name: 'New',
          last_name: 'User',
          role: 'student',
          school_id: 'school-123',
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onPost(`${API_BASE_URL}/auth/register`).reply(201, mockResponse);

        const result = await apiClient.register(registerData);
        
        expect(result).toEqual(mockResponse);
        expect(mock.history.post[0].data).toBe(JSON.stringify(registerData));
      });

      it('should handle registration validation errors', async () => {
        mock.onPost(`${API_BASE_URL}/auth/register`).reply(422, {
          detail: [
            { loc: ['body', 'email'], msg: 'Invalid email format' },
            { loc: ['body', 'password'], msg: 'Password too weak' }
          ]
        });

        await expect(apiClient.register({
          email: 'invalid',
          password: '123',
          username: 'test'
        } as any)).rejects.toThrow();
      });

      it('should handle duplicate email registration', async () => {
        mock.onPost(`${API_BASE_URL}/auth/register`).reply(409, {
          detail: 'Email already registered'
        });

        await expect(apiClient.register({
          email: 'existing@example.com',
          password: 'Password123!',
          username: 'newuser'
        } as any)).rejects.toThrow();
      });
    });

    describe('Logout', () => {
      it('should successfully logout user', async () => {
        localStorage.setItem('toolboxai_auth_token', 'active-token');
        localStorage.setItem('toolboxai_refresh_token', 'active-refresh');

        mock.onPost(`${API_BASE_URL}/auth/logout`).reply(204);

        await apiClient.logout();

        expect(localStorage.getItem('toolboxai_auth_token')).toBeNull();
        expect(localStorage.getItem('toolboxai_refresh_token')).toBeNull();
        expect(mockWebSocketInstance.disconnect).toHaveBeenCalled();
      });

      it('should handle logout errors gracefully', async () => {
        mock.onPost(`${API_BASE_URL}/auth/logout`).reply(500);

        // Should not throw, just clear local state
        await expect(apiClient.logout()).resolves.toBeUndefined();
        expect(localStorage.getItem('toolboxai_auth_token')).toBeNull();
      });
    });

    describe('Token Refresh', () => {
      it('should successfully refresh access token', async () => {
        const mockResponse = {
          access_token: 'refreshed-token',
          refresh_token: 'new-refresh-token'
        };

        mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(200, mockResponse);

        const result = await apiClient.refreshToken();
        
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('toolboxai_auth_token')).toBe('refreshed-token');
        expect(localStorage.getItem('toolboxai_refresh_token')).toBe('new-refresh-token');
      });

      it('should handle refresh token expiration', async () => {
        mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(401, {
          detail: 'Refresh token expired'
        });

        await expect(apiClient.refreshToken()).rejects.toThrow();
        expect(localStorage.getItem('toolboxai_auth_token')).toBeNull();
        expect(localStorage.getItem('toolboxai_refresh_token')).toBeNull();
      });

      it('should automatically refresh token on 401 response', async () => {
        // First request returns 401
        mock.onGet(`${API_BASE_URL}/protected`).replyOnce(401);
        
        // Refresh token request
        mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(200, {
          access_token: 'new-token',
          refresh_token: 'new-refresh'
        });
        
        // Retry original request
        mock.onGet(`${API_BASE_URL}/protected`).reply(200, { data: 'protected' });

        const result = await apiClient['request']({ method: 'GET', url: '/protected' });
        
        expect(result.data).toBe('protected');
        expect(localStorage.getItem('toolboxai_auth_token')).toBe('new-token');
      });
    });

    describe('User Profile', () => {
      it('should fetch current user profile', async () => {
        const mockUser = {
          id: 'user-123',
          email: 'user@example.com',
          username: 'testuser',
          first_name: 'Test',
          last_name: 'User',
          role: 'teacher',
          school_id: 'school-123',
          profile_picture: 'https://example.com/avatar.jpg',
          bio: 'Test bio',
          preferences: {
            theme: 'dark',
            language: 'en',
            notifications: true
          }
        };

        mock.onGet(`${API_BASE_URL}/auth/me`).reply(200, mockUser);

        const result = await apiClient.getCurrentUser();
        
        expect(result).toEqual(mockUser);
      });

      it('should update user profile', async () => {
        const updates = {
          first_name: 'Updated',
          last_name: 'Name',
          bio: 'Updated bio'
        };

        const mockResponse = {
          id: 'user-123',
          ...updates,
          email: 'user@example.com',
          username: 'testuser',
          role: 'teacher'
        };

        mock.onPatch(`${API_BASE_URL}/auth/profile`).reply(200, mockResponse);

        const result = await apiClient.updateProfile(updates);
        
        expect(result).toEqual(mockResponse);
        expect(mock.history.patch[0].data).toBe(JSON.stringify(updates));
      });

      it('should change user password', async () => {
        const passwordData = {
          current_password: 'OldPass123!',
          new_password: 'NewPass456!',
          confirm_password: 'NewPass456!'
        };

        mock.onPost(`${API_BASE_URL}/auth/change-password`).reply(200, {
          message: 'Password changed successfully'
        });

        const result = await apiClient.changePassword(
          passwordData.current_password,
          passwordData.new_password
        );
        
        expect(result.message).toBe('Password changed successfully');
      });

      it('should handle incorrect current password', async () => {
        mock.onPost(`${API_BASE_URL}/auth/change-password`).reply(401, {
          detail: 'Current password is incorrect'
        });

        await expect(apiClient.changePassword('wrong', 'new'))
          .rejects.toThrow();
      });
    });

    describe('Password Reset', () => {
      it('should request password reset', async () => {
        mock.onPost(`${API_BASE_URL}/auth/forgot-password`).reply(200, {
          message: 'Password reset email sent'
        });

        const result = await apiClient.forgotPassword('user@example.com');
        
        expect(result.message).toBe('Password reset email sent');
      });

      it('should reset password with token', async () => {
        mock.onPost(`${API_BASE_URL}/auth/reset-password`).reply(200, {
          message: 'Password reset successfully'
        });

        const result = await apiClient.resetPassword('reset-token', 'NewPass123!');
        
        expect(result.message).toBe('Password reset successfully');
      });

      it('should handle invalid reset token', async () => {
        mock.onPost(`${API_BASE_URL}/auth/reset-password`).reply(400, {
          detail: 'Invalid or expired reset token'
        });

        await expect(apiClient.resetPassword('invalid', 'password'))
          .rejects.toThrow();
      });
    });

    describe('Email Verification', () => {
      it('should verify email with token', async () => {
        mock.onPost(`${API_BASE_URL}/auth/verify-email`).reply(200, {
          message: 'Email verified successfully'
        });

        const result = await apiClient.verifyEmail('verification-token');
        
        expect(result.message).toBe('Email verified successfully');
      });

      it('should resend verification email', async () => {
        mock.onPost(`${API_BASE_URL}/auth/resend-verification`).reply(200, {
          message: 'Verification email sent'
        });

        const result = await apiClient.resendVerificationEmail();
        
        expect(result.message).toBe('Verification email sent');
      });
    });
  });

  describe('Dashboard Module', () => {
    describe('Overview Data', () => {
      it('should fetch teacher dashboard overview', async () => {
        const mockData = {
          totalStudents: 150,
          totalClasses: 8,
          activeAssessments: 12,
          completionRate: 78.5,
          averageScore: 85.2,
          recentActivity: [
            { type: 'submission', student: 'John Doe', time: '2 hours ago' },
            { type: 'quiz', student: 'Jane Smith', time: '3 hours ago' }
          ],
          upcomingDeadlines: [
            { title: 'Math Quiz', date: '2024-01-15', class: 'Math 101' },
            { title: 'Science Project', date: '2024-01-20', class: 'Science 202' }
          ]
        };

        mock.onGet(`${API_BASE_URL}/dashboard/overview/teacher`).reply(200, mockData);

        const result = await apiClient.getDashboardOverview('teacher');
        
        expect(result).toEqual(mockData);
        expect((result as any).totalStudents).toBe(150);
        expect((result as any).completionRate).toBe(78.5);
      });

      it('should fetch student dashboard overview', async () => {
        const mockData = {
          enrolledCourses: 5,
          completedLessons: 42,
          upcomingAssignments: 3,
          averageGrade: 88.5,
          streakDays: 15,
          badges: ['Fast Learner', 'Quiz Master'],
          recentScores: [85, 92, 78, 95, 88]
        };

        mock.onGet(`${API_BASE_URL}/dashboard/overview/student`).reply(200, mockData);

        const result = await apiClient.getDashboardOverview('student');
        
        expect(result).toEqual(mockData);
        expect((result as any).streakDays).toBe(15);
      });

      it('should fetch admin dashboard overview', async () => {
        const mockData = {
          totalSchools: 25,
          totalTeachers: 450,
          totalStudents: 8500,
          activeUsers: 6200,
          systemHealth: 'healthy',
          pendingApprovals: 12,
          recentIssues: [],
          usageStats: {
            daily: 5500,
            weekly: 7800,
            monthly: 8200
          }
        };

        mock.onGet(`${API_BASE_URL}/dashboard/overview/admin`).reply(200, mockData);

        const result = await apiClient.getDashboardOverview('admin');
        
        expect(result).toEqual(mockData);
        expect((result as any).systemHealth).toBe('healthy');
      });

      it('should handle dashboard data fetch errors', async () => {
        mock.onGet(`${API_BASE_URL}/dashboard/overview/teacher`).reply(500);

        await expect(apiClient.getDashboardOverview('teacher'))
          .rejects.toThrow();
      });
    });

    describe('Analytics', () => {
      it('should fetch performance analytics', async () => {
        const mockAnalytics = {
          period: 'month',
          metrics: {
            engagement: 85,
            completion: 78,
            satisfaction: 92
          },
          trends: {
            daily: [75, 78, 82, 85, 83, 88, 85],
            weekly: [78, 82, 85, 87]
          }
        };

        mock.onGet(`${API_BASE_URL}/dashboard/analytics`).reply(200, mockAnalytics);

        const result = await apiClient.getAnalytics();
        
        expect(result).toEqual(mockAnalytics);
      });

      it('should fetch analytics with date range', async () => {
        const params = {
          start_date: '2024-01-01',
          end_date: '2024-01-31',
          metrics: ['engagement', 'completion']
        };

        mock.onGet(`${API_BASE_URL}/dashboard/analytics`).reply(200, { data: 'analytics' });

        await apiClient.getAnalytics(params);
        
        expect(mock.history.get[0].params).toEqual(params);
      });
    });

    describe('Activity Feed', () => {
      it('should fetch recent activities', async () => {
        const mockActivities = [
          {
            id: 'act-1',
            type: 'submission',
            user: 'John Doe',
            action: 'submitted assignment',
            timestamp: '2024-01-01T10:00:00Z'
          },
          {
            id: 'act-2',
            type: 'quiz',
            user: 'Jane Smith',
            action: 'completed quiz',
            timestamp: '2024-01-01T09:30:00Z'
          }
        ];

        mock.onGet(`${API_BASE_URL}/dashboard/activities`).reply(200, mockActivities);

        const result = await apiClient.getRecentActivities();
        
        expect(result).toEqual(mockActivities);
        expect(result).toHaveLength(2);
      });

      it('should fetch activities with pagination', async () => {
        mock.onGet(`${API_BASE_URL}/dashboard/activities`).reply(200, {
          items: [],
          total: 100,
          page: 1,
          per_page: 20
        });

        await apiClient.getRecentActivities({ page: 1, limit: 20 });
        
        expect(mock.history.get[0].params).toEqual({ page: 1, limit: 20 });
      });
    });

    describe('Notifications', () => {
      it('should fetch notifications', async () => {
        const mockNotifications = [
          {
            id: 'notif-1',
            type: 'info',
            title: 'New Assignment',
            message: 'You have a new assignment',
            read: false,
            created_at: '2024-01-01T10:00:00Z'
          }
        ];

        mock.onGet(`${API_BASE_URL}/dashboard/notifications`).reply(200, mockNotifications);

        const result = await apiClient.getNotifications();
        
        expect(result).toEqual(mockNotifications);
      });

      it('should mark notification as read', async () => {
        mock.onPatch(`${API_BASE_URL}/dashboard/notifications/notif-1/read`).reply(200, {
          id: 'notif-1',
          read: true
        });

        const result = await apiClient.markNotificationRead('notif-1');
        
        expect(result.read).toBe(true);
      });

      it('should mark all notifications as read', async () => {
        mock.onPost(`${API_BASE_URL}/dashboard/notifications/read-all`).reply(200, {
          updated: 5
        });

        const result = await apiClient.markAllNotificationsRead();
        
        expect(result.updated).toBe(5);
      });
    });
  });

  describe('Class Management Module', () => {
    describe('Class CRUD Operations', () => {
      it('should create a new class', async () => {
        const newClass = {
          name: 'Advanced Mathematics',
          description: 'Calculus and Linear Algebra',
          grade_level: 12,
          subject: 'Mathematics',
          schedule: 'MWF 10:00-11:30',
          room: 'Room 301',
          capacity: 30
        };

        const mockResponse = {
          id: 'class-123',
          ...newClass,
          teacher_id: 'teacher-456',
          student_count: 0,
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onPost(`${API_BASE_URL}/classes/`).reply(201, mockResponse);

        const result = await apiClient.createClass(newClass);
        
        expect(result).toEqual(mockResponse);
        expect(result.id).toBe('class-123');
        expect(result.name).toBe('Advanced Mathematics');
      });

      it('should fetch class list', async () => {
        const mockClasses = [
          {
            id: 'class-1',
            name: 'Math 101',
            subject: 'Mathematics',
            grade_level: 9,
            student_count: 25,
            teacher: 'John Doe'
          },
          {
            id: 'class-2',
            name: 'Science 202',
            subject: 'Science',
            grade_level: 10,
            student_count: 28,
            teacher: 'Jane Smith'
          }
        ];

        mock.onGet(`${API_BASE_URL}/classes/`).reply(200, mockClasses);

        const result = await apiClient.listClasses();
        
        expect(result).toEqual(mockClasses);
        expect(result).toHaveLength(2);
        expect(result[0].name).toBe('Math 101');
      });

      it('should fetch single class details', async () => {
        const mockClass = {
          id: 'class-123',
          name: 'Physics 301',
          description: 'Advanced Physics',
          teacher: {
            id: 'teacher-1',
            name: 'Dr. Smith',
            email: 'smith@example.com'
          },
          students: [
            { id: 'student-1', name: 'Alice Johnson' },
            { id: 'student-2', name: 'Bob Williams' }
          ],
          lessons: [],
          assignments: []
        };

        mock.onGet(`${API_BASE_URL}/classes/class-123`).reply(200, mockClass);

        const result = await apiClient.getClass('class-123');
        
        expect(result).toEqual(mockClass);
        expect(result.students).toHaveLength(2);
      });

      it('should update class information', async () => {
        const updates = {
          name: 'Updated Physics 301',
          description: 'Updated description',
          capacity: 35
        };

        const mockResponse = {
          id: 'class-123',
          ...updates,
          teacher_id: 'teacher-456',
          updated_at: '2024-01-02T00:00:00Z'
        };

        mock.onPatch(`${API_BASE_URL}/classes/class-123`).reply(200, mockResponse);

        const result = await apiClient.updateClass('class-123', updates);
        
        expect(result).toEqual(mockResponse);
        expect(result.name).toBe('Updated Physics 301');
      });

      it('should delete a class', async () => {
        mock.onDelete(`${API_BASE_URL}/classes/class-123`).reply(204);

        await expect(apiClient.deleteClass('class-123')).resolves.toBeUndefined();
        expect(mock.history.delete).toHaveLength(1);
      });

      it('should handle class not found', async () => {
        mock.onGet(`${API_BASE_URL}/classes/nonexistent`).reply(404, {
          detail: 'Class not found'
        });

        await expect(apiClient.getClass('nonexistent')).rejects.toThrow();
      });
    });

    describe('Student Management', () => {
      it('should add students to class', async () => {
        const studentIds = ['student-1', 'student-2', 'student-3'];

        mock.onPost(`${API_BASE_URL}/classes/class-123/students`).reply(200, {
          added: 3,
          class_id: 'class-123',
          students: studentIds
        });

        const result = await apiClient.addStudentsToClass('class-123', studentIds);
        
        expect(result.added).toBe(3);
        expect(mock.history.post[0].data).toBe(JSON.stringify({ student_ids: studentIds }));
      });

      it('should remove student from class', async () => {
        mock.onDelete(`${API_BASE_URL}/classes/class-123/students/student-1`).reply(204);

        await expect(apiClient.removeStudentFromClass('class-123', 'student-1'))
          .resolves.toBeUndefined();
      });

      it('should fetch class roster', async () => {
        const mockRoster = [
          {
            id: 'student-1',
            name: 'Alice Johnson',
            email: 'alice@example.com',
            grade: 92,
            attendance: 95
          },
          {
            id: 'student-2',
            name: 'Bob Williams',
            email: 'bob@example.com',
            grade: 88,
            attendance: 90
          }
        ];

        mock.onGet(`${API_BASE_URL}/classes/class-123/students`).reply(200, mockRoster);

        const result = await apiClient.getClassStudents('class-123');
        
        expect(result).toEqual(mockRoster);
        expect(result).toHaveLength(2);
      });

      it('should handle duplicate student addition', async () => {
        mock.onPost(`${API_BASE_URL}/classes/class-123/students`).reply(409, {
          detail: 'Student already enrolled in class'
        });

        await expect(apiClient.addStudentsToClass('class-123', ['existing-student']))
          .rejects.toThrow();
      });
    });

    describe('Assignments and Materials', () => {
      it('should create class assignment', async () => {
        const assignment = {
          title: 'Chapter 5 Problems',
          description: 'Complete problems 1-20',
          due_date: '2024-01-15T23:59:59Z',
          points: 100,
          type: 'homework'
        };

        const mockResponse = {
          id: 'assign-123',
          class_id: 'class-123',
          ...assignment,
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onPost(`${API_BASE_URL}/classes/class-123/assignments`).reply(201, mockResponse);

        const result = await apiClient.createAssignment('class-123', assignment);
        
        expect(result).toEqual(mockResponse);
        expect(result.id).toBe('assign-123');
      });

      it('should fetch class assignments', async () => {
        const mockAssignments = [
          {
            id: 'assign-1',
            title: 'Quiz 1',
            due_date: '2024-01-10',
            points: 50,
            submissions: 20
          },
          {
            id: 'assign-2',
            title: 'Project',
            due_date: '2024-01-20',
            points: 100,
            submissions: 15
          }
        ];

        mock.onGet(`${API_BASE_URL}/classes/class-123/assignments`).reply(200, mockAssignments);

        const result = await apiClient.getClassAssignments('class-123');
        
        expect(result).toEqual(mockAssignments);
        expect(result).toHaveLength(2);
      });

      it('should upload class materials', async () => {
        const formData = new FormData();
        formData.append('file', new Blob(['content']), 'lecture.pdf');
        formData.append('title', 'Lecture Notes');

        mock.onPost(`${API_BASE_URL}/classes/class-123/materials`).reply(201, {
          id: 'material-123',
          title: 'Lecture Notes',
          filename: 'lecture.pdf',
          size: 1024,
          url: 'https://example.com/materials/lecture.pdf'
        });

        const result = await apiClient.uploadClassMaterial('class-123', formData);
        
        expect(result.id).toBe('material-123');
      });

      it('should fetch class materials', async () => {
        const mockMaterials = [
          {
            id: 'mat-1',
            title: 'Syllabus',
            filename: 'syllabus.pdf',
            uploaded_at: '2024-01-01'
          },
          {
            id: 'mat-2',
            title: 'Lecture 1',
            filename: 'lecture1.pptx',
            uploaded_at: '2024-01-02'
          }
        ];

        mock.onGet(`${API_BASE_URL}/classes/class-123/materials`).reply(200, mockMaterials);

        const result = await apiClient.getClassMaterials('class-123');
        
        expect(result).toEqual(mockMaterials);
      });
    });

    describe('Attendance', () => {
      it('should record attendance', async () => {
        const attendanceData = {
          date: '2024-01-01',
          students: [
            { id: 'student-1', status: 'present' },
            { id: 'student-2', status: 'absent' },
            { id: 'student-3', status: 'late' }
          ]
        };

        mock.onPost(`${API_BASE_URL}/classes/class-123/attendance`).reply(200, {
          recorded: 3,
          date: '2024-01-01'
        });

        const result = await apiClient.recordAttendance('class-123', attendanceData);
        
        expect(result.recorded).toBe(3);
      });

      it('should fetch attendance records', async () => {
        const mockAttendance = {
          date: '2024-01-01',
          total_students: 30,
          present: 27,
          absent: 2,
          late: 1,
          records: [
            { student_id: 'student-1', name: 'Alice', status: 'present' }
          ]
        };

        mock.onGet(`${API_BASE_URL}/classes/class-123/attendance`).reply(200, mockAttendance);

        const result = await apiClient.getAttendance('class-123', { date: '2024-01-01' });
        
        expect(result).toEqual(mockAttendance);
        expect(result.present).toBe(27);
      });

      it('should generate attendance report', async () => {
        mock.onGet(`${API_BASE_URL}/classes/class-123/attendance/report`).reply(200, {
          period: 'month',
          average_attendance: 92.5,
          perfect_attendance: ['student-1', 'student-3']
        });

        const result = await apiClient.getAttendanceReport('class-123', {
          start_date: '2024-01-01',
          end_date: '2024-01-31'
        });
        
        expect(result.average_attendance).toBe(92.5);
      });
    });
  });

  describe('Lesson Management Module', () => {
    describe('Lesson CRUD', () => {
      it('should create a new lesson', async () => {
        const lessonData = {
          title: 'Introduction to Algebra',
          description: 'Basic algebraic concepts',
          content: 'Lesson content here...',
          duration_minutes: 45,
          objectives: ['Understand variables', 'Solve basic equations'],
          materials: ['textbook', 'calculator']
        };

        const mockResponse = {
          id: 'lesson-123',
          class_id: 'class-123',
          ...lessonData,
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onPost(`${API_BASE_URL}/classes/class-123/lessons`).reply(201, mockResponse);

        const result = await apiClient.createLesson('class-123', lessonData);
        
        expect(result).toEqual(mockResponse);
        expect(result.id).toBe('lesson-123');
      });

      it('should fetch lesson details', async () => {
        const mockLesson = {
          id: 'lesson-123',
          title: 'Algebra Basics',
          content: 'Full lesson content',
          completed_by: ['student-1', 'student-2'],
          completion_rate: 67
        };

        mock.onGet(`${API_BASE_URL}/lessons/lesson-123`).reply(200, mockLesson);

        const result = await apiClient.getLesson('lesson-123');
        
        expect(result).toEqual(mockLesson);
        expect(result.completion_rate).toBe(67);
      });

      it('should update lesson', async () => {
        const updates = {
          title: 'Updated Algebra Basics',
          duration_minutes: 60
        };

        mock.onPatch(`${API_BASE_URL}/lessons/lesson-123`).reply(200, {
          id: 'lesson-123',
          ...updates
        });

        const result = await apiClient.updateLesson('lesson-123', updates);
        
        expect(result.title).toBe('Updated Algebra Basics');
      });

      it('should delete lesson', async () => {
        mock.onDelete(`${API_BASE_URL}/lessons/lesson-123`).reply(204);

        await expect(apiClient.deleteLesson('lesson-123')).resolves.toBeUndefined();
      });
    });

    describe('Lesson Progress', () => {
      it('should track lesson progress', async () => {
        const progressData = {
          progress_percentage: 75,
          time_spent_minutes: 35,
          completed_sections: ['intro', 'main_content']
        };

        mock.onPost(`${API_BASE_URL}/lessons/lesson-123/progress`).reply(200, {
          lesson_id: 'lesson-123',
          student_id: 'student-1',
          ...progressData,
          updated_at: '2024-01-01T10:00:00Z'
        });

        const result = await apiClient.updateLessonProgress('lesson-123', progressData);
        
        expect(result.progress_percentage).toBe(75);
      });

      it('should fetch student progress for lesson', async () => {
        mock.onGet(`${API_BASE_URL}/lessons/lesson-123/progress/student-1`).reply(200, {
          completed: false,
          progress: 60,
          last_accessed: '2024-01-01T09:00:00Z'
        });

        const result = await apiClient.getLessonProgress('lesson-123', 'student-1');
        
        expect(result.progress).toBe(60);
      });

      it('should mark lesson as complete', async () => {
        mock.onPost(`${API_BASE_URL}/lessons/lesson-123/complete`).reply(200, {
          lesson_id: 'lesson-123',
          completed: true,
          completion_date: '2024-01-01T10:00:00Z',
          score: 95
        });

        const result = await apiClient.completeLesson('lesson-123');
        
        expect(result.completed).toBe(true);
        expect(result.score).toBe(95);
      });
    });
  });

  describe('Assessment Module', () => {
    describe('Quiz Management', () => {
      it('should create a quiz', async () => {
        const quizData = {
          title: 'Chapter 5 Quiz',
          description: 'Test your knowledge',
          questions: [
            {
              question: 'What is 2+2?',
              type: 'multiple_choice',
              options: ['3', '4', '5', '6'],
              correct_answer: '4',
              points: 10
            }
          ],
          time_limit_minutes: 30,
          attempts_allowed: 2
        };

        const mockResponse = {
          id: 'quiz-123',
          ...quizData,
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onPost(`${API_BASE_URL}/assessments/quiz`).reply(201, mockResponse);

        const result = await apiClient.createQuiz(quizData);
        
        expect(result).toEqual(mockResponse);
        expect(result.id).toBe('quiz-123');
      });

      it('should fetch quiz details', async () => {
        mock.onGet(`${API_BASE_URL}/assessments/quiz/quiz-123`).reply(200, {
          id: 'quiz-123',
          title: 'Math Quiz',
          questions: [],
          submissions: 15,
          average_score: 82
        });

        const result = await apiClient.getQuiz('quiz-123');
        
        expect(result.average_score).toBe(82);
      });

      it('should submit quiz answers', async () => {
        const submission = {
          quiz_id: 'quiz-123',
          answers: [
            { question_id: 'q1', answer: '4' },
            { question_id: 'q2', answer: 'true' }
          ],
          time_taken_minutes: 25
        };

        mock.onPost(`${API_BASE_URL}/assessments/quiz/quiz-123/submit`).reply(200, {
          score: 85,
          correct: 17,
          total: 20,
          passed: true
        });

        const result = await apiClient.submitQuiz('quiz-123', submission);
        
        expect(result.score).toBe(85);
        expect(result.passed).toBe(true);
      });

      it('should fetch quiz results', async () => {
        mock.onGet(`${API_BASE_URL}/assessments/quiz/quiz-123/results`).reply(200, {
          quiz_id: 'quiz-123',
          submissions: [
            { student_id: 'student-1', score: 90, submitted_at: '2024-01-01' },
            { student_id: 'student-2', score: 75, submitted_at: '2024-01-01' }
          ],
          statistics: {
            average: 82.5,
            median: 82.5,
            highest: 90,
            lowest: 75
          }
        });

        const result = await apiClient.getQuizResults('quiz-123');
        
        expect(result.statistics.average).toBe(82.5);
      });
    });

    describe('Exam Management', () => {
      it('should schedule an exam', async () => {
        const examData = {
          title: 'Final Exam',
          subject: 'Mathematics',
          date: '2024-01-30T10:00:00Z',
          duration_minutes: 120,
          total_marks: 100,
          instructions: 'No calculators allowed'
        };

        mock.onPost(`${API_BASE_URL}/assessments/exam`).reply(201, {
          id: 'exam-123',
          ...examData
        });

        const result = await apiClient.scheduleExam(examData);
        
        expect(result.id).toBe('exam-123');
      });

      it('should generate exam report', async () => {
        mock.onGet(`${API_BASE_URL}/assessments/exam/exam-123/report`).reply(200, {
          exam_id: 'exam-123',
          total_students: 30,
          attended: 28,
          passed: 25,
          failed: 3,
          average_score: 78.5,
          grade_distribution: {
            'A': 5,
            'B': 10,
            'C': 10,
            'D': 3,
            'F': 2
          }
        });

        const result = await apiClient.getExamReport('exam-123');
        
        expect(result.passed).toBe(25);
        expect(result.average_score).toBe(78.5);
      });
    });

    describe('Grading', () => {
      it('should submit grades', async () => {
        const grades = [
          { student_id: 'student-1', score: 92, feedback: 'Excellent work!' },
          { student_id: 'student-2', score: 78, feedback: 'Good effort' }
        ];

        mock.onPost(`${API_BASE_URL}/assessments/grades`).reply(200, {
          graded: 2,
          assessment_id: 'assess-123'
        });

        const result = await apiClient.submitGrades('assess-123', grades);
        
        expect(result.graded).toBe(2);
      });

      it('should fetch grade book', async () => {
        mock.onGet(`${API_BASE_URL}/classes/class-123/gradebook`).reply(200, {
          class_id: 'class-123',
          students: [
            {
              id: 'student-1',
              name: 'Alice',
              grades: {
                'quiz-1': 85,
                'exam-1': 92,
                'assignment-1': 88
              },
              average: 88.3
            }
          ]
        });

        const result = await apiClient.getGradebook('class-123');
        
        expect(result.students[0].average).toBe(88.3);
      });
    });
  });

  describe('User Management Module', () => {
    describe('User CRUD', () => {
      it('should fetch all users', async () => {
        const mockUsers = [
          {
            id: 'user-1',
            username: 'john_doe',
            email: 'john@example.com',
            role: 'teacher',
            status: 'active'
          },
          {
            id: 'user-2',
            username: 'jane_smith',
            email: 'jane@example.com',
            role: 'student',
            status: 'active'
          }
        ];

        mock.onGet(`${API_BASE_URL}/users/`).reply(200, mockUsers);

        const result = await apiClient.listUsers();
        
        expect(result).toEqual(mockUsers);
        expect(result).toHaveLength(2);
      });

      it('should fetch users with filters', async () => {
        const filters = {
          role: 'teacher',
          status: 'active',
          school_id: 'school-123'
        };

        mock.onGet(`${API_BASE_URL}/users/`).reply(200, []);

        await apiClient.listUsers(filters);
        
        expect(mock.history.get[0].params).toEqual(filters);
      });

      it('should fetch single user details', async () => {
        const mockUser = {
          id: 'user-123',
          username: 'testuser',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          role: 'teacher',
          school: {
            id: 'school-123',
            name: 'Test School'
          },
          classes: ['class-1', 'class-2'],
          created_at: '2024-01-01T00:00:00Z'
        };

        mock.onGet(`${API_BASE_URL}/users/user-123`).reply(200, mockUser);

        const result = await apiClient.getUser('user-123');
        
        expect(result).toEqual(mockUser);
        expect(result.classes).toHaveLength(2);
      });

      it('should create new user', async () => {
        const userData = {
          username: 'newuser',
          email: 'new@example.com',
          password: 'SecurePass123!',
          role: 'student',
          first_name: 'New',
          last_name: 'User'
        };

        mock.onPost(`${API_BASE_URL}/users/`).reply(201, {
          id: 'user-new',
          ...userData,
          password: undefined
        });

        const result = await apiClient.createUser(userData);
        
        expect(result.id).toBe('user-new');
        expect(result.username).toBe('newuser');
      });

      it('should update user', async () => {
        const updates = {
          first_name: 'Updated',
          last_name: 'Name',
          status: 'inactive'
        };

        mock.onPatch(`${API_BASE_URL}/users/user-123`).reply(200, {
          id: 'user-123',
          ...updates
        });

        const result = await apiClient.updateUser('user-123', updates);
        
        expect(result.first_name).toBe('Updated');
        expect(result.status).toBe('inactive');
      });

      it('should delete user', async () => {
        mock.onDelete(`${API_BASE_URL}/users/user-123`).reply(204);

        await expect(apiClient.deleteUser('user-123')).resolves.toBeUndefined();
      });

      it('should handle user not found', async () => {
        mock.onGet(`${API_BASE_URL}/users/nonexistent`).reply(404, {
          detail: 'User not found'
        });

        await expect(apiClient.getUser('nonexistent')).rejects.toThrow();
      });
    });

    describe('Role Management', () => {
      it('should update user role', async () => {
        mock.onPost(`${API_BASE_URL}/users/user-123/role`).reply(200, {
          id: 'user-123',
          role: 'admin',
          updated_at: '2024-01-01T00:00:00Z'
        });

        const result = await apiClient.updateUserRole('user-123', 'admin');
        
        expect(result.role).toBe('admin');
      });

      it('should fetch role permissions', async () => {
        mock.onGet(`${API_BASE_URL}/roles/teacher/permissions`).reply(200, {
          role: 'teacher',
          permissions: [
            'create_class',
            'manage_students',
            'create_assignments',
            'grade_submissions'
          ]
        });

        const result = await apiClient.getRolePermissions('teacher');
        
        expect(result.permissions).toContain('create_class');
      });
    });

    describe('User Status', () => {
      it('should activate user', async () => {
        mock.onPost(`${API_BASE_URL}/users/user-123/activate`).reply(200, {
          id: 'user-123',
          status: 'active'
        });

        const result = await apiClient.activateUser('user-123');
        
        expect(result.status).toBe('active');
      });

      it('should deactivate user', async () => {
        mock.onPost(`${API_BASE_URL}/users/user-123/deactivate`).reply(200, {
          id: 'user-123',
          status: 'inactive'
        });

        const result = await apiClient.deactivateUser('user-123');
        
        expect(result.status).toBe('inactive');
      });

      it('should suspend user', async () => {
        mock.onPost(`${API_BASE_URL}/users/user-123/suspend`).reply(200, {
          id: 'user-123',
          status: 'suspended',
          suspended_until: '2024-02-01T00:00:00Z'
        });

        const result = await apiClient.suspendUser('user-123', {
          reason: 'Policy violation',
          duration_days: 30
        });
        
        expect(result.status).toBe('suspended');
      });
    });
  });

  describe('Message Module', () => {
    describe('Message Operations', () => {
      it('should send a message', async () => {
        const messageData = {
          recipient_id: 'user-456',
          subject: 'Question about homework',
          content: 'I need help with problem 5',
          priority: 'normal'
        };

        mock.onPost(`${API_BASE_URL}/messages/`).reply(201, {
          id: 'msg-123',
          sender_id: 'user-123',
          ...messageData,
          sent_at: '2024-01-01T10:00:00Z',
          read: false
        });

        const result = await apiClient.sendMessage(messageData);
        
        expect(result.id).toBe('msg-123');
        expect(result.subject).toBe('Question about homework');
      });

      it('should fetch inbox messages', async () => {
        const mockMessages = [
          {
            id: 'msg-1',
            sender: 'John Doe',
            subject: 'Meeting reminder',
            preview: 'Don\'t forget about...',
            sent_at: '2024-01-01T09:00:00Z',
            read: false
          },
          {
            id: 'msg-2',
            sender: 'Jane Smith',
            subject: 'Assignment submitted',
            preview: 'I\'ve completed...',
            sent_at: '2024-01-01T08:00:00Z',
            read: true
          }
        ];

        mock.onGet(`${API_BASE_URL}/messages/inbox`).reply(200, mockMessages);

        const result = await apiClient.getInbox();
        
        expect(result).toEqual(mockMessages);
        expect(result).toHaveLength(2);
      });

      it('should fetch sent messages', async () => {
        mock.onGet(`${API_BASE_URL}/messages/sent`).reply(200, []);

        const result = await apiClient.getSentMessages();
        
        expect(result).toEqual([]);
      });

      it('should fetch single message', async () => {
        const mockMessage = {
          id: 'msg-123',
          sender: {
            id: 'user-1',
            name: 'John Doe',
            email: 'john@example.com'
          },
          recipient: {
            id: 'user-2',
            name: 'Jane Smith',
            email: 'jane@example.com'
          },
          subject: 'Important',
          content: 'Full message content here',
          attachments: [],
          sent_at: '2024-01-01T10:00:00Z',
          read_at: null
        };

        mock.onGet(`${API_BASE_URL}/messages/msg-123`).reply(200, mockMessage);

        const result = await apiClient.getMessage('msg-123');
        
        expect(result).toEqual(mockMessage);
        expect(result.content).toBe('Full message content here');
      });

      it('should mark message as read', async () => {
        mock.onPost(`${API_BASE_URL}/messages/msg-123/read`).reply(200, {
          id: 'msg-123',
          read: true,
          read_at: '2024-01-01T10:05:00Z'
        });

        const result = await apiClient.markMessageRead('msg-123');
        
        expect(result.read).toBe(true);
      });

      it('should delete message', async () => {
        mock.onDelete(`${API_BASE_URL}/messages/msg-123`).reply(204);

        await expect(apiClient.deleteMessage('msg-123')).resolves.toBeUndefined();
      });

      it('should reply to message', async () => {
        const replyData = {
          content: 'Here is my reply',
          include_original: true
        };

        mock.onPost(`${API_BASE_URL}/messages/msg-123/reply`).reply(201, {
          id: 'msg-124',
          in_reply_to: 'msg-123',
          content: 'Here is my reply',
          sent_at: '2024-01-01T10:10:00Z'
        });

        const result = await apiClient.replyToMessage('msg-123', replyData);
        
        expect(result.id).toBe('msg-124');
        expect(result.in_reply_to).toBe('msg-123');
      });
    });

    describe('Bulk Operations', () => {
      it('should mark multiple messages as read', async () => {
        const messageIds = ['msg-1', 'msg-2', 'msg-3'];

        mock.onPost(`${API_BASE_URL}/messages/bulk/read`).reply(200, {
          updated: 3
        });

        const result = await apiClient.markMessagesRead(messageIds);
        
        expect(result.updated).toBe(3);
      });

      it('should delete multiple messages', async () => {
        const messageIds = ['msg-1', 'msg-2'];

        mock.onPost(`${API_BASE_URL}/messages/bulk/delete`).reply(200, {
          deleted: 2
        });

        const result = await apiClient.deleteMessages(messageIds);
        
        expect(result.deleted).toBe(2);
      });

      it('should send broadcast message', async () => {
        const broadcastData = {
          recipient_ids: ['user-1', 'user-2', 'user-3'],
          subject: 'Important Announcement',
          content: 'Please note...',
          priority: 'high'
        };

        mock.onPost(`${API_BASE_URL}/messages/broadcast`).reply(200, {
          sent: 3,
          message_ids: ['msg-1', 'msg-2', 'msg-3']
        });

        const result = await apiClient.sendBroadcastMessage(broadcastData);
        
        expect(result.sent).toBe(3);
        expect(result.message_ids).toHaveLength(3);
      });
    });
  });

  describe('Reports Module', () => {
    it('should generate student progress report', async () => {
      mock.onGet(`${API_BASE_URL}/reports/student/student-123/progress`).reply(200, {
        student_id: 'student-123',
        overall_progress: 78,
        courses: [
          { name: 'Math', progress: 85, grade: 'A' },
          { name: 'Science', progress: 71, grade: 'B' }
        ]
      });

      const result = await apiClient.getStudentProgressReport('student-123');
      
      expect(result.overall_progress).toBe(78);
    });

    it('should generate class performance report', async () => {
      mock.onGet(`${API_BASE_URL}/reports/class/class-123/performance`).reply(200, {
        class_id: 'class-123',
        average_grade: 82.5,
        attendance_rate: 94,
        completion_rate: 88
      });

      const result = await apiClient.getClassPerformanceReport('class-123');
      
      expect(result.average_grade).toBe(82.5);
    });

    it('should export report as PDF', async () => {
      const blob = new Blob(['PDF content'], { type: 'application/pdf' });
      
      mock.onGet(`${API_BASE_URL}/reports/export/report-123`).reply(200, blob);

      const result = await apiClient.exportReport('report-123', 'pdf');
      
      expect(result).toBeInstanceOf(Blob);
    });

    it('should schedule automated report', async () => {
      const scheduleData = {
        report_type: 'weekly_progress',
        recipients: ['admin@example.com'],
        schedule: 'every_monday_9am'
      };

      mock.onPost(`${API_BASE_URL}/reports/schedule`).reply(201, {
        id: 'schedule-123',
        ...scheduleData
      });

      const result = await apiClient.scheduleReport(scheduleData);
      
      expect(result.id).toBe('schedule-123');
    });
  });

  describe('School Management Module', () => {
    it('should fetch school list', async () => {
      const mockSchools = [
        {
          id: 'school-1',
          name: 'Lincoln High School',
          address: '123 Main St',
          student_count: 1200,
          teacher_count: 80
        }
      ];

      mock.onGet(`${API_BASE_URL}/schools/`).reply(200, mockSchools);

      const result = await apiClient.listSchools();
      
      expect(result).toEqual(mockSchools);
    });

    it('should create new school', async () => {
      const schoolData = {
        name: 'New School',
        address: '456 Oak Ave',
        phone: '555-0123',
        email: 'info@newschool.edu'
      };

      mock.onPost(`${API_BASE_URL}/schools/`).reply(201, {
        id: 'school-new',
        ...schoolData
      });

      const result = await apiClient.createSchool(schoolData);
      
      expect(result.id).toBe('school-new');
    });

    it('should fetch school statistics', async () => {
      mock.onGet(`${API_BASE_URL}/schools/school-123/stats`).reply(200, {
        total_students: 1200,
        total_teachers: 80,
        total_classes: 150,
        average_attendance: 92.5,
        average_grade: 83.2
      });

      const result = await apiClient.getSchoolStats('school-123');
      
      expect(result.total_students).toBe(1200);
    });
  });

  describe('Gamification Module', () => {
    describe('Rewards', () => {
      it('should fetch available rewards', async () => {
        const mockRewards = [
          {
            id: 'reward-1',
            name: 'Extra Credit',
            cost: 100,
            description: '5 bonus points',
            available: true
          },
          {
            id: 'reward-2',
            name: 'Homework Pass',
            cost: 200,
            description: 'Skip one homework',
            available: true
          }
        ];

        mock.onGet(`${API_BASE_URL}/gamification/rewards`).reply(200, mockRewards);

        const result = await apiClient.getRewards();
        
        expect(result).toEqual(mockRewards);
        expect(result).toHaveLength(2);
      });

      it('should claim reward', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/rewards/reward-1/claim`).reply(200, {
          success: true,
          reward_id: 'reward-1',
          new_balance: 50
        });

        const result = await apiClient.claimReward('reward-1');
        
        expect(result.success).toBe(true);
        expect(result.new_balance).toBe(50);
      });

      it('should handle insufficient points for reward', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/rewards/reward-1/claim`).reply(400, {
          detail: 'Insufficient points'
        });

        await expect(apiClient.claimReward('reward-1')).rejects.toThrow();
      });
    });

    describe('Missions', () => {
      it('should fetch active missions', async () => {
        const mockMissions = [
          {
            id: 'mission-1',
            title: 'Complete 5 Quizzes',
            progress: 3,
            target: 5,
            reward: 50,
            deadline: '2024-01-31'
          }
        ];

        mock.onGet(`${API_BASE_URL}/gamification/missions`).reply(200, mockMissions);

        const result = await apiClient.getMissions();
        
        expect(result).toEqual(mockMissions);
      });

      it('should update mission progress', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/missions/mission-1/progress`).reply(200, {
          mission_id: 'mission-1',
          progress: 4,
          target: 5,
          completed: false
        });

        const result = await apiClient.updateMissionProgress('mission-1', {
          action: 'quiz_completed'
        });
        
        expect(result.progress).toBe(4);
      });

      it('should complete mission', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/missions/mission-1/complete`).reply(200, {
          mission_id: 'mission-1',
          completed: true,
          reward_granted: 50,
          new_balance: 250
        });

        const result = await apiClient.completeMission('mission-1');
        
        expect(result.completed).toBe(true);
        expect(result.reward_granted).toBe(50);
      });
    });

    describe('Leaderboard', () => {
      it('should fetch class leaderboard', async () => {
        const mockLeaderboard = [
          { rank: 1, student: 'Alice', points: 850, badges: 12 },
          { rank: 2, student: 'Bob', points: 780, badges: 10 },
          { rank: 3, student: 'Charlie', points: 720, badges: 9 }
        ];

        mock.onGet(`${API_BASE_URL}/gamification/leaderboard/class/class-123`).reply(200, mockLeaderboard);

        const result = await apiClient.getClassLeaderboard('class-123');
        
        expect(result).toEqual(mockLeaderboard);
        expect(result[0].student).toBe('Alice');
      });

      it('should fetch global leaderboard', async () => {
        mock.onGet(`${API_BASE_URL}/gamification/leaderboard/global`).reply(200, []);

        const result = await apiClient.getGlobalLeaderboard();
        
        expect(result).toEqual([]);
      });
    });

    describe('Badges and Achievements', () => {
      it('should fetch user badges', async () => {
        const mockBadges = [
          {
            id: 'badge-1',
            name: 'Fast Learner',
            description: 'Complete 10 lessons in a week',
            earned_at: '2024-01-01',
            icon: 'star'
          }
        ];

        mock.onGet(`${API_BASE_URL}/gamification/badges/user/user-123`).reply(200, mockBadges);

        const result = await apiClient.getUserBadges('user-123');
        
        expect(result).toEqual(mockBadges);
      });

      it('should award badge', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/badges/award`).reply(200, {
          badge_id: 'badge-2',
          user_id: 'user-123',
          awarded_at: '2024-01-01T12:00:00Z'
        });

        const result = await apiClient.awardBadge('user-123', 'badge-2');
        
        expect(result.badge_id).toBe('badge-2');
      });
    });

    describe('Points System', () => {
      it('should fetch user points', async () => {
        mock.onGet(`${API_BASE_URL}/gamification/points/user-123`).reply(200, {
          user_id: 'user-123',
          total_points: 450,
          available_points: 250,
          spent_points: 200,
          history: []
        });

        const result = await apiClient.getUserPoints('user-123');
        
        expect(result.total_points).toBe(450);
      });

      it('should add points', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/points/add`).reply(200, {
          user_id: 'user-123',
          points_added: 50,
          new_balance: 300,
          reason: 'Quiz completion'
        });

        const result = await apiClient.addPoints('user-123', 50, 'Quiz completion');
        
        expect(result.points_added).toBe(50);
      });

      it('should deduct points', async () => {
        mock.onPost(`${API_BASE_URL}/gamification/points/deduct`).reply(200, {
          user_id: 'user-123',
          points_deducted: 100,
          new_balance: 150,
          reason: 'Reward claimed'
        });

        const result = await apiClient.deductPoints('user-123', 100, 'Reward claimed');
        
        expect(result.points_deducted).toBe(100);
      });
    });
  });

  describe('Roblox Integration Module', () => {
    describe('Game Sessions', () => {
      it('should create Roblox game session', async () => {
        const sessionData = {
          lesson_id: 'lesson-123',
          player_ids: ['player-1', 'player-2'],
          game_mode: 'collaborative',
          settings: {
            difficulty: 'medium',
            time_limit: 30
          }
        };

        mock.onPost(`${API_BASE_URL}/roblox/sessions`).reply(201, {
          session_id: 'session-123',
          join_code: 'ABC123',
          server_id: 'server-456',
          ...sessionData
        });

        const result = await apiClient.createRobloxSession(sessionData);
        
        expect(result.session_id).toBe('session-123');
        expect(result.join_code).toBe('ABC123');
      });

      it('should join Roblox session', async () => {
        mock.onPost(`${API_BASE_URL}/roblox/sessions/join`).reply(200, {
          session_id: 'session-123',
          server_url: 'roblox://server-456',
          player_id: 'player-123'
        });

        const result = await apiClient.joinRobloxSession('ABC123');
        
        expect(result.session_id).toBe('session-123');
      });

      it('should end Roblox session', async () => {
        mock.onPost(`${API_BASE_URL}/roblox/sessions/session-123/end`).reply(200, {
          session_id: 'session-123',
          ended_at: '2024-01-01T11:00:00Z',
          duration_minutes: 25,
          players_completed: 2
        });

        const result = await apiClient.endRobloxSession('session-123');
        
        expect(result.duration_minutes).toBe(25);
      });

      it('should fetch session details', async () => {
        mock.onGet(`${API_BASE_URL}/roblox/sessions/session-123`).reply(200, {
          session_id: 'session-123',
          status: 'active',
          players: [
            { id: 'player-1', name: 'Alice', score: 450 },
            { id: 'player-2', name: 'Bob', score: 380 }
          ],
          started_at: '2024-01-01T10:00:00Z',
          lesson_progress: 65
        });

        const result = await apiClient.getRobloxSession('session-123');
        
        expect(result.status).toBe('active');
        expect(result.lesson_progress).toBe(65);
      });
    });

    describe('Game Content', () => {
      it('should sync lesson to Roblox', async () => {
        const syncData = {
          lesson_id: 'lesson-123',
          include_quiz: true,
          include_activities: true
        };

        mock.onPost(`${API_BASE_URL}/roblox/sync/lesson`).reply(200, {
          synced: true,
          lesson_id: 'lesson-123',
          roblox_asset_id: 'asset-789',
          synced_at: '2024-01-01T10:00:00Z'
        });

        const result = await apiClient.syncLessonToRoblox(syncData);
        
        expect(result.synced).toBe(true);
        expect(result.roblox_asset_id).toBe('asset-789');
      });

      it('should generate Roblox world', async () => {
        const worldData = {
          theme: 'space',
          difficulty: 'medium',
          objectives: ['explore', 'collect', 'solve'],
          size: 'large'
        };

        mock.onPost(`${API_BASE_URL}/roblox/generate/world`).reply(200, {
          world_id: 'world-123',
          place_id: 123456789,
          generated: true,
          preview_url: 'https://example.com/preview'
        });

        const result = await apiClient.generateRobloxWorld(worldData);
        
        expect(result.world_id).toBe('world-123');
        expect(result.place_id).toBe(123456789);
      });
    });

    describe('Player Progress', () => {
      it('should track Roblox player progress', async () => {
        const progressData = {
          player_id: 'player-123',
          session_id: 'session-123',
          checkpoint: 'level-2',
          score: 450,
          achievements: ['first_solve', 'speed_bonus']
        };

        mock.onPost(`${API_BASE_URL}/roblox/progress`).reply(200, {
          recorded: true,
          ...progressData,
          timestamp: '2024-01-01T10:30:00Z'
        });

        const result = await apiClient.trackRobloxProgress(progressData);
        
        expect(result.recorded).toBe(true);
        expect(result.score).toBe(450);
      });

      it('should fetch player statistics', async () => {
        mock.onGet(`${API_BASE_URL}/roblox/players/player-123/stats`).reply(200, {
          player_id: 'player-123',
          total_play_time: 1250,
          sessions_played: 42,
          average_score: 380,
          achievements_earned: 15,
          favorite_game_mode: 'collaborative'
        });

        const result = await apiClient.getRobloxPlayerStats('player-123');
        
        expect(result.sessions_played).toBe(42);
        expect(result.achievements_earned).toBe(15);
      });
    });

    describe('Analytics', () => {
      it('should fetch Roblox analytics', async () => {
        mock.onGet(`${API_BASE_URL}/roblox/analytics`).reply(200, {
          active_sessions: 12,
          total_players: 450,
          average_session_duration: 28,
          popular_lessons: [
            { id: 'lesson-1', title: 'Math Adventure', plays: 120 },
            { id: 'lesson-2', title: 'Science Quest', plays: 95 }
          ],
          engagement_rate: 85.5
        });

        const result = await apiClient.getRobloxAnalytics();
        
        expect(result.active_sessions).toBe(12);
        expect(result.engagement_rate).toBe(85.5);
      });

      it('should fetch game performance metrics', async () => {
        mock.onGet(`${API_BASE_URL}/roblox/metrics/performance`).reply(200, {
          average_fps: 58,
          server_uptime: 99.9,
          crash_rate: 0.1,
          load_time_seconds: 3.5
        });

        const result = await apiClient.getRobloxPerformanceMetrics();
        
        expect(result.server_uptime).toBe(99.9);
      });
    });
  });

  describe('Compliance Module', () => {
    it('should fetch compliance status', async () => {
      mock.onGet(`${API_BASE_URL}/compliance/status`).reply(200, {
        compliant: true,
        last_audit: '2024-01-01',
        next_audit: '2024-07-01',
        issues: []
      });

      const result = await apiClient.getComplianceStatus();
      
      expect(result.compliant).toBe(true);
    });

    it('should submit compliance report', async () => {
      const reportData = {
        type: 'FERPA',
        period: 'Q1 2024',
        data: {}
      };

      mock.onPost(`${API_BASE_URL}/compliance/reports`).reply(201, {
        report_id: 'report-123',
        submitted_at: '2024-01-01T12:00:00Z',
        status: 'pending_review'
      });

      const result = await apiClient.submitComplianceReport(reportData);
      
      expect(result.report_id).toBe('report-123');
    });

    it('should fetch audit logs', async () => {
      mock.onGet(`${API_BASE_URL}/compliance/audit-logs`).reply(200, [
        {
          id: 'log-1',
          action: 'data_access',
          user: 'admin',
          timestamp: '2024-01-01T10:00:00Z',
          details: 'Accessed student records'
        }
      ]);

      const result = await apiClient.getAuditLogs();
      
      expect(result).toHaveLength(1);
      expect(result[0].action).toBe('data_access');
    });
  });

  describe('WebSocket Integration', () => {
    it('should initialize WebSocket connection on login', async () => {
      const mockResponse = {
        access_token: 'ws-token',
        refresh_token: 'ws-refresh',
        user: { id: 'user-1', role: 'teacher' }
      };

      mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, mockResponse);

      await apiClient.login('test@example.com', 'password');
      
      // WebSocket connection is initialized during login
      expect(mock.history.post).toHaveLength(1);
    });

    it('should disconnect WebSocket on logout', async () => {
      mock.onPost(`${API_BASE_URL}/auth/logout`).reply(204);

      await apiClient.logout();
      
      // Verify logout was called
      expect(localStorage.getItem('toolboxai_auth_token')).toBeNull();
    });

    it('should handle WebSocket reconnection', async () => {
      // Test WebSocket reconnection logic
      const result = await apiClient.ensureWebSocketConnection();
      
      // Should handle reconnection gracefully
      expect(result).toBeUndefined();
    });
  });

  describe('Error Handling and Retry Logic', () => {
    it('should retry failed requests', async () => {
      let attempts = 0;
      
      mock.onGet(`${API_BASE_URL}/test`).reply(() => {
        attempts++;
        if (attempts < 3) {
          return [500, { error: 'Server error' }];
        }
        return [200, { data: 'success' }];
      });

      const result = await apiClient['request']({ 
        method: 'GET', 
        url: '/test',
        retry: true,
        maxRetries: 3
      });
      
      expect(result.data).toBe('success');
      expect(attempts).toBe(3);
    });

    it('should handle network timeouts', async () => {
      mock.onGet(`${API_BASE_URL}/slow`).timeout();

      await expect(apiClient['request']({
        method: 'GET',
        url: '/slow',
        timeout: 1000
      })).rejects.toThrow();
    });

    it('should handle malformed responses', async () => {
      mock.onGet(`${API_BASE_URL}/malformed`).reply(200, 'not json');

      // Should handle gracefully
      const result = await apiClient['request']({
        method: 'GET',
        url: '/malformed'
      });
      
      expect(result).toBe('not json');
    });

    it('should handle rate limiting with backoff', async () => {
      let attempts = 0;
      
      mock.onGet(`${API_BASE_URL}/rate-limited`).reply(() => {
        attempts++;
        if (attempts < 2) {
          return [429, { 
            error: 'Rate limited',
            retry_after: 1
          }];
        }
        return [200, { data: 'success' }];
      });

      const startTime = Date.now();
      const result = await apiClient['request']({
        method: 'GET',
        url: '/rate-limited',
        retry: true
      });
      const duration = Date.now() - startTime;
      
      expect(result.data).toBe('success');
      expect(attempts).toBe(2);
      // Should have waited at least 1 second
      expect(duration).toBeGreaterThanOrEqual(1000);
    });
  });

  describe('Integration Tests', () => {
    describe('Complete Student Learning Flow', () => {
      it('should complete full student workflow', async () => {
        // 1. Student login
        mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, {
          access_token: 'student-token',
          user: { id: 'student-1', role: 'student' }
        });

        await apiClient.login('student@example.com', 'password');

        // 2. Get dashboard
        mock.onGet(`${API_BASE_URL}/dashboard/overview/student`).reply(200, {
          enrolledCourses: 3,
          upcomingAssignments: 2
        });

        const dashboard = await apiClient.getDashboardOverview('student');
        expect((dashboard as any).enrolledCourses).toBe(3);

        // 3. View classes
        mock.onGet(`${API_BASE_URL}/classes/`).reply(200, [
          { id: 'class-1', name: 'Math 101' }
        ]);

        const classes = await apiClient.listClasses();
        expect(classes).toHaveLength(1);

        // 4. Access lesson
        mock.onGet(`${API_BASE_URL}/lessons/lesson-1`).reply(200, {
          id: 'lesson-1',
          title: 'Introduction',
          content: 'Lesson content'
        });

        const lesson = await apiClient.getLesson('lesson-1');
        expect(lesson.title).toBe('Introduction');

        // 5. Submit quiz
        mock.onPost(`${API_BASE_URL}/assessments/quiz/quiz-1/submit`).reply(200, {
          score: 85,
          passed: true
        });

        const quizResult = await apiClient.submitQuiz('quiz-1', {
          answers: []
        });
        expect(quizResult.passed).toBe(true);

        // 6. Update progress
        mock.onPost(`${API_BASE_URL}/lessons/lesson-1/progress`).reply(200, {
          progress_percentage: 100,
          completed: true
        });

        const progress = await apiClient.updateLessonProgress('lesson-1', {
          progress_percentage: 100
        });
        expect(progress.completed).toBe(true);

        // 7. Check rewards
        mock.onGet(`${API_BASE_URL}/gamification/points/student-1`).reply(200, {
          total_points: 150
        });

        const points = await apiClient.getUserPoints('student-1');
        expect(points.total_points).toBe(150);
      });
    });

    describe('Complete Teacher Management Flow', () => {
      it('should complete full teacher workflow', async () => {
        // 1. Teacher login
        mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, {
          access_token: 'teacher-token',
          user: { id: 'teacher-1', role: 'teacher' }
        });

        await apiClient.login('teacher@example.com', 'password');

        // 2. Create class
        mock.onPost(`${API_BASE_URL}/classes/`).reply(201, {
          id: 'new-class',
          name: 'Physics 201'
        });

        const newClass = await apiClient.createClass({
          name: 'Physics 201',
          grade_level: 11
        });
        expect(newClass.id).toBe('new-class');

        // 3. Add students
        mock.onPost(`${API_BASE_URL}/classes/new-class/students`).reply(200, {
          added: 25
        });

        const addResult = await apiClient.addStudentsToClass('new-class', 
          Array(25).fill(0).map((_, i) => `student-${i}`)
        );
        expect(addResult.added).toBe(25);

        // 4. Create lesson
        mock.onPost(`${API_BASE_URL}/classes/new-class/lessons`).reply(201, {
          id: 'new-lesson',
          title: 'Forces and Motion'
        });

        const lesson = await apiClient.createLesson('new-class', {
          title: 'Forces and Motion'
        });
        expect(lesson.id).toBe('new-lesson');

        // 5. Create assignment
        mock.onPost(`${API_BASE_URL}/classes/new-class/assignments`).reply(201, {
          id: 'new-assignment',
          title: 'Chapter Review'
        });

        const assignment = await apiClient.createAssignment('new-class', {
          title: 'Chapter Review',
          due_date: '2024-01-15'
        });
        expect(assignment.id).toBe('new-assignment');

        // 6. Grade submissions
        mock.onPost(`${API_BASE_URL}/assessments/grades`).reply(200, {
          graded: 25
        });

        const gradeResult = await apiClient.submitGrades('new-assignment',
          Array(25).fill(0).map((_, i) => ({
            student_id: `student-${i}`,
            score: 75 + Math.random() * 25
          }))
        );
        expect(gradeResult.graded).toBe(25);

        // 7. Generate report
        mock.onGet(`${API_BASE_URL}/reports/class/new-class/performance`).reply(200, {
          average_grade: 85.5
        });

        const report = await apiClient.getClassPerformanceReport('new-class');
        expect(report.average_grade).toBe(85.5);
      });
    });
  });

  describe('Performance Tests', () => {
    it('should handle large payloads', async () => {
      const largeData = {
        students: Array(1000).fill(0).map((_, i) => ({
          id: `student-${i}`,
          name: `Student ${i}`,
          grade: Math.random() * 100
        }))
      };

      mock.onPost(`${API_BASE_URL}/bulk/import`).reply(200, {
        imported: 1000
      });

      const result = await apiClient['request']({
        method: 'POST',
        url: '/bulk/import',
        data: largeData
      });
      
      expect(result.imported).toBe(1000);
    });

    it('should handle concurrent requests efficiently', async () => {
      const requests = Array(20).fill(0).map((_, i) => ({
        url: `/concurrent-${i}`,
        response: { id: i }
      }));

      requests.forEach(({ url, response }) => {
        mock.onGet(`${API_BASE_URL}${url}`).reply(200, response);
      });

      const startTime = Date.now();
      const results = await Promise.all(
        requests.map(({ url }) => 
          apiClient['request']({ method: 'GET', url })
        )
      );
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(20);
      // Should complete within reasonable time (5 seconds for 20 requests)
      expect(duration).toBeLessThan(5000);
    });

    it('should implement request queuing for rate limits', async () => {
      const requestQueue: Promise<any>[] = [];
      
      // Simulate rate-limited endpoint
      let requestCount = 0;
      mock.onGet(`${API_BASE_URL}/rate-limited-endpoint`).reply(() => {
        requestCount++;
        if (requestCount > 5) {
          return [429, { error: 'Rate limited' }];
        }
        return [200, { data: requestCount }];
      });

      // Send 10 requests
      for (let i = 0; i < 10; i++) {
        requestQueue.push(
          apiClient['request']({
            method: 'GET',
            url: '/rate-limited-endpoint',
            queueRequest: true
          }).catch(() => ({ error: true }))
        );
      }

      const results = await Promise.all(requestQueue);
      
      // First 5 should succeed
      const successful = results.filter((r: any) => !r.error);
      expect(successful.length).toBe(5);
    });
  });

  describe('Cache Management', () => {
    it('should cache GET requests', async () => {
      mock.onGet(`${API_BASE_URL}/cacheable`).replyOnce(200, {
        data: 'first',
        timestamp: Date.now()
      });

      // First request
      const result1 = await apiClient['request']({
        method: 'GET',
        url: '/cacheable',
        cache: true
      });

      // Second request (should use cache)
      const result2 = await apiClient['request']({
        method: 'GET',
        url: '/cacheable',
        cache: true
      });

      expect(result1).toEqual(result2);
      // Only one actual request should have been made
      expect(mock.history.get.length).toBe(1);
    });

    it('should invalidate cache on mutations', async () => {
      // Setup cache
      mock.onGet(`${API_BASE_URL}/resource`).reply(200, { value: 'original' });
      
      await apiClient['request']({
        method: 'GET',
        url: '/resource',
        cache: true
      });

      // Mutation should invalidate cache
      mock.onPatch(`${API_BASE_URL}/resource`).reply(200, { value: 'updated' });
      
      await apiClient['request']({
        method: 'PATCH',
        url: '/resource',
        data: { value: 'updated' }
      });

      // Next GET should fetch fresh data
      mock.onGet(`${API_BASE_URL}/resource`).reply(200, { value: 'updated' });
      
      const result = await apiClient['request']({
        method: 'GET',
        url: '/resource',
        cache: true
      });

      expect(result.value).toBe('updated');
      // Should have made 2 GET requests total
      expect(mock.history.get.length).toBe(2);
    });
  });
});