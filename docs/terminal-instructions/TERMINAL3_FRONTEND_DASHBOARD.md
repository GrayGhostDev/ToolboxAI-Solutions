# Terminal 3: Frontend Dashboard Implementation Specialist

## CRITICAL: Complete Dashboard with Real Data Integration

### Your Role
You are the **Frontend Dashboard Implementation Specialist**. Your mission is to complete the React dashboard, fix all UI issues, and ensure real data flows from the backend to the frontend.

### Immediate Tasks

#### 1. Fix API Service Connection (HIGH PRIORITY)
```bash
cd src/dashboard

# Update API service with proper error handling
cat > src/services/api.ts << 'EOF'
/**
 * API Service with Real Backend Integration
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { toast } from 'react-toastify';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8008';
const API_TIMEOUT = 30000;

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return apiClient.request(error.config);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login';
      }
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.response?.status === 404) {
      toast.error('Resource not found.');
    }
    
    return Promise.reject(error);
  }
);

// API service methods
export const api = {
  // Authentication
  async login(email: string, password: string) {
    const response = await apiClient.post('/api/v1/auth/login', {
      username: email,
      password,
    });
    
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  async logout() {
    await apiClient.post('/api/v1/auth/logout');
    localStorage.clear();
  },

  async getCurrentUser() {
    const response = await apiClient.get('/api/v1/users/me');
    return response.data;
  },

  // Courses
  async getCourses() {
    const response = await apiClient.get('/api/v1/courses');
    return response.data;
  },

  async getCourse(courseId: string) {
    const response = await apiClient.get(`/api/v1/courses/${courseId}`);
    return response.data;
  },

  async createCourse(courseData: any) {
    const response = await apiClient.post('/api/v1/courses', courseData);
    return response.data;
  },

  async updateCourse(courseId: string, courseData: any) {
    const response = await apiClient.put(`/api/v1/courses/${courseId}`, courseData);
    return response.data;
  },

  // Students
  async getStudents() {
    const response = await apiClient.get('/api/v1/students');
    return response.data;
  },

  async getStudent(studentId: string) {
    const response = await apiClient.get(`/api/v1/students/${studentId}`);
    return response.data;
  },

  async getStudentProgress(studentId: string, courseId: string) {
    const response = await apiClient.get(
      `/api/v1/students/${studentId}/courses/${courseId}/progress`
    );
    return response.data;
  },

  // Content Generation
  async generateContent(params: {
    subject: string;
    grade_level: number;
    learning_objectives: string[];
    content_type: string;
    course_id?: string;
  }) {
    const response = await apiClient.post('/api/v1/content/generate', params);
    return response.data;
  },

  async getGeneratedContent(contentId: string) {
    const response = await apiClient.get(`/api/v1/content/${contentId}`);
    return response.data;
  },

  // Quiz
  async generateQuiz(params: {
    topic: string;
    difficulty: string;
    num_questions: number;
    question_types: string[];
    course_id?: string;
  }) {
    const response = await apiClient.post('/api/v1/quiz/generate', params);
    return response.data;
  },

  async submitQuizResult(quizId: string, answers: any[]) {
    const response = await apiClient.post(`/api/v1/quiz/${quizId}/submit`, {
      answers,
    });
    return response.data;
  },

  async getQuizResults(quizId: string) {
    const response = await apiClient.get(`/api/v1/quiz/${quizId}/results`);
    return response.data;
  },

  // Analytics
  async getAnalytics(params: {
    start_date?: string;
    end_date?: string;
    metric_type?: string;
  }) {
    const response = await apiClient.get('/api/v1/analytics', { params });
    return response.data;
  },

  async getClassAnalytics(classId: string) {
    const response = await apiClient.get(`/api/v1/analytics/class/${classId}`);
    return response.data;
  },

  // Schools (Admin)
  async getSchools() {
    const response = await apiClient.get('/api/v1/admin/schools');
    return response.data;
  },

  async createSchool(schoolData: any) {
    const response = await apiClient.post('/api/v1/admin/schools', schoolData);
    return response.data;
  },

  // Health check
  async checkHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default api;
EOF
```

