/**
 * Mock data service for bypass/development mode
 * Provides realistic sample data for all dashboard components
 */

export const mockAssessments = [
  {
    id: 'assess-001',
    title: 'Variables Quiz',
    description: 'Test your knowledge of variable types and declarations',
    questions: 10,
    duration: 15,
    difficulty: 'beginner',
    maxScore: 100,
    attempts: 45,
    averageScore: 82,
    status: 'published',
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
    tags: ['variables', 'basics', 'quiz']
  },
  {
    id: 'assess-002',
    title: 'Loop Master Challenge',
    description: 'Demonstrate your understanding of loops and iteration',
    questions: 15,
    duration: 20,
    difficulty: 'intermediate',
    maxScore: 150,
    attempts: 32,
    averageScore: 75,
    status: 'published',
    dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['loops', 'control-flow', 'challenge']
  },
  {
    id: 'assess-003',
    title: 'Function Implementation Test',
    description: 'Create and implement functions to solve problems',
    questions: 8,
    duration: 30,
    difficulty: 'advanced',
    maxScore: 200,
    attempts: 12,
    averageScore: 68,
    status: 'draft',
    dueDate: null,
    tags: ['functions', 'advanced', 'coding']
  }
];

export const mockMessages = [
  {
    id: 'msg-001',
    from: 'John Smith',
    fromRole: 'student',
    subject: 'Help with loops homework',
    preview: "Hi, I'm having trouble understanding the while loop example from today's class...",
    body: "Hi, I'm having trouble understanding the while loop example from today's class. Can you explain when to use while vs for loops?",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    read: false,
    starred: true,
    category: 'academic'
  },
  {
    id: 'msg-002',
    from: 'Sarah Johnson',
    fromRole: 'parent',
    subject: 'Progress update request',
    preview: "I'd like to schedule a meeting to discuss my child's progress...",
    body: "I'd like to schedule a meeting to discuss my child's progress in the programming course. Are you available next week?",
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    read: true,
    starred: false,
    category: 'parent'
  },
  {
    id: 'msg-003',
    from: 'System Administrator',
    fromRole: 'admin',
    subject: 'New features available!',
    preview: "We've added new Roblox Studio integration features...",
    body: "We've added new Roblox Studio integration features that allow real-time collaboration. Check out the new tools in your dashboard!",
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    read: true,
    starred: false,
    category: 'system'
  },
  {
    id: 'msg-004',
    from: 'Emily Chen',
    fromRole: 'student',
    subject: 'Submitted my game project!',
    preview: 'Just wanted to let you know I submitted my Roblox game project...',
    body: 'Just wanted to let you know I submitted my Roblox game project. I added extra features like power-ups and a leaderboard!',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    read: false,
    starred: false,
    category: 'academic'
  }
];

export const mockReports = {
  overview: {
    totalStudents: 156,
    activeClasses: 8,
    completionRate: 78,
    averageScore: 82,
    weeklyProgress: 12,
    engagementRate: 85
  },
  performanceData: [
    { month: 'Jan', score: 75, completion: 65 },
    { month: 'Feb', score: 78, completion: 70 },
    { month: 'Mar', score: 82, completion: 75 },
    { month: 'Apr', score: 85, completion: 78 },
    { month: 'May', score: 88, completion: 82 },
    { month: 'Jun', score: 90, completion: 85 }
  ],
  topPerformers: [
    { name: 'Alex Thompson', score: 98, badges: 15, xp: 2400 },
    { name: 'Sarah Lee', score: 96, badges: 14, xp: 2250 },
    { name: 'Mike Johnson', score: 94, badges: 12, xp: 2100 },
    { name: 'Emma Davis', score: 92, badges: 11, xp: 1950 },
    { name: 'Chris Wilson', score: 90, badges: 10, xp: 1800 }
  ]
};

export const mockSettings = {
  profile: {
    name: 'Demo Teacher',
    email: 'teacher@demo.com',
    school: 'ToolboxAI Academy',
    bio: 'Passionate educator teaching programming and game development',
    avatar: '/avatars/teacher.png'
  },
  preferences: {
    theme: 'light',
    language: 'en',
    notifications: true,
    emailDigest: 'weekly',
    autoSave: true,
    soundEffects: false
  },
  privacy: {
    profileVisibility: 'school',
    showEmail: false,
    showProgress: true,
    allowMessages: true
  }
};

