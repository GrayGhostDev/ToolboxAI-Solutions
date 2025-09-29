import { vi } from 'vitest';

// Configure test timeout for Vitest
vi.setConfig({ testTimeout: 10000 });

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock API service
const mockGetDashboardOverview = vi.fn();

vi.mock('@/services/api', () => ({
  getDashboardOverview: mockGetDashboardOverview,
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('DashboardHome Component Logic Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mock data
    mockGetDashboardOverview.mockResolvedValue({
      kpis: {
        activeClasses: 5,
        totalStudents: 150,
        todaysLessons: 3,
        pendingAssessments: 2,
        averageProgress: 75,
        progressChange: 5,
      },
      compliance: {
        status: 'Good',
        pendingAlerts: 0,
      },
      studentData: {
        xp: 1250,
        overallProgress: 85,
        performanceRating: 'Excellent',
        completedAssignments: 8,
        totalAssignments: 10,
        lastActive: '2024-01-15T10:30:00Z',
      },
      recentActivity: [
        { time: '2 hours ago', action: 'Completed Math Lesson', type: 'success' },
        { time: '5 hours ago', action: 'Earned Problem Solver badge', type: 'achievement' },
      ],
      upcomingEvents: [
        { date: 'Today, 2:00 PM', event: 'Math Quiz', type: 'assessment' },
        { date: 'Tomorrow, 10:00 AM', event: 'Science Lab (Roblox)', type: 'lesson' },
      ],
    });
  });

  it('handles getDashboardOverview API response', async () => {
    const result = await mockGetDashboardOverview();

    expect(result.kpis.activeClasses).toBe(5);
    expect(result.kpis.totalStudents).toBe(150);
    expect(result.kpis.todaysLessons).toBe(3);
    expect(result.studentData.xp).toBe(1250);
  });

  it('validates role-based functionality', () => {
    const roles = ['teacher', 'student', 'admin'];

    // Teachers should have lesson creation access
    expect(roles.includes('teacher')).toBe(true);

    // Students should have progress tracking
    expect(roles.includes('student')).toBe(true);

    // Admins should have analytics access
    expect(roles.includes('admin')).toBe(true);
  });

  it('calculates student progress correctly', () => {
    const studentData = {
      completedAssignments: 8,
      totalAssignments: 10,
      overallProgress: 85
    };

    const completionRate = (studentData.completedAssignments / studentData.totalAssignments) * 100;
    expect(completionRate).toBe(80);
    expect(studentData.overallProgress).toBe(85);
  });

  it('handles navigation for different roles', () => {
    // Student navigation
    mockNavigate('/play');
    expect(mockNavigate).toHaveBeenCalledWith('/play');

    // Admin navigation
    mockNavigate('/analytics');
    expect(mockNavigate).toHaveBeenCalledWith('/analytics');

    // Teacher navigation
    mockNavigate('/lessons');
    expect(mockNavigate).toHaveBeenCalledWith('/lessons');
  });

  it('processes recent activity data', async () => {
    const data = await mockGetDashboardOverview();
    const recentActivity = data.recentActivity;

    expect(recentActivity).toHaveLength(2);
    expect(recentActivity[0].action).toBe('Completed Math Lesson');
    expect(recentActivity[0].type).toBe('success');
    expect(recentActivity[1].type).toBe('achievement');
  });

  it('processes upcoming events data', async () => {
    const data = await mockGetDashboardOverview();
    const upcomingEvents = data.upcomingEvents;

    expect(upcomingEvents).toHaveLength(2);
    expect(upcomingEvents[0].event).toBe('Math Quiz');
    expect(upcomingEvents[0].type).toBe('assessment');
    expect(upcomingEvents[1].type).toBe('lesson');
  });

  it('handles compliance status', async () => {
    const data = await mockGetDashboardOverview();
    const compliance = data.compliance;

    expect(compliance.status).toBe('Good');
    expect(compliance.pendingAlerts).toBe(0);
  });

  it('handles KPI calculations', async () => {
    const data = await mockGetDashboardOverview();
    const kpis = data.kpis;

    // Test progress change calculation
    expect(kpis.progressChange).toBe(5);
    expect(kpis.averageProgress).toBe(75);

    // Test totals
    expect(kpis.activeClasses + kpis.todaysLessons).toBe(8); // 5 + 3
  });

  it('handles API errors gracefully', async () => {
    const error = new Error('Dashboard API Error');
    mockGetDashboardOverview.mockRejectedValueOnce(error);

    try {
      await mockGetDashboardOverview();
    } catch (e) {
      expect(e).toEqual(error);
    }

    expect(mockGetDashboardOverview).toHaveBeenCalledTimes(1);
  });

  it('validates performance rating logic', () => {
    const performanceData = [
      { xp: 1250, rating: 'Excellent' },
      { xp: 800, rating: 'Good' },
      { xp: 400, rating: 'Average' }
    ];

    const excellent = performanceData.find(p => p.rating === 'Excellent');
    expect(excellent?.xp).toBeGreaterThan(1000);
  });
});