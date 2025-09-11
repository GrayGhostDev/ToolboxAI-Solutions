import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { API_BASE_URL, AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, API_TIMEOUT } from "../config";
import type {
  ApiResponse,
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

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

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
            window.location.href = "/login";
          }
        }

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
      // Check if the response is already in the expected format (for auth endpoints)
      // Auth endpoints return data directly, not wrapped in ApiResponse
      if (response.data) {
        return response.data as T;
      }
      throw new Error("No data in response");
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
    return this.request<AuthResponse>({
      method: "POST",
      url: "/auth/register",
      data,
    });
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return this.request<AuthResponse>({
      method: "POST",
      url: "/auth/refresh",
      data: { refreshToken },
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
      url: "/classes",
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
      url: "/classes",
      data,
    });
  }

  // Assessments
  async listAssessments(classId?: string): Promise<Assessment[]> {
    return this.request<Assessment[]>({
      method: "GET",
      url: "/assessments",
      params: { classId },
    });
  }

  async getAssessment(id: string): Promise<Assessment> {
    return this.request<Assessment>({
      method: "GET",
      url: `/assessments/${id}`,
    });
  }

  async createAssessment(data: Partial<Assessment>): Promise<Assessment> {
    return this.request<Assessment>({
      method: "POST",
      url: "/assessments",
      data,
    });
  }

  async submitAssessment(data: Partial<AssessmentSubmission>): Promise<AssessmentSubmission> {
    return this.request<AssessmentSubmission>({
      method: "POST",
      url: "/assessments/submit",
      data,
    });
  }

  // Student Progress
  async getStudentProgress(studentId: string): Promise<StudentProgress> {
    return this.request<StudentProgress>({
      method: "GET",
      url: `/students/${studentId}/progress`,
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
      data: { type, userId },
    });
  }

  // Messages
  async listMessages(userId: string): Promise<Message[]> {
    return this.request<Message[]>({
      method: "GET",
      url: "/messages",
      params: { userId },
    });
  }

  async sendMessage(data: Partial<Message>): Promise<Message> {
    return this.request<Message>({
      method: "POST",
      url: "/messages",
      data,
    });
  }

  async markMessageRead(id: string): Promise<void> {
    return this.request<void>({
      method: "PUT",
      url: `/messages/${id}/read`,
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
export const markMessageRead = apiClient.markMessageRead.bind(apiClient);
export const connectGoogleClassroom = apiClient.connectGoogleClassroom.bind(apiClient);
export const connectCanvas = apiClient.connectCanvas.bind(apiClient);
export const syncLMSData = apiClient.syncLMSData.bind(apiClient);