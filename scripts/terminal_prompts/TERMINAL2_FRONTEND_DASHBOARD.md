# TERMINAL 2: FRONTEND/DASHBOARD SPECIALIST
**Priority: HIGH | Status: Dashboard at 60% (Down) | Target: 100% in 24 hours**

## YOUR MISSION
You are the Frontend/Dashboard Specialist responsible for fixing the dashboard that's currently down, implementing real-time WebSocket connections, and ensuring seamless user experience. The dashboard is CRITICAL for user interaction with the platform.

## CURRENT SYSTEM STATUS
```
✅ Node process on port 5179 (but dashboard not responding)
❌ Dashboard UI not loading properly
⚠️ WebSocket connections need implementation
⚠️ Authentication flow incomplete
⚠️ Real-time updates not working
```

## DEPENDENCY
**WAIT FOR TERMINAL 1**: FastAPI must be running on port 8008 before proceeding with API integration.

## PHASE 1: DIAGNOSE AND FIX DASHBOARD (First 1 hour)

### Task 1.1: Investigate Dashboard Issues
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/src/dashboard

# Check what's actually running on port 5179
lsof -iTCP:5179 -sTCP:LISTEN
ps aux | grep 5179

# Check if it's the dashboard or something else
curl -v http://127.0.0.1:5179

# Check package.json for correct start script
cat package.json | jq '.scripts'

# Check for build errors
npm run build 2>&1 | tee build.log

# Check node_modules integrity
npm ls --depth=0
```

### Task 1.2: Restart Dashboard Properly
```bash
# Kill existing process on 5179
lsof -iTCP:5179 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs kill -9

# Clear cache and reinstall
rm -rf node_modules package-lock.json
rm -rf dist build .next .cache

# Install dependencies fresh
npm install

# Fix any peer dependency issues
npm audit fix

# Update vite config for proper port
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types')
    }
  },
  server: {
    port: 5179,
    host: '127.0.0.1',
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8008',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://127.0.0.1:8008',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          store: ['@reduxjs/toolkit', 'react-redux'],
          ui: ['@mui/material', '@emotion/react', '@emotion/styled']
        }
      }
    }
  }
})
EOF

# Start development server
npm run dev &

# Save PID
echo $! > ../../scripts/pids/dashboard.pid