#### 2. Fix WebSocket Connection
```bash
# Update WebSocket service
cat > src/services/websocket.ts << 'EOF'
/**
 * WebSocket Service for Real-time Updates
 */
import { io, Socket } from 'socket.io-client';
import { EventEmitter } from 'events';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8008';

class WebSocketService extends EventEmitter {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  
  connect(token?: string) {
    if (this.socket?.connected) {
      return;
    }
    
    this.socket = io(WS_URL, {
      transports: ['websocket'],
      auth: token ? { token } : undefined,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });
    
    this.setupEventListeners();
  }
  
  private setupEventListeners() {
    if (!this.socket) return;
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
    });
    
    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('disconnected', reason);
    });
    
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });
    
    // Real-time data events
    this.socket.on('content_generated', (data) => {
      this.emit('content_generated', data);
    });
    
    this.socket.on('quiz_submitted', (data) => {
      this.emit('quiz_submitted', data);
    });
    
    this.socket.on('student_progress', (data) => {
      this.emit('student_progress', data);
    });
    
    this.socket.on('class_update', (data) => {
      this.emit('class_update', data);
    });
    
    this.socket.on('notification', (data) => {
      this.emit('notification', data);
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  send(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected. Message not sent:', event);
    }
  }
  
  joinRoom(room: string) {
    this.send('join_room', { room });
  }
  
  leaveRoom(room: string) {
    this.send('leave_room', { room });
  }
  
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
export default wsService;
EOF
```

#### 3. Implement Real Data Hooks
```bash
# Create data fetching hooks
cat > src/hooks/useRealTimeData.ts << 'EOF'
/**
 * Custom Hooks for Real-time Data
 */
import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import wsService from '../services/websocket';
import { toast } from 'react-toastify';

// Fetch courses with real-time updates
export function useCourses() {
  const queryClient = useQueryClient();
  
  const query = useQuery({
    queryKey: ['courses'],
    queryFn: api.getCourses,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  useEffect(() => {
    const handleCourseUpdate = (data: any) => {
      queryClient.setQueryData(['courses'], (old: any) => {
        if (!old) return old;
        return old.map((course: any) =>
          course.id === data.id ? data : course
        );
      });
    };
    
    wsService.on('course_update', handleCourseUpdate);
    return () => {
      wsService.off('course_update', handleCourseUpdate);
    };
  }, [queryClient]);
  
  return query;
}

// Fetch students with progress
export function useStudents(courseId?: string) {
  const queryClient = useQueryClient();
  
  const query = useQuery({
    queryKey: ['students', courseId],
    queryFn: () => courseId ? 
      api.getStudents().then(students => 
        Promise.all(students.map(async (student: any) => ({
          ...student,
          progress: await api.getStudentProgress(student.id, courseId)
        })))
      ) : api.getStudents(),
    enabled: true,
  });
  
  useEffect(() => {
    const handleProgressUpdate = (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['students', courseId] });
    };
    
    wsService.on('student_progress', handleProgressUpdate);
    return () => {
      wsService.off('student_progress', handleProgressUpdate);
    };
  }, [queryClient, courseId]);
  
  return query;
}

// Generate content with progress tracking
export function useGenerateContent() {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'error'>('idle');
  
  const mutation = useMutation({
    mutationFn: api.generateContent,
    onMutate: () => {
      setStatus('generating');
      setProgress(0);
    },
    onSuccess: (data) => {
      setStatus('completed');
      setProgress(100);
      toast.success('Content generated successfully!');
    },
    onError: (error: any) => {
      setStatus('error');
      toast.error(error.response?.data?.detail || 'Failed to generate content');
    },
  });
  
  useEffect(() => {
    const handleProgress = (data: any) => {
      setProgress(data.progress);
    };
    
    wsService.on('content_generation_progress', handleProgress);
    return () => {
      wsService.off('content_generation_progress', handleProgress);
    };
  }, []);
  
  return {
    generate: mutation.mutate,
    isGenerating: mutation.isPending,
    progress,
    status,
    data: mutation.data,
    error: mutation.error,
  };
}

// Real-time analytics
export function useAnalytics(params?: any) {
  const [realtimeData, setRealtimeData] = useState<any>(null);
  
  const query = useQuery({
    queryKey: ['analytics', params],
    queryFn: () => api.getAnalytics(params),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  useEffect(() => {
    const handleAnalyticsUpdate = (data: any) => {
      setRealtimeData(data);
    };
    
    wsService.on('analytics_update', handleAnalyticsUpdate);
    return () => {
      wsService.off('analytics_update', handleAnalyticsUpdate);
    };
  }, []);
  
  return {
    ...query,
    realtimeData: realtimeData || query.data,
  };
}

// Class management
export function useClassData(classId: string) {
  const queryClient = useQueryClient();
  
  const studentsQuery = useStudents(classId);
  const analyticsQuery = useQuery({
    queryKey: ['class-analytics', classId],
    queryFn: () => api.getClassAnalytics(classId),
  });
  
  useEffect(() => {
    wsService.joinRoom(`class_${classId}`);
    
    const handleClassUpdate = (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['class-analytics', classId] });
      queryClient.invalidateQueries({ queryKey: ['students', classId] });
    };
    
    wsService.on('class_update', handleClassUpdate);
    
    return () => {
      wsService.leaveRoom(`class_${classId}`);
      wsService.off('class_update', handleClassUpdate);
    };
  }, [classId, queryClient]);
  
  return {
    students: studentsQuery.data,
    analytics: analyticsQuery.data,
    isLoading: studentsQuery.isLoading || analyticsQuery.isLoading,
    error: studentsQuery.error || analyticsQuery.error,
  };
}
EOF
```

