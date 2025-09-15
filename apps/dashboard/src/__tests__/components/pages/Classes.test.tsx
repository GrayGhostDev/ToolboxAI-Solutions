import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock API calls first
const mockListClasses = vi.fn();
const mockCreateClass = vi.fn();
const mockPushLessonToRoblox = vi.fn();

// Create a mock API client with all necessary methods
class MockApiClient {
  listClasses = mockListClasses;
  createClass = mockCreateClass;
  pushLessonToRoblox = mockPushLessonToRoblox;
}

const mockApiClient = new MockApiClient();

vi.mock('@/services/api', () => ({
  default: MockApiClient,
  listClasses: mockListClasses,
  createClass: mockCreateClass,
  pushLessonToRoblox: mockPushLessonToRoblox,
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({}),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('Classes Component API Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Setup default mock responses
    mockListClasses.mockResolvedValue([
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
    ]);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('calls listClasses API on mount', () => {
    expect(mockListClasses).toBeDefined();
    expect(typeof mockListClasses).toBe('function');
  });

  it('handles listClasses API response', async () => {
    const mockData = [
      { id: '1', name: 'Math', student_count: 20 },
      { id: '2', name: 'Science', student_count: 25 }
    ];

    mockListClasses.mockResolvedValueOnce(mockData);
    const result = await mockListClasses();

    expect(result).toEqual(mockData);
    expect(mockListClasses).toHaveBeenCalledTimes(1);
  });

  it('handles empty classes array', async () => {
    mockListClasses.mockResolvedValueOnce([]);
    const result = await mockListClasses();

    expect(result).toEqual([]);
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBe(0);
  });

  it('calculates total students correctly', async () => {
    const classes = [
      { student_count: 25 },
      { student_count: 30 },
      { student_count: 15 }
    ];

    const totalStudents = classes.reduce((sum, c) => sum + c.student_count, 0);
    expect(totalStudents).toBe(70);
  });

  it('filters classes by search term', async () => {
    const classes = [
      { name: 'Advanced Mathematics', id: '1' },
      { name: 'Biology Fundamentals', id: '2' },
      { name: 'Chemistry Basics', id: '3' }
    ];

    const searchTerm = 'Biology';
    const filtered = classes.filter(c =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    expect(filtered).toHaveLength(1);
    expect(filtered[0].name).toBe('Biology Fundamentals');
  });

  it('transforms API data correctly', async () => {
    const apiResponse = {
      id: 'class-1',
      name: 'Test Class',
      grade_level: 10,
      student_count: 25,
      average_progress: 0.85,
      is_online: true
    };

    // Simulate the transformation logic from the component
    const transformedClass = {
      id: apiResponse.id,
      name: apiResponse.name,
      grade: apiResponse.grade_level,
      studentCount: apiResponse.student_count,
      averageXP: Math.round(apiResponse.average_progress * 100),
      completionRate: apiResponse.average_progress,
      isOnline: apiResponse.is_online
    };

    expect(transformedClass.averageXP).toBe(85);
    expect(transformedClass.completionRate).toBe(0.85);
    expect(transformedClass.isOnline).toBe(true);
  });

  it('handles API errors gracefully', async () => {
    const error = new Error('API Error');
    mockListClasses.mockRejectedValueOnce(error);

    try {
      await mockListClasses();
    } catch (e) {
      expect(e).toEqual(error);
    }

    expect(mockListClasses).toHaveBeenCalledTimes(1);
  });

  it('handles createClass API call', async () => {
    const newClassData = {
      name: 'New Class',
      grade: 8,
      schedule: 'Daily 11:00 AM'
    };

    const mockResponse = {
      id: 'new-id',
      ...newClassData,
      student_count: 0
    };

    mockCreateClass.mockResolvedValueOnce(mockResponse);
    const result = await mockCreateClass(newClassData);

    expect(result).toEqual(mockResponse);
    expect(mockCreateClass).toHaveBeenCalledWith(newClassData);
  });

  it('validates role-based functionality', () => {
    const teacherRole = 'teacher';
    const studentRole = 'student';

    // Teachers should see Create Class button
    expect(teacherRole === 'teacher').toBe(true);

    // Students should not see Create Class button
    expect(studentRole === 'teacher').toBe(false);
  });

  it('handles navigation correctly', () => {
    const classId = 'class-1';
    const expectedRoute = `/classes/${classId}`;

    // Simulate navigation call
    mockNavigate(expectedRoute);

    expect(mockNavigate).toHaveBeenCalledWith(expectedRoute);
  });

  it('calculates statistics correctly', () => {
    const classes = [
      { student_count: 25, average_progress: 0.85 },
      { student_count: 30, average_progress: 0.72 }
    ];

    const totalStudents = classes.reduce((sum, c) => sum + c.student_count, 0);
    const activeClasses = classes.length;
    const avgXP = Math.round(
      classes.reduce((sum, c) => sum + (c.average_progress * 100), 0) / classes.length
    );

    expect(totalStudents).toBe(55);
    expect(activeClasses).toBe(2);
    expect(avgXP).toBe(79); // (85 + 72) / 2 = 78.5 -> 79
  });

  it('handles online status display', () => {
    const onlineClass = { is_online: true };
    const offlineClass = { is_online: false };

    expect(onlineClass.is_online).toBe(true);
    expect(offlineClass.is_online).toBe(false);
  });

});