export const mockStudentData = {
  missions: [
    {
      id: 'mission-001',
      title: 'Code Your First Adventure',
      description: 'Create a simple adventure game in Roblox',
      xpReward: 500,
      progress: 75,
      tasks: [
        { id: 't1', name: 'Set up game world', completed: true },
        { id: 't2', name: 'Add player character', completed: true },
        { id: 't3', name: 'Create obstacles', completed: true },
        { id: 't4', name: 'Add scoring system', completed: false }
      ],
      deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 'mission-002',
      title: 'Master of Variables',
      description: 'Complete all variable-related challenges',
      xpReward: 300,
      progress: 40,
      tasks: [
        { id: 't1', name: 'Declare 5 different types', completed: true },
        { id: 't2', name: 'Use variables in calculations', completed: true },
        { id: 't3', name: 'Create a variable swap function', completed: false },
        { id: 't4', name: 'Pass the final quiz', completed: false }
      ],
      deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
    }
  ],
  rewards: [
    {
      id: 'reward-001',
      name: 'Code Warrior Badge',
      description: 'Complete 10 coding challenges',
      icon: '🗡️',
      earned: true,
      earnedDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      rarity: 'rare'
    },
    {
      id: 'reward-002',
      name: 'Speed Coder',
      description: 'Complete a challenge in under 5 minutes',
      icon: '⚡',
      earned: true,
      earnedDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      rarity: 'uncommon'
    },
    {
      id: 'reward-003',
      name: 'Perfect Score',
      description: 'Get 100% on any assessment',
      icon: '🎯',
      earned: false,
      earnedDate: null,
      rarity: 'epic'
    },
    {
      id: 'reward-004',
      name: 'Team Player',
      description: 'Help 5 classmates with their code',
      icon: '🤝',
      earned: false,
      earnedDate: null,
      rarity: 'common'
    }
  ],
  progress: {
    level: 8,
    currentXP: 1850,
    nextLevelXP: 2000,
    totalBadges: 12,
    completedLessons: 24,
    streak: 7
  }
};

// Helper function to check if we're in bypass mode
export const isBypassMode = () => {
  return import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.VITE_USE_MOCK_DATA === 'true';
};

// Mock API delay to simulate network requests
export const mockDelay = (ms: number = 300) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Additional mock data for missing endpoints
export const mockSchools = {
  results: [
    { id: 1, name: 'Springfield Elementary', district: 'Springfield', student_count: 450 },
    { id: 2, name: 'Shelbyville Academy', district: 'Shelbyville', student_count: 380 },
    { id: 3, name: 'Capital City High', district: 'Capital City', student_count: 1200 }
  ],
  count: 3,
  next: null,
  previous: null
};

export const mockUsers = {
  results: [
    { id: 1, email: 'teacher@demo.com', name: 'Demo Teacher', role: 'teacher', is_active: true },
    { id: 2, email: 'student1@demo.com', name: 'Alice Johnson', role: 'student', is_active: true },
    { id: 3, email: 'student2@demo.com', name: 'Bob Smith', role: 'student', is_active: true }
  ],
  count: 3,
  next: null,
  previous: null
};

export const mockDashboardOverview = {
  role: 'teacher',
  metrics: {
    totalStudents: 32,
    activeClasses: 4,
    averageProgress: 78,
    weeklyGrowth: 12
  },
  recentActivity: [
    { time: '2 hours ago', action: 'Completed Math Lesson', type: 'success', userId: 'user1' },
    { time: '5 hours ago', action: "Earned 'Problem Solver' badge", type: 'achievement', userId: 'user2' },
    { time: 'Yesterday', action: 'Submitted Science Assignment', type: 'info', userId: 'user3' }
  ],
  upcomingEvents: [
    { date: 'Today, 2:00 PM', event: 'Math Quiz', type: 'assessment', id: 'event1' },
    { date: 'Tomorrow, 10:00 AM', event: 'Science Lab (Roblox)', type: 'lesson', id: 'event2' }
  ],
  kpis: {
    studentsOnline: 18,
    lessonsCompleted: 145,
    averageScore: 82,
    averageProgress: 78,
    progressChange: 5
  },
  compliance: {
    status: 'Compliant',
    pendingAlerts: 0
  }
};

export const mockAnalytics = {
  weeklyXP: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'XP Earned',
        data: [120, 150, 180, 140, 200, 90, 110],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }
    ]
  },
  subjectMastery: {
    subjects: [
      { name: 'Mathematics', mastery: 85, trend: 'up' },
      { name: 'Science', mastery: 78, trend: 'up' },
      { name: 'English', mastery: 92, trend: 'stable' },
      { name: 'History', mastery: 70, trend: 'up' },
      { name: 'Art', mastery: 88, trend: 'up' }
    ]
  }
};

export const mockGamification = {
  leaderboard: [
    { rank: 1, userId: 'user1', name: 'Alice Johnson', xp: 2450, level: 12 },
    { rank: 2, userId: 'user2', name: 'Bob Smith', xp: 2380, level: 11 },
    { rank: 3, userId: 'user3', name: 'Charlie Brown', xp: 2100, level: 10 },
    { rank: 4, userId: 'user4', name: 'Diana Prince', xp: 1950, level: 9 },
    { rank: 5, userId: 'user5', name: 'Eva Green', xp: 1800, level: 8 }
  ],
  userPosition: {
    rank: 3,
    userId: 'current-user',
    name: 'You',
    xp: 2100,
    level: 10
  }
};