#### 4. Update Dashboard Components with Real Data
```bash
# Update main dashboard
cat > src/components/pages/DashboardHome.tsx << 'EOF'
import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  School,
  Assignment,
  People,
  Refresh,
  CheckCircle,
  Warning,
} from '@mui/icons-material';
import { useCourses, useStudents, useAnalytics } from '../../hooks/useRealTimeData';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { format } from 'date-fns';

const DashboardHome: React.FC = () => {
  const { data: courses, isLoading: coursesLoading } = useCourses();
  const { data: students, isLoading: studentsLoading } = useStudents();
  const { realtimeData: analytics, isLoading: analyticsLoading, refetch } = useAnalytics();
  
  const [refreshing, setRefreshing] = useState(false);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };
  
  if (coursesLoading || studentsLoading || analyticsLoading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }
  
  // Calculate statistics
  const totalStudents = students?.length || 0;
  const activeStudents = students?.filter((s: any) => s.is_active).length || 0;
  const totalCourses = courses?.length || 0;
  const completionRate = analytics?.overall_completion_rate || 0;
  
  // Chart data
  const engagementData = {
    labels: analytics?.engagement_timeline?.map((d: any) => 
      format(new Date(d.date), 'MMM dd')
    ) || [],
    datasets: [{
      label: 'Student Engagement',
      data: analytics?.engagement_timeline?.map((d: any) => d.value) || [],
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
    }],
  };
  
  const performanceData = {
    labels: ['Excellent', 'Good', 'Average', 'Below Average'],
    datasets: [{
      data: [
        analytics?.performance_distribution?.excellent || 0,
        analytics?.performance_distribution?.good || 0,
        analytics?.performance_distribution?.average || 0,
        analytics?.performance_distribution?.below_average || 0,
      ],
      backgroundColor: [
        '#4caf50',
        '#8bc34a',
        '#ff9800',
        '#f44336',
      ],
    }],
  };
  
  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard Overview
        </Typography>
        <Tooltip title="Refresh data">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <Refresh className={refreshing ? 'rotating' : ''} />
          </IconButton>
        </Tooltip>
      </Box>
      
      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <People color="primary" sx={{ mr: 2 }} />
                <Typography color="textSecondary" gutterBottom>
                  Total Students
                </Typography>
              </Box>
              <Typography variant="h4">{totalStudents}</Typography>
              <Chip
                label={`${activeStudents} active`}
                color="success"
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <School color="primary" sx={{ mr: 2 }} />
                <Typography color="textSecondary" gutterBottom>
                  Active Courses
                </Typography>
              </Box>
              <Typography variant="h4">{totalCourses}</Typography>
              <LinearProgress
                variant="determinate"
                value={completionRate}
                sx={{ mt: 2 }}
              />
              <Typography variant="caption" color="textSecondary">
                {completionRate.toFixed(1)}% average completion
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assignment color="primary" sx={{ mr: 2 }} />
                <Typography color="textSecondary" gutterBottom>
                  Assignments
                </Typography>
              </Box>
              <Typography variant="h4">
                {analytics?.total_assignments || 0}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip
                  icon={<CheckCircle />}
                  label={`${analytics?.completed_assignments || 0}`}
                  color="success"
                  size="small"
                />
                <Chip
                  icon={<Warning />}
                  label={`${analytics?.pending_assignments || 0}`}
                  color="warning"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp color="primary" sx={{ mr: 2 }} />
                <Typography color="textSecondary" gutterBottom>
                  Avg. Score
                </Typography>
              </Box>
              <Typography variant="h4">
                {analytics?.average_score?.toFixed(1) || 0}%
              </Typography>
              <Typography
                variant="caption"
                color={analytics?.score_trend > 0 ? 'success.main' : 'error.main'}
              >
                {analytics?.score_trend > 0 ? '↑' : '↓'} 
                {Math.abs(analytics?.score_trend || 0).toFixed(1)}% from last week
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Charts */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Student Engagement Trend
            </Typography>
            <Line data={engagementData} options={{ responsive: true }} />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Distribution
            </Typography>
            <Doughnut data={performanceData} options={{ responsive: true }} />
          </Paper>
        </Grid>
        
        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {analytics?.recent_activities?.map((activity: any, index: number) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  py: 1,
                  borderBottom: index < analytics.recent_activities.length - 1 ? 1 : 0,
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body1">{activity.description}</Typography>
                  <Typography variant="caption" color="textSecondary">
                    {format(new Date(activity.timestamp), 'PPp')}
                  </Typography>
                </Box>
                <Chip
                  label={activity.type}
                  size="small"
                  color={activity.type === 'success' ? 'success' : 'default'}
                />
              </Box>
            )) || <Typography color="textSecondary">No recent activity</Typography>}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardHome;
EOF
```