# Wait and verify
sleep 10
curl http://127.0.0.1:5179
```

## PHASE 2: FIX AUTHENTICATION FLOW (Next 2 hours)

### Task 2.1: Implement Login Component with Real API
```bash
# Update Login component
cat > src/components/pages/Login.tsx << 'EOF'
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { setUser, setToken } from '../../store/slices/userSlice';
import { api } from '../../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    // Check API availability
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8008/health');
      if (response.ok) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
        setError('Backend API is not responding properly');
      }
    } catch (error) {
      setApiStatus('offline');
      setError('Cannot connect to backend API. Please ensure Terminal 1 has started the FastAPI server.');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (apiStatus !== 'online') {
      setError('Backend API is offline. Cannot authenticate.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call real authentication API
      const response = await api.post('/auth/login', {
        username,
        password
      });

      const { access_token, user } = response.data;

      // Store token in localStorage
      localStorage.setItem('access_token', access_token);
      
      // Update Redux store
      dispatch(setToken(access_token));
      dispatch(setUser({
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        isAuthenticated: true
      }));

      // Initialize WebSocket connection after successful login
      initializeWebSocket(user.id, access_token);

      // Navigate based on role
      switch (user.role) {
        case 'admin':
          navigate('/admin/dashboard');
          break;
        case 'teacher':
          navigate('/dashboard');
          break;
        case 'student':
          navigate('/student/dashboard');
          break;
        case 'parent':
          navigate('/parent/dashboard');
          break;
        default:
          navigate('/dashboard');
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      
      if (error.response?.status === 401) {
        setError('Invalid username or password');
      } else if (error.response?.status === 500) {
        setError('Server error. Please try again later.');
      } else {
        setError('Login failed. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const initializeWebSocket = (userId: string, token: string) => {
    // This will be handled by WebSocketContext
    window.dispatchEvent(new CustomEvent('ws-init', { 
      detail: { userId, token } 
    }));
  };

  // Test credentials for development
  const fillTestCredentials = (role: string) => {
    switch (role) {
      case 'teacher':
        setUsername('john_teacher');
        setPassword('Teacher123!');
        break;
      case 'student':
        setUsername('alice_student');
        setPassword('Student123!');
        break;
      case 'admin':
        setUsername('admin_user');
        setPassword('Admin123!');
        break;
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}
    >
      <Card sx={{ maxWidth: 400, width: '100%', mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom align="center">
            ToolBoxAI Login
          </Typography>
          
          {apiStatus === 'checking' && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Checking API connection...
            </Alert>
          )}
          
          {apiStatus === 'offline' && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {apiStatus === 'online' && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Connected to backend API
            </Alert>
          )}

          <form onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              disabled={loading}
              autoComplete="username"
            />
            
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              disabled={loading}
              autoComplete="current-password"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />

            {error && !apiStatus && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading || apiStatus !== 'online'}
            >
              {loading ? <CircularProgress size={24} /> : 'Login'}
            </Button>
          </form>

          {/* Test credential buttons for development */}
          {process.env.NODE_ENV === 'development' && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" display="block" gutterBottom>
                Quick fill for testing:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" onClick={() => fillTestCredentials('teacher')}>
                  Teacher
                </Button>
                <Button size="small" onClick={() => fillTestCredentials('student')}>
                  Student
                </Button>
                <Button size="small" onClick={() => fillTestCredentials('admin')}>
                  Admin
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;
EOF
```

### Task 2.2: Update API Service for Real Backend
```bash
cat > src/services/api.ts << 'EOF'
import axios, { AxiosInstance, AxiosError } from 'axios';
import { store } from '../store';
import { clearUser } from '../store/slices/userSlice';

// Create axios instance with correct backend URL
const api: AxiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8008',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    // Log responses in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Response] ${response.config.url}:`, response.data);
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Clear authentication
      localStorage.removeItem('access_token');
      store.dispatch(clearUser());
      
      // Redirect to login
      window.location.href = '/login';
    }
    
    // Log errors in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`[API Error] ${error.config?.url}:`, error.response?.data || error.message);
    }
    
    return Promise.reject(error);
  }
);

// API methods for different endpoints
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
    
  logout: () => api.post('/auth/logout'),
  
  refreshToken: () => api.post('/auth/refresh'),
  
  getCurrentUser: () => api.get('/auth/me'),
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  
  getStudentDashboard: () => api.get('/dashboard/student'),
  
  getTeacherDashboard: () => api.get('/dashboard/teacher'),
  
  getAdminDashboard: () => api.get('/dashboard/admin'),
  
  getParentDashboard: () => api.get('/dashboard/parent'),
};

export const contentAPI = {
  generateContent: (params: any) =>
    api.post('/generate_content', params),
    
  getContent: (id: string) =>
    api.get(`/content/${id}`),
    
  listContent: (filters?: any) =>
    api.get('/content', { params: filters }),
    
  updateContent: (id: string, data: any) =>
    api.put(`/content/${id}`, data),
    
  deleteContent: (id: string) =>
    api.delete(`/content/${id}`),
};

export const quizAPI = {
  createQuiz: (data: any) =>
    api.post('/quizzes', data),
    
  getQuiz: (id: string) =>
    api.get(`/quizzes/${id}`),
    
  submitAnswer: (quizId: string, answer: any) =>
    api.post(`/quizzes/${quizId}/answer`, answer),
    
  getResults: (quizId: string) =>
    api.get(`/quizzes/${quizId}/results`),
};

export const robloxAPI = {
  getPluginStatus: () =>
    api.get('/roblox/plugin/status'),
    
  generateRobloxContent: (params: any) =>
    api.post('/roblox/generate', params),
    
  deployToRoblox: (content: any) =>
    api.post('/roblox/deploy', content),
};

export { api };
EOF
```

## PHASE 3: IMPLEMENT WEBSOCKET CONNECTIONS (Next 2 hours)

### Task 3.1: Create WebSocket Context with Real Connection
```bash
cat > src/contexts/WebSocketContext.tsx << 'EOF'
import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

interface WebSocketContextType {
  socket: WebSocket | null;
  connected: boolean;
  lastMessage: any;
  sendMessage: (message: any) => void;
  subscribeToChannel: (channel: string) => void;
  unsubscribeFromChannel: (channel: string) => void;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnectAttempt: number;
}

const WebSocketContext = createContext<WebSocketContextType>({
  socket: null,
  connected: false,
  lastMessage: null,
  sendMessage: () => {},
  subscribeToChannel: () => {},
  unsubscribeFromChannel: () => {},
  connectionStatus: 'disconnected',
  reconnectAttempt: 0,
});

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();
  const messageQueueRef = useRef<any[]>([]);
  
  const user = useSelector((state: RootState) => state.user);
  const token = localStorage.getItem('access_token');

  const connectWebSocket = useCallback(() => {
    if (!user.isAuthenticated || !token) {
      console.log('[WebSocket] Not authenticated, skipping connection');
      return;
    }

    setConnectionStatus('connecting');
    console.log('[WebSocket] Attempting to connect...');

    const wsUrl = `ws://127.0.0.1:8008/ws/${user.id}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WebSocket] Connected successfully');
      setSocket(ws);
      setConnected(true);
      setConnectionStatus('connected');
      setReconnectAttempt(0);

      // Send queued messages
      while (messageQueueRef.current.length > 0) {
        const msg = messageQueueRef.current.shift();
        ws.send(JSON.stringify(msg));
      }

      // Start heartbeat
      startHeartbeat(ws);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('[WebSocket] Message received:', message);
        setLastMessage(message);
        
        // Handle different message types
        handleMessage(message);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      setConnectionStatus('error');
    };

    ws.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason);
      setSocket(null);
      setConnected(false);
      setConnectionStatus('disconnected');
      
      // Stop heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }

      // Attempt reconnection with exponential backoff
      if (user.isAuthenticated && reconnectAttempt < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempt + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempt(prev => prev + 1);
          connectWebSocket();
        }, delay);
      }
    };

    return ws;
  }, [user, token, reconnectAttempt]);

  const startHeartbeat = (ws: WebSocket) => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, 30000); // Ping every 30 seconds
  };

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'pong':
        // Heartbeat response
        break;
        
      case 'notification':
        // Show notification to user
        showNotification(message.data);
        break;
        
      case 'content_update':
        // Update content in real-time
        window.dispatchEvent(new CustomEvent('content-update', { detail: message.data }));
        break;
        
      case 'quiz_result':
        // Handle quiz results
        window.dispatchEvent(new CustomEvent('quiz-result', { detail: message.data }));
        break;
        
      case 'collaboration':
        // Handle collaborative editing
        window.dispatchEvent(new CustomEvent('collaboration', { detail: message.data }));
        break;
        
      default:
        console.log('[WebSocket] Unhandled message type:', message.type);
    }
  };

  const showNotification = (notification: any) => {
    // Use browser notifications if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.body,
        icon: '/logo.png',
      });
    }
    
    // Also dispatch event for in-app notifications
    window.dispatchEvent(new CustomEvent('app-notification', { detail: notification }));
  };

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      console.log('[WebSocket] Message sent:', message);
    } else {
      console.log('[WebSocket] Queuing message (not connected):', message);
      messageQueueRef.current.push(message);
    }
  }, [socket]);

  const subscribeToChannel = useCallback((channel: string) => {
    sendMessage({
      type: 'subscribe',
      channel,
      timestamp: Date.now(),
    });
  }, [sendMessage]);

  const unsubscribeFromChannel = useCallback((channel: string) => {
    sendMessage({
      type: 'unsubscribe',
      channel,
      timestamp: Date.now(),
    });
  }, [sendMessage]);

  // Initialize WebSocket on mount and auth change
  useEffect(() => {
    if (user.isAuthenticated && token) {
      const ws = connectWebSocket();
      return () => {
        if (ws) {
          ws.close();
        }
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }
      };
    }
  }, [user.isAuthenticated, token]);

  // Listen for manual WebSocket initialization
  useEffect(() => {
    const handleInit = (event: CustomEvent) => {
      if (event.detail.userId && event.detail.token) {
        connectWebSocket();
      }
    };

    window.addEventListener('ws-init' as any, handleInit);
    return () => {
      window.removeEventListener('ws-init' as any, handleInit);
    };
  }, [connectWebSocket]);

  return (
    <WebSocketContext.Provider
      value={{
        socket,
        connected,
        lastMessage,
        sendMessage,
        subscribeToChannel,
        unsubscribeFromChannel,
        connectionStatus,
        reconnectAttempt,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};
EOF
```

### Task 3.2: Create Real-Time Dashboard Components
```bash
cat > src/components/widgets/RealTimeMetrics.tsx << 'EOF'
import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  People,
  School,
  Quiz,
  CheckCircle,
} from '@mui/icons-material';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { dashboardAPI } from '../../services/api';

interface Metrics {
  activeUsers: number;
  lessonsCompleted: number;
  quizzesSubmitted: number;
  averageScore: number;
  contentGenerated: number;
  trend: 'up' | 'down' | 'stable';
}

interface Activity {
  id: string;
  user: string;
  action: string;
  timestamp: string;
  avatar?: string;
}

const RealTimeMetrics: React.FC = () => {
  const { lastMessage, connected, subscribeToChannel } = useWebSocket();
  const [metrics, setMetrics] = useState<Metrics>({
    activeUsers: 0,
    lessonsCompleted: 0,
    quizzesSubmitted: 0,
    averageScore: 0,
    contentGenerated: 0,
    trend: 'stable',
  });
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load initial metrics
    loadMetrics();
    
    // Subscribe to real-time updates
    if (connected) {
      subscribeToChannel('metrics');
      subscribeToChannel('activities');
    }
  }, [connected]);

  useEffect(() => {
    // Handle real-time updates
    if (lastMessage) {
      if (lastMessage.type === 'metrics_update') {
        setMetrics(prev => ({
          ...prev,
          ...lastMessage.data,
        }));
      } else if (lastMessage.type === 'activity') {
        addActivity(lastMessage.data);
      }
    }
  }, [lastMessage]);

  const loadMetrics = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setMetrics(response.data.statistics);
      setActivities(response.data.recentActivities || []);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const addActivity = (activity: Activity) => {
    setActivities(prev => {
      const updated = [activity, ...prev].slice(0, 10); // Keep last 10
      return updated;
    });
  };

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'users': return <People />;
      case 'lessons': return <School />;
      case 'quizzes': return <Quiz />;
      case 'success': return <CheckCircle />;
      default: return <TrendingUp />;
    }
  };

  const getMetricColor = (trend: string) => {
    switch (trend) {
      case 'up': return 'success.main';
      case 'down': return 'error.main';
      default: return 'text.secondary';
    }
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Grid container spacing={3}>
      {/* Connection Status */}
      <Grid item xs={12}>
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={connected ? 'Live' : 'Offline'}
            color={connected ? 'success' : 'default'}
            size="small"
            sx={{ animation: connected ? 'pulse 2s infinite' : 'none' }}
          />
          <Typography variant="caption" color="text.secondary">
            Real-time updates {connected ? 'active' : 'paused'}
          </Typography>
        </Box>
      </Grid>

      {/* Metric Cards */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <People />
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography color="text.secondary" variant="caption">
                  Active Users
                </Typography>
                <Typography variant="h4">
                  {metrics.activeUsers}
                </Typography>
              </Box>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(metrics.activeUsers / 100) * 100}
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                <School />
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography color="text.secondary" variant="caption">
                  Lessons Today
                </Typography>
                <Typography variant="h4">
                  {metrics.lessonsCompleted}
                </Typography>
              </Box>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(metrics.lessonsCompleted / 50) * 100}
              color="success"
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                <Quiz />
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography color="text.secondary" variant="caption">
                  Quizzes Submitted
                </Typography>
                <Typography variant="h4">
                  {metrics.quizzesSubmitted}
                </Typography>
              </Box>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(metrics.quizzesSubmitted / 30) * 100}
              color="warning"
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                <CheckCircle />
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography color="text.secondary" variant="caption">
                  Average Score
                </Typography>
                <Typography variant="h4">
                  {metrics.averageScore}%
                </Typography>
              </Box>
            </Box>
            <LinearProgress
              variant="determinate"
              value={metrics.averageScore}
              color="info"
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>

      {/* Live Activity Feed */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Live Activity Feed
            </Typography>
            <List>
              {activities.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  {index > 0 && <Divider />}
                  <ListItem
                    sx={{
                      animation: 'slideIn 0.3s ease-out',
                      '@keyframes slideIn': {
                        from: { opacity: 0, transform: 'translateX(-20px)' },
                        to: { opacity: 1, transform: 'translateX(0)' },
                      },
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar src={activity.avatar}>
                        {activity.user[0]}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={activity.action}
                      secondary={`${activity.user} • ${new Date(activity.timestamp).toLocaleTimeString()}`}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
              {activities.length === 0 && (
                <ListItem>
                  <ListItemText
                    primary="No recent activity"
                    secondary="Activities will appear here in real-time"
                  />
                </ListItem>
              )}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default RealTimeMetrics;

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
`;
document.head.appendChild(style);
EOF
```

## PHASE 4: FIX ROUTING AND NAVIGATION (Next 1 hour)

### Task 4.1: Update App.tsx with Proper Routes
```bash
cat > src/App.tsx << 'EOF'
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Provider } from 'react-redux';
import { store } from './store';
import { WebSocketProvider } from './contexts/WebSocketContext';

// Pages
import Login from './components/pages/Login';
import DashboardHome from './components/pages/DashboardHome';
import Classes from './components/pages/Classes';
import Messages from './components/pages/Messages';
import Missions from './components/pages/Missions';
import Reports from './components/pages/Reports';
import Rewards from './components/pages/Rewards';
import Compliance from './components/pages/Compliance';

// Admin Pages
import AdminControlPanel from './components/pages/admin/AdminControlPanel';
import Schools from './components/pages/admin/Schools';
import Users from './components/pages/admin/Users';
import SystemSettings from './components/pages/admin/SystemSettings';
import ActivityLogs from './components/pages/admin/ActivityLogs';

// Layout
import MainLayout from './components/layout/MainLayout';

// Auth Guard
import PrivateRoute from './components/auth/PrivateRoute';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#667eea',
    },
    secondary: {
      main: '#764ba2',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: {
    borderRadius: 12,
  },
});

function App() {
  useEffect(() => {
    // Request notification permission on app load
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Check for saved authentication
    const token = localStorage.getItem('access_token');
    if (token) {
      // Validate token with backend
      validateToken(token);
    }
  }, []);

  const validateToken = async (token: string) => {
    try {
      const response = await fetch('http://127.0.0.1:8008/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Token validation failed:', error);
    }
  };

  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <WebSocketProvider>
          <Router>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected Routes */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <MainLayout />
                  </PrivateRoute>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<DashboardHome />} />
                <Route path="classes" element={<Classes />} />
                <Route path="messages" element={<Messages />} />
                <Route path="missions" element={<Missions />} />
                <Route path="reports" element={<Reports />} />
                <Route path="rewards" element={<Rewards />} />
                <Route path="compliance" element={<Compliance />} />
                
                {/* Admin Routes */}
                <Route path="admin">
                  <Route index element={<Navigate to="/admin/dashboard" replace />} />
                  <Route path="dashboard" element={<AdminControlPanel />} />
                  <Route path="schools" element={<Schools />} />
                  <Route path="users" element={<Users />} />
                  <Route path="settings" element={<SystemSettings />} />
                  <Route path="logs" element={<ActivityLogs />} />
                </Route>
              </Route>
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Router>
        </WebSocketProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
EOF
```

## PHASE 5: TESTING AND VERIFICATION (Final 1 hour)

### Task 5.1: Create Dashboard Test Suite
```bash
cat > src/__tests__/dashboard.test.tsx << 'EOF'
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { store } from '../store';
import Login from '../components/pages/Login';
import DashboardHome from '../components/pages/DashboardHome';

// Mock fetch
global.fetch = jest.fn();

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('Login component renders and connects to API', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'healthy' }),
    });

    render(
      <Provider store={store}>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Connected to backend API/i)).toBeInTheDocument();
    });
  });

  test('Login with valid credentials', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'test-token',
          user: {
            id: '1',
            username: 'john_teacher',
            email: 'john@school.edu',
            role: 'teacher',
          },
        }),
      });

    render(
      <Provider store={store}>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </Provider>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(usernameInput, { target: { value: 'john_teacher' } });
    fireEvent.change(passwordInput, { target: { value: 'Teacher123!' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBe('test-token');
    });
  });

  test('WebSocket connection initializes after login', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };

    (global as any).WebSocket = jest.fn(() => mockWebSocket);

    // Simulate successful login
    localStorage.setItem('access_token', 'test-token');
    
    render(
      <Provider store={store}>
        <BrowserRouter>
          <DashboardHome />
        </BrowserRouter>
      </Provider>
    );

    await waitFor(() => {
      expect(WebSocket).toHaveBeenCalledWith(expect.stringContaining('ws://127.0.0.1:8008/ws/'));
    });
  });
});
EOF

