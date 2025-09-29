import { createSelector } from '@reduxjs/toolkit';
import { api } from './index';
import type { RootState } from '../index';
import type {
  ClassSummary,
  Lesson,
  Assessment,
  Message,
  User,
  Badge,
  LeaderboardEntry,
} from '../../types';

// Base selectors from RTK Query
export const selectDashboardData = api.endpoints.getDashboardOverview.select();
export const selectClasses = api.endpoints.getClasses.select();
export const selectLessons = (classId?: string) =>
  api.endpoints.getLessons.select(classId);
export const selectAssessments = (classId?: string) =>
  api.endpoints.getAssessments.select(classId);
export const selectMessages = (params: any = {}) =>
  api.endpoints.getMessages.select(params);
export const selectUsers = (params: any = {}) =>
  api.endpoints.getUsers.select(params);
export const selectBadges = (studentId?: string) =>
  api.endpoints.getBadges.select(studentId);
export const selectLeaderboard = (params: any = {}) =>
  api.endpoints.getLeaderboard.select(params);

// Enhanced selectors with transformations

// Classes with enhanced data
export const selectClassesWithStats = createSelector(
  [selectClasses],
  (classesResult) => {
    if (!classesResult.data) return [];

    return classesResult.data.map(classItem => ({
      ...classItem,
      // Add computed properties
      utilization: classItem.max_students > 0
        ? (classItem.student_count / classItem.max_students) * 100
        : 0,
      status: classItem.is_active
        ? classItem.is_online
          ? 'online'
          : 'offline'
        : 'inactive',
      enrollmentStatus: classItem.student_count >= classItem.max_students
        ? 'full'
        : classItem.student_count === 0
        ? 'empty'
        : 'available',
    }));
  }
);

// Classes grouped by subject
export const selectClassesBySubject = createSelector(
  [selectClassesWithStats],
  (classes) => {
    const grouped = classes.reduce((acc, classItem) => {
      const subject = classItem.subject || 'Other';
      if (!acc[subject]) {
        acc[subject] = [];
      }
      acc[subject].push(classItem);
      return acc;
    }, {} as Record<string, typeof classes>);

    return grouped;
  }
);

// Active classes only
export const selectActiveClasses = createSelector(
  [selectClassesWithStats],
  (classes) => classes.filter(c => c.is_active)
);

// Classes with low enrollment (less than 50% capacity)
export const selectLowEnrollmentClasses = createSelector(
  [selectClassesWithStats],
  (classes) => classes.filter(c => c.utilization < 50 && c.is_active)
);

// Messages organized by folder
export const selectMessagesByFolder = createSelector(
  [selectMessages()],
  (messagesResult) => {
    if (!messagesResult.data) return {};

    return messagesResult.data.reduce((acc, message) => {
      const folder = message.folder || 'inbox';
      if (!acc[folder]) {
        acc[folder] = [];
      }
      acc[folder].push(message);
      return acc;
    }, {} as Record<string, Message[]>);
  }
);

// Unread message count
export const selectUnreadMessageCount = createSelector(
  [selectMessages()],
  (messagesResult) => {
    if (!messagesResult.data) return 0;
    return messagesResult.data.filter(m => !m.is_read).length;
  }
);

// Priority messages
export const selectPriorityMessages = createSelector(
  [selectMessages()],
  (messagesResult) => {
    if (!messagesResult.data) return [];
    return messagesResult.data.filter(m =>
      m.priority === 'high' || m.priority === 'urgent'
    );
  }
);

// Users by role
export const selectUsersByRole = createSelector(
  [selectUsers()],
  (usersResult) => {
    if (!usersResult.data) return {};

    return usersResult.data.reduce((acc, user) => {
      const role = user.role || 'unknown';
      if (!acc[role]) {
        acc[role] = [];
      }
      acc[role].push(user);
      return acc;
    }, {} as Record<string, User[]>);
  }
);

// Active teachers
export const selectActiveTeachers = createSelector(
  [selectUsers()],
  (usersResult) => {
    if (!usersResult.data) return [];
    return usersResult.data.filter(u =>
      u.role === 'teacher' && u.isActive
    );
  }
);

// Students with performance data
export const selectStudentsWithPerformance = createSelector(
  [selectUsers(), selectLeaderboard()],
  (usersResult, leaderboardResult) => {
    if (!usersResult.data || !leaderboardResult.data) return [];

    const students = usersResult.data.filter(u => u.role === 'student');
    const leaderboardMap = new Map(
      leaderboardResult.data.map(entry => [entry.userId, entry])
    );

    return students.map(student => ({
      ...student,
      performance: leaderboardMap.get(student.id) || {
        userId: student.id,
        displayName: student.displayName,
        totalXP: student.totalXP || 0,
        level: student.level || 1,
        rank: 0,
        badges: [],
      },
    }));
  }
);

// Recent activity from multiple sources
export const selectRecentActivity = createSelector(
  [selectMessages(), selectAssessments(), selectLessons()],
  (messagesResult, assessmentsResult, lessonsResult) => {
    const activities = [];

    // Recent messages
    if (messagesResult.data) {
      messagesResult.data
        .slice(0, 5)
        .forEach(message => {
          activities.push({
            id: `message-${message.id}`,
            type: 'message',
            title: message.subject,
            description: `New message from ${message.sender_id}`,
            timestamp: message.created_at,
            priority: message.priority || 'normal',
          });
        });
    }

    // Recent assessments
    if (assessmentsResult.data) {
      assessmentsResult.data
        .slice(0, 3)
        .forEach(assessment => {
          activities.push({
            id: `assessment-${assessment.id}`,
            type: 'assessment',
            title: assessment.title,
            description: `Assessment ${assessment.status}`,
            timestamp: assessment.updatedAt || assessment.createdAt,
            priority: assessment.dueDate ? 'high' : 'normal',
          });
        });
    }

    // Recent lessons
    if (lessonsResult.data) {
      lessonsResult.data
        .slice(0, 3)
        .forEach(lesson => {
          activities.push({
            id: `lesson-${lesson.id}`,
            type: 'lesson',
            title: lesson.title,
            description: `Lesson ${lesson.status}`,
            timestamp: lesson.updatedAt || lesson.createdAt,
            priority: 'normal',
          });
        });
    }

    // Sort by timestamp (most recent first)
    return activities
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 10);
  }
);

