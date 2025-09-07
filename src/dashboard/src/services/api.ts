import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { API_BASE_URL, AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, API_TIMEOUT } from "../config";
import { store } from "../store";
import { addNotification } from "../store/slices/uiSlice";
import type {
  ApiResponse,
  AuthResponse,
  User,
  UserCreate,
  UserUpdate,
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
  ProgressPoint,
} from "../types/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    try {
      this.client = axios.create({
        baseURL: API_BASE_URL,
        timeout: API_TIMEOUT,
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (!this.client) {
        throw new Error("Failed to create axios client instance");
      }
    } catch (error) {
      console.error("Failed to initialize API client:", error);
      throw new Error(`API Client initialization failed: ${error}`);
    }

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for token refresh and error handling
    this.client.interceptors.response.use(
      (response) => {
        // Handle successful responses with notifications for important actions
        if (response.config.method && ['post', 'put', 'delete'].includes(response.config.method.toLowerCase())) {
          const url = response.config.url || '';
          let message = '';
          
          // Determine success message based on endpoint
          if (url.includes('/register')) {
            message = 'Registration successful! Welcome to ToolBoxAI.';
          } else if (url.includes('/login')) {
            message = 'Welcome back! Successfully logged in.';
          } else if (url.includes('/assessments') && response.config.method === 'post') {
            message = 'Assessment created successfully!';
          } else if (url.includes('/submit')) {
            message = 'Assessment submitted successfully!';
          } else if (url.includes('/messages') && response.config.method === 'post') {
            message = 'Message sent successfully!';
          } else if (url.includes('/consent')) {
            message = 'Consent recorded successfully!';
          }
          
          if (message) {
            store.dispatch(addNotification({
              type: 'success',
              message,
              autoHide: true,
            }));
          }
        }
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - Token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem(AUTH_TOKEN_KEY, response.accessToken);
              localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, response.refreshToken);
              originalRequest.headers.Authorization = `Bearer ${response.accessToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem(AUTH_TOKEN_KEY);
            localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
            store.dispatch(addNotification({
              type: 'error',
              message: 'Session expired. Please log in again.',
              autoHide: false,
            }));
            setTimeout(() => {
              window.location.href = "/login";
            }, 2000);
            return Promise.reject(refreshError);
          }
        }

        // Handle other errors with user-friendly messages
        let errorMessage = 'An unexpected error occurred. Please try again.';
        
        if (error.response) {
          const status = error.response.status;
          const data = error.response.data;
          
          // Extract error message from response
          if (data?.message) {
            errorMessage = data.message;
          } else if (data?.detail) {
            // Handle Pydantic validation errors (422)
            if (Array.isArray(data.detail)) {
              // Extract messages from validation error array
              const errors = data.detail.map((err: any) => 
                err.msg || err.message || 'Validation error'
              );
              errorMessage = errors.join(', ');
            } else if (typeof data.detail === 'string') {
              errorMessage = data.detail;
            } else {
              errorMessage = 'Validation error occurred';
            }
          } else if (data?.error) {
            errorMessage = data.error;
          } else {
            // Provide status-specific messages
            switch (status) {
              case 400:
                errorMessage = 'Invalid request. Please check your input.';
                break;
              case 403:
                errorMessage = 'You do not have permission to perform this action.';
                break;
              case 404:
                errorMessage = 'The requested resource was not found.';
                break;
              case 409:
                errorMessage = 'This action conflicts with existing data.';
                break;
              case 422:
                errorMessage = 'Validation error. Please check your input.';
                break;
              case 429:
                errorMessage = 'Too many requests. Please slow down.';
                break;
              case 500:
                errorMessage = 'Server error. Our team has been notified.';
                break;
              case 502:
              case 503:
                errorMessage = 'Service temporarily unavailable. Please try again later.';
                break;
            }
          }
        } else if (error.request) {
          // Request was made but no response received
          errorMessage = 'Unable to connect to the server. Please check your internet connection.';
        }

        // Dispatch error notification
        store.dispatch(addNotification({
          type: 'error',
          message: errorMessage,
          autoHide: false,
        }));

        return Promise.reject(error);
      }
    );
  }

  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    if (!this.client) {
      throw new Error("API client not initialized");
    }
    
    try {
      const response: AxiosResponse<T> = await this.client(config);
      
      // Handle 204 No Content responses (typically from DELETE operations)
      if (response.status === 204) {
        return undefined as unknown as T;
      }
      
      // Check if the response is already in the expected format (for auth endpoints)
      // Auth endpoints return data directly, not wrapped in ApiResponse
      if (response.data !== undefined) {
        return response.data as T;
      }
      
      // Only throw error if we expected data but got none
      if (config.method?.toUpperCase() !== 'DELETE') {
        throw new Error("No data in response");
      }
      
      return undefined as unknown as T;
    } catch (error) {
      console.error("API Error:", {
        error,
        config,
        clientInitialized: !!this.client,
        baseURL: API_BASE_URL,
      });
      throw error;
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>({
      method: "POST",
      url: "/auth/login",
      data: { email, password },
    });
  }

  async register(data: {
    email: string;
    password: string;
    displayName: string;
    role: string;
  }): Promise<AuthResponse> {
    // Map frontend fields to backend expected format
    const [firstName, ...lastNameParts] = data.displayName.split(' ');
    const lastName = lastNameParts.join(' ') || firstName;
    
    const backendData = {
      email: data.email,
      password: data.password,
      username: data.email.split('@')[0], // Generate username from email
      first_name: firstName,
      last_name: lastName,
      role: data.role,
    };
    
    const response = await this.request<any>({
      method: "POST",
      url: "/auth/register",
      data: backendData,
    });
    
    // Map backend response to frontend format
    return {
      accessToken: response.access_token || response.accessToken,
      refreshToken: response.refresh_token || response.refreshToken,
      expiresIn: response.expires_in || 3600, // Default to 1 hour if not provided
      user: {
        id: response.user.id,
        email: response.user.email,
        username: response.user.username,
        firstName: response.user.first_name || firstName,
        lastName: response.user.last_name || lastName,
        displayName: response.user.display_name || `${response.user.first_name} ${response.user.last_name}`,
        avatarUrl: response.user.avatar_url || response.user.avatarUrl,
        role: response.user.role,
        schoolId: response.user.school_id || response.user.schoolId,
        schoolName: response.user.school_name,
        classIds: response.user.class_ids || response.user.classIds || [],
        parentIds: response.user.parent_ids || [],
        childIds: response.user.child_ids || [],
        isActive: response.user.is_active ?? true,
        isVerified: response.user.is_verified ?? false,
        totalXP: response.user.total_xp || 0,
        level: response.user.level || 1,
        lastLogin: response.user.last_login,
        createdAt: response.user.created_at || new Date().toISOString(),
        updatedAt: response.user.updated_at || new Date().toISOString(),
        status: response.user.status || 'active',
      },
    };
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return this.request<AuthResponse>({
      method: "POST",
      url: "/auth/refresh",
      data: { refresh_token: refreshToken },
    });
  }

  async logout(): Promise<void> {
    return this.request<void>({
      method: "POST",
      url: "/auth/logout",
    });
  }

  // Dashboard
  async getDashboardOverview(role: string): Promise<DashboardOverview> {
    return this.request<DashboardOverview>({
      method: "GET",
      url: `/dashboard/overview/${role}`,
    });
  }

  async getWeeklyXP(studentId?: string): Promise<ProgressPoint[]> {
    return this.request<ProgressPoint[]>({
      method: "GET",
      url: "/analytics/weekly_xp",
      params: { studentId },
    });
  }

  async getSubjectMastery(studentId?: string): Promise<{ subject: string; mastery: number }[]> {
    return this.request<{ subject: string; mastery: number }[]>({
      method: "GET",
      url: "/analytics/subject_mastery",
      params: { studentId },
    });
  }

  // Lessons
  async listLessons(classId?: string): Promise<Lesson[]> {
    return this.request<Lesson[]>({
      method: "GET",
      url: "/lessons",
      params: { classId },
    });
  }

  async getLesson(id: string): Promise<Lesson> {
    return this.request<Lesson>({
      method: "GET",
      url: `/lessons/${id}`,
    });
  }

  async createLesson(data: Partial<Lesson>): Promise<Lesson> {
    return this.request<Lesson>({
      method: "POST",
      url: "/lessons",
      data,
    });
  }

  async updateLesson(id: string, data: Partial<Lesson>): Promise<Lesson> {
    return this.request<Lesson>({
      method: "PUT",
      url: `/lessons/${id}`,
      data,
    });
  }

  async deleteLesson(id: string): Promise<void> {
    return this.request<void>({
      method: "DELETE",
      url: `/lessons/${id}`,
    });
  }

  // Classes
  async listClasses(): Promise<ClassSummary[]> {
    return this.request<ClassSummary[]>({
      method: "GET",
      url: "/classes/",
    });
  }

  async getClass(id: string): Promise<ClassDetails> {
    return this.request<ClassDetails>({
      method: "GET",
      url: `/classes/${id}`,
    });
  }

  async createClass(data: Partial<ClassSummary>): Promise<ClassSummary> {
    return this.request<ClassSummary>({
      method: "POST",
      url: "/classes/",
      data,
    });
  }

  // Assessments
  async listAssessments(classId?: string): Promise<Assessment[]> {
    return this.request<Assessment[]>({
      method: "GET",
      url: "/assessments/",
      params: classId ? { class_id: classId } : undefined, // Transform to snake_case for backend
    });
  }

  async getAssessment(id: string): Promise<Assessment> {
    return this.request<Assessment>({
      method: "GET",
      url: `/assessments/${id}`,
    });
  }

  async createAssessment(data: Partial<Assessment>): Promise<Assessment> {
    // Transform camelCase to snake_case for backend
    const transformedData: any = {};
    if (data.title !== undefined) transformedData.title = data.title;
    if (data.lessonId !== undefined) transformedData.lesson_id = data.lessonId;
    if (data.classId !== undefined) transformedData.class_id = data.classId;
    if (data.type !== undefined) transformedData.type = data.type;
    // Ensure questions array is always included (backend requires it)
    transformedData.questions = data.questions || [];
    if (data.dueDate !== undefined) transformedData.due_date = data.dueDate;
    if (data.maxSubmissions !== undefined) transformedData.max_attempts = data.maxSubmissions;
    // Note: Assessment interface doesn't have description property
    if (data.status !== undefined) transformedData.status = data.status;
    
    return this.request<Assessment>({
      method: "POST",
      url: "/assessments/",
      data: transformedData,
    });
  }

  async submitAssessment(assessmentId: string, data: { answers: any; time_spent_minutes?: number }): Promise<AssessmentSubmission> {
    return this.request<AssessmentSubmission>({
      method: "POST",
      url: `/assessments/${assessmentId}/submit`,
      data,
    });
  }

  async updateAssessment(id: string, data: Partial<Assessment>): Promise<Assessment> {
    return this.request<Assessment>({
      method: "PUT",
      url: `/assessments/${id}`,
      data,
    });
  }

  async deleteAssessment(id: string): Promise<void> {
    return this.request<void>({
      method: "DELETE",
      url: `/assessments/${id}`,
    });
  }

  async getAssessmentSubmissions(assessmentId: string, studentId?: string): Promise<AssessmentSubmission[]> {
    return this.request<AssessmentSubmission[]>({
      method: "GET",
      url: `/assessments/${assessmentId}/submissions`,
      params: { student_id: studentId },
    });
  }

  async publishAssessment(assessmentId: string): Promise<Assessment> {
    return this.request<Assessment>({
      method: "PUT",
      url: `/assessments/${assessmentId}/publish`,
    });
  }

  // Student Progress
  async getStudentProgress(studentId: string): Promise<StudentProgress> {
    return this.request<StudentProgress>({
      method: "GET",
      url: `/progress/student/${studentId}`,
    });
  }

  async getClassProgress(classId: string): Promise<any> {
    return this.request<any>({
      method: "GET",
      url: `/progress/class/${classId}`,
    });
  }

  async getLessonAnalytics(lessonId: string): Promise<any> {
    return this.request<any>({
      method: "GET",
      url: `/progress/lesson/${lessonId}`,
    });
  }

  async updateProgress(lessonId: string, progressPercentage: number, timeSpentMinutes: number, score?: number): Promise<any> {
    return this.request<any>({
      method: "POST",
      url: `/progress/update`,
      params: { lesson_id: lessonId, progress_percentage: progressPercentage, time_spent_minutes: timeSpentMinutes, score },
    });
  }

  async getProgressAnalytics(filters?: { studentId?: string; classId?: string; subject?: string }): Promise<any> {
    return this.request<any>({
      method: "GET",
      url: `/progress/analytics`,
      params: filters,
    });
  }

  // Gamification
  async getStudentXP(studentId: string): Promise<{ xp: number; level: number }> {
    return this.request<{ xp: number; level: number }>({
      method: "GET",
      url: `/gamification/xp/${studentId}`,
    });
  }

  async addXP(studentId: string, amount: number, reason: string): Promise<XPTransaction> {
    return this.request<XPTransaction>({
      method: "POST",
      url: `/gamification/xp/${studentId}`,
      data: { amount, reason },
    });
  }

  async getBadges(studentId?: string): Promise<Badge[]> {
    return this.request<Badge[]>({
      method: "GET",
      url: "/gamification/badges",
      params: { studentId },
    });
  }

  async awardBadge(studentId: string, badgeId: string): Promise<Badge> {
    return this.request<Badge>({
      method: "POST",
      url: `/gamification/badges/award`,
      data: { studentId, badgeId },
    });
  }

  async getLeaderboard(classId?: string, timeframe?: "daily" | "weekly" | "monthly" | "all"): Promise<LeaderboardEntry[]> {
    return this.request<LeaderboardEntry[]>({
      method: "GET",
      url: "/gamification/leaderboard",
      params: { classId, timeframe },
    });
  }

  // Roblox Integration
  async listRobloxWorlds(lessonId?: string): Promise<RobloxWorld[]> {
    return this.request<RobloxWorld[]>({
      method: "GET",
      url: "/roblox/worlds",
      params: { lessonId },
    });
  }

  async pushLessonToRoblox(lessonId: string): Promise<{ jobId: string; status: string }> {
    return this.request<{ jobId: string; status: string }>({
      method: "POST",
      url: `/roblox/push/${lessonId}`,
    });
  }

  async getRobloxJoinUrl(classId: string): Promise<{ joinUrl: string }> {
    return this.request<{ joinUrl: string }>({
      method: "GET",
      url: `/roblox/join/${classId}`,
    });
  }

  // Messages
  async listMessages(folder?: string, filters?: { unread_only?: boolean; class_id?: string; search?: string }): Promise<Message[]> {
    return this.request<Message[]>({
      method: "GET",
      url: "/messages/",
      params: { folder, ...filters },
    });
  }

  async sendMessage(data: { subject: string; body: string; recipient_ids: string[]; class_id?: string; priority?: string }): Promise<Message> {
    return this.request<Message>({
      method: "POST",
      url: "/messages/",
      data,
    });
  }

  async getMessage(id: string): Promise<Message> {
    return this.request<Message>({
      method: "GET",
      url: `/messages/${id}`,
    });
  }

  async getMessageThread(threadId: string): Promise<any> {
    return this.request<any>({
      method: "GET",
      url: `/messages/thread/${threadId}`,
    });
  }

  async markMessageAsRead(id: string): Promise<void> {
    return this.request<void>({
      method: "PUT",
      url: `/messages/${id}/read`,
    });
  }

  async markMessageAsUnread(id: string): Promise<void> {
    return this.request<void>({
      method: "PUT",
      url: `/messages/${id}/unread`,
    });
  }

  async starMessage(id: string): Promise<void> {
    return this.request<void>({
      method: "PUT",
      url: `/messages/${id}/star`,
    });
  }

  async archiveMessage(id: string): Promise<void> {
    return this.request<void>({
      method: "PUT",
      url: `/messages/${id}/archive`,
    });
  }

  async deleteMessage(id: string, permanent?: boolean): Promise<void> {
    return this.request<void>({
      method: "DELETE",
      url: `/messages/${id}`,
      params: { permanent },
    });
  }

  async replyToMessage(id: string, data: { subject: string; body: string; recipient_ids: string[] }): Promise<Message> {
    return this.request<Message>({
      method: "POST",
      url: `/messages/${id}/reply`,
      data,
    });
  }

  async forwardMessage(id: string, data: { subject: string; body: string; recipient_ids: string[] }): Promise<Message> {
    return this.request<Message>({
      method: "POST",
      url: `/messages/${id}/forward`,
      data,
    });
  }

  async getMessageStats(): Promise<any> {
    return this.request<any>({
      method: "GET",
      url: "/messages/stats",
    });
  }

  // Compliance
  async getComplianceStatus(): Promise<ComplianceStatus> {
    return this.request<ComplianceStatus>({
      method: "GET",
      url: "/compliance/status",
    });
  }

  async recordConsent(type: "coppa" | "ferpa" | "gdpr", userId: string): Promise<void> {
    return this.request<void>({
      method: "POST",
      url: "/compliance/consent",
      data: { 
        consent_type: type,  // Backend expects 'consent_type' not 'type'
        granted: true,       // Backend requires this field
        details: {          // Optional additional details
          userId: userId,
          timestamp: new Date().toISOString()
        }
      },
    });
  }


  // LMS Integrations
  async connectGoogleClassroom(token: string): Promise<{ connected: boolean }> {
    return this.request<{ connected: boolean }>({
      method: "POST",
      url: "/integrations/google_classroom",
      data: { token },
    });
  }

  async connectCanvas(token: string): Promise<{ connected: boolean }> {
    return this.request<{ connected: boolean }>({
      method: "POST",
      url: "/integrations/canvas",
      data: { token },
    });
  }

  async syncLMSData(platform: "google_classroom" | "canvas"): Promise<{ synced: boolean }> {
    return this.request<{ synced: boolean }>({
      method: "POST",
      url: `/integrations/${platform}/sync`,
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export bound convenience functions to preserve 'this' context
export const login = apiClient.login.bind(apiClient);
export const register = apiClient.register.bind(apiClient);
export const refreshToken = apiClient.refreshToken.bind(apiClient);
export const logout = apiClient.logout.bind(apiClient);
export const getDashboardOverview = apiClient.getDashboardOverview.bind(apiClient);
export const getWeeklyXP = apiClient.getWeeklyXP.bind(apiClient);
export const getSubjectMastery = apiClient.getSubjectMastery.bind(apiClient);
export const listLessons = apiClient.listLessons.bind(apiClient);
export const getLesson = apiClient.getLesson.bind(apiClient);
export const createLesson = apiClient.createLesson.bind(apiClient);
export const updateLesson = apiClient.updateLesson.bind(apiClient);
export const deleteLesson = apiClient.deleteLesson.bind(apiClient);
export const listClasses = apiClient.listClasses.bind(apiClient);
export const getClass = apiClient.getClass.bind(apiClient);
export const createClass = apiClient.createClass.bind(apiClient);
export const listAssessments = apiClient.listAssessments.bind(apiClient);
export const getAssessment = apiClient.getAssessment.bind(apiClient);
export const createAssessment = apiClient.createAssessment.bind(apiClient);
export const submitAssessment = apiClient.submitAssessment.bind(apiClient);
export const getStudentProgress = apiClient.getStudentProgress.bind(apiClient);
export const getStudentXP = apiClient.getStudentXP.bind(apiClient);
export const addXP = apiClient.addXP.bind(apiClient);
export const getBadges = apiClient.getBadges.bind(apiClient);
export const awardBadge = apiClient.awardBadge.bind(apiClient);
export const getLeaderboard = apiClient.getLeaderboard.bind(apiClient);
export const listRobloxWorlds = apiClient.listRobloxWorlds.bind(apiClient);
export const pushLessonToRoblox = apiClient.pushLessonToRoblox.bind(apiClient);
export const getRobloxJoinUrl = apiClient.getRobloxJoinUrl.bind(apiClient);
export const getComplianceStatus = apiClient.getComplianceStatus.bind(apiClient);
export const recordConsent = apiClient.recordConsent.bind(apiClient);
export const listMessages = apiClient.listMessages.bind(apiClient);
export const sendMessage = apiClient.sendMessage.bind(apiClient);
export const connectGoogleClassroom = apiClient.connectGoogleClassroom.bind(apiClient);
export const connectCanvas = apiClient.connectCanvas.bind(apiClient);
export const syncLMSData = apiClient.syncLMSData.bind(apiClient);

// Additional API methods for Redux slices
// Assessment-related exports
export const updateAssessment = apiClient.updateAssessment.bind(apiClient);
export const deleteAssessment = apiClient.deleteAssessment.bind(apiClient);
export const getAssessmentSubmissions = apiClient.getAssessmentSubmissions.bind(apiClient);
export const publishAssessment = apiClient.publishAssessment.bind(apiClient);

export const gradeSubmission = async (submissionId: string, data: { score: number; feedback?: string }) => {
  return apiClient['request']<any>({
    method: 'POST',
    url: `/assessments/submissions/${submissionId}/grade`,
    data,
  });
};

// Message-related exports
export const getMessage = apiClient.getMessage.bind(apiClient);
export const getMessageThread = apiClient.getMessageThread.bind(apiClient);
export const markMessageAsRead = apiClient.markMessageAsRead.bind(apiClient);
export const markMessageAsUnread = apiClient.markMessageAsUnread.bind(apiClient);
export const starMessage = apiClient.starMessage.bind(apiClient);
export const archiveMessage = apiClient.archiveMessage.bind(apiClient);
export const deleteMessage = apiClient.deleteMessage.bind(apiClient);
export const replyToMessage = apiClient.replyToMessage.bind(apiClient);
export const forwardMessage = apiClient.forwardMessage.bind(apiClient);
export const getMessageStats = apiClient.getMessageStats.bind(apiClient);

export const markAsRead = apiClient.markMessageAsRead.bind(apiClient);

export const moveToFolder = async (messageId: string, folder: string) => {
  return apiClient['request']<any>({
    method: 'PUT',
    url: `/messages/${messageId}/move`,
    data: { folder },
  });
};

export const searchMessages = async (query: string) => {
  return apiClient['request']<any>({
    method: 'GET',
    url: `/messages/search`,
    params: { q: query },
  });
};

export const getUnreadCount = async () => {
  const response = await apiClient['request']<any>({
    method: 'GET',
    url: `/messages/unread-count`,
  });
  return response.count || 0;
};

// Progress-related exports  
export const getClassProgress = apiClient.getClassProgress.bind(apiClient);
export const getLessonAnalytics = apiClient.getLessonAnalytics.bind(apiClient);
export const updateProgress = apiClient.updateProgress.bind(apiClient);
export const getProgressAnalytics = apiClient.getProgressAnalytics.bind(apiClient);

export const recordAchievement = async (studentId: string, data: { badgeId: string; xpEarned: number }) => {
  return apiClient['request']<any>({
    method: 'POST',
    url: `/progress/student/${studentId}/achievement`,
    data,
  });
};

export const getSkillMastery = async (studentId: string, skillId: string) => {
  return apiClient['request']<any>({
    method: 'GET',
    url: `/progress/student/${studentId}/skill/${skillId}`,
  });
};

// ==================== Schools Management ====================

export interface SchoolCreate {
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone?: string;
  email?: string;
  principal_name?: string;
  district?: string;
  max_students: number;
  is_active: boolean;
}

export interface School extends SchoolCreate {
  id: string;
  student_count: number;
  teacher_count: number;
  class_count: number;
  created_at: string;
  updated_at: string;
}

export const listSchools = async (params?: {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  search?: string;
}) => {
  return apiClient['request']<School[]>({
    method: 'GET',
    url: `/schools/`,
    params,
  });
};

export const getSchool = async (schoolId: string) => {
  return apiClient['request']<School>({
    method: 'GET',
    url: `/schools/${schoolId}`,
  });
};

export const createSchool = async (data: SchoolCreate) => {
  return apiClient['request']<School>({
    method: 'POST',
    url: `/schools/`,
    data,
  });
};

export const updateSchool = async (schoolId: string, data: Partial<SchoolCreate>) => {
  return apiClient['request']<School>({
    method: 'PUT',
    url: `/schools/${schoolId}`,
    data,
  });
};

export const deleteSchool = async (schoolId: string) => {
  return apiClient['request']<void>({
    method: 'DELETE',
    url: `/schools/${schoolId}`,
  });
};

export const activateSchool = async (schoolId: string) => {
  return apiClient['request']<School>({
    method: 'POST',
    url: `/schools/${schoolId}/activate`,
  });
};

export const getSchoolStats = async (schoolId: string) => {
  return apiClient['request']<any>({
    method: 'GET',
    url: `/schools/${schoolId}/stats`,
  });
};

// Reports Management API
export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  type: string;
  category?: string;
  icon?: string;
  fields?: string[];
  filters?: any;
  default_format: string;
  is_popular: boolean;
  is_active: boolean;
}

export interface ReportGenerateRequest {
  name: string;
  type: 'progress' | 'attendance' | 'grades' | 'behavior' | 'assessment' | 'compliance' | 'gamification' | 'custom';
  format?: 'pdf' | 'excel' | 'csv' | 'html' | 'json';
  template_id?: string;
  filters?: any;
  parameters?: any;
  school_id?: string;
  class_id?: string;
  recipients?: string[];
  auto_email?: boolean;
}

export interface ReportScheduleRequest {
  name: string;
  description?: string;
  template_id: string;
  frequency: 'once' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date: string;
  end_date?: string;
  hour?: number;
  minute?: number;
  day_of_week?: number;
  day_of_month?: number;
  format?: 'pdf' | 'excel' | 'csv' | 'html' | 'json';
  filters?: any;
  parameters?: any;
  school_id?: string;
  class_id?: string;
  recipients?: string[];
  auto_email?: boolean;
}

export interface Report {
  id: string;
  name: string;
  type: string;
  format: string;
  status: string;
  template_id?: string;
  generated_by?: string;
  filters?: any;
  parameters?: any;
  school_id?: string;
  class_id?: string;
  file_path?: string;
  file_size?: number;
  generated_at?: string;
  generation_time?: number;
  error_message?: string;
  recipients?: string[];
  emailed_at?: string;
  row_count?: number;
  page_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface ReportSchedule {
  id: string;
  name: string;
  description?: string;
  template_id: string;
  frequency: string;
  start_date: string;
  end_date?: string;
  next_run?: string;
  last_run?: string;
  hour: number;
  minute: number;
  day_of_week?: number;
  day_of_month?: number;
  format: string;
  filters?: any;
  parameters?: any;
  school_id?: string;
  class_id?: string;
  recipients?: string[];
  auto_email: boolean;
  created_by?: string;
  is_active: boolean;
  failure_count: number;
  created_at: string;
  updated_at?: string;
}

export const listReportTemplates = async (params?: {
  popular_only?: boolean;
  category?: string;
  type?: string;
}) => {
  // Transform type to lowercase if provided
  const transformedParams = params ? {
    ...params,
    type: params.type?.toLowerCase(),
  } : undefined;
  
  return apiClient['request']<ReportTemplate[]>({
    method: 'GET',
    url: `/reports/templates`,
    params: transformedParams,
  });
};

export const listReports = async (params?: {
  skip?: number;
  limit?: number;
  status?: string;
  type?: string;
  school_id?: string;
  class_id?: string;
  generated_by_me?: boolean;
}) => {
  return apiClient['request']<Report[]>({
    method: 'GET',
    url: `/reports/`,
    params,
  });
};

export const getReport = async (reportId: string) => {
  return apiClient['request']<Report>({
    method: 'GET',
    url: `/reports/${reportId}`,
  });
};

export const generateReport = async (data: ReportGenerateRequest) => {
  // Transform enum values to lowercase for backend compatibility
  const transformedData = {
    ...data,
    type: data.type?.toLowerCase(),
    format: data.format?.toLowerCase() || 'pdf',
  };
  
  return apiClient['request']<Report>({
    method: 'POST',
    url: `/reports/generate`,
    data: transformedData,
  });
};

export const scheduleReport = async (data: ReportScheduleRequest) => {
  return apiClient['request']<ReportSchedule>({
    method: 'POST',
    url: `/reports/schedule`,
    data,
  });
};

export const emailReport = async (data: {
  report_id: string;
  recipients: string[];
  subject?: string;
  message?: string;
}) => {
  return apiClient['request']<{ message: string; recipients: string[] }>({
    method: 'POST',
    url: `/reports/email`,
    data,
  });
};

export const downloadReport = async (reportId: string) => {
  return apiClient['request']<any>({
    method: 'GET',
    url: `/reports/${reportId}/download`,
  });
};

export const deleteReport = async (reportId: string) => {
  return apiClient['request']<void>({
    method: 'DELETE',
    url: `/reports/${reportId}`,
  });
};

export const listScheduledReports = async (params?: {
  skip?: number;
  limit?: number;
  active_only?: boolean;
}) => {
  return apiClient['request']<ReportSchedule[]>({
    method: 'GET',
    url: `/reports/schedules/`,
    params,
  });
};

export const cancelScheduledReport = async (scheduleId: string) => {
  return apiClient['request']<ReportSchedule>({
    method: 'PUT',
    url: `/reports/schedules/${scheduleId}/cancel`,
  });
};

export const getReportStatistics = async () => {
  return apiClient['request']<{
    reports_generated: number;
    reports_this_month: number;
    scheduled_reports: number;
    next_scheduled_time?: string;
    total_recipients: number;
    storage_used_bytes: number;
    storage_used_gb: number;
  }>({
    method: 'GET',
    url: `/reports/stats/overview`,
  });
};

// Users Management API
export const listUsers = async (params?: {
  skip?: number;
  limit?: number;
  role?: string;
  school_id?: string;
  is_active?: boolean;
  search?: string;
}) => {
  return apiClient['request']<User[]>({
    method: 'GET',
    url: `/users/`,
    params,
  });
};

export const getUser = async (userId: string) => {
  return apiClient['request']<User>({
    method: 'GET',
    url: `/users/${userId}`,
  });
};

export const createUser = async (data: UserCreate) => {
  // Transform camelCase to snake_case for backend
  const transformedData = {
    email: data.email,
    username: data.username,
    password: data.password,
    first_name: data.firstName,
    last_name: data.lastName,
    display_name: data.displayName,
    role: data.role,
    school_id: data.schoolId,
    language: data.language,
    timezone: data.timezone,
  };
  
  return apiClient['request']<User>({
    method: 'POST',
    url: `/users/`,
    data: transformedData,
  });
};

export const updateUser = async (userId: string, data: UserUpdate) => {
  // Transform camelCase to snake_case for backend
  const transformedData: any = {};
  if (data.email !== undefined) transformedData.email = data.email;
  if (data.username !== undefined) transformedData.username = data.username;
  if (data.password !== undefined) transformedData.password = data.password;
  if (data.firstName !== undefined) transformedData.first_name = data.firstName;
  if (data.lastName !== undefined) transformedData.last_name = data.lastName;
  if (data.displayName !== undefined) transformedData.display_name = data.displayName;
  if (data.role !== undefined) transformedData.role = data.role;
  if (data.schoolId !== undefined) transformedData.school_id = data.schoolId;
  if (data.isActive !== undefined) transformedData.is_active = data.isActive;
  
  return apiClient['request']<User>({
    method: 'PUT',
    url: `/users/${userId}`,
    data: transformedData,
  });
};

export const deleteUser = async (userId: string) => {
  return apiClient['request']<void>({
    method: 'DELETE',
    url: `/users/${userId}`,
  });
};

export const suspendUser = async (userId: string) => {
  return apiClient['request']<User>({
    method: 'PUT',
    url: `/users/${userId}/suspend`,
  });
};

export const getMyProfile = async () => {
  return apiClient['request']<User>({
    method: 'GET',
    url: `/users/me/profile`,
  });
};