# Run tests
npm test -- --coverage
```

### Task 5.2: Manual Testing Checklist
```bash
cat > dashboard_test_checklist.md << 'EOF'
# Dashboard Testing Checklist

## Pre-requisites
- [ ] Terminal 1 has started FastAPI on port 8008
- [ ] Health endpoint responds: `curl http://127.0.0.1:8008/health`
- [ ] Dashboard is running on port 5179

## Authentication Tests
- [ ] Login page loads without errors
- [ ] API connection status shows "Connected"
- [ ] Login with teacher credentials works
- [ ] Login with student credentials works
- [ ] Invalid credentials show error message
- [ ] Token is stored in localStorage
- [ ] Logout clears token and redirects to login

## WebSocket Tests
- [ ] WebSocket connects after login
- [ ] Connection status shows "Live"
- [ ] Heartbeat ping/pong works
- [ ] Reconnection works after disconnect
- [ ] Messages are received in real-time

## Dashboard Features
- [ ] Metrics load from API
- [ ] Real-time updates appear
- [ ] Navigation between pages works
- [ ] Role-based access control works
- [ ] Activity feed updates live

## Responsive Design
- [ ] Mobile view (< 768px) works
- [ ] Tablet view (768px - 1024px) works
- [ ] Desktop view (> 1024px) works
- [ ] Components resize properly