export const mockComplianceStatus = {
  status: 'compliant',
  lastCheck: new Date().toISOString(),
  issues: [],
  nextAudit: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
};

export const mockUnreadMessages = {
  count: 3,
  hasUnread: true
};

export const mockClasses = {
  classes: [
    { id: 1, name: 'Math 101', students: 25, progress: 75, teacher: 'Dr. Smith' },
    { id: 2, name: 'Science 202', students: 22, progress: 68, teacher: 'Ms. Johnson' },
    { id: 3, name: 'English 303', students: 28, progress: 82, teacher: 'Mr. Davis' },
    { id: 4, name: 'History 404', students: 20, progress: 70, teacher: 'Mrs. Wilson' }
  ],
  totalCount: 4
};

export const mockLessons = {
  lessons: [
    { id: 1, title: 'Introduction to Algebra', subject: 'Math', duration: 45, difficulty: 'Beginner' },
    { id: 2, title: 'Chemical Reactions', subject: 'Science', duration: 60, difficulty: 'Intermediate' },
    { id: 3, title: 'Creative Writing', subject: 'English', duration: 50, difficulty: 'Beginner' },
    { id: 4, title: 'World War II', subject: 'History', duration: 55, difficulty: 'Advanced' },
    { id: 5, title: 'Photosynthesis', subject: 'Science', duration: 40, difficulty: 'Intermediate' }
  ],
  totalCount: 5
};

// Admin Dashboard Mock Data
export const mockAdminAnalytics = {
  overview: {
    totalUsers: 1250,
    activeUsers: 890,
    newUsersToday: 24,
    newUsersWeek: 145,
    totalClasses: 48,
    activeClasses: 42,
    totalLessons: 324,
    completedLessons: 289,
    systemHealth: 98.5,
    apiLatency: 145, // ms
    errorRate: 0.02, // percentage
    storageUsed: 67.3, // percentage
  },
  userGrowth: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Students',
        data: [320, 380, 450, 520, 650, 780],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
      {
        label: 'Teachers',
        data: [45, 52, 58, 65, 72, 85],
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
      }
    ]
  },
  systemMetrics: {
    cpu: 34.5,
    memory: 67.8,
    disk: 45.2,
    network: 23.4,
    uptime: 99.99,
    requestsPerSecond: 142,
    activeConnections: 234,
    cacheHitRate: 92.3,
  },
  topContent: [
    { id: 1, title: 'Introduction to Programming', views: 3240, engagement: 92 },
    { id: 2, title: 'Advanced Mathematics', views: 2890, engagement: 88 },
    { id: 3, title: 'Science Lab Basics', views: 2450, engagement: 95 },
    { id: 4, title: 'History of Computing', views: 2100, engagement: 78 },
    { id: 5, title: 'Creative Writing', views: 1980, engagement: 85 },
  ]
};

// System Settings Mock Data
export const mockSystemSettings = {
  general: {
    siteName: 'ToolBoxAI Learning Platform',
    siteUrl: 'https://app.toolboxai.com',
    maintenanceMode: false,
    debugMode: true,
    timezone: 'America/Los_Angeles',
    language: 'en-US',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
  },
  authentication: {
    sessionTimeout: 3600, // seconds
    maxLoginAttempts: 5,
    passwordMinLength: 8,
    requireMFA: false,
    allowRegistration: true,
    emailVerification: true,
    socialLogin: ['google', 'microsoft'],
  },
  email: {
    provider: 'sendgrid',
    fromEmail: 'noreply@toolboxai.com',
    fromName: 'ToolBoxAI',
    replyToEmail: 'support@toolboxai.com',
    smtpHost: 'smtp.sendgrid.net',
    smtpPort: 587,
    smtpEncryption: 'tls',
  },
  storage: {
    provider: 'aws',
    maxUploadSize: 10485760, // bytes (10MB)
    allowedFileTypes: ['pdf', 'doc', 'docx', 'jpg', 'png', 'mp4'],
    storagePath: 's3://toolboxai-uploads',
    cdnUrl: 'https://cdn.toolboxai.com',
  },
  features: {
    pusher: true,
    roblox: true,
    ai: true,
    analytics: true,
    gamification: true,
    messaging: true,
    videoConferencing: false,
    advancedReporting: true,
  },
  limits: {
    maxStudentsPerClass: 50,
    maxClassesPerTeacher: 10,
    maxStoragePerUser: 1073741824, // 1GB
    maxApiRequestsPerMinute: 100,
    maxConcurrentSessions: 3,
  }
};

