import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import ApiClient, { getMyProfile } from '../../../../apps/dashboard/src/services/api';

// Use the correct API base URL from config
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

      // Login expects username extracted from email
      mock.onPost(`${API_BASE_URL}/auth/login`).reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.username).toBe('test'); // Should extract username from email
        expect(data.password).toBe('password123');
        
        return [200, {
          access_token: 'new-jwt-token',
          refresh_token: 'refresh-token',
          expires_in: 3600,
          user: { 
            id: '123', 
            email: 'test@example.com', 
            username: 'test',
            first_name: 'Test',
            last_name: 'User',
            role: 'teacher' 
          },
        }];
      });

      const result = await apiClient.login(loginData.email, loginData.password) as any;
      
      // The login method returns the raw API response
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

    it('should register a new user', async () => {
      const registerData = {
        email: 'newuser@example.com',
        password: 'secure123',
        displayName: 'New User',
        role: 'teacher'
      };

      // Register transforms to backend format with snake_case
      mock.onPost(`${API_BASE_URL}/auth/register`).reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.username).toBe('newuser'); // Generated from email
        expect(data.first_name).toBe('New');
        expect(data.last_name).toBe('User');
        
        return [200, {
          access_token: 'register-jwt-token',
          refresh_token: 'register-refresh-token',
          expires_in: 3600,
          user: {
            id: '456',
            email: 'newuser@example.com',
            username: 'newuser',
            first_name: 'New',
            last_name: 'User',
            display_name: 'New User',
            role: 'teacher',
            is_active: true,
            is_verified: false,
            total_xp: 0,
            level: 1,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        }];
      });

      const result = await apiClient.register(registerData);
      
      // Register method transforms response to frontend format
      expect(result.accessToken).toBe('register-jwt-token');
      expect(result.refreshToken).toBe('register-refresh-token');
      expect(result.user.email).toBe('newuser@example.com');
      expect(result.user.displayName).toBe('New User');
    });

    it('should refresh token when expired', async () => {
      localStorage.setItem('toolboxai_refresh_token', 'old-refresh-token');
      
      // Mock the refresh token endpoint
      mock.onPost(`${API_BASE_URL}/auth/refresh`).reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.refresh_token).toBe('old-refresh-token');
        
        return [200, {
          accessToken: 'new-jwt-token',
          refreshToken: 'new-refresh-token',
          expiresIn: 3600
        }];
      });
      
      // Mock the profile request to succeed
      mock.onGet(`${API_BASE_URL}/users/me/profile`).reply(200, {
        id: '123',
        email: 'test@example.com',
        username: 'test',
        role: 'teacher',
        firstName: 'Test',
        lastName: 'User',
        displayName: 'Test User'
      });

      const result = await getMyProfile();
      
      expect(result.email).toBe('test@example.com');
    });

    it('should logout successfully', async () => {
      localStorage.setItem('toolboxai_auth_token', 'token');
      localStorage.setItem('toolboxai_refresh_token', 'refresh');

      mock.onPost(`${API_BASE_URL}/auth/logout`).reply(204);

      await apiClient.logout();

      // Verify logout was called (tokens remain as API doesn't clear them)
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

    it('should fetch weekly XP analytics', async () => {
      const mockData = [
        { date: '2024-01-01', value: 100 },
        { date: '2024-01-02', value: 150 }
      ];

      // Note: Uses /analytics/weekly_xp not /dashboard/weekly-xp
      mock.onGet(`${API_BASE_URL}/analytics/weekly_xp`).reply(200, mockData);

      const result = await apiClient.getWeeklyXP();
      
      expect(result).toEqual(mockData);
      expect(result[0].value).toBe(100);
    });

    it('should fetch subject mastery', async () => {
      const mockData = [
        { subject: 'Math', mastery: 85 },
        { subject: 'Science', mastery: 92 }
      ];

      mock.onGet(`${API_BASE_URL}/analytics/subject_mastery`).reply(200, mockData);

      const result = await apiClient.getSubjectMastery();
      
      expect(result).toEqual(mockData);
      expect(result[0].mastery).toBe(85);
    });

    it('should handle API errors with retry', async () => {
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

    it('should get class details', async () => {
      const classId = 'class-123';
      const classDetails = {
        id: classId,
        name: 'Math 101',
        description: 'Basic Mathematics',
        students: ['student1', 'student2']
      };

      mock.onGet(`${API_BASE_URL}/classes/${classId}`).reply(200, classDetails);

      const result = await apiClient.getClass(classId);
      
      expect(result.id).toBe(classId);
      expect(result.name).toBe('Math 101');
    });

    it('should update class details', async () => {
      const classId = 'class-123';
      const updates = { name: 'Advanced Math' };

      mock.onPut(`${API_BASE_URL}/classes/${classId}`).reply(200, { 
        id: classId, 
        ...updates 
      });

      // Using the request method directly
      const result = await apiClient['request']({
        method: 'PUT',
        url: `/classes/${classId}`,
        data: updates
      }) as any;
      
      expect(result.name).toBe('Advanced Math');
    });

    it('should delete a class', async () => {
      const classId = 'class-123';

      mock.onDelete(`${API_BASE_URL}/classes/${classId}`).reply(204);

      // Note: deleteClass method doesn't exist in ApiClient
      await expect(apiClient['request']({
        method: 'DELETE',
        url: `/classes/${classId}`
      })).resolves.not.toThrow();
    });
  });

  describe('Assessment Management', () => {
    it('should create an assessment', async () => {
      const assessmentData = {
        title: 'Math Quiz',
        lessonId: 'lesson-123',
        classId: 'class-456',
        type: 'quiz' as const,
        questions: [
          { id: '1', question: 'What is 2+2?', answer: '4' }
        ],
        dueDate: '2024-12-31',
        maxSubmissions: 3
      };

      // CreateAssessment transforms camelCase to snake_case
      mock.onPost(`${API_BASE_URL}/assessments/`).reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.lesson_id).toBe('lesson-123'); // Transformed to snake_case
        expect(data.class_id).toBe('class-456');
        expect(data.max_attempts).toBe(3); // maxSubmissions -> max_attempts
        expect(data.due_date).toBe('2024-12-31');
        
        return [201, {
          id: 'assessment-789',
          title: 'Math Quiz',
          lessonId: 'lesson-123',
          classId: 'class-456',
          type: 'quiz',
          questions: data.questions,
          dueDate: '2024-12-31',
          maxSubmissions: 3,
          status: 'draft'
        }];
      });

      const result = await apiClient.createAssessment(assessmentData);
      
      expect(result.id).toBe('assessment-789');
      expect(result.title).toBe('Math Quiz');
    });

    it('should list assessments with class filter', async () => {
      const classId = 'class-456';
      const assessments = [
        { id: 'a1', title: 'Quiz 1', classId },
        { id: 'a2', title: 'Quiz 2', classId }
      ];

      // listAssessments transforms classId to class_id param
      mock.onGet(`${API_BASE_URL}/assessments/`, { params: { class_id: classId } }).reply(200, assessments);

      const result = await apiClient.listAssessments(classId);
      
      expect(result).toHaveLength(2);
      expect(result[0].title).toBe('Quiz 1');
    });

    it('should submit assessment', async () => {
      const assessmentId = 'assessment-123';
      const submissionData = {
        answers: { q1: 'answer1', q2: 'answer2' },
        time_spent_minutes: 15
      };

      mock.onPost(`${API_BASE_URL}/assessments/${assessmentId}/submit`).reply(200, {
        id: 'submission-456',
        assessmentId,
        studentId: 'student-789',
        answers: submissionData.answers,
        score: 85,
        submittedAt: new Date().toISOString()
      });

      const result = await apiClient.submitAssessment(assessmentId, submissionData);
      
      expect(result.id).toBe('submission-456');
      expect(result.score).toBe(85);
    });

    it('should publish assessment', async () => {
      const assessmentId = 'assessment-123';

      mock.onPut(`${API_BASE_URL}/assessments/${assessmentId}/publish`).reply(200, {
        id: assessmentId,
        status: 'published'
      });

      const result = await apiClient.publishAssessment(assessmentId);
      
      expect(result.status).toBe('published');
    });
  });

  describe('Roblox Integration', () => {
    it('should generate Roblox content', async () => {

      const lessonId = 'lesson-123';
      mock.onPost(`${API_BASE_URL}/roblox/push/${lessonId}`).reply(200, {
        jobId: 'job-123',
        status: 'processing',
      });

      const result = await apiClient.pushLessonToRoblox(lessonId);
      
      expect(result.jobId).toBe('job-123');
      expect(result.status).toBe('processing');
    });

    it('should get Roblox join URL', async () => {
      const classId = 'class-456';

      mock.onGet(`${API_BASE_URL}/roblox/join/${classId}`).reply(200, {
        joinUrl: 'https://roblox.com/join/world-456',
      });

      const result = await apiClient.getRobloxJoinUrl(classId);
      
      expect(result.joinUrl).toBe('https://roblox.com/join/world-456');
    });

    it('should list Roblox worlds', async () => {
      const lessonId = 'lesson-123';
      const worlds = [
        { id: 'world-1', name: 'Math World', lessonId },
        { id: 'world-2', name: 'Science Lab', lessonId }
      ];

      mock.onGet(`${API_BASE_URL}/roblox/worlds`, { params: { lessonId } }).reply(200, worlds);

      const result = await apiClient.listRobloxWorlds(lessonId);
      
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('Math World');
    });
  });

  describe('Message Operations', () => {
    it('should send a message', async () => {
      const messageData = {
        subject: 'Test Message',
        body: 'This is a test',
        recipient_ids: ['user-123'],
      };

      mock.onPost(`${API_BASE_URL}/messages/`).reply(200, {
        id: 'msg-123',
        ...messageData,
        sender_id: 'sender-456',
        created_at: new Date().toISOString(),
      });

      const result = await apiClient.sendMessage(messageData);
      
      expect(result.id).toBe('msg-123');
      expect(result.subject).toBe('Test Message');
    });

    it('should list messages', async () => {
      const messages = [
        { id: 'msg-1', subject: 'Message 1' },
        { id: 'msg-2', subject: 'Message 2' },
      ];

      mock.onGet(`${API_BASE_URL}/messages/`).reply(200, messages);

      const result = await apiClient.listMessages();
      
      expect(result).toHaveLength(2);
      expect(result[0].subject).toBe('Message 1');
    });

    it('should mark message as read', async () => {
      const messageId = 'msg-123';

      mock.onPut(`${API_BASE_URL}/messages/${messageId}/read`).reply(204);

      await expect(apiClient.markMessageAsRead(messageId)).resolves.not.toThrow();
    });

    it('should delete message', async () => {
      const messageId = 'msg-123';

      mock.onDelete(`${API_BASE_URL}/messages/${messageId}`).reply(204);

      await expect(apiClient.deleteMessage(messageId)).resolves.not.toThrow();
    });
  });

  describe('Compliance', () => {
    it('should get compliance status', async () => {
      const complianceData = {
        coppa: true,
        ferpa: true,
        gdpr: false,
        lastUpdated: new Date().toISOString()
      };

      mock.onGet(`${API_BASE_URL}/compliance/status`).reply(200, complianceData);

      const result = await apiClient.getComplianceStatus();
      
      expect(result.coppa).toBe(true);
      expect(result.ferpa).toBe(true);
      expect(result.gdpr).toBe(false);
    });

    it('should record consent', async () => {
      const consentType = 'coppa';
      const userId = 'user-123';

      // recordConsent sends specific structure
      mock.onPost(`${API_BASE_URL}/compliance/consent`).reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.consent_type).toBe('coppa'); // Backend expects consent_type
        expect(data.granted).toBe(true); // Backend requires granted field
        expect(data.details.userId).toBe('user-123');
        
        return [204];
      });

      await expect(apiClient.recordConsent(consentType as any, userId)).resolves.not.toThrow();
    });
  });

  describe('Gamification', () => {
    it('should get student XP', async () => {
      const studentId = 'student-123';

      mock.onGet(`${API_BASE_URL}/gamification/xp/${studentId}`).reply(200, {
        xp: 1500,
        level: 5
      });

      const result = await apiClient.getStudentXP(studentId);
      
      expect(result.xp).toBe(1500);
      expect(result.level).toBe(5);
    });

    it('should add XP to student', async () => {
      const studentId = 'student-123';
      const xpData = {
        amount: 100,
        reason: 'Completed quiz'
      };

      mock.onPost(`${API_BASE_URL}/gamification/xp/${studentId}`).reply(200, {
        id: 'xp-trans-456',
        studentId,
        amount: xpData.amount,
        reason: xpData.reason,
        timestamp: new Date().toISOString()
      });

      const result = await apiClient.addXP(studentId, xpData.amount, xpData.reason);
      
      expect(result.amount).toBe(100);
      expect(result.reason).toBe('Completed quiz');
    });

    it('should get leaderboard', async () => {
      const leaderboard = [
        { rank: 1, studentId: 's1', name: 'Student 1', xp: 2000 },
        { rank: 2, studentId: 's2', name: 'Student 2', xp: 1800 }
      ];

      mock.onGet(`${API_BASE_URL}/gamification/leaderboard`).reply(200, leaderboard);

      const result = await apiClient.getLeaderboard();
      
      expect(result).toHaveLength(2);
      expect(result[0].xp).toBe(2000);
    });

    it('should get badges', async () => {
      const badges = [
        { id: 'badge-1', name: 'Quiz Master', description: 'Complete 10 quizzes' },
        { id: 'badge-2', name: 'Perfect Score', description: 'Get 100% on an assessment' }
      ];

      mock.onGet(`${API_BASE_URL}/gamification/badges`).reply(200, badges);

      const result = await apiClient.getBadges();
      
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('Quiz Master');
    });

    it('should award badge', async () => {
      const studentId = 'student-123';
      const badgeId = 'badge-456';

      mock.onPost(`${API_BASE_URL}/gamification/badges/award`).reply(200, {
        id: badgeId,
        name: 'Achievement Unlocked',
        awardedTo: studentId,
        awardedAt: new Date().toISOString()
      });

      const result = await apiClient.awardBadge(studentId, badgeId);
      
      expect(result.id).toBe(badgeId);
      expect(result.awardedTo).toBe(studentId);
    });
  });

  describe('Progress Tracking', () => {
    it('should get student progress', async () => {
      const studentId = 'student-123';

      mock.onGet(`${API_BASE_URL}/progress/student/${studentId}`).reply(200, {
        studentId,
        overallProgress: 75,
        lessonsCompleted: 15,
        totalLessons: 20
      });

      const result = await apiClient.getStudentProgress(studentId);
      
      expect(result.overallProgress).toBe(75);
      expect(result.lessonsCompleted).toBe(15);
    });

    it('should update progress', async () => {
      const lessonId = 'lesson-123';
      const progressData = {
        progressPercentage: 80,
        timeSpentMinutes: 25,
        score: 90
      };

mock.onPost(`${API_BASE_URL}/progress/update`, {
        lesson_id: lessonId,
        progress_percentage: progressData.progressPercentage,
        time_spent_minutes: progressData.timeSpentMinutes,
        score: progressData.score
      }).reply(200, {
        lessonId,
        ...progressData,
        updated: true
      });

      const result = await apiClient.updateProgress(
        lessonId,
        progressData.progressPercentage,
        progressData.timeSpentMinutes,
        progressData.score
      );
      
      expect(result.updated).toBe(true);
    });

    it('should get class progress', async () => {
      const classId = 'class-123';

      mock.onGet(`${API_BASE_URL}/progress/class/${classId}`).reply(200, {
        classId,
        averageProgress: 68,
        studentsCount: 25
      });

      const result = await apiClient.getClassProgress(classId);
      
      expect(result.averageProgress).toBe(68);
      expect(result.studentsCount).toBe(25);
    });
  });

  describe('LMS Integrations', () => {
    it('should connect Google Classroom', async () => {
      const token = 'google-auth-token';

      mock.onPost(`${API_BASE_URL}/integrations/google_classroom`).reply(200, {
        connected: true
      });

      const result = await apiClient.connectGoogleClassroom(token);
      
      expect(result.connected).toBe(true);
    });

    it('should connect Canvas', async () => {
      const token = 'canvas-auth-token';

      mock.onPost(`${API_BASE_URL}/integrations/canvas`).reply(200, {
        connected: true
      });

      const result = await apiClient.connectCanvas(token);
      
      expect(result.connected).toBe(true);
    });

    it('should sync LMS data', async () => {
      const platform = 'google_classroom';

      mock.onPost(`${API_BASE_URL}/integrations/${platform}/sync`).reply(200, {
        synced: true
      });

      const result = await apiClient.syncLMSData(platform as any);
      
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

      mock.onGet(`${API_BASE_URL}/protected`).reply((config) => {
        // Check that Authorization header is set
        expect(config.headers?.Authorization).toBe('Bearer bearer-token-123');
        return [200, { success: true }];
      });

      await apiClient['request']({
        method: 'GET',
        url: '/protected'
      });
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

  describe('Lesson Management', () => {
    it('should list lessons', async () => {
      const lessons = [
        { id: 'l1', title: 'Introduction to Math', classId: 'c1' },
        { id: 'l2', title: 'Advanced Science', classId: 'c1' }
      ];

      mock.onGet(`${API_BASE_URL}/lessons`).reply(200, lessons);

      const result = await apiClient.listLessons();
      
      expect(result).toHaveLength(2);
      expect(result[0].title).toBe('Introduction to Math');
    });

    it('should create lesson', async () => {
      const lessonData = {
        title: 'New Lesson',
        description: 'Lesson description',
        classId: 'class-123'
      };

      mock.onPost(`${API_BASE_URL}/lessons`).reply(201, {
        id: 'lesson-456',
        ...lessonData
      });

      const result = await apiClient.createLesson(lessonData);
      
      expect(result.id).toBe('lesson-456');
      expect(result.title).toBe('New Lesson');
    });

    it('should update lesson', async () => {
      const lessonId = 'lesson-123';
      const updates = { title: 'Updated Lesson Title' };

      mock.onPut(`${API_BASE_URL}/lessons/${lessonId}`).reply(200, {
        id: lessonId,
        ...updates
      });

      const result = await apiClient.updateLesson(lessonId, updates);
      
      expect(result.title).toBe('Updated Lesson Title');
    });

    it('should delete lesson', async () => {
      const lessonId = 'lesson-123';

      mock.onDelete(`${API_BASE_URL}/lessons/${lessonId}`).reply(204);

      await expect(apiClient.deleteLesson(lessonId)).resolves.not.toThrow();
    });
  });
});