## Error Handling
- [ ] API errors show user-friendly messages
- [ ] Network errors are handled gracefully
- [ ] Loading states display correctly
- [ ] 401 errors redirect to login

## Performance
- [ ] Page load time < 3 seconds
- [ ] API requests < 1 second
- [ ] No memory leaks in WebSocket
- [ ] Smooth animations and transitions
EOF

echo "Run through this checklist manually to verify all features work"
```

## SUCCESS CRITERIA

Before marking Terminal 2 complete:

- [ ] Dashboard loads on http://127.0.0.1:5179
- [ ] Login page connects to FastAPI backend
- [ ] Authentication works with real credentials
- [ ] WebSocket connects and maintains connection
- [ ] Real-time updates display in dashboard
- [ ] All routes navigate correctly
- [ ] Role-based access control enforced
- [ ] Responsive design works on all screen sizes
- [ ] No console errors in browser
- [ ] All tests pass

## HANDOFF TO OTHER TERMINALS

Once complete, notify:

1. **Terminal 3**: Dashboard ready for Roblox plugin integration
2. **Terminal 4**: Frontend ready for security testing
3. **Terminal 5**: Dashboard components ready for documentation
4. **Terminal 6**: Frontend optimized and ready
5. **Terminal 7**: Dashboard ready for CI/CD integration
6. **Terminal 8**: Frontend ready for containerization

## TROUBLESHOOTING

### If dashboard won't start:
```bash
# Check what's using port 5179
lsof -iTCP:5179
kill -9 <PID>

# Clear all caches
rm -rf node_modules .next dist build
npm cache clean --force
npm install
```

### If WebSocket won't connect:
```bash
# Verify FastAPI WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://127.0.0.1:8008/ws/test

# Check browser console for errors
# Ensure token is valid and present
```

### If authentication fails:
```bash
# Test login endpoint directly
curl -X POST http://127.0.0.1:8008/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "john_teacher", "password": "Teacher123!"}'

# Check CORS settings in FastAPI
# Verify token is being sent in headers
```

Remember: The dashboard is the USER INTERFACE. Make it work perfectly!