/**
 * Mock Data Factories
 * 
 * Factory functions for generating test data for the ToolBoxAI Dashboard.
 */

import { vi } from 'vitest';

// ============================================================================
// USER DATA
// ============================================================================

export interface MockUser {
  id: string
  userId?: string
  username: string
  email: string
  role: 'admin' | 'teacher' | 'student' | 'parent'
  firstName: string
  lastName: string
  displayName?: string
  avatarUrl?: string
  isAuthenticated?: boolean
  classIds?: string[]
  gradeLevel?: number
  schoolId?: string
  createdAt?: string
  updatedAt?: string
}

export function createMockUser(overrides: Partial<MockUser> = {}): MockUser {
  const id = overrides.id || `user-${Math.random().toString(36).substr(2, 9)}`;
  const firstName = overrides.firstName || 'John';
  const lastName = overrides.lastName || 'Doe';
  
  return {
    id,
    userId: id,
    username: overrides.username || 'johndoe',
    email: overrides.email || 'john.doe@example.com',
    role: overrides.role || 'student',
    firstName,
    lastName,
    displayName: overrides.displayName || `${firstName} ${lastName}`,
    avatarUrl: overrides.avatarUrl || '',
    isAuthenticated: overrides.isAuthenticated ?? true,
    classIds: overrides.classIds || [],
    gradeLevel: overrides.gradeLevel,
    schoolId: overrides.schoolId || 'school-1',
    createdAt: overrides.createdAt || new Date().toISOString(),
    updatedAt: overrides.updatedAt || new Date().toISOString(),
    ...overrides,
  };
}

// ============================================================================
// CLASS DATA
// ============================================================================

export interface MockClass {
  id: string
  name: string
  subject: string
  gradeLevel: number
  teacherId: string
  teacherName?: string
  studentIds: string[]
  studentCount?: number
  schedule?: string
  room?: string
  description?: string
  createdAt?: string
  updatedAt?: string
}

export function createMockClass(overrides: Partial<MockClass> = {}): MockClass {
  return {
    id: overrides.id || `class-${Math.random().toString(36).substr(2, 9)}`,
    name: overrides.name || 'Mathematics 101',
    subject: overrides.subject || 'Mathematics',
    gradeLevel: overrides.gradeLevel || 5,
    teacherId: overrides.teacherId || 'teacher-1',
    teacherName: overrides.teacherName || 'Ms. Smith',
    studentIds: overrides.studentIds || [],
    studentCount: overrides.studentCount || overrides.studentIds?.length || 25,
    schedule: overrides.schedule || 'MWF 9:00-10:00',
    room: overrides.room || 'Room 101',
    description: overrides.description || 'Introduction to basic mathematics',
    createdAt: overrides.createdAt || new Date().toISOString(),
    updatedAt: overrides.updatedAt || new Date().toISOString(),
    ...overrides,
  };
}

// ============================================================================
// LESSON DATA
// ============================================================================

export interface MockLesson {
  id: string
  title: string
  subject: string
  gradeLevel: number
  description: string
  content: string
  duration: number // in minutes
  objectives: string[]
  materials: string[]
  classId?: string
  teacherId?: string
  status: 'draft' | 'published' | 'archived'
  createdAt?: string
  updatedAt?: string
}

export function createMockLesson(overrides: Partial<MockLesson> = {}): MockLesson {
  return {
    id: overrides.id || `lesson-${Math.random().toString(36).substr(2, 9)}`,
    title: overrides.title || 'Introduction to Fractions',
    subject: overrides.subject || 'Mathematics',
    gradeLevel: overrides.gradeLevel || 5,
    description: overrides.description || 'Learn the basics of fractions',
    content: overrides.content || 'Lesson content goes here...',
    duration: overrides.duration || 45,
    objectives: overrides.objectives || ['Understand fractions', 'Add simple fractions'],
    materials: overrides.materials || ['Textbook', 'Worksheet'],
    classId: overrides.classId,
    teacherId: overrides.teacherId,
    status: overrides.status || 'published',
    createdAt: overrides.createdAt || new Date().toISOString(),
    updatedAt: overrides.updatedAt || new Date().toISOString(),
    ...overrides,
  };
}

