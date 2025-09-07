import { UserRole } from "./roles";

// User & Authentication
export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  displayName: string;
  avatarUrl?: string;
  role: UserRole;
  schoolId?: string;
  schoolName?: string;
  classIds?: string[];
  parentIds?: string[]; // For students
  childIds?: string[]; // For parents
  isActive: boolean;
  isVerified: boolean;
  totalXP: number;
  level: number;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  status: "active" | "suspended" | "pending";
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  displayName?: string;
  role: string;
  schoolId?: string;
  language?: string;
  timezone?: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
  password?: string;
  firstName?: string;
  lastName?: string;
  displayName?: string;
  role?: string;
  schoolId?: string;
  isActive?: boolean;
  language?: string;
  timezone?: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Lessons
export interface Lesson {
  id: string;
  title: string;
  description: string;
  subject:
    | "Math"
    | "Science"
    | "Language"
    | "Arts"
    | "Technology"
    | "Social Studies"
    | "Physical Education"
    | "Life Skills";
  status: "draft" | "published" | "archived";
  teacherId: string;
  classIds: string[];
  robloxWorldId?: string;
  content: any;
  createdAt: string;
  updatedAt: string;
}

// Classes
export interface ClassSummary {
  id: string;
  name: string;
  grade: number;
  teacherId: string;
  studentCount: number;
  averageXP: number;
  schedule?: string;
  createdAt: string;
}

export interface ClassDetails extends ClassSummary {
  students: Student[];
  lessons: Lesson[];
  assessments: Assessment[];
}

// Students
export interface Student {
  id: string;
  userId: string;
  displayName: string;
  avatarUrl?: string;
  xp: number;
  level: number;
  badges: Badge[];
  rank?: number;
  streakDays: number;
  lastActive: string;
}

// Gamification
export interface Badge {
  id: string;
  name: string;
  description: string;
  imageUrl: string;
  category: "achievement" | "milestone" | "special" | "seasonal";
  rarity: "common" | "rare" | "epic" | "legendary";
  earnedAt?: string;
  progress?: number;
  maxProgress?: number;
}

export interface XPTransaction {
  id: string;
  studentId: string;
  amount: number;
  reason: string;
  source: "lesson" | "assessment" | "achievement" | "bonus";
  timestamp: string;
}

export interface LeaderboardEntry {
  rank: number;
  studentId: string;
  displayName: string;
  avatarUrl?: string;
  xp: number;
  level: number;
  badgeCount: number;
  change: number; // Position change from last week
}

// Assessments
export interface Assessment {
  id: string;
  title: string;
  lessonId?: string;
  classId: string;
  type: "quiz" | "test" | "assignment" | "project";
  questions: Question[];
  dueDate?: string;
  status: "draft" | "active" | "closed" | "graded";
  averageScore?: number;
  submissions: number;
  maxSubmissions: number;
}

export interface Question {
  id: string;
  type: "multiple_choice" | "true_false" | "short_answer" | "essay";
  question: string;
  options?: string[];
  correctAnswer?: string | number;
  points: number;
}

export interface AssessmentSubmission {
  id: string;
  assessmentId: string;
  studentId: string;
  answers: any[];
  score?: number;
  feedback?: string;
  submittedAt: string;
  gradedAt?: string;
}

// Progress & Analytics
export interface ProgressPoint {
  x: string; // Date or label
  y: number; // Value
}

export interface StudentProgress {
  studentId: string;
  subjects: SubjectProgress[];
  overallMastery: number;
  weeklyXP: ProgressPoint[];
  monthlyProgress: ProgressPoint[];
  strengths: string[];
  weaknesses: string[];
}

export interface SubjectProgress {
  subject: string;
  mastery: number;
  lessonsCompleted: number;
  totalLessons: number;
  averageScore: number;
  trend: "improving" | "stable" | "declining";
}

// Compliance
export interface ComplianceStatus {
  coppa: ComplianceCheck;
  ferpa: ComplianceCheck;
  gdpr: ComplianceCheck;
  overallStatus: "compliant" | "warning" | "critical";
  lastAudit: string;
  nextAudit: string;
}

