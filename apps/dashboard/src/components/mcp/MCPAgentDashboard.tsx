import * as React from "react";
import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  IconButton,
  Skeleton,
  Alert,
  Grid,
  Paper,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import {
  SmartToy,
  Psychology,
  School,
  Quiz,
  Terrain,
  Code,
  RateReview,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  Memory,
  Speed,
  CheckCircle,
  Error,
  Warning,
  Info,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { useWebSocketContext } from "../../contexts/WebSocketContext";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";

interface MCPAgent {
  id: string;
  name: string;
  type: "supervisor" | "content" | "quiz" | "terrain" | "script" | "review";
  status: "active" | "idle" | "working" | "error" | "offline";
  lastActivity: string;
  tasksCompleted: number;
  avgResponseTime: number;
  successRate: number;
  memoryUsage: number;
  cpuUsage: number;
  currentTask?: {
    id: string;
    type: string;
    progress: number;
    startedAt: string;
  };
  capabilities: string[];
  metrics: {
    timestamp: string;
    responseTime: number;
    memoryUsage: number;
    cpuUsage: number;
  }[];
}

interface MCPMessage {
  id: string;
  type: "request" | "response" | "notification" | "error";
  agentId: string;
  content: string;
  timestamp: string;
  data?: any;
}

interface MCPAgentDashboardProps {
  autoRefresh?: boolean;
  showLogs?: boolean;
}

const AGENT_ICONS: Record<string, React.ReactElement> = {
  supervisor: <SmartToy />,
  content: <Psychology />,
  quiz: <Quiz />,
  terrain: <Terrain />,
  script: <Code />,
  review: <RateReview />,
};

const AGENT_COLORS: Record<string, string> = {
  supervisor: "#2563EB",
  content: "#22C55E",
  quiz: "#FACC15",
  terrain: "#9333EA",
  script: "#EF4444",
  review: "#06B6D4",
};

export function MCPAgentDashboard({ 
  autoRefresh = true,
  showLogs = true 
}: MCPAgentDashboardProps) {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { isConnected, subscribe, unsubscribe, sendMessage } = useWebSocketContext();
  
  const [agents, setAgents] = useState<MCPAgent[]>([]);
  const [messages, setMessages] = useState<MCPMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<MCPAgent | null>(null);
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false);
  const [taskType, setTaskType] = useState<string>("");
  const [taskContent, setTaskContent] = useState<string>("");
  const [mcpWebSocket, setMcpWebSocket] = useState<WebSocket | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const MAX_RECONNECT_ATTEMPTS = 3;
  const RECONNECT_DELAY_BASE = 5000; // Base delay in ms

  // Connect to MCP WebSocket server on port 9876 with retry logic
  const connectToMCP = React.useCallback(async () => {
    // Check if we've exceeded max reconnection attempts
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log('Max reconnection attempts reached. Using mock data.');
      setError('MCP server unavailable - using mock data');
      loadMockData();
      setLoading(false);
      return;
    }

    // Close existing connection if any
    if (mcpWebSocket && mcpWebSocket.readyState !== WebSocket.CLOSED) {
      mcpWebSocket.close();
    }

    try {
      setLoading(true);
      setError(null);

      // Initialize WebSocket connection to MCP server
      const mcpWs = new WebSocket('ws://localhost:9876/mcp');
      setMcpWebSocket(mcpWs);
      
      mcpWs.onopen = () => {
        console.log('Connected to MCP server');
        setReconnectAttempts(0); // Reset attempts on successful connection
        // Request agent status
        mcpWs.send(JSON.stringify({
          type: 'get_agents_status',
          timestamp: new Date().toISOString(),
        }));
      };

      mcpWs.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMCPMessage(message);
      };

      mcpWs.onerror = (error) => {
        console.error('MCP WebSocket error:', error);
        setError('MCP connection error - will retry');
      };

      mcpWs.onclose = (event) => {
        console.log('MCP WebSocket connection closed:', event.code, event.reason);
        setMcpWebSocket(null);
        
        // Only retry if autoRefresh is enabled and we haven't exceeded max attempts
        if (autoRefresh && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttempts); // Exponential backoff
          console.log(`Reconnecting in ${delay/1000} seconds... (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          setReconnectAttempts(prev => prev + 1);
          setTimeout(() => {
            connectToMCP();
          }, delay);
        } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          setError('MCP server unavailable - using mock data');
          loadMockData();
        }
      };

    } catch (err: any) {
      console.error('Failed to create WebSocket connection:', err);
      setError(err.message || 'Failed to connect to MCP server');
      setMcpWebSocket(null);
      
      // Use mock data as fallback
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS - 1) {
        loadMockData();
      }
    } finally {
      setLoading(false);
    }
  }, [autoRefresh, reconnectAttempts, mcpWebSocket]);

  // Handle MCP messages
  const handleMCPMessage = (message: any) => {
    switch (message.type) {
      case 'agents_status':
        if (message.agents) {
          setAgents(message.agents);
        }
        break;
      case 'agent_update':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { ...agent, ...message.updates }
              : agent
          )
        );
        break;
      case 'task_progress':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { 
                  ...agent, 
                  currentTask: message.task,
                  status: "working"
                }
              : agent
          )
        );
        break;
      case 'task_completed':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { 
                  ...agent, 
                  currentTask: undefined,
                  status: "active",
                  tasksCompleted: agent.tasksCompleted + 1,
                  lastActivity: new Date().toISOString(),
                }
              : agent
          )
        );
        break;
      case 'error':
        dispatch(addNotification({
          type: 'error',
          message: `MCP Error: ${message.error}`,
        }));
        break;
      default:
        // Add to message log
        setMessages(prevMessages => [
          {
            id: Date.now().toString(),
            type: message.type,
            agentId: message.agentId || 'system',
            content: message.content || JSON.stringify(message),
            timestamp: new Date().toISOString(),
            data: message,
          },
          ...prevMessages.slice(0, 99), // Keep last 100 messages
        ]);
        break;
    }
  };

  // Load mock data when MCP is not available
  const loadMockData = () => {
    const mockAgents: MCPAgent[] = [
      {
        id: "supervisor",
        name: "Supervisor Agent",
        type: "supervisor",
        status: "active",
        lastActivity: new Date().toISOString(),
        tasksCompleted: 156,
        avgResponseTime: 245,
        successRate: 98.5,
        memoryUsage: 68,
        cpuUsage: 42,
        capabilities: ["orchestration", "task_routing", "error_handling"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 500) + 200,
          memoryUsage: Math.floor(Math.random() * 20) + 60,
          cpuUsage: Math.floor(Math.random() * 30) + 30,
        })),
      },
      {
        id: "content",
        name: "Content Generator",
        type: "content",
        status: "working",
        lastActivity: new Date().toISOString(),
        tasksCompleted: 89,
        avgResponseTime: 1200,
        successRate: 94.2,
        memoryUsage: 85,
        cpuUsage: 78,
        currentTask: {
          id: "task_001",
          type: "generate_lesson",
          progress: 65,
          startedAt: new Date(Date.now() - 120000).toISOString(),
        },
        capabilities: ["lesson_generation", "content_creation", "curriculum_design"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 1000) + 800,
          memoryUsage: Math.floor(Math.random() * 25) + 70,
          cpuUsage: Math.floor(Math.random() * 40) + 60,
        })),
      },
      {
        id: "quiz",
        name: "Quiz Agent",
        type: "quiz",
        status: "idle",
        lastActivity: new Date(Date.now() - 300000).toISOString(),
        tasksCompleted: 234,
        avgResponseTime: 180,
        successRate: 96.8,
        memoryUsage: 45,
        cpuUsage: 25,
        capabilities: ["quiz_generation", "assessment_creation", "grading"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 300) + 150,
          memoryUsage: Math.floor(Math.random() * 15) + 40,
          cpuUsage: Math.floor(Math.random() * 20) + 20,
        })),
      },
      {
        id: "terrain",
        name: "Terrain Builder",
        type: "terrain",
        status: "active",
        lastActivity: new Date(Date.now() - 60000).toISOString(),
        tasksCompleted: 67,
        avgResponseTime: 3400,
        successRate: 91.5,
        memoryUsage: 92,
        cpuUsage: 85,
        capabilities: ["3d_modeling", "environment_design", "world_building"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 2000) + 2500,
          memoryUsage: Math.floor(Math.random() * 20) + 80,
          cpuUsage: Math.floor(Math.random() * 30) + 70,
        })),
      },
      {
        id: "script",
        name: "Script Agent",
        type: "script",
        status: "error",
        lastActivity: new Date(Date.now() - 180000).toISOString(),
        tasksCompleted: 145,
        avgResponseTime: 890,
        successRate: 89.2,
        memoryUsage: 58,
        cpuUsage: 35,
        capabilities: ["lua_scripting", "code_generation", "debugging"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 800) + 600,
          memoryUsage: Math.floor(Math.random() * 20) + 50,
          cpuUsage: Math.floor(Math.random() * 25) + 30,
        })),
      },
      {
        id: "review",
        name: "Review Agent",
        type: "review",
        status: "active",
        lastActivity: new Date(Date.now() - 30000).toISOString(),
        tasksCompleted: 201,
        avgResponseTime: 320,
        successRate: 97.1,
        memoryUsage: 52,
        cpuUsage: 28,
        capabilities: ["content_review", "quality_assurance", "validation"],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 400) + 250,
          memoryUsage: Math.floor(Math.random() * 15) + 45,
          cpuUsage: Math.floor(Math.random() * 20) + 25,
        })),
      },
    ];

    setAgents(mockAgents);
  };

  // Initial connection with cleanup
  useEffect(() => {
    let mounted = true;
    
    // Only connect if component is mounted and no existing connection
    if (mounted && !mcpWebSocket) {
      connectToMCP();
    }
    
    // Cleanup on unmount
    return () => {
      mounted = false;
      if (mcpWebSocket && mcpWebSocket.readyState !== WebSocket.CLOSED) {
        mcpWebSocket.close();
      }
    };
  }, []); // Remove connectToMCP from dependencies to avoid reconnection loops

  // Real-time updates via regular WebSocket
  useEffect(() => {
    if (!isConnected || !autoRefresh) return;

    const subscriptionId = subscribe('mcp_agents', (message: any) => {
      handleMCPMessage(message);
    });

    return () => {
      unsubscribe(subscriptionId);
    };
  }, [isConnected, autoRefresh, subscribe, unsubscribe]);

  // Send task to agent
  const handleSendTask = async () => {
    if (!selectedAgent || !taskType || !taskContent) return;

    try {
      // Send task via WebSocket or MCP
      const message = {
        type: 'assign_task',
        agentId: selectedAgent.id,
        task: {
          type: taskType,
          content: taskContent,
          timestamp: new Date().toISOString(),
        },
      };

      if (sendMessage) {
        sendMessage('mcp_agents', message);
      }

      dispatch(addNotification({
        type: 'success',
        message: `Task sent to ${selectedAgent.name}`,
      }));

      setIsTaskDialogOpen(false);
      setTaskType("");
      setTaskContent("");
    } catch (error) {
      dispatch(addNotification({
        type: 'error',
        message: 'Failed to send task to agent',
      }));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "success";
      case "working":
        return "warning";
      case "idle":
        return "default";
      case "error":
        return "error";
      case "offline":
        return "error";
      default:
        return "default";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle color="success" />;
      case "working":
        return <PlayArrow color="warning" />;
      case "idle":
        return <Pause color="disabled" />;
      case "error":
        return <Error color="error" />;
      case "offline":
        return <Stop color="error" />;
      default:
        return <Info />;
    }
  };

  if (loading) {
    return (
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} md={6} lg={4} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" height={40} />
                <Skeleton variant="rectangular" height={200} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Header */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                MCP Agent Dashboard
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                {mcpWebSocket && mcpWebSocket.readyState === WebSocket.OPEN ? (
                  <Chip label="MCP Connected" color="success" size="small" />
                ) : reconnectAttempts > 0 ? (
                  <Chip 
                    label={`Reconnecting... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`} 
                    color="warning" 
                    size="small" 
                  />
                ) : (
                  <Chip label="MCP Offline" color="default" size="small" />
                )}
                <IconButton 
                  onClick={() => {
                    setReconnectAttempts(0);
                    connectToMCP();
                  }}
                  disabled={mcpWebSocket && mcpWebSocket.readyState === WebSocket.CONNECTING}
                >
                  <Refresh />
                </IconButton>
              </Stack>
            </Stack>

            {error && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                MCP Connection Issue: {error} (Using mock data)
              </Alert>
            )}

            {/* Quick Stats */}
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Active Agents
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {agents.filter(a => a.status === "active" || a.status === "working").length}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Tasks Completed
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0)}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Avg Response Time
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'info.main' }}>
                    {Math.round(agents.reduce((sum, agent) => sum + agent.avgResponseTime, 0) / agents.length)}ms
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Success Rate
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'warning.main' }}>
                    {Math.round(agents.reduce((sum, agent) => sum + agent.successRate, 0) / agents.length)}%
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Agent Cards */}
      {agents.map((agent) => (
        <Grid item xs={12} md={6} lg={4} key={agent.id}>
          <Card>
            <CardContent>
              <Stack spacing={2}>
                {/* Agent Header */}
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar sx={{ bgcolor: AGENT_COLORS[agent.type] + '20', color: AGENT_COLORS[agent.type] }}>
                      {AGENT_ICONS[agent.type]}
                    </Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {agent.name}
                      </Typography>
                      <Chip 
                        label={agent.status} 
                        size="small" 
                        color={getStatusColor(agent.status) as any}
                        icon={getStatusIcon(agent.status)}
                      />
                    </Box>
                  </Stack>
                  <IconButton 
                    size="small"
                    onClick={() => {
                      setSelectedAgent(agent);
                      setIsTaskDialogOpen(true);
                    }}
                  >
                    <Settings />
                  </IconButton>
                </Stack>

                {/* Current Task */}
                {agent.currentTask && (
                  <Paper sx={{ p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Current Task: {agent.currentTask.type}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={agent.currentTask.progress}
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="caption">
                      {agent.currentTask.progress}% complete • Started {new Date(agent.currentTask.startedAt).toLocaleTimeString()}
                    </Typography>
                  </Paper>
                )}

                {/* Agent Stats */}
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Tasks Completed
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.tasksCompleted}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Success Rate
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.successRate.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Response Time
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.avgResponseTime}ms
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Memory Usage
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.memoryUsage}%
                    </Typography>
                  </Grid>
                </Grid>

                {/* Performance Chart */}
                <Box sx={{ height: 100 }}>
                  <ResponsiveContainer>
                    <LineChart data={agent.metrics.slice(-10)}>
                      <Line
                        type="monotone"
                        dataKey="responseTime"
                        stroke={AGENT_COLORS[agent.type]}
                        strokeWidth={2}
                        dot={false}
                      />
                      <Tooltip />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>

                {/* Capabilities */}
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {agent.capabilities.slice(0, 3).map((capability) => (
                    <Chip
                      key={capability}
                      label={capability}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      ))}

      {/* Message Log */}
      {showLogs && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                MCP Message Log
              </Typography>
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {messages.slice(0, 20).map((message, index) => (
                  <React.Fragment key={message.id}>
                    <ListItem>
                      <ListItemIcon>
                        {AGENT_ICONS[agents.find(a => a.id === message.agentId)?.type || 'supervisor']}
                      </ListItemIcon>
                      <ListItemText
                        primary={message.content}
                        secondary={`${message.type} • ${new Date(message.timestamp).toLocaleTimeString()}`}
                      />
                    </ListItem>
                    {index < messages.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Task Assignment Dialog */}
      <Dialog open={isTaskDialogOpen} onClose={() => setIsTaskDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Assign Task to {selectedAgent?.name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Task Type</InputLabel>
              <Select
                value={taskType}
                label="Task Type"
                onChange={(e) => setTaskType(e.target.value)}
              >
                <MenuItem value="generate_content">Generate Content</MenuItem>
                <MenuItem value="create_quiz">Create Quiz</MenuItem>
                <MenuItem value="build_terrain">Build Terrain</MenuItem>
                <MenuItem value="write_script">Write Script</MenuItem>
                <MenuItem value="review_content">Review Content</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Task Content"
              value={taskContent}
              onChange={(e) => setTaskContent(e.target.value)}
              placeholder="Describe the task details..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsTaskDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSendTask} variant="contained">Assign Task</Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}

export default MCPAgentDashboard;