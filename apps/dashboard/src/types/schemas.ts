/**
 * Zod Schemas for Runtime Validation
 *
 * These schemas provide runtime validation for API responses and form data,
 * ensuring type safety at runtime boundaries.
 */

import { z } from 'zod';

// Base validation schemas
export const IdSchema = z.string().min(1, 'ID cannot be empty');
export const EmailSchema = z.string().email('Invalid email format');
export const UrlSchema = z.string().url('Invalid URL format');
export const DateStringSchema = z.string().datetime('Invalid date format');
export const NonNegativeNumberSchema = z.number().min(0, 'Value cannot be negative');
export const PositiveNumberSchema = z.number().min(1, 'Value must be positive');
export const ProgressPercentageSchema = z.number().min(0).max(100, 'Progress must be between 0 and 100');

// User Role Schema
export const UserRoleSchema = z.enum(['admin', 'teacher', 'student', 'parent']);

// User Status Schema
export const UserStatusSchema = z.enum(['active', 'suspended', 'pending', 'inactive']);

// Lesson Subject Schema
export const SubjectSchema = z.enum([
  'Math',
  'Science',
  'Language',
  'Arts',
  'Technology',
  'Social Studies',
  'Physical Education',
  'Life Skills'
]);

// Lesson Status Schema
export const LessonStatusSchema = z.enum(['draft', 'published', 'archived']);

// Badge Category and Rarity Schemas
export const BadgeCategorySchema = z.enum(['achievement', 'milestone', 'special', 'seasonal']);
export const BadgeRaritySchema = z.enum(['common', 'rare', 'epic', 'legendary']);

// Assessment Type Schema
export const AssessmentTypeSchema = z.enum(['quiz', 'test', 'assignment', 'project']);
export const AssessmentStatusSchema = z.enum(['draft', 'active', 'closed', 'graded']);

// Question Type Schema
export const QuestionTypeSchema = z.enum(['multiple_choice', 'true_false', 'short_answer', 'essay']);

// XP Source Schema
export const XPSourceSchema = z.enum(['lesson', 'assessment', 'achievement', 'bonus']);

// Notification Type Schema
export const NotificationTypeSchema = z.enum(['info', 'warning', 'success', 'error']);

// Compliance Status Schema
export const ComplianceStatusSchema = z.enum(['compliant', 'warning', 'critical']);

// Mission and Challenge Schemas
export const MissionTypeSchema = z.enum(['daily', 'weekly', 'monthly', 'special', 'custom']);
export const MissionCategorySchema = z.enum(['academic', 'social', 'creativity', 'physical', 'community']);
export const MissionDifficultySchema = z.enum(['easy', 'medium', 'hard', 'expert']);
export const MissionStatusSchema = z.enum(['not_started', 'in_progress', 'completed', 'claimed']);

export const ChallengeTypeSchema = z.enum(['speed', 'accuracy', 'creativity', 'collaboration', 'endurance']);
export const ChallengeStatusSchema = z.enum(['upcoming', 'active', 'completed']);

// Reward Category Schema
export const RewardCategorySchema = z.enum(['digital', 'physical', 'experience', 'privilege']);
export const RedemptionStatusSchema = z.enum(['pending', 'approved', 'delivered', 'rejected']);

// Roblox World Schema
export const RobloxWorldStatusSchema = z.enum(['draft', 'published', 'archived']);
export const RobloxDifficultySchema = z.enum(['easy', 'medium', 'hard']);

// Event Type Schema
export const EventTypeSchema = z.enum(['lesson', 'assessment', 'meeting', 'deadline']);

// Trend Schema
export const TrendSchema = z.enum(['improving', 'stable', 'declining']);

// User Schema
export const UserSchema = z.object({
  id: IdSchema,
  email: EmailSchema,
  username: z.string().min(3).max(30),
  firstName: z.string().min(1).max(50),
  lastName: z.string().min(1).max(50),
  displayName: z.string().min(1).max(50),
  avatarUrl: UrlSchema.optional(),
  role: UserRoleSchema,
  schoolId: IdSchema.optional(),
  schoolName: z.string().optional(),
  classIds: z.array(IdSchema).optional(),
  parentIds: z.array(IdSchema).optional(),
  childIds: z.array(IdSchema).optional(),
  isActive: z.boolean(),
  isVerified: z.boolean(),
  totalXP: NonNegativeNumberSchema,
  level: PositiveNumberSchema,
  lastLogin: DateStringSchema.optional(),
  createdAt: DateStringSchema,
  updatedAt: DateStringSchema,
  status: UserStatusSchema,
});