// Activity Logs Mock Data
export const mockActivityLogs = {
  logs: [
    {
      id: 1,
      timestamp: new Date().toISOString(),
      user: 'admin@demo.com',
      userId: 1,
      action: 'LOGIN',
      category: 'authentication',
      details: 'Successful login from Chrome on Windows',
      ip: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      status: 'success',
      duration: 234, // ms
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      user: 'teacher@demo.com',
      userId: 2,
      action: 'CREATE_CLASS',
      category: 'class_management',
      details: 'Created class "Advanced Programming"',
      ip: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      status: 'success',
      duration: 456,
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      user: 'student1@demo.com',
      userId: 3,
      action: 'SUBMIT_ASSESSMENT',
      category: 'assessment',
      details: 'Submitted "Variables Quiz" - Score: 85%',
      ip: '192.168.1.102',
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)',
      status: 'success',
      duration: 1234,
    },
    {
      id: 4,
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      user: 'teacher@demo.com',
      userId: 2,
      action: 'UPDATE_LESSON',
      category: 'content',
      details: 'Updated lesson "Introduction to Variables"',
      ip: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
      status: 'success',
      duration: 567,
    },
    {
      id: 5,
      timestamp: new Date(Date.now() - 14400000).toISOString(),
      user: 'admin@demo.com',
      userId: 1,
      action: 'DELETE_USER',
      category: 'user_management',
      details: 'Deleted inactive user account (ID: 456)',
      ip: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      status: 'success',
      duration: 345,
    },
    {
      id: 6,
      timestamp: new Date(Date.now() - 18000000).toISOString(),
      user: 'system',
      userId: 0,
      action: 'BACKUP_DATABASE',
      category: 'system',
      details: 'Automated daily database backup completed',
      ip: '127.0.0.1',
      userAgent: 'System Process',
      status: 'success',
      duration: 45678,
    },
    {
      id: 7,
      timestamp: new Date(Date.now() - 21600000).toISOString(),
      user: 'student2@demo.com',
      userId: 4,
      action: 'LOGIN_FAILED',
      category: 'authentication',
      details: 'Failed login attempt - incorrect password',
      ip: '192.168.1.103',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      status: 'error',
      duration: 123,
    }
  ],
  totalCount: 7,
  categories: [
    { name: 'authentication', count: 2 },
    { name: 'class_management', count: 1 },
    { name: 'assessment', count: 1 },
    { name: 'content', count: 1 },
    { name: 'user_management', count: 1 },
    { name: 'system', count: 1 },
  ]
};

// Enhanced User Management Mock Data
export const mockUserManagement = {
  users: [
    {
      id: 1,
      email: 'admin@demo.com',
      name: 'System Administrator',
      role: 'admin',
      status: 'active',
      createdAt: '2024-01-15T08:00:00Z',
      lastLogin: new Date().toISOString(),
      loginCount: 234,
      avatar: '/avatars/admin.png',
      permissions: ['all'],
      mfaEnabled: true,
      emailVerified: true,
      department: 'IT',
      phone: '+1 555-0100',
    },
    {
      id: 2,
      email: 'teacher@demo.com',
      name: 'Jane Smith',
      role: 'teacher',
      status: 'active',
      createdAt: '2024-02-20T10:30:00Z',
      lastLogin: new Date(Date.now() - 3600000).toISOString(),
      loginCount: 156,
      avatar: '/avatars/teacher.png',
      permissions: ['create_class', 'manage_students', 'create_content'],
      mfaEnabled: false,
      emailVerified: true,
      department: 'Mathematics',
      phone: '+1 555-0101',
      classes: ['Math 101', 'Advanced Algebra'],
      studentCount: 45,
    },
    {
      id: 3,
      email: 'student1@demo.com',
      name: 'Alice Johnson',
      role: 'student',
      status: 'active',
      createdAt: '2024-03-10T14:45:00Z',
      lastLogin: new Date(Date.now() - 7200000).toISOString(),
      loginCount: 89,
      avatar: '/avatars/student1.png',
      permissions: ['view_content', 'submit_assessments'],
      mfaEnabled: false,
      emailVerified: true,
      grade: 8,
      parentEmail: 'parent1@demo.com',
      gpa: 3.8,
      enrolledClasses: 4,
    },
    {
      id: 4,
      email: 'student2@demo.com',
      name: 'Bob Williams',
      role: 'student',
      status: 'suspended',
      suspendedReason: 'Pending fee payment',
      createdAt: '2024-03-15T09:20:00Z',
      lastLogin: new Date(Date.now() - 86400000).toISOString(),
      loginCount: 45,
      avatar: '/avatars/student2.png',
      permissions: ['view_content'],
      mfaEnabled: false,
      emailVerified: false,
      grade: 7,
      parentEmail: 'parent2@demo.com',
      gpa: 3.2,
      enrolledClasses: 3,
    },
    {
      id: 5,
      email: 'teacher2@demo.com',
      name: 'John Davis',
      role: 'teacher',
      status: 'inactive',
      createdAt: '2024-01-25T11:00:00Z',
      lastLogin: new Date(Date.now() - 604800000).toISOString(), // 7 days ago
      loginCount: 78,
      avatar: '/avatars/teacher2.png',
      permissions: ['create_class', 'manage_students', 'create_content'],
      mfaEnabled: false,
      emailVerified: true,
      department: 'Science',
      phone: '+1 555-0102',
      classes: ['Biology 101', 'Chemistry Basics'],
      studentCount: 38,
    }
  ],
  totalCount: 5,
  roles: [
    { name: 'admin', count: 1, permissions: 15 },
    { name: 'teacher', count: 2, permissions: 8 },
    { name: 'student', count: 2, permissions: 3 },
  ],
  stats: {
    totalActive: 3,
    totalInactive: 1,
    totalSuspended: 1,
    newToday: 2,
    newThisWeek: 12,
    newThisMonth: 45,
  }
};

