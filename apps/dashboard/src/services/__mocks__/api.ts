/**
 * Mock API Service for Testing
 *
 * This provides a complete mock implementation of the API service
 * that prevents real network calls and axios serialization issues
 */

import { vi } from 'vitest';

// Mock login function
export const login = vi.fn(async (email: string, password: string) => {
  // Simulate successful login
  if (email === 'test@example.com' && password === 'password123') {
    return {
      accessToken: 'mock-jwt-token',
      refreshToken: 'mock-refresh-token',
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'test',
        displayName: 'Test User',
        role: 'student',
        schoolId: 'school-1',
        classIds: ['class-1'],
        avatarUrl: null,
      }
    };
  }

  // Simulate admin login
  if (email === 'admin@toolboxai.com' && password === 'Admin123!') {
    return {
      accessToken: 'mock-jwt-token',
      refreshToken: 'mock-refresh-token',
      user: {
        id: '1',
        email: 'admin@toolboxai.com',
        username: 'admin',
        displayName: 'Admin User',
        role: 'admin',
        schoolId: 'school-1',
        classIds: [],
        avatarUrl: null,
      }
    };
  }

  // Simulate invalid credentials
  if (email === 'wrong@example.com') {
    throw new Error('Invalid credentials');
  }

  // Default success response
  return {
    accessToken: 'mock-jwt-token',
    refreshToken: 'mock-refresh-token',
    user: {
      id: '1',
      email,
      username: email.split('@')[0],
      displayName: 'Test User',
      role: 'student',
      schoolId: 'school-1',
      classIds: ['class-1'],
      avatarUrl: null,
    }
  };
});

// Mock register function
export const register = vi.fn(async (data: any) => {
  return {
    accessToken: 'mock-jwt-token',
    refreshToken: 'mock-refresh-token',
    user: {
      id: '2',
      email: data.email,
      username: data.username || data.email.split('@')[0],
      displayName: `${data.firstName} ${data.lastName}`,
      role: data.role || 'student',
      schoolId: 'school-1',
      classIds: [],
      avatarUrl: null,
    }
  };
});

// Mock the API class and all its methods
class MockApiClient {
  async login(email: string, password: string) {
    // Simulate successful login
    if (email === 'test@example.com' && password === 'password123') {
      return {
        accessToken: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token',
        user: {
          id: '1',
          email: 'test@example.com',
          username: 'test',
          firstName: 'Test',
          lastName: 'User',
          role: 'student',
        }
      };
    }

    // Simulate invalid credentials
    if (email === 'wrong@example.com') {
      throw new Error('Invalid email or password');
    }

    // Default success response
    return {
      accessToken: 'mock-jwt-token',
      refreshToken: 'mock-refresh-token',
      user: {
        id: '1',
        email,
        username: email.split('@')[0],
        firstName: 'Test',
        lastName: 'User',
        role: 'student',
      }
    };
  }

  async register(data: any) {
    return {
      accessToken: 'mock-jwt-token',
      refreshToken: 'mock-refresh-token',
      user: {
        id: '2',
        email: data.email,
        username: data.email.split('@')[0],
        firstName: data.displayName?.split(' ')[0] || 'New',
        lastName: data.displayName?.split(' ')[1] || 'User',
        role: data.role || 'student',
      }
    };
  }

  async logout() {
    return { success: true };
  }

  async refreshToken(refreshToken: string) {
    return {
      accessToken: 'new-mock-jwt-token',
      refreshToken: 'new-mock-refresh-token',
    };
  }

  async forgotPassword(email: string) {
    return { message: 'Password reset email sent' };
  }

  async resetPassword(token: string, password: string) {
    return { message: 'Password reset successful' };
  }

  // Dashboard methods
  async getDashboardOverview() {
    return {
      totalStudents: 150,
      totalTeachers: 12,
      totalClasses: 8,
      activeUsers: 45,
      recentActivities: [],
      upcomingAssessments: [],
    };
  }

  async listClasses() {
    return [
      {
        id: 'class-1',
        name: 'Advanced Mathematics',
        grade_level: 10,
        student_count: 25,
        schedule: 'Mon, Wed, Fri 9:00 AM',
        average_progress: 0.85,
        next_lesson: 'Calculus Introduction',
        is_online: true,
      },
      {
        id: 'class-2',
        name: 'Biology Fundamentals',
        grade_level: 9,
        student_count: 30,
        schedule: 'Tue, Thu 10:30 AM',
        average_progress: 0.72,
        next_lesson: 'Cell Structure',
        is_online: false,
      }
    ];
  }

  async getClass(id: string) {
    return {
      id,
      name: 'Math 101',
      description: 'Introduction to Mathematics',
      teacherId: '1',
      students: [],
      assignments: [],
      schedule: 'Mon, Wed, Fri 10:00 AM',
    };
  }

  async createClass(data: any) {
    return {
      id: '3',
      ...data,
      studentCount: 0,
    };
  }

  async updateClass(id: string, data: any) {
    return {
      id,
      ...data,
    };
  }

  async deleteClass(id: string) {
    return { success: true };
  }