// User Create/Update Schemas
export const UserCreateSchema = z.object({
  email: EmailSchema,
  username: z.string().min(3).max(30),
  password: z.string().min(8),
  firstName: z.string().min(1).max(50),
  lastName: z.string().min(1).max(50),
  displayName: z.string().min(1).max(50).optional(),
  role: UserRoleSchema,
  schoolId: IdSchema.optional(),
  language: z.string().optional(),
  timezone: z.string().optional(),
});

export const UserUpdateSchema = UserCreateSchema.partial().omit({ password: true }).extend({
  password: z.string().min(8).optional(),
  isActive: z.boolean().optional(),
});

// Auth Response Schema
export const AuthResponseSchema = z.object({
  user: UserSchema,
  accessToken: z.string(),
  refreshToken: z.string(),
  expiresIn: PositiveNumberSchema,
});

// Badge Schema
export const BadgeSchema = z.object({
  id: IdSchema,
  name: z.string().min(1).max(100),
  description: z.string().min(1).max(500),
  imageUrl: UrlSchema,
  category: BadgeCategorySchema,
  rarity: BadgeRaritySchema,
  earnedAt: DateStringSchema.optional(),
  progress: NonNegativeNumberSchema.optional(),
  maxProgress: PositiveNumberSchema.optional(),
});

// XP Transaction Schema
export const XPTransactionSchema = z.object({
  id: IdSchema,
  studentId: IdSchema,
  amount: z.number(),
  reason: z.string().min(1).max(200),
  source: XPSourceSchema,
  timestamp: DateStringSchema,
});

// Leaderboard Entry Schema
export const LeaderboardEntrySchema = z.object({
  rank: PositiveNumberSchema,
  studentId: IdSchema,
  displayName: z.string().min(1).max(50),
  avatarUrl: UrlSchema.optional(),
  xp: NonNegativeNumberSchema,
  level: PositiveNumberSchema,
  badgeCount: NonNegativeNumberSchema,
  change: z.number(),
});

// Student Schema
export const StudentSchema = z.object({
  id: IdSchema,
  userId: IdSchema,
  displayName: z.string().min(1).max(50),
  avatarUrl: UrlSchema.optional(),
  xp: NonNegativeNumberSchema,
  level: PositiveNumberSchema,
  badges: z.array(BadgeSchema),
  rank: PositiveNumberSchema.optional(),
  streakDays: NonNegativeNumberSchema,
  lastActive: DateStringSchema,
});

// Question Schema
export const QuestionSchema = z.object({
  id: IdSchema,
  type: QuestionTypeSchema,
  question: z.string().min(1),
  options: z.array(z.string()).optional(),
  correctAnswer: z.union([z.string(), z.number()]).optional(),
  points: PositiveNumberSchema,
});

// Assessment Schema
export const AssessmentSchema = z.object({
  id: IdSchema,
  title: z.string().min(1).max(200),
  lessonId: IdSchema.optional(),
  classId: IdSchema,
  type: AssessmentTypeSchema,
  questions: z.array(QuestionSchema),
  dueDate: DateStringSchema.optional(),
  status: AssessmentStatusSchema,
  averageScore: NonNegativeNumberSchema.optional(),
  submissions: NonNegativeNumberSchema,
  maxSubmissions: PositiveNumberSchema,
});

// Assessment Submission Schema
export const AssessmentSubmissionSchema = z.object({
  id: IdSchema,
  assessmentId: IdSchema,
  studentId: IdSchema,
  answers: z.array(z.any()),
  score: NonNegativeNumberSchema.optional(),
  feedback: z.string().optional(),
  submittedAt: DateStringSchema,
  gradedAt: DateStringSchema.optional(),
});

// Lesson Schema
export const LessonSchema = z.object({
  id: IdSchema,
  title: z.string().min(1).max(200),
  description: z.string().min(1),
  subject: SubjectSchema,
  status: LessonStatusSchema,
  teacherId: IdSchema,
  classIds: z.array(IdSchema),
  robloxWorldId: IdSchema.optional(),
  content: z.any(),
  createdAt: DateStringSchema,
  updatedAt: DateStringSchema,
});