// Roblox Integration Mock Data
export const mockRobloxData = {
  environments: [
    {
      id: 'env-001',
      name: 'Math Adventure World',
      status: 'active',
      players: 12,
      maxPlayers: 30,
      createdBy: 'teacher@demo.com',
      createdAt: '2024-04-01T10:00:00Z',
      lastModified: new Date(Date.now() - 3600000).toISOString(),
      thumbnail: '/images/math-world.png',
      description: 'Interactive mathematical problem-solving environment',
      difficulty: 'beginner',
      subject: 'mathematics',
      tags: ['algebra', 'geometry', 'problem-solving'],
    },
    {
      id: 'env-002',
      name: 'Science Laboratory',
      status: 'maintenance',
      players: 0,
      maxPlayers: 25,
      createdBy: 'teacher2@demo.com',
      createdAt: '2024-03-28T14:30:00Z',
      lastModified: new Date(Date.now() - 7200000).toISOString(),
      thumbnail: '/images/science-lab.png',
      description: 'Virtual science experiments and simulations',
      difficulty: 'intermediate',
      subject: 'science',
      tags: ['chemistry', 'physics', 'experiments'],
    },
    {
      id: 'env-003',
      name: 'History Quest',
      status: 'active',
      players: 8,
      maxPlayers: 40,
      createdBy: 'admin@demo.com',
      createdAt: '2024-03-15T09:00:00Z',
      lastModified: new Date(Date.now() - 86400000).toISOString(),
      thumbnail: '/images/history-quest.png',
      description: 'Time-travel adventure through historical periods',
      difficulty: 'advanced',
      subject: 'history',
      tags: ['ancient-history', 'world-war', 'exploration'],
    }
  ],
  sessions: [
    {
      id: 'session-001',
      environmentId: 'env-001',
      environmentName: 'Math Adventure World',
      startTime: new Date(Date.now() - 1800000).toISOString(),
      endTime: null,
      status: 'active',
      participants: 12,
      teacherId: 2,
      teacherName: 'Jane Smith',
    },
    {
      id: 'session-002',
      environmentId: 'env-003',
      environmentName: 'History Quest',
      startTime: new Date(Date.now() - 3600000).toISOString(),
      endTime: new Date(Date.now() - 600000).toISOString(),
      status: 'completed',
      participants: 15,
      teacherId: 1,
      teacherName: 'System Administrator',
      completionRate: 92,
      averageScore: 85,
    }
  ],
  stats: {
    totalEnvironments: 3,
    activeEnvironments: 2,
    totalSessions: 45,
    activeSessions: 1,
    totalPlaytime: 12450, // minutes
    averageSessionLength: 45, // minutes
    totalPlayers: 234,
    activePlayers: 20,
  }
};

// Integration Status Mock Data
// Student Gameplay Mock Data
export const mockStudentGameplay = {
  missions: [
    {
      id: 'mission-001',
      title: 'Code Explorer',
      description: 'Complete your first coding challenge in Roblox Studio',
      difficulty: 'beginner',
      xpReward: 100,
      status: 'active',
      progress: 75,
      objectives: [
        { id: 'obj-1', title: 'Open Roblox Studio', completed: true },
        { id: 'obj-2', title: 'Create a new place', completed: true },
        { id: 'obj-3', title: 'Add a script', completed: true },
        { id: 'obj-4', title: 'Run your first program', completed: false },
      ],
      deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      category: 'programming',
      icon: '🚀',
    },
    {
      id: 'mission-002',
      title: 'Master Builder',
      description: 'Build your first interactive game object',
      difficulty: 'intermediate',
      xpReward: 200,
      status: 'locked',
      progress: 0,
      requiredLevel: 5,
      category: 'game-design',
      icon: '🏗️',
    },
    {
      id: 'mission-003',
      title: 'Team Player',
      description: 'Collaborate with 3 classmates on a group project',
      difficulty: 'beginner',
      xpReward: 150,
      status: 'active',
      progress: 33,
      objectives: [
        { id: 'obj-1', title: 'Join a team', completed: true },
        { id: 'obj-2', title: 'Share your code', completed: false },
        { id: 'obj-3', title: 'Review teammate code', completed: false },
      ],
      category: 'collaboration',
      icon: '🤝',
    },
  ],
  achievements: [
    {
      id: 'ach-001',
      title: 'First Steps',
      description: 'Complete your first lesson',
      icon: '🎯',
      unlockedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      rarity: 'common',
      xpReward: 50,
    },
    {
      id: 'ach-002',
      title: 'Streak Master',
      description: 'Maintain a 7-day learning streak',
      icon: '🔥',
      unlockedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      rarity: 'rare',
      xpReward: 200,
    },
    {
      id: 'ach-003',
      title: 'Bug Hunter',
      description: 'Fix 10 code errors',
      icon: '🐛',
      progress: 7,
      maxProgress: 10,
      rarity: 'uncommon',
      xpReward: 100,
    },
    {
      id: 'ach-004',
      title: 'Lua Legend',
      description: 'Master all Lua basics',
      icon: '💎',
      locked: true,
      rarity: 'legendary',
      xpReward: 500,
    },
  ],
  leaderboard: [
    {
      rank: 1,
      userId: 'user-001',
      username: 'CodeMaster2025',
      avatar: '🦊',
      xp: 5420,
      level: 12,
      badges: 15,
      streak: 21,
    },
    {
      rank: 2,
      userId: 'user-002',
      username: 'LuaWizard',
      avatar: '🐉',
      xp: 4890,
      level: 11,
      badges: 12,
      streak: 14,
    },
    {
      rank: 3,
      userId: 'user-003',
      username: 'GameBuilder',
      avatar: '🦁',
      xp: 4200,
      level: 10,
      badges: 10,
      streak: 7,
    },
    {
      rank: 4,
      userId: 'current-user',
      username: 'You',
      avatar: '🐺',
      xp: 3850,
      level: 9,
      badges: 8,
      streak: 5,
      isCurrentUser: true,
    },
  ],
  rewards: [
    {
      id: 'reward-001',
      title: 'Custom Avatar',
      description: 'Unlock a special avatar for your profile',
      cost: 500,
      type: 'cosmetic',
      available: true,
      icon: '🎨',
    },
    {
      id: 'reward-002',
      title: 'Extra Lives',
      description: 'Get 3 extra attempts on challenges',
      cost: 200,
      type: 'powerup',
      available: true,
      icon: '❤️',
    },
    {
      id: 'reward-003',
      title: 'Skip Challenge',
      description: 'Skip one difficult challenge',
      cost: 300,
      type: 'powerup',
      available: false,
      requiredLevel: 10,
      icon: '⏭️',
    },
  ],
  gameWorlds: [
    {
      id: 'world-001',
      title: 'Coding Island',
      description: 'Learn programming basics in a tropical paradise',
      thumbnail: '/assets/worlds/coding-island.jpg',
      playerCount: 24,
      maxPlayers: 50,
      status: 'online',
      lastPlayed: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      progress: 65,
    },
    {
      id: 'world-002',
      title: 'Logic Labyrinth',
      description: 'Master conditionals and loops in a mysterious maze',
      thumbnail: '/assets/worlds/logic-labyrinth.jpg',
      playerCount: 18,
      maxPlayers: 30,
      status: 'online',
      progress: 40,
    },
    {
      id: 'world-003',
      title: 'Function Factory',
      description: 'Build and test functions in an industrial setting',
      thumbnail: '/assets/worlds/function-factory.jpg',
      playerCount: 0,
      maxPlayers: 25,
      status: 'maintenance',
      progress: 0,
    },
  ],
  challenges: [
    {
      id: 'challenge-001',
      title: 'Daily Code Challenge',
      description: 'Fix the broken script to make the door open',
      difficulty: 'easy',
      timeLimit: 600, // seconds
      xpReward: 50,
      attempts: 2,
      maxAttempts: 3,
      bestTime: 245,
      category: 'debugging',
      status: 'in-progress',
    },
    {
      id: 'challenge-002',
      title: 'Weekly Boss Battle',
      description: 'Create an AI enemy with patrol behavior',
      difficulty: 'hard',
      timeLimit: 3600,
      xpReward: 300,
      attempts: 0,
      maxAttempts: 5,
      category: 'ai-programming',
      status: 'available',
      unlocksIn: 2 * 24 * 60 * 60 * 1000, // milliseconds
    },
  ],
};

// Teacher Gradebook Mock Data
export const mockTeacherGradebook = {
  assessments: [
    {
      id: 'grade-001',
      studentId: 'student-001',
      studentName: 'Alex Johnson',
      assessmentId: 'assess-001',
      assessmentTitle: 'Variables Quiz',
      submittedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      score: 85,
      maxScore: 100,
      status: 'graded',
      feedback: 'Good understanding of variable types. Review string concatenation.',
    },
    {
      id: 'grade-002',
      studentId: 'student-002',
      studentName: 'Sarah Chen',
      assessmentId: 'assess-001',
      assessmentTitle: 'Variables Quiz',
      submittedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      score: 92,
      maxScore: 100,
      status: 'graded',
      feedback: 'Excellent work!',
    },
    {
      id: 'grade-003',
      studentId: 'student-003',
      studentName: 'Mike Davis',
      assessmentId: 'assess-002',
      assessmentTitle: 'Loop Challenge',
      submittedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      score: null,
      maxScore: 100,
      status: 'pending',
    },
  ],
  classPerformance: {
    averageScore: 78,
    highestScore: 95,
    lowestScore: 42,
    submissionRate: 0.87,
    onTimeRate: 0.92,
  },
};