// ============================================================================
// ASSESSMENT DATA
// ============================================================================

export interface MockAssessment {
  id: string
  title: string
  type: 'quiz' | 'test' | 'assignment' | 'project'
  subject: string
  gradeLevel: number
  questions: MockQuestion[]
  duration?: number // in minutes
  totalPoints: number
  passingScore: number
  classId?: string
  dueDate?: string
  status: 'draft' | 'published' | 'closed'
  createdAt?: string
  updatedAt?: string
}

export interface MockQuestion {
  id: string
  question: string
  type: 'multiple-choice' | 'true-false' | 'short-answer' | 'essay'
  options?: string[]
  correctAnswer?: string | number
  points: number
}

export function createMockQuestion(overrides: Partial<MockQuestion> = {}): MockQuestion {
  return {
    id: overrides.id || `question-${Math.random().toString(36).substr(2, 9)}`,
    question: overrides.question || 'What is 2 + 2?',
    type: overrides.type || 'multiple-choice',
    options: overrides.options || ['3', '4', '5', '6'],
    correctAnswer: overrides.correctAnswer ?? 1,
    points: overrides.points || 10,
    ...overrides,
  };
}

export function createMockAssessment(overrides: Partial<MockAssessment> = {}): MockAssessment {
  const questions = overrides.questions || [
    createMockQuestion(),
    createMockQuestion({ question: 'What is 3 + 3?', correctAnswer: 2 }),
  ];
  
  return {
    id: overrides.id || `assessment-${Math.random().toString(36).substr(2, 9)}`,
    title: overrides.title || 'Math Quiz 1',
    type: overrides.type || 'quiz',
    subject: overrides.subject || 'Mathematics',
    gradeLevel: overrides.gradeLevel || 5,
    questions,
    duration: overrides.duration || 30,
    totalPoints: overrides.totalPoints || questions.reduce((sum, q) => sum + q.points, 0),
    passingScore: overrides.passingScore || 70,
    classId: overrides.classId,
    dueDate: overrides.dueDate || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    status: overrides.status || 'published',
    createdAt: overrides.createdAt || new Date().toISOString(),
    updatedAt: overrides.updatedAt || new Date().toISOString(),
    ...overrides,
  };
}

// ============================================================================
// GAMIFICATION DATA
// ============================================================================

export interface MockBadge {
  id: string
  name: string
  description: string
  icon: string
  category: string
  xpReward: number
  unlockedAt?: string
}

export function createMockBadge(overrides: Partial<MockBadge> = {}): MockBadge {
  return {
    id: overrides.id || `badge-${Math.random().toString(36).substr(2, 9)}`,
    name: overrides.name || 'Problem Solver',
    description: overrides.description || 'Solved 10 math problems',
    icon: overrides.icon || '🏆',
    category: overrides.category || 'achievement',
    xpReward: overrides.xpReward || 100,
    unlockedAt: overrides.unlockedAt,
    ...overrides,
  };
}

export interface MockLeaderboardEntry {
  rank: number
  userId: string
  studentId?: string
  displayName: string
  avatarUrl?: string
  className: string
  level: number
  xp: number
  badgeCount: number
  streakDays: number
  change: number
}

export function createMockLeaderboardEntry(overrides: Partial<MockLeaderboardEntry> = {}): MockLeaderboardEntry {
  return {
    rank: overrides.rank || 1,
    userId: overrides.userId || 'user-1',
    studentId: overrides.studentId || overrides.userId || 'user-1',
    displayName: overrides.displayName || 'John Doe',
    avatarUrl: overrides.avatarUrl || '',
    className: overrides.className || 'Class 5A',
    level: overrides.level || Math.floor((overrides.xp || 1000) / 100),
    xp: overrides.xp || 1000,
    badgeCount: overrides.badgeCount || 5,
    streakDays: overrides.streakDays || 7,
    change: overrides.change || 0,
    ...overrides,
  };
}

// ============================================================================
// MESSAGE DATA
// ============================================================================

export interface MockMessage {
  id: string
  subject: string
  content: string
  senderId: string
  senderName: string
  recipientId: string
  recipientName: string
  timestamp: string
  read: boolean
  type: 'message' | 'announcement' | 'notification'
  attachments?: string[]
}