// Dashboard summary statistics
export const selectDashboardSummary = createSelector(
  [
    selectDashboardData,
    selectClasses,
    selectUsers(),
    selectMessages(),
    selectAssessments()
  ],
  (dashboardResult, classesResult, usersResult, messagesResult, assessmentsResult) => {
    const dashboard = dashboardResult.data;
    const classes = classesResult.data || [];
    const users = usersResult.data || [];
    const messages = messagesResult.data || [];
    const assessments = assessmentsResult.data || [];

    return {
      // From API
      ...dashboard,
      // Computed statistics
      totalClasses: classes.length,
      activeClasses: classes.filter(c => c.is_active).length,
      totalStudents: users.filter(u => u.role === 'student').length,
      totalTeachers: users.filter(u => u.role === 'teacher').length,
      unreadMessages: messages.filter(m => !m.is_read).length,
      pendingAssessments: assessments.filter(a => a.status === 'draft').length,
      // Ratios and percentages
      classUtilization: classes.length > 0
        ? classes.reduce((sum, c) => sum + (c.student_count / c.max_students), 0) / classes.length * 100
        : 0,
      activeUserRatio: users.length > 0
        ? users.filter(u => u.isActive).length / users.length * 100
        : 0,
    };
  }
);

// Performance metrics for caching
export const selectCachePerformance = createSelector(
  [(state: RootState) => state.api],
  (apiState) => {
    const queries = apiState.queries || {};
    const mutations = apiState.mutations || {};

    const totalQueries = Object.keys(queries).length;
    const successfulQueries = Object.values(queries).filter(
      (query: any) => query.status === 'fulfilled'
    ).length;
    const errorQueries = Object.values(queries).filter(
      (query: any) => query.status === 'rejected'
    ).length;
    const pendingQueries = Object.values(queries).filter(
      (query: any) => query.status === 'pending'
    ).length;

    const totalMutations = Object.keys(mutations).length;
    const successfulMutations = Object.values(mutations).filter(
      (mutation: any) => mutation.status === 'fulfilled'
    ).length;

    return {
      queries: {
        total: totalQueries,
        successful: successfulQueries,
        errors: errorQueries,
        pending: pendingQueries,
        successRate: totalQueries > 0 ? (successfulQueries / totalQueries) * 100 : 0,
      },
      mutations: {
        total: totalMutations,
        successful: successfulMutations,
        successRate: totalMutations > 0 ? (successfulMutations / totalMutations) * 100 : 0,
      },
      cacheHitRatio: totalQueries > 0 ? (successfulQueries / totalQueries) * 100 : 0,
    };
  }
);

// Search and filter helpers
export const createSearchSelector = <T>(
  dataSelector: (state: RootState) => { data?: T[] },
  searchFields: (keyof T)[]
) => createSelector(
  [dataSelector, (state: RootState, searchTerm: string) => searchTerm],
  (dataResult, searchTerm) => {
    if (!dataResult.data || !searchTerm.trim()) {
      return dataResult.data || [];
    }

    const lowerSearchTerm = searchTerm.toLowerCase();
    return dataResult.data.filter(item =>
      searchFields.some(field => {
        const value = item[field];
        return value && String(value).toLowerCase().includes(lowerSearchTerm);
      })
    );
  }
);

// Create specialized search selectors
export const selectSearchClasses = createSearchSelector(
  selectClasses,
  ['name', 'subject', 'teacher_name']
);

export const selectSearchLessons = createSearchSelector(
  selectLessons(),
  ['title', 'description', 'subject']
);

export const selectSearchUsers = createSearchSelector(
  selectUsers(),
  ['displayName', 'email', 'username']
);

// Data freshness indicators
export const selectDataFreshness = createSelector(
  [(state: RootState) => state.api],
  (apiState) => {
    const queries = apiState.queries || {};
    const now = Date.now();
    const fiveMinutes = 5 * 60 * 1000;

    const freshness = Object.entries(queries).reduce((acc, [key, query]: [string, any]) => {
      if (query.fulfilledTimeStamp) {
        const age = now - query.fulfilledTimeStamp;
        acc[key] = {
          age,
          isFresh: age < fiveMinutes,
          isStale: age > fiveMinutes,
          lastUpdated: new Date(query.fulfilledTimeStamp).toISOString(),
        };
      }
      return acc;
    }, {} as Record<string, any>);

    return freshness;
  }
);

// Export all selectors
export default {
  selectDashboardData,
  selectClasses,
  selectLessons,
  selectAssessments,
  selectMessages,
  selectUsers,
  selectBadges,
  selectLeaderboard,
  selectClassesWithStats,
  selectClassesBySubject,
  selectActiveClasses,
  selectLowEnrollmentClasses,
  selectMessagesByFolder,
  selectUnreadMessageCount,
  selectPriorityMessages,
  selectUsersByRole,
  selectActiveTeachers,
  selectStudentsWithPerformance,
  selectRecentActivity,
  selectDashboardSummary,
  selectCachePerformance,
  selectSearchClasses,
  selectSearchLessons,
  selectSearchUsers,
  selectDataFreshness,
};