// Class Schema
export const ClassSummarySchema = z.object({
  id: IdSchema,
  name: z.string().min(1).max(100),
  grade: z.number().min(1).max(12),
  teacherId: IdSchema,
  studentCount: NonNegativeNumberSchema,
  averageXP: NonNegativeNumberSchema,
  schedule: z.string().optional(),
  createdAt: DateStringSchema,
});

export const ClassDetailsSchema = ClassSummarySchema.extend({
  students: z.array(StudentSchema),
  lessons: z.array(LessonSchema),
  assessments: z.array(AssessmentSchema),
});

// Progress Schema
export const ProgressPointSchema = z.object({
  x: z.string(),
  y: z.number(),
});

export const SubjectProgressSchema = z.object({
  subject: z.string(),
  mastery: ProgressPercentageSchema,
  lessonsCompleted: NonNegativeNumberSchema,
  totalLessons: NonNegativeNumberSchema,
  averageScore: ProgressPercentageSchema,
  trend: TrendSchema,
});

export const StudentProgressSchema = z.object({
  studentId: IdSchema,
  subjects: z.array(SubjectProgressSchema),
  overallMastery: ProgressPercentageSchema,
  weeklyXP: z.array(ProgressPointSchema),
  monthlyProgress: z.array(ProgressPointSchema),
  strengths: z.array(z.string()),
  weaknesses: z.array(z.string()),
});

// Compliance Schema
export const ComplianceCheckSchema = z.object({
  status: ComplianceStatusSchema,
  issues: z.array(z.string()),
  lastChecked: DateStringSchema,
  recommendations: z.array(z.string()),
});

export const ComplianceStatusResponseSchema = z.object({
  coppa: ComplianceCheckSchema,
  ferpa: ComplianceCheckSchema,
  gdpr: ComplianceCheckSchema,
  overallStatus: ComplianceStatusSchema,
  lastAudit: DateStringSchema,
  nextAudit: DateStringSchema,
});

// Notification Schema
export const NotificationSchema = z.object({
  id: IdSchema,
  userId: IdSchema,
  type: NotificationTypeSchema,
  title: z.string().min(1).max(100),
  message: z.string().min(1).max(500),
  read: z.boolean(),
  actionUrl: UrlSchema.optional(),
  createdAt: DateStringSchema,
});

// Activity Schema
export const ActivitySchema = z.object({
  id: IdSchema,
  type: z.string(),
  description: z.string(),
  timestamp: DateStringSchema,
  userId: IdSchema.optional(),
  metadata: z.any().optional(),
});

// Event Schema
export const EventSchema = z.object({
  id: IdSchema,
  title: z.string().min(1).max(200),
  type: EventTypeSchema,
  date: DateStringSchema,
  classId: IdSchema.optional(),
  description: z.string().optional(),
});

// Roblox World Schema
export const RobloxWorldSchema = z.object({
  id: IdSchema,
  name: z.string().min(1).max(100),
  description: z.string().min(1),
  thumbnailUrl: UrlSchema,
  lessonId: IdSchema,
  placeId: IdSchema,
  universeId: IdSchema,
  maxPlayers: PositiveNumberSchema,
  isActive: z.boolean(),
  joinUrl: UrlSchema.optional(),
  status: RobloxWorldStatusSchema.optional(),
  previewUrl: UrlSchema.optional(),
  downloadUrl: UrlSchema.optional(),
  theme: z.string().optional(),
  mapType: z.string().optional(),
  learningObjectives: z.array(z.string()).optional(),
  difficulty: RobloxDifficultySchema.optional(),
});

// Message Schema
export const MessageSchema = z.object({
  id: IdSchema,
  fromUserId: IdSchema,
  toUserId: IdSchema,
  subject: z.string().min(1).max(200),
  content: z.string().min(1),
  read: z.boolean(),
  attachments: z.array(z.string()).optional(),
  sentAt: DateStringSchema,
  readAt: DateStringSchema.optional(),
});

// Mission Requirement Schema
export const MissionRequirementSchema = z.object({
  id: IdSchema,
  type: z.enum([
    'lesson_complete',
    'assessment_score',
    'xp_earned',
    'badge_earned',
    'attendance',
    'social_interaction',
    'time_spent',
    'custom'
  ]),
  target: NonNegativeNumberSchema,
  current: NonNegativeNumberSchema.optional(),
  description: z.string().min(1),
  metadata: z.any().optional(),
});