  // Assessment methods
  async getAssessments() {
    return [
      {
        id: '1',
        title: 'Quiz 1',
        type: 'quiz',
        status: 'published',
        dueDate: '2025-01-01',
        questions: [],
      }
    ];
  }

  async createAssessment(data: any) {
    return {
      id: '2',
      ...data,
      status: 'draft',
    };
  }

  async submitAssessment(assessmentId: string, data: any) {
    return {
      id: '1',
      assessmentId,
      score: 85,
      submitted: true,
    };
  }

  // Messages
  async getMessages() {
    return [];
  }

  async sendMessage(data: any) {
    return {
      id: '1',
      ...data,
      sentAt: new Date().toISOString(),
    };
  }

  // Progress
  async getStudentProgress(studentId?: string) {
    return {
      overallProgress: 75,
      completedLessons: 15,
      averageScore: 82.5,
      weeklyData: [],
    };
  }

  // Compliance
  async getComplianceStatus() {
    return {
      coppa: { compliant: true, lastAudit: '2025-01-01' },
      ferpa: { compliant: true, lastAudit: '2025-01-01' },
      gdpr: { compliant: false, issues: ['Missing privacy policy update'] },
    };
  }

  // Users
  async getUsers() {
    return [];
  }

  async createUser(data: any) {
    return {
      id: '3',
      ...data,
    };
  }

  async updateUser(id: string, data: any) {
    return {
      id,
      ...data,
    };
  }

  async deleteUser(id: string) {
    return { success: true };
  }

  // Leaderboard
  async getLeaderboard() {
    return [];
  }

  // Settings
  async updateSettings(data: any) {
    return {
      ...data,
      updated: true,
    };
  }
}

// Create a singleton instance
const apiClient = new MockApiClient();

// Export both the class and instance
export { MockApiClient as ApiClient };
export default apiClient;

// Export individual functions that match the real API
export const listClasses = vi.fn(apiClient.listClasses.bind(apiClient));
export const logout = vi.fn(apiClient.logout.bind(apiClient));
export const refreshToken = vi.fn(apiClient.refreshToken.bind(apiClient));
export const forgotPassword = vi.fn(apiClient.forgotPassword.bind(apiClient));
export const resetPassword = vi.fn(apiClient.resetPassword.bind(apiClient));
export const getDashboardOverview = vi.fn(apiClient.getDashboardOverview.bind(apiClient));
export const getClass = vi.fn(apiClient.getClass.bind(apiClient));
export const createClass = vi.fn(apiClient.createClass.bind(apiClient));
export const updateClass = vi.fn(apiClient.updateClass.bind(apiClient));
export const deleteClass = vi.fn(apiClient.deleteClass.bind(apiClient));
export const getAssessments = vi.fn(apiClient.getAssessments.bind(apiClient));
export const createAssessment = vi.fn(apiClient.createAssessment.bind(apiClient));
export const submitAssessment = vi.fn(apiClient.submitAssessment.bind(apiClient));
export const getMessages = vi.fn(apiClient.getMessages.bind(apiClient));
export const sendMessage = vi.fn(apiClient.sendMessage.bind(apiClient));
export const getStudentProgress = vi.fn(apiClient.getStudentProgress.bind(apiClient));
export const getComplianceStatus = vi.fn(apiClient.getComplianceStatus.bind(apiClient));
export const getUsers = vi.fn(apiClient.getUsers.bind(apiClient));
export const createUser = vi.fn(apiClient.createUser.bind(apiClient));
export const updateUser = vi.fn(apiClient.updateUser.bind(apiClient));
export const deleteUser = vi.fn(apiClient.deleteUser.bind(apiClient));
export const getLeaderboard = vi.fn(apiClient.getLeaderboard.bind(apiClient));
export const updateSettings = vi.fn(apiClient.updateSettings.bind(apiClient));

// Additional methods used by tests
export const listAssessments = vi.fn(apiClient.getAssessments.bind(apiClient));
export const getAssessmentStats = vi.fn(() => Promise.resolve({
  total: 10,
  completed: 5,
  pending: 3,
  inProgress: 2,
  averageScore: 82.5
}));
export const listMessages = vi.fn(apiClient.getMessages.bind(apiClient));
export const getMessageFolders = vi.fn(() => Promise.resolve([
  { id: 'inbox', name: 'Inbox', count: 5 },
  { id: 'sent', name: 'Sent', count: 3 },
  { id: 'drafts', name: 'Drafts', count: 1 },
  { id: 'trash', name: 'Trash', count: 0 }
]));
export const updateProfile = vi.fn((data) => Promise.resolve({ ...data, updated: true }));
export const updatePassword = vi.fn(() => Promise.resolve({ success: true }));
export const updateNotificationSettings = vi.fn((settings) => Promise.resolve(settings));
export const updatePrivacySettings = vi.fn((settings) => Promise.resolve(settings));
export const getActivityLogs = vi.fn(() => Promise.resolve([]));
export const enable2FA = vi.fn(() => Promise.resolve({ qrCode: 'mock-qr', secret: 'mock-secret' }));
export const disable2FA = vi.fn(() => Promise.resolve({ success: true }));
export const exportData = vi.fn(() => Promise.resolve({ url: 'mock-download-url' }));
export const deleteAccount = vi.fn(() => Promise.resolve({ success: true }));