export interface ComplianceCheck {
  status: "compliant" | "warning" | "critical";
  issues: string[];
  lastChecked: string;
  recommendations: string[];
}

// Notifications
export interface Notification {
  id: string;
  userId: string;
  type: "info" | "warning" | "success" | "error";
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  createdAt: string;
}

// Dashboard Overview
export interface DashboardOverview {
  role: UserRole;
  metrics: DashboardMetrics;
  recentActivity: Activity[];
  upcomingEvents: Event[];
  notifications: Notification[];
}

export interface DashboardMetrics {
  xp?: number;
  level?: number;
  badges?: number;
  activeClasses?: number;
  totalStudents?: number;
  totalTeachers?: number;
  compliance?: "ok" | "warning" | "critical";
  averageProgress?: number;
}

export interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  userId?: string;
  metadata?: any;
}

export interface Event {
  id: string;
  title: string;
  type: "lesson" | "assessment" | "meeting" | "deadline";
  date: string;
  classId?: string;
  description?: string;
}

// Roblox Integration
export interface RobloxWorld {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  lessonId: string;
  placeId: string;
  universeId: string;
  maxPlayers: number;
  isActive: boolean;
  joinUrl?: string;
}

// Messages
export interface Message {
  id: string;
  fromUserId: string;
  toUserId: string;
  subject: string;
  content: string;
  read: boolean;
  attachments?: string[];
  sentAt: string;
  readAt?: string;
}

// Missions & Challenges
export interface Mission {
  id: string;
  title: string;
  description: string;
  type: "daily" | "weekly" | "monthly" | "special" | "custom";
  category: "academic" | "social" | "creativity" | "physical" | "community";
  xpReward: number;
  badgeReward?: string;
  requirements: MissionRequirement[];
  startDate?: string;
  endDate?: string;
  isActive: boolean;
  isRepeatable: boolean;
  maxCompletions?: number;
  difficulty: "easy" | "medium" | "hard" | "expert";
  imageUrl?: string;
  createdBy: string;
  createdAt: string;
}

export interface MissionRequirement {
  id: string;
  type: "lesson_complete" | "assessment_score" | "xp_earned" | "badge_earned" | 
        "attendance" | "social_interaction" | "time_spent" | "custom";
  target: number;
  current?: number;
  description: string;
  metadata?: any;
}

export interface MissionProgress {
  id: string;
  missionId: string;
  studentId: string;
  status: "not_started" | "in_progress" | "completed" | "claimed";
  startedAt?: string;
  completedAt?: string;
  claimedAt?: string;
  progress: number; // 0-100
  requirementsProgress: {
    requirementId: string;
    current: number;
    target: number;
    completed: boolean;
  }[];
  completionCount: number; // For repeatable missions
}

export interface Challenge {
  id: string;
  title: string;
  description: string;
  type: "speed" | "accuracy" | "creativity" | "collaboration" | "endurance";
  classId?: string; // null for school-wide challenges
  participants: string[];
  startTime: string;
  endTime: string;
  rules: string[];
  prizes: {
    position: number;
    xpReward: number;
    badgeId?: string;
    customReward?: string;
  }[];
  leaderboard?: ChallengeLeaderboard[];
  status: "upcoming" | "active" | "completed";
  createdBy: string;
  createdAt: string;
}

export interface ChallengeLeaderboard {
  rank: number;
  studentId: string;
  displayName: string;
  score: number;
  submittedAt: string;
  metadata?: any;
}

// Rewards (moved from separate definition)
export interface Reward {
  id: string;
  name: string;
  description: string;
  cost: number;
  category: "digital" | "physical" | "experience" | "privilege";
  imageUrl?: string;
  stock?: number;
  isActive: boolean;
  requirements?: {
    level?: number;
    badges?: string[];
  };
  rarity: "common" | "rare" | "epic" | "legendary";
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface RewardRedemption {
  id: string;
  rewardId: string;
  studentId: string;
  redeemedAt: string;
  status: "pending" | "approved" | "delivered" | "rejected";
  notes?: string;
  approvedBy?: string;
  approvedAt?: string;
}

// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  pagination?: {
    page: number;
    perPage: number;
    total: number;
    pages: number;
  };
}