// Mission Schema
export const MissionSchema = z.object({
  id: IdSchema,
  title: z.string().min(1).max(200),
  description: z.string().min(1),
  type: MissionTypeSchema,
  category: MissionCategorySchema,
  xpReward: NonNegativeNumberSchema,
  badgeReward: IdSchema.optional(),
  requirements: z.array(MissionRequirementSchema),
  startDate: DateStringSchema.optional(),
  endDate: DateStringSchema.optional(),
  isActive: z.boolean(),
  isRepeatable: z.boolean(),
  maxCompletions: PositiveNumberSchema.optional(),
  difficulty: MissionDifficultySchema,
  imageUrl: UrlSchema.optional(),
  createdBy: IdSchema,
  createdAt: DateStringSchema,
});

// Mission Progress Schema
export const MissionProgressSchema = z.object({
  id: IdSchema,
  missionId: IdSchema,
  studentId: IdSchema,
  status: MissionStatusSchema,
  startedAt: DateStringSchema.optional(),
  completedAt: DateStringSchema.optional(),
  claimedAt: DateStringSchema.optional(),
  progress: ProgressPercentageSchema,
  requirementsProgress: z.array(z.object({
    requirementId: IdSchema,
    current: NonNegativeNumberSchema,
    target: NonNegativeNumberSchema,
    completed: z.boolean(),
  })),
  completionCount: NonNegativeNumberSchema,
});

// Challenge Schema
export const ChallengeLeaderboardSchema = z.object({
  rank: PositiveNumberSchema,
  studentId: IdSchema,
  displayName: z.string().min(1).max(50),
  score: NonNegativeNumberSchema,
  submittedAt: DateStringSchema,
  metadata: z.any().optional(),
});

export const ChallengeSchema = z.object({
  id: IdSchema,
  title: z.string().min(1).max(200),
  description: z.string().min(1),
  type: ChallengeTypeSchema,
  classId: IdSchema.optional(),
  participants: z.array(IdSchema),
  startTime: DateStringSchema,
  endTime: DateStringSchema,
  rules: z.array(z.string()),
  prizes: z.array(z.object({
    position: PositiveNumberSchema,
    xpReward: NonNegativeNumberSchema,
    badgeId: IdSchema.optional(),
    customReward: z.string().optional(),
  })),
  leaderboard: z.array(ChallengeLeaderboardSchema).optional(),
  status: ChallengeStatusSchema,
  createdBy: IdSchema,
  createdAt: DateStringSchema,
});

// Reward Schema
export const RewardSchema = z.object({
  id: IdSchema,
  name: z.string().min(1).max(100),
  description: z.string().min(1),
  cost: NonNegativeNumberSchema,
  category: RewardCategorySchema,
  imageUrl: UrlSchema.optional(),
  stock: NonNegativeNumberSchema.optional(),
  isActive: z.boolean(),
  requirements: z.object({
    level: PositiveNumberSchema.optional(),
    badges: z.array(IdSchema).optional(),
  }).optional(),
  rarity: BadgeRaritySchema,
  createdBy: IdSchema,
  createdAt: DateStringSchema,
  updatedAt: DateStringSchema,
});

// Reward Redemption Schema
export const RewardRedemptionSchema = z.object({
  id: IdSchema,
  rewardId: IdSchema,
  studentId: IdSchema,
  redeemedAt: DateStringSchema,
  status: RedemptionStatusSchema,
  notes: z.string().optional(),
  approvedBy: IdSchema.optional(),
  approvedAt: DateStringSchema.optional(),
});

// Dashboard Metrics Schema
export const DashboardMetricsSchema = z.object({
  xp: NonNegativeNumberSchema.optional(),
  level: PositiveNumberSchema.optional(),
  badges: NonNegativeNumberSchema.optional(),
  activeClasses: NonNegativeNumberSchema.optional(),
  totalStudents: NonNegativeNumberSchema.optional(),
  totalTeachers: NonNegativeNumberSchema.optional(),
  compliance: z.enum(['ok', 'warning', 'critical']).optional(),
  averageProgress: ProgressPercentageSchema.optional(),
  lessonsCompleted: NonNegativeNumberSchema.optional(),
});