export function createMockMessage(overrides: Partial<MockMessage> = {}): MockMessage {
  return {
    id: overrides.id || `message-${Math.random().toString(36).substr(2, 9)}`,
    subject: overrides.subject || 'Homework Reminder',
    content: overrides.content || 'Please remember to submit your homework by Friday.',
    senderId: overrides.senderId || 'teacher-1',
    senderName: overrides.senderName || 'Ms. Smith',
    recipientId: overrides.recipientId || 'student-1',
    recipientName: overrides.recipientName || 'John Doe',
    timestamp: overrides.timestamp || new Date().toISOString(),
    read: overrides.read ?? false,
    type: overrides.type || 'message',
    attachments: overrides.attachments || [],
    ...overrides,
  };
}

// ============================================================================
// PROGRESS DATA
// ============================================================================

export interface MockProgress {
  userId: string
  courseId?: string
  lessonId?: string
  progress: number // 0-100
  completedAt?: string
  timeSpent: number // in seconds
  score?: number
  attempts: number
}

export function createMockProgress(overrides: Partial<MockProgress> = {}): MockProgress {
  return {
    userId: overrides.userId || 'user-1',
    courseId: overrides.courseId,
    lessonId: overrides.lessonId,
    progress: overrides.progress || 0,
    completedAt: overrides.completedAt,
    timeSpent: overrides.timeSpent || 0,
    score: overrides.score,
    attempts: overrides.attempts || 0,
    ...overrides,
  };
}

// ============================================================================
// DASHBOARD DATA
// ============================================================================

export interface MockDashboardData {
  totalStudents: number
  totalClasses: number
  totalLessons: number
  totalAssessments: number
  averageScore: number
  completionRate: number
  activeUsers: number
  recentActivity: any[]
  upcomingEvents: any[]
  notifications: any[]
}

export function createMockDashboardData(overrides: Partial<MockDashboardData> = {}): MockDashboardData {
  return {
    totalStudents: overrides.totalStudents || 150,
    totalClasses: overrides.totalClasses || 6,
    totalLessons: overrides.totalLessons || 45,
    totalAssessments: overrides.totalAssessments || 12,
    averageScore: overrides.averageScore || 82.5,
    completionRate: overrides.completionRate || 78.3,
    activeUsers: overrides.activeUsers || 89,
    recentActivity: overrides.recentActivity || [
      { time: '2 hours ago', action: 'Completed Math Lesson', type: 'success' },
      { time: '5 hours ago', action: 'Submitted Assignment', type: 'info' },
    ],
    upcomingEvents: overrides.upcomingEvents || [
      { date: 'Tomorrow', event: 'Math Quiz', type: 'assessment' },
      { date: 'Friday', event: 'Science Project Due', type: 'deadline' },
    ],
    notifications: overrides.notifications || [],
    ...overrides,
  };
}

// ============================================================================
// API RESPONSE MOCKS
// ============================================================================

export function createMockApiResponse<T>(data: T, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: new Headers({
      'content-type': 'application/json',
    }),
    json: vi.fn(() => Promise.resolve(data)),
    text: vi.fn(() => Promise.resolve(JSON.stringify(data))),
    blob: vi.fn(() => Promise.resolve(new Blob([JSON.stringify(data)]))),
    arrayBuffer: vi.fn(() => Promise.resolve(new ArrayBuffer(0))),
    formData: vi.fn(() => Promise.resolve(new FormData())),
    clone: vi.fn(function(): Response { return createMockApiResponse(data, status); }),
  } as unknown as Response;
}

export function createMockError(message = 'An error occurred', status = 500) {
  return createMockApiResponse({ error: message }, status);
}

// ============================================================================
// WEBSOCKET EVENT MOCKS
// ============================================================================

export function createMockWebSocketMessage(type: string, payload: any) {
  return {
    type,
    payload,
    timestamp: new Date().toISOString(),
    channel: 'public',
  };
}

export function createMockPusherEvent(event: string, data: any, channel = 'public') {
  return {
    event,
    data,
    channel,
    user_id: 'user-1',
  };
}