#### 5. Fix Browser Console Errors
```bash
# Update vite config to fix module resolution
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5177,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8008',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1600,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
      'axios',
      'socket.io-client',
      'chart.js',
      'react-chartjs-2',
    ],
  },
});
EOF
```

#### 6. Update Authentication Context
```bash
# Fix auth context with real backend
cat > src/contexts/AuthContext.tsx << 'EOF'
import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import wsService from '../services/websocket';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  school_id?: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await api.getCurrentUser();
          setUser(userData);
          wsService.connect(token);
        } catch (error) {
          localStorage.clear();
        }
      }
      setIsLoading(false);
    };
    
    checkAuth();
  }, []);
  
  const login = async (email: string, password: string) => {
    const response = await api.login(email, password);
    setUser(response.user);
    wsService.connect(response.access_token);
  };
  
  const logout = async () => {
    await api.logout();
    setUser(null);
    wsService.disconnect();
    localStorage.clear();
  };
  
  const updateUser = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };
  
  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
EOF
```

#### 7. Build Production Bundle
```bash
# Install missing dependencies
npm install @tanstack/react-query date-fns react-toastify chart.js react-chartjs-2

# Build for production
npm run build

# Test production build
npm run preview
```

## Communication Protocol
- Get API endpoints from Terminal 2
- Coordinate with Terminal 1 for file paths
- Share UI components with Terminal 5 for testing
- Update Terminal 4 on data requirements

## Success Metrics
✅ Dashboard loads without errors
✅ Real data displayed from backend
✅ WebSocket connection stable
✅ All charts rendering correctly
✅ Authentication working
✅ No console errors
✅ Responsive on all devices
✅ Performance score > 90

## Notes
- Use real API endpoints, not mocks
- Implement proper loading states
- Add error boundaries
- Test on different screen sizes
- Optimize bundle size