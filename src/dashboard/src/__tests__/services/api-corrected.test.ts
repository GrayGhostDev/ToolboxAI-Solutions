import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

// Mock WebSocketService before imports
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
    }))
  },
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    getState: vi.fn(() => 'DISCONNECTED'),
    isConnected: vi.fn(() => false)
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
      }
    })),
    subscribe: vi.fn(() => vi.fn())
  }
}));

// Mock UI slice
vi.mock('../../store/slices/uiSlice', () => ({
  addNotification: vi.fn()
}));

import ApiClient from '../../services/api';
import type { 
  AuthResponse,
  User,
  Lesson,
  ClassSummary,
  ClassDetails,
  Assessment,
  AssessmentSubmission,
  StudentProgress,
  DashboardOverview,
  ComplianceStatus,
  RobloxWorld,
  Message,
  Badge,
  LeaderboardEntry,
  XPTransaction,
  ProgressPoint
} from '../../types/api';

const API_BASE_URL = 'http://localhost:8008';

describe('Complete API Service Test Suite - Corrected', () => {
  let mock: MockAdapter;
  let apiClient: ApiClient;
  let localStorageMock: { [key: string]: string };

  beforeAll(() => {
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

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup axios mock
    mock = new MockAdapter(axios, { 
      delayResponse: 0,
      onNoMatch: "throwException"
    });
    
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
        const mockResponse: AuthResponse = {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          user: {
            id: 'user-123',
            email: 'teacher@example.com',
            displayName: 'John Doe',
            role: 'teacher',
            avatarUrl: null,
            preferences: {},
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z'
          }
        };

        mock.onPost(`${API_BASE_URL}/auth/login`).reply(200, mockResponse);

        const result = await apiClient.login('teacher@example.com', 'SecurePass123!');
        
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('toolboxai_auth_token')).toBe('new-access-token');
        expect(localStorage.getItem('toolboxai_refresh_token')).toBe('new-refresh-token');
        expect(mock.history.post[0].data).toBe(JSON.stringify({ 
          email: 'teacher@example.com', 
          password: 'SecurePass123!' 
        }));
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
    });

    describe('Registration', () => {
      it('should successfully register a new user', async () => {
        const registerData = {
          email: 'newuser@example.com',
          password: 'SecurePass123!',
          displayName: 'New User',
          role: 'student'
        };

        const mockResponse: AuthResponse = {
          access_token: 'new-token',
          refresh_token: 'new-refresh',
          user: {
            id: 'user-789',
            email: 'newuser@example.com',
            displayName: 'New User',
            role: 'student',
            avatarUrl: null,
            preferences: {},
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z'
          }
        };

        mock.onPost(`${API_BASE_URL}/auth/register`).reply(201, mockResponse);

        const result = await apiClient.register(registerData);
        
        expect(result).toEqual(mockResponse);
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
          displayName: 'Test',
          role: 'student'
        })).rejects.toThrow();
      });
    });

    describe('Token Management', () => {
      it('should refresh access token', async () => {
        const mockResponse: AuthResponse = {
          access_token: 'refreshed-token',
          refresh_token: 'new-refresh-token',
          user: {
            id: 'user-123',
            email: 'user@example.com',
            displayName: 'User',
            role: 'teacher',
            avatarUrl: null,
            preferences: {},
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z'
          }
        };

        mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(200, mockResponse);

        const result = await apiClient.refreshToken('test-refresh-token');
        
        expect(result).toEqual(mockResponse);
      });

      it('should handle refresh token expiration', async () => {
        mock.onPost(`${API_BASE_URL}/auth/refresh`).reply(401, {
          detail: 'Refresh token expired'
        });

        await expect(apiClient.refreshToken('expired-token')).rejects.toThrow();
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
      });
    });
  });

  describe('Dashboard Module', () => {
    it('should fetch dashboard overview for teacher', async () => {
      const mockData: DashboardOverview = {
        totalStudents: 150,
        totalClasses: 8,
        activeAssessments: 12,
        completionRate: 78.5,
        recentActivity: []
      };

      mock.onGet(`${API_BASE_URL}/dashboard/overview/teacher`).reply(200, mockData);

      const result = await apiClient.getDashboardOverview('teacher');
      
      expect(result).toEqual(mockData);
      expect(result.totalStudents).toBe(150);
    });

    it('should fetch weekly XP data', async () => {
      const mockData: ProgressPoint[] = [
        { week: 1, xp: 100 },
        { week: 2, xp: 150 }
      ];

      mock.onGet(`${API_BASE_URL}/dashboard/weekly-xp`).reply(200, mockData);

      const result = await apiClient.getWeeklyXP();
      
      expect(result).toEqual(mockData);
      expect(result).toHaveLength(2);
    });

    it('should fetch subject mastery', async () => {
      const mockData = [
        { subject: 'Math', mastery: 85 },
        { subject: 'Science', mastery: 92 }
      ];

      mock.onGet(`${API_BASE_URL}/dashboard/subject-mastery`).reply(200, mockData);

      const result = await apiClient.getSubjectMastery();
      
      expect(result).toEqual(mockData);
    });
  });

  describe('Lesson Management', () => {
    it('should list lessons', async () => {
      const mockLessons: Lesson[] = [
        {
          id: 'lesson-1',
          title: 'Introduction to Algebra',
          description: 'Basic algebraic concepts',
          subject: 'Mathematics',
          gradeLevel: 9,
          duration: 45,
          objectives: ['Understand variables'],
          content: {},
          robloxWorldId: null,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/lessons`).reply(200, mockLessons);

      const result = await apiClient.listLessons();
      
      expect(result).toEqual(mockLessons);
      expect(result[0].title).toBe('Introduction to Algebra');
    });

    it('should get single lesson', async () => {
      const mockLesson: Lesson = {
        id: 'lesson-123',
        title: 'Algebra Basics',
        description: 'Learn algebra',
        subject: 'Mathematics',
        gradeLevel: 9,
        duration: 45,
        objectives: [],
        content: {},
        robloxWorldId: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/lessons/lesson-123`).reply(200, mockLesson);

      const result = await apiClient.getLesson('lesson-123');
      
      expect(result).toEqual(mockLesson);
    });

    it('should create lesson', async () => {
      const lessonData = {
        title: 'New Lesson',
        description: 'Description',
        subject: 'Math',
        gradeLevel: 9
      };

      const mockResponse: Lesson = {
        id: 'lesson-new',
        ...lessonData,
        duration: 45,
        objectives: [],
        content: {},
        robloxWorldId: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/lessons`).reply(201, mockResponse);

      const result = await apiClient.createLesson(lessonData);
      
      expect(result.id).toBe('lesson-new');
    });

    it('should update lesson', async () => {
      const updates = { title: 'Updated Title' };
      const mockResponse: Lesson = {
        id: 'lesson-123',
        title: 'Updated Title',
        description: 'Description',
        subject: 'Math',
        gradeLevel: 9,
        duration: 45,
        objectives: [],
        content: {},
        robloxWorldId: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z'
      };

      mock.onPut(`${API_BASE_URL}/lessons/lesson-123`).reply(200, mockResponse);

      const result = await apiClient.updateLesson('lesson-123', updates);
      
      expect(result.title).toBe('Updated Title');
    });

    it('should delete lesson', async () => {
      mock.onDelete(`${API_BASE_URL}/lessons/lesson-123`).reply(204);

      await expect(apiClient.deleteLesson('lesson-123')).resolves.toBeUndefined();
    });
  });

  describe('Class Management', () => {
    it('should list classes', async () => {
      const mockClasses: ClassSummary[] = [
        {
          id: 'class-1',
          name: 'Math 101',
          subject: 'Mathematics',
          teacherId: 'teacher-1',
          teacherName: 'John Doe',
          studentCount: 25,
          schedule: 'MWF 10:00-11:00',
          avatarUrl: null
        }
      ];

      mock.onGet(`${API_BASE_URL}/classes`).reply(200, mockClasses);

      const result = await apiClient.listClasses();
      
      expect(result).toEqual(mockClasses);
      expect(result[0].name).toBe('Math 101');
    });

    it('should get single class details', async () => {
      const mockClass: ClassDetails = {
        id: 'class-123',
        name: 'Physics 301',
        subject: 'Physics',
        description: 'Advanced Physics',
        teacherId: 'teacher-1',
        teacherName: 'Dr. Smith',
        students: [],
        lessons: [],
        assessments: [],
        schedule: 'TTh 2:00-3:30',
        avatarUrl: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/classes/class-123`).reply(200, mockClass);

      const result = await apiClient.getClass('class-123');
      
      expect(result).toEqual(mockClass);
    });

    it('should create class', async () => {
      const classData = {
        name: 'New Class',
        subject: 'Science',
        teacherId: 'teacher-1'
      };

      const mockResponse: ClassSummary = {
        id: 'class-new',
        name: 'New Class',
        subject: 'Science',
        teacherId: 'teacher-1',
        teacherName: 'Teacher Name',
        studentCount: 0,
        schedule: '',
        avatarUrl: null
      };

      mock.onPost(`${API_BASE_URL}/classes`).reply(201, mockResponse);

      const result = await apiClient.createClass(classData);
      
      expect(result.id).toBe('class-new');
    });
  });

  describe('Assessment Management', () => {
    it('should list assessments', async () => {
      const mockAssessments: Assessment[] = [
        {
          id: 'assess-1',
          title: 'Math Quiz',
          description: 'Chapter 5 Quiz',
          type: 'quiz',
          classId: 'class-1',
          questions: [],
          totalPoints: 100,
          duration: 30,
          dueDate: '2024-01-15T00:00:00Z',
          published: true,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/assessments`).reply(200, mockAssessments);

      const result = await apiClient.listAssessments();
      
      expect(result).toEqual(mockAssessments);
    });

    it('should get single assessment', async () => {
      const mockAssessment: Assessment = {
        id: 'assess-123',
        title: 'Final Exam',
        description: 'End of semester exam',
        type: 'exam',
        classId: 'class-1',
        questions: [],
        totalPoints: 200,
        duration: 120,
        dueDate: '2024-01-30T00:00:00Z',
        published: false,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/assessments/assess-123`).reply(200, mockAssessment);

      const result = await apiClient.getAssessment('assess-123');
      
      expect(result).toEqual(mockAssessment);
    });

    it('should create assessment', async () => {
      const assessmentData = {
        title: 'Pop Quiz',
        description: 'Surprise quiz',
        type: 'quiz' as const,
        classId: 'class-1'
      };

      const mockResponse: Assessment = {
        id: 'assess-new',
        title: 'Pop Quiz',
        description: 'Surprise quiz',
        type: 'quiz',
        classId: 'class-1',
        questions: [],
        totalPoints: 50,
        duration: 15,
        dueDate: '2024-01-10T00:00:00Z',
        published: false,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/assessments`).reply(201, mockResponse);

      const result = await apiClient.createAssessment(assessmentData);
      
      expect(result.id).toBe('assess-new');
    });

    it('should submit assessment', async () => {
      const submissionData = {
        answers: { q1: 'A', q2: 'B' },
        time_spent_minutes: 25
      };

      const mockResponse: AssessmentSubmission = {
        id: 'sub-123',
        assessmentId: 'assess-123',
        studentId: 'student-1',
        answers: submissionData.answers,
        score: 85,
        feedback: 'Good work!',
        submittedAt: '2024-01-01T10:00:00Z',
        gradedAt: '2024-01-01T11:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/assessments/assess-123/submit`).reply(200, mockResponse);

      const result = await apiClient.submitAssessment('assess-123', submissionData);
      
      expect(result.score).toBe(85);
    });

    it('should update assessment', async () => {
      const updates = { title: 'Updated Quiz' };
      const mockResponse: Assessment = {
        id: 'assess-123',
        title: 'Updated Quiz',
        description: 'Description',
        type: 'quiz',
        classId: 'class-1',
        questions: [],
        totalPoints: 100,
        duration: 30,
        dueDate: '2024-01-15T00:00:00Z',
        published: false,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z'
      };

      mock.onPut(`${API_BASE_URL}/assessments/assess-123`).reply(200, mockResponse);

      const result = await apiClient.updateAssessment('assess-123', updates);
      
      expect(result.title).toBe('Updated Quiz');
    });

    it('should delete assessment', async () => {
      mock.onDelete(`${API_BASE_URL}/assessments/assess-123`).reply(204);

      await expect(apiClient.deleteAssessment('assess-123')).resolves.toBeUndefined();
    });

    it('should publish assessment', async () => {
      const mockResponse: Assessment = {
        id: 'assess-123',
        title: 'Quiz',
        description: 'Description',
        type: 'quiz',
        classId: 'class-1',
        questions: [],
        totalPoints: 100,
        duration: 30,
        dueDate: '2024-01-15T00:00:00Z',
        published: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/assessments/assess-123/publish`).reply(200, mockResponse);

      const result = await apiClient.publishAssessment('assess-123');
      
      expect(result.published).toBe(true);
    });

    it('should get assessment submissions', async () => {
      const mockSubmissions: AssessmentSubmission[] = [
        {
          id: 'sub-1',
          assessmentId: 'assess-123',
          studentId: 'student-1',
          answers: {},
          score: 90,
          feedback: 'Excellent!',
          submittedAt: '2024-01-01T10:00:00Z',
          gradedAt: '2024-01-01T11:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/assessments/assess-123/submissions`).reply(200, mockSubmissions);

      const result = await apiClient.getAssessmentSubmissions('assess-123');
      
      expect(result).toEqual(mockSubmissions);
    });
  });

  describe('Progress Tracking', () => {
    it('should get student progress', async () => {
      const mockProgress: StudentProgress = {
        studentId: 'student-123',
        overallProgress: 75,
        subjectProgress: { Math: 80, Science: 70 },
        completedLessons: 42,
        totalLessons: 56,
        averageScore: 85.5,
        streakDays: 15,
        lastActiveAt: '2024-01-01T10:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/progress/student-123`).reply(200, mockProgress);

      const result = await apiClient.getStudentProgress('student-123');
      
      expect(result).toEqual(mockProgress);
      expect(result.overallProgress).toBe(75);
    });

    it('should get class progress', async () => {
      const mockProgress = {
        classId: 'class-123',
        averageProgress: 82,
        studentProgress: []
      };

      mock.onGet(`${API_BASE_URL}/progress/class/class-123`).reply(200, mockProgress);

      const result = await apiClient.getClassProgress('class-123');
      
      expect(result.averageProgress).toBe(82);
    });

    it('should update progress', async () => {
      const mockResponse = {
        lessonId: 'lesson-123',
        progress: 85,
        completed: false
      };

      mock.onPost(`${API_BASE_URL}/progress/update`).reply(200, mockResponse);

      const result = await apiClient.updateProgress('lesson-123', 85, 30, 90);
      
      expect(result.progress).toBe(85);
    });
  });

  describe('Gamification', () => {
    it('should get student XP', async () => {
      const mockData = { xp: 1250, level: 5 };

      mock.onGet(`${API_BASE_URL}/gamification/xp/student-123`).reply(200, mockData);

      const result = await apiClient.getStudentXP('student-123');
      
      expect(result.xp).toBe(1250);
      expect(result.level).toBe(5);
    });

    it('should add XP', async () => {
      const mockTransaction: XPTransaction = {
        id: 'xp-123',
        studentId: 'student-123',
        amount: 50,
        reason: 'Quiz completion',
        timestamp: '2024-01-01T10:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/gamification/xp`).reply(200, mockTransaction);

      const result = await apiClient.addXP('student-123', 50, 'Quiz completion');
      
      expect(result.amount).toBe(50);
    });

    it('should get badges', async () => {
      const mockBadges: Badge[] = [
        {
          id: 'badge-1',
          name: 'Fast Learner',
          description: 'Complete 10 lessons in a week',
          imageUrl: 'https://example.com/badge.png',
          earnedAt: '2024-01-01T00:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/gamification/badges`).reply(200, mockBadges);

      const result = await apiClient.getBadges();
      
      expect(result).toEqual(mockBadges);
    });

    it('should award badge', async () => {
      const mockBadge: Badge = {
        id: 'badge-2',
        name: 'Quiz Master',
        description: 'Score 100% on 5 quizzes',
        imageUrl: 'https://example.com/badge2.png',
        earnedAt: '2024-01-01T10:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/gamification/badges/award`).reply(200, mockBadge);

      const result = await apiClient.awardBadge('student-123', 'badge-2');
      
      expect(result.id).toBe('badge-2');
    });

    it('should get leaderboard', async () => {
      const mockLeaderboard: LeaderboardEntry[] = [
        { rank: 1, studentId: 'student-1', studentName: 'Alice', xp: 2500, level: 8 },
        { rank: 2, studentId: 'student-2', studentName: 'Bob', xp: 2300, level: 7 }
      ];

      mock.onGet(`${API_BASE_URL}/gamification/leaderboard`).reply(200, mockLeaderboard);

      const result = await apiClient.getLeaderboard();
      
      expect(result).toEqual(mockLeaderboard);
      expect(result[0].rank).toBe(1);
    });
  });

  describe('Roblox Integration', () => {
    it('should list Roblox worlds', async () => {
      const mockWorlds: RobloxWorld[] = [
        {
          id: 'world-1',
          name: 'Math Adventure',
          description: 'Learn math through gaming',
          placeId: '123456789',
          lessonId: 'lesson-1',
          thumbnailUrl: 'https://example.com/thumb.png',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/roblox/worlds`).reply(200, mockWorlds);

      const result = await apiClient.listRobloxWorlds();
      
      expect(result).toEqual(mockWorlds);
    });

    it('should push lesson to Roblox', async () => {
      const mockResponse = { jobId: 'job-123', status: 'processing' };

      mock.onPost(`${API_BASE_URL}/roblox/push/lesson-123`).reply(200, mockResponse);

      const result = await apiClient.pushLessonToRoblox('lesson-123');
      
      expect(result.jobId).toBe('job-123');
      expect(result.status).toBe('processing');
    });

    it('should get Roblox join URL', async () => {
      const mockResponse = { joinUrl: 'https://roblox.com/join/abc123' };

      mock.onGet(`${API_BASE_URL}/roblox/join/class-123`).reply(200, mockResponse);

      const result = await apiClient.getRobloxJoinUrl('class-123');
      
      expect(result.joinUrl).toBe('https://roblox.com/join/abc123');
    });
  });

  describe('Messaging', () => {
    it('should list messages', async () => {
      const mockMessages: Message[] = [
        {
          id: 'msg-1',
          subject: 'Test Message',
          body: 'Message body',
          senderId: 'user-1',
          senderName: 'John Doe',
          recipientIds: ['user-2'],
          priority: 'normal',
          read: false,
          starred: false,
          archived: false,
          folder: 'inbox',
          sentAt: '2024-01-01T10:00:00Z'
        }
      ];

      mock.onGet(`${API_BASE_URL}/messages`).reply(200, mockMessages);

      const result = await apiClient.listMessages();
      
      expect(result).toEqual(mockMessages);
    });

    it('should send message', async () => {
      const messageData = {
        subject: 'New Message',
        body: 'Message content',
        recipient_ids: ['user-2', 'user-3'],
        priority: 'high'
      };

      const mockResponse: Message = {
        id: 'msg-new',
        subject: 'New Message',
        body: 'Message content',
        senderId: 'user-1',
        senderName: 'Sender',
        recipientIds: ['user-2', 'user-3'],
        priority: 'high',
        read: false,
        starred: false,
        archived: false,
        folder: 'sent',
        sentAt: '2024-01-01T10:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/messages`).reply(201, mockResponse);

      const result = await apiClient.sendMessage(messageData);
      
      expect(result.id).toBe('msg-new');
    });

    it('should get single message', async () => {
      const mockMessage: Message = {
        id: 'msg-123',
        subject: 'Important',
        body: 'Full message content',
        senderId: 'user-1',
        senderName: 'John Doe',
        recipientIds: ['user-2'],
        priority: 'high',
        read: false,
        starred: false,
        archived: false,
        folder: 'inbox',
        sentAt: '2024-01-01T10:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/messages/msg-123`).reply(200, mockMessage);

      const result = await apiClient.getMessage('msg-123');
      
      expect(result).toEqual(mockMessage);
    });

    it('should mark message as read', async () => {
      mock.onPut(`${API_BASE_URL}/messages/msg-123/read`).reply(204);

      await expect(apiClient.markMessageAsRead('msg-123')).resolves.toBeUndefined();
    });

    it('should delete message', async () => {
      mock.onDelete(`${API_BASE_URL}/messages/msg-123`).reply(204);

      await expect(apiClient.deleteMessage('msg-123')).resolves.toBeUndefined();
    });

    it('should reply to message', async () => {
      const replyData = {
        subject: 'Re: Original',
        body: 'Reply content',
        recipient_ids: ['user-1']
      };

      const mockResponse: Message = {
        id: 'msg-reply',
        subject: 'Re: Original',
        body: 'Reply content',
        senderId: 'user-2',
        senderName: 'Replier',
        recipientIds: ['user-1'],
        priority: 'normal',
        read: false,
        starred: false,
        archived: false,
        folder: 'sent',
        sentAt: '2024-01-01T11:00:00Z'
      };

      mock.onPost(`${API_BASE_URL}/messages/msg-123/reply`).reply(201, mockResponse);

      const result = await apiClient.replyToMessage('msg-123', replyData);
      
      expect(result.id).toBe('msg-reply');
    });
  });

  describe('Compliance', () => {
    it('should get compliance status', async () => {
      const mockStatus: ComplianceStatus = {
        coppaCompliant: true,
        ferpaCompliant: true,
        gdprCompliant: false,
        lastAuditDate: '2024-01-01T00:00:00Z',
        nextAuditDate: '2024-07-01T00:00:00Z'
      };

      mock.onGet(`${API_BASE_URL}/compliance/status`).reply(200, mockStatus);

      const result = await apiClient.getComplianceStatus();
      
      expect(result).toEqual(mockStatus);
      expect(result.coppaCompliant).toBe(true);
    });

    it('should record consent', async () => {
      mock.onPost(`${API_BASE_URL}/compliance/consent`).reply(204);

      await expect(apiClient.recordConsent('coppa', 'user-123')).resolves.toBeUndefined();
    });
  });

  describe('LMS Integration', () => {
    it('should connect Google Classroom', async () => {
      const mockResponse = { connected: true };

      mock.onPost(`${API_BASE_URL}/integrations/google-classroom/connect`).reply(200, mockResponse);

      const result = await apiClient.connectGoogleClassroom('google-token');
      
      expect(result.connected).toBe(true);
    });

    it('should connect Canvas', async () => {
      const mockResponse = { connected: true };

      mock.onPost(`${API_BASE_URL}/integrations/canvas/connect`).reply(200, mockResponse);

      const result = await apiClient.connectCanvas('canvas-token');
      
      expect(result.connected).toBe(true);
    });

    it('should sync LMS data', async () => {
      const mockResponse = { synced: true };

      mock.onPost(`${API_BASE_URL}/integrations/google_classroom/sync`).reply(200, mockResponse);

      const result = await apiClient.syncLMSData('google_classroom');
      
      expect(result.synced).toBe(true);
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
        detail: 'Resource not found'
      });

      await expect(apiClient['request']({
        method: 'GET',
        url: '/nonexistent'
      })).rejects.toThrow();
    });

    it('should handle validation errors', async () => {
      mock.onPost(`${API_BASE_URL}/classes`).reply(422, {
        detail: [
          { msg: 'Name is required', loc: ['body', 'name'] }
        ]
      });

      await expect(apiClient.createClass({})).rejects.toThrow();
    });
  });
});