// Dashboard Overview Schema
export const DashboardOverviewSchema = z.object({
  role: UserRoleSchema,
  metrics: DashboardMetricsSchema.optional(),
  recentActivity: z.array(ActivitySchema).optional(),
  upcomingEvents: z.array(EventSchema).optional(),
  notifications: z.array(NotificationSchema).optional(),
  kpis: z.object({
    activeClasses: NonNegativeNumberSchema.optional(),
    totalStudents: NonNegativeNumberSchema.optional(),
    activeSessions: NonNegativeNumberSchema.optional(),
    completedLessons: NonNegativeNumberSchema.optional(),
    averageScore: ProgressPercentageSchema.optional(),
    todaysLessons: NonNegativeNumberSchema.optional(),
    pendingAssessments: NonNegativeNumberSchema.optional(),
    averageProgress: ProgressPercentageSchema.optional(),
    progressChange: z.number().optional(),
  }).optional(),
  compliance: z.object({
    status: z.string().optional(),
    pendingAlerts: NonNegativeNumberSchema.optional(),
  }).optional(),
  studentData: z.object({
    xp: NonNegativeNumberSchema.optional(),
    overallProgress: ProgressPercentageSchema.optional(),
    performanceRating: z.string().optional(),
    completedAssignments: NonNegativeNumberSchema.optional(),
    totalAssignments: NonNegativeNumberSchema.optional(),
    lastActive: DateStringSchema.optional(),
  }).optional(),
});

// API Response Schema
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z.object({
      code: z.string(),
      message: z.string(),
      details: z.any().optional(),
    }).optional(),
    pagination: z.object({
      page: PositiveNumberSchema,
      perPage: PositiveNumberSchema,
      total: NonNegativeNumberSchema,
      pages: PositiveNumberSchema,
    }).optional(),
  });

// Export type inference helpers
export type User = z.infer<typeof UserSchema>;
export type UserCreate = z.infer<typeof UserCreateSchema>;
export type UserUpdate = z.infer<typeof UserUpdateSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type Badge = z.infer<typeof BadgeSchema>;
export type XPTransaction = z.infer<typeof XPTransactionSchema>;
export type LeaderboardEntry = z.infer<typeof LeaderboardEntrySchema>;
export type Student = z.infer<typeof StudentSchema>;
export type Question = z.infer<typeof QuestionSchema>;
export type Assessment = z.infer<typeof AssessmentSchema>;
export type AssessmentSubmission = z.infer<typeof AssessmentSubmissionSchema>;
export type Lesson = z.infer<typeof LessonSchema>;
export type ClassSummary = z.infer<typeof ClassSummarySchema>;
export type ClassDetails = z.infer<typeof ClassDetailsSchema>;
export type ProgressPoint = z.infer<typeof ProgressPointSchema>;
export type SubjectProgress = z.infer<typeof SubjectProgressSchema>;
export type StudentProgress = z.infer<typeof StudentProgressSchema>;
export type ComplianceCheck = z.infer<typeof ComplianceCheckSchema>;
export type ComplianceStatus = z.infer<typeof ComplianceStatusResponseSchema>;
export type Notification = z.infer<typeof NotificationSchema>;
export type Activity = z.infer<typeof ActivitySchema>;
export type Event = z.infer<typeof EventSchema>;
export type RobloxWorld = z.infer<typeof RobloxWorldSchema>;
export type Message = z.infer<typeof MessageSchema>;
export type MissionRequirement = z.infer<typeof MissionRequirementSchema>;
export type Mission = z.infer<typeof MissionSchema>;
export type MissionProgress = z.infer<typeof MissionProgressSchema>;
export type ChallengeLeaderboard = z.infer<typeof ChallengeLeaderboardSchema>;
export type Challenge = z.infer<typeof ChallengeSchema>;
export type Reward = z.infer<typeof RewardSchema>;
export type RewardRedemption = z.infer<typeof RewardRedemptionSchema>;
export type DashboardMetrics = z.infer<typeof DashboardMetricsSchema>;
export type DashboardOverview = z.infer<typeof DashboardOverviewSchema>;

// Validation helper function
export const validateApiResponse = <T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: string } => {
  try {
    const validatedData = schema.parse(data);
    return { success: true, data: validatedData };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ')
      };
    }
    return { success: false, error: 'Unknown validation error' };
  }
};