export const mockIntegrations = {
  services: [
    {
      id: 'google-classroom',
      name: 'Google Classroom',
      status: 'connected',
      icon: '/icons/google-classroom.png',
      connectedAt: '2024-03-01T10:00:00Z',
      lastSync: new Date(Date.now() - 3600000).toISOString(),
      syncStatus: 'success',
      dataPoints: {
        classes: 12,
        students: 234,
        assignments: 45,
      },
      features: ['import_students', 'sync_grades', 'export_assignments'],
    },
    {
      id: 'canvas',
      name: 'Canvas LMS',
      status: 'disconnected',
      icon: '/icons/canvas.png',
      connectedAt: null,
      lastSync: null,
      syncStatus: null,
      features: ['import_courses', 'sync_enrollments', 'grade_passback'],
    },
    {
      id: 'zoom',
      name: 'Zoom',
      status: 'connected',
      icon: '/icons/zoom.png',
      connectedAt: '2024-02-15T14:30:00Z',
      lastSync: new Date(Date.now() - 7200000).toISOString(),
      syncStatus: 'success',
      dataPoints: {
        meetings: 8,
        recordings: 24,
      },
      features: ['schedule_meetings', 'auto_recording', 'attendance_tracking'],
    },
    {
      id: 'stripe',
      name: 'Stripe',
      status: 'connected',
      icon: '/icons/stripe.png',
      connectedAt: '2024-01-01T00:00:00Z',
      lastSync: new Date().toISOString(),
      syncStatus: 'success',
      dataPoints: {
        customers: 156,
        subscriptions: 145,
        revenue: 24500,
      },
      features: ['payment_processing', 'subscription_management', 'invoicing'],
    },
    {
      id: 'sendgrid',
      name: 'SendGrid',
      status: 'connected',
      icon: '/icons/sendgrid.png',
      connectedAt: '2024-01-05T08:00:00Z',
      lastSync: new Date().toISOString(),
      syncStatus: 'success',
      dataPoints: {
        emailsSent: 12450,
        deliveryRate: 98.5,
        openRate: 42.3,
      },
      features: ['transactional_email', 'marketing_campaigns', 'analytics'],
    }
  ],
  webhooks: [
    {
      id: 'wh-001',
      url: 'https://app.toolboxai.com/webhooks/stripe',
      service: 'stripe',
      events: ['payment_intent.succeeded', 'customer.created'],
      status: 'active',
      lastTriggered: new Date(Date.now() - 1800000).toISOString(),
      successRate: 99.8,
    },
    {
      id: 'wh-002',
      url: 'https://app.toolboxai.com/webhooks/pusher',
      service: 'pusher',
      events: ['channel_occupied', 'channel_vacated'],
      status: 'active',
      lastTriggered: new Date(Date.now() - 300000).toISOString(),
      successRate: 100,
    }
  ]
};

// Billing & Subscription Mock Data
export const mockSubscription = {
  id: 'sub_1QBxyz789',
  userId: 2,
  planId: 'professional',
  planName: 'Professional',
  planPrice: '$79',
  interval: 'month',
  status: 'active', // active, cancelled, past_due, trialing
  currentPeriodStart: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  currentPeriodEnd: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: false,
  canceledAt: null,
  trialStart: null,
  trialEnd: null,
  createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
  updatedAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString()
};

export const mockSubscriptionTrialing = {
  id: 'sub_trial123',
  userId: 2,
  planId: 'professional',
  planName: 'Professional',
  planPrice: '$79',
  interval: 'month',
  status: 'trialing',
  currentPeriodStart: new Date().toISOString(),
  currentPeriodEnd: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: false,
  canceledAt: null,
  trialStart: new Date().toISOString(),
  trialEnd: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
};

export const mockSubscriptionCancelled = {
  id: 'sub_cancelled456',
  userId: 2,
  planId: 'starter',
  planName: 'Starter',
  planPrice: '$29',
  interval: 'month',
  status: 'cancelled',
  currentPeriodStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  currentPeriodEnd: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: true,
  canceledAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  trialStart: null,
  trialEnd: null,
  createdAt: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString(),
  updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
};

export const mockPaymentMethods = [
  {
    id: 'pm_1QBxyzVisa4242',
    userId: 2,
    type: 'card',
    brand: 'visa',
    last4: '4242',
    expMonth: 12,
    expYear: 2026,
    isDefault: true,
    holderName: 'Demo Teacher',
    createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'pm_2QBxyzMaster5555',
    userId: 2,
    type: 'card',
    brand: 'mastercard',
    last4: '5555',
    expMonth: 8,
    expYear: 2025,
    isDefault: false,
    holderName: 'Demo Teacher',
    createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString()
  }
];

export const mockInvoices = [
  {
    id: 'in_1QBxyz001',
    subscriptionId: 'sub_1QBxyz789',
    userId: 2,
    amount: '$79.00',
    amountPaid: 7900, // cents
    currency: 'usd',
    status: 'paid',
    invoiceNumber: 'INV-2025-001',
    date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    dueDate: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    paidAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    invoiceUrl: 'https://invoice.stripe.com/i/acct_test/inv_xyz001',
    invoicePdf: 'https://invoice.stripe.com/i/acct_test/inv_xyz001/pdf',
    description: 'Professional Plan - Monthly',
    periodStart: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    periodEnd: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'in_1QBxyz002',
    subscriptionId: 'sub_1QBxyz789',
    userId: 2,
    amount: '$79.00',
    amountPaid: 7900,
    currency: 'usd',
    status: 'paid',
    invoiceNumber: 'INV-2025-002',
    date: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    dueDate: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    paidAt: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    invoiceUrl: 'https://invoice.stripe.com/i/acct_test/inv_xyz002',
    invoicePdf: 'https://invoice.stripe.com/i/acct_test/inv_xyz002/pdf',
    description: 'Professional Plan - Monthly',
    periodStart: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
    periodEnd: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'in_1QBxyz003',
    subscriptionId: 'sub_1QBxyz789',
    userId: 2,
    amount: '$79.00',
    amountPaid: 7900,
    currency: 'usd',
    status: 'paid',
    invoiceNumber: 'INV-2025-003',
    date: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
    dueDate: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
    paidAt: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
    invoiceUrl: 'https://invoice.stripe.com/i/acct_test/inv_xyz003',
    invoicePdf: 'https://invoice.stripe.com/i/acct_test/inv_xyz003/pdf',
    description: 'Professional Plan - Monthly',
    periodStart: new Date(Date.now() - 105 * 24 * 60 * 60 * 1000).toISOString(),
    periodEnd: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'in_1QBxyz004',
    subscriptionId: 'sub_1QBxyz789',
    userId: 2,
    amount: '$79.00',
    amountPaid: 0,
    currency: 'usd',
    status: 'pending',
    invoiceNumber: 'INV-2025-004',
    date: new Date().toISOString(),
    dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    paidAt: null,
    invoiceUrl: 'https://invoice.stripe.com/i/acct_test/inv_xyz004',
    invoicePdf: 'https://invoice.stripe.com/i/acct_test/inv_xyz004/pdf',
    description: 'Professional Plan - Monthly',
    periodStart: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    periodEnd: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
  }
];

// Billing Plans Configuration
export const mockBillingPlans = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for small classrooms and individual teachers',
    monthlyPrice: 29,
    yearlyPrice: 290,
    priceId: {
      monthly: 'price_starter_monthly',
      yearly: 'price_starter_yearly'
    },
    features: [
      { text: 'Up to 3 classes', included: true },
      { text: 'Up to 30 students', included: true },
      { text: 'Basic Roblox environments', included: true },
      { text: 'AI content generation', included: true },
      { text: 'Email support', included: true },
      { text: 'Basic analytics', included: true },
      { text: 'Custom branding', included: false },
      { text: 'Priority support', included: false },
      { text: 'API access', included: false }
    ],
    popular: false,
    icon: 'star'
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'For growing schools and experienced educators',
    monthlyPrice: 79,
    yearlyPrice: 790,
    priceId: {
      monthly: 'price_professional_monthly',
      yearly: 'price_professional_yearly'
    },
    features: [
      { text: 'Unlimited classes', included: true },
      { text: 'Up to 150 students', included: true },
      { text: 'Advanced Roblox environments', included: true },
      { text: 'AI content generation', included: true },
      { text: 'Priority support', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'Integrations', included: true },
      { text: 'API access', included: false }
    ],
    popular: true,
    icon: 'rocket'
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For large institutions with advanced needs',
    monthlyPrice: 199,
    yearlyPrice: 1990,
    priceId: {
      monthly: 'price_enterprise_monthly',
      yearly: 'price_enterprise_yearly'
    },
    features: [
      { text: 'Unlimited classes', included: true },
      { text: 'Unlimited students', included: true },
      { text: 'Premium Roblox environments', included: true },
      { text: 'AI content generation', included: true },
      { text: 'Dedicated account manager', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'All integrations', included: true },
      { text: 'API access', included: true },
      { text: 'SLA guarantee', included: true },
      { text: 'Custom development', included: true }
    ],
    popular: false,
    icon: 'building'
  }
];