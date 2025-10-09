/**
 * RobloxSessionManager Component
 * 
 * Manages Roblox educational game sessions
 * Handles session creation, configuration, and lifecycle management
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  Grid,
  Button,
  ActionIcon,
  Badge,
  Modal,
  TextInput,
  Select,
  Checkbox,
  Switch,
  Slider,
  List,
  Avatar,
  Group,
  Tooltip,
  Alert,
  Stepper,
  Paper,
  Stack,
  Title,
  Radio,
  MultiSelect,
  Textarea,
  Divider,
  useMantineTheme
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconSettings,
  IconUsers,
  IconCalendar,
  IconLock,
  IconLockOpen,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCopy,
  IconShare,
  IconQrcode,
  IconLink,
  IconClock,
  IconSchool,
  IconNotes,
  IconHelp,
  IconMountain,
  IconDeviceGamepad,
  IconTrophy,
  IconAlertTriangle,
  IconCircleCheck,
  IconInfoCircle,
  IconUserPlus,
  IconUserMinus,
  IconRefresh,
  IconDownload,
  IconUpload,
  IconDeviceFloppy,
  IconX
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { usePusherContext } from '../../contexts/PusherContext';
import { WebSocketMessageType } from '../../types/websocket';
import { useAppSelector } from '../../store';

interface RobloxSession {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'ready' | 'active' | 'paused' | 'completed' | 'archived';
  createdAt: Date;
  startedAt?: Date;
  endedAt?: Date;
  settings: {
    maxPlayers: number;
    minPlayers: number;
    timeLimit?: number;
    accessType: 'public' | 'private' | 'invite-only';
    accessCode?: string;
    allowLateJoin: boolean;
    allowRejoin: boolean;
    recordSession: boolean;
    enableChat: boolean;
    enableVoice: boolean;
  };
  content: {
    subject: string;
    gradeLevel: number;
    environmentType: string;
    objectives: string[];
    hasQuiz: boolean;
    quizSettings?: {
      numQuestions: number;
      timePerQuestion?: number;
      passingScore: number;
      allowRetake: boolean;
    };
  };
  participants: {
    teacherId: string;
    students: Array<{
      id: string;
      name: string;
      status: 'invited' | 'joined' | 'active' | 'left' | 'kicked';
      joinedAt?: Date;
      leftAt?: Date;
    }>;
  };
  metrics: {
    totalPlayers: number;
    activePlayers: number;
    averageProgress: number;
    completionRate: number;
  };
  gameServerInfo?: {
    serverId: string;
    serverUrl: string;
    placeId: string;
    jobId: string;
  };
}

interface SessionTemplate {
  id: string;
  name: string;
  description: string;
  settings: RobloxSession['settings'];
  content: RobloxSession['content'];
}

const SESSION_TEMPLATES: SessionTemplate[] = [
  // Mathematics Templates
  {
    id: 'quick-math',
    name: 'Quick Math Challenge',
    description: '15-minute math practice session',
    settings: {
      maxPlayers: 30,
      minPlayers: 1,
      timeLimit: 15,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: false,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Mathematics',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: ['Basic arithmetic', 'Problem solving'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 10,
        timePerQuestion: 60,
        passingScore: 70,
        allowRetake: true
      }
    }
  },
  {
    id: 'algebra-adventure',
    name: 'Algebra Adventure',
    description: 'Interactive algebra problem-solving quest',
    settings: {
      maxPlayers: 20,
      minPlayers: 2,
      timeLimit: 45,
      accessType: 'private',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Mathematics',
      gradeLevel: 8,
      environmentType: 'adventure',
      objectives: ['Linear equations', 'Variables', 'Graphing'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 20,
        timePerQuestion: 90,
        passingScore: 75,
        allowRetake: true
      }
    }
  },
  {
    id: 'geometry-builder',
    name: 'Geometry Builder',
    description: 'Build and explore 3D geometric shapes',
    settings: {
      maxPlayers: 15,
      minPlayers: 1,
      timeLimit: 30,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Mathematics',
      gradeLevel: 6,
      environmentType: 'sandbox',
      objectives: ['3D shapes', 'Volume', 'Surface area', 'Spatial reasoning'],
      hasQuiz: false
    }
  },
  
  // Science Templates
  {
    id: 'science-exploration',
    name: 'Science Lab',
    description: 'Interactive science discovery session',
    settings: {
      maxPlayers: 25,
      minPlayers: 5,
      timeLimit: 30,
      accessType: 'private',
      allowLateJoin: false,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Science',
      gradeLevel: 7,
      environmentType: 'laboratory',
      objectives: ['Scientific method', 'Experimentation'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 15,
        passingScore: 75,
        allowRetake: false
      }
    }
  },
  {
    id: 'chemistry-reactions',
    name: 'Chemistry Reactions',
    description: 'Safe virtual chemistry experiments',
    settings: {
      maxPlayers: 20,
      minPlayers: 2,
      timeLimit: 40,
      accessType: 'private',
      allowLateJoin: false,
      allowRejoin: false,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Chemistry',
      gradeLevel: 9,
      environmentType: 'laboratory',
      objectives: ['Chemical reactions', 'Periodic table', 'Lab safety'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 25,
        timePerQuestion: 60,
        passingScore: 80,
        allowRetake: false
      }
    }
  },
  {
    id: 'physics-playground',
    name: 'Physics Playground',
    description: 'Explore physics concepts through interactive simulations',
    settings: {
      maxPlayers: 30,
      minPlayers: 1,
      timeLimit: 35,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Physics',
      gradeLevel: 10,
      environmentType: 'sandbox',
      objectives: ['Newton\'s laws', 'Energy', 'Motion', 'Forces'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 15,
        timePerQuestion: 90,
        passingScore: 70,
        allowRetake: true
      }
    }
  },
  {
    id: 'biology-ecosystem',
    name: 'Biology Ecosystem',
    description: 'Explore living organisms and ecosystems',
    settings: {
      maxPlayers: 25,
      minPlayers: 3,
      timeLimit: 45,
      accessType: 'private',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Biology',
      gradeLevel: 8,
      environmentType: 'outdoor',
      objectives: ['Ecosystems', 'Food chains', 'Biodiversity', 'Conservation'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 20,
        passingScore: 75,
        allowRetake: true
      }
    }
  },
  
  // History & Social Studies Templates
  {
    id: 'history-quest',
    name: 'History Time Travel',
    description: 'Journey through historical periods',
    settings: {
      maxPlayers: 35,
      minPlayers: 5,
      timeLimit: 50,
      accessType: 'private',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'History',
      gradeLevel: 7,
      environmentType: 'adventure',
      objectives: ['Historical events', 'Chronology', 'Cause and effect'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 30,
        passingScore: 70,
        allowRetake: true
      }
    }
  },
  {
    id: 'geography-explorer',
    name: 'World Geography Explorer',
    description: 'Explore countries, cultures, and landmarks',
    settings: {
      maxPlayers: 40,
      minPlayers: 1,
      timeLimit: 30,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Geography',
      gradeLevel: 6,
      environmentType: 'outdoor',
      objectives: ['Countries', 'Capitals', 'Landmarks', 'Cultures'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 25,
        timePerQuestion: 45,
        passingScore: 65,
        allowRetake: true
      }
    }
  },
  
  // Language Arts Templates
  {
    id: 'vocabulary-race',
    name: 'Vocabulary Race',
    description: 'Fast-paced vocabulary building game',
    settings: {
      maxPlayers: 30,
      minPlayers: 2,
      timeLimit: 20,
      accessType: 'public',
      allowLateJoin: false,
      allowRejoin: false,
      recordSession: true,
      enableChat: false,
      enableVoice: false
    },
    content: {
      subject: 'English',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: ['Vocabulary', 'Spelling', 'Word meanings'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 50,
        timePerQuestion: 15,
        passingScore: 70,
        allowRetake: false
      }
    }
  },
  {
    id: 'story-builder',
    name: 'Collaborative Story Builder',
    description: 'Create stories together with classmates',
    settings: {
      maxPlayers: 15,
      minPlayers: 3,
      timeLimit: 40,
      accessType: 'invite-only',
      allowLateJoin: false,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Creative Writing',
      gradeLevel: 6,
      environmentType: 'classroom',
      objectives: ['Story structure', 'Character development', 'Collaboration'],
      hasQuiz: false
    }
  },
  
  // Computer Science Templates
  {
    id: 'coding-basics',
    name: 'Coding Basics',
    description: 'Learn programming fundamentals',
    settings: {
      maxPlayers: 20,
      minPlayers: 1,
      timeLimit: 45,
      accessType: 'private',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Computer Science',
      gradeLevel: 7,
      environmentType: 'laboratory',
      objectives: ['Algorithms', 'Logic', 'Problem-solving', 'Debugging'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 15,
        timePerQuestion: 120,
        passingScore: 75,
        allowRetake: true
      }
    }
  },
  
  // Art & Music Templates
  {
    id: 'art-studio',
    name: 'Digital Art Studio',
    description: 'Create and share digital artwork',
    settings: {
      maxPlayers: 25,
      minPlayers: 1,
      timeLimit: 60,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: false,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Art',
      gradeLevel: 5,
      environmentType: 'sandbox',
      objectives: ['Color theory', 'Composition', 'Digital tools'],
      hasQuiz: false
    }
  },
  {
    id: 'music-composer',
    name: 'Music Composer',
    description: 'Compose and perform music together',
    settings: {
      maxPlayers: 20,
      minPlayers: 2,
      timeLimit: 45,
      accessType: 'private',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Music',
      gradeLevel: 6,
      environmentType: 'classroom',
      objectives: ['Rhythm', 'Melody', 'Harmony', 'Collaboration'],
      hasQuiz: false
    }
  },
  
  // Special Sessions
  {
    id: 'quick-review',
    name: 'Quick Review Session',
    description: '10-minute review before tests',
    settings: {
      maxPlayers: 50,
      minPlayers: 1,
      timeLimit: 10,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: false,
      recordSession: false,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'General',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: ['Review', 'Test preparation'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 10,
        timePerQuestion: 45,
        passingScore: 60,
        allowRetake: false
      }
    }
  },
  {
    id: 'group-project',
    name: 'Group Project Space',
    description: 'Collaborative project work environment',
    settings: {
      maxPlayers: 10,
      minPlayers: 2,
      timeLimit: 90,
      accessType: 'invite-only',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'General',
      gradeLevel: 7,
      environmentType: 'sandbox',
      objectives: ['Collaboration', 'Project management', 'Presentation'],
      hasQuiz: false
    }
  }
];

export const RobloxSessionManager: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const navigate = useNavigate();
  const { sendMessage, on, isConnected } = usePusherContext();
  const currentUser = useAppSelector(state => state.user);
  
  const [sessions, setSessions] = useState<RobloxSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<RobloxSession | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [newSession, setNewSession] = useState<Partial<RobloxSession>>({
    name: '',
    description: '',
    settings: {
      maxPlayers: 30,
      minPlayers: 1,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: '',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: [],
      hasQuiz: false
    }
  });
  const [studentSearch, setStudentSearch] = useState('');
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  // WebSocket event handlers
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeSessions = on(WebSocketMessageType.SESSION_UPDATE, (data: any) => {
      if (data.action === 'created') {
        setSessions(prev => [...prev, data.session]);
      } else if (data.action === 'updated') {
        setSessions(prev => prev.map(s => s.id === data.session.id ? data.session : s));
      } else if (data.action === 'deleted') {
        setSessions(prev => prev.filter(s => s.id !== data.sessionId));
      }
    });

    const unsubscribeStatus = on(WebSocketMessageType.SESSION_STATUS, (data: any) => {
      setSessions(prev => prev.map(session => {
        if (session.id === data.sessionId) {
          return {
            ...session,
            status: data.status,
            metrics: data.metrics || session.metrics
          };
        }
        return session;
      }));
    });

    // Load existing sessions
    sendMessage(WebSocketMessageType.REQUEST_SESSIONS, {});

    return () => {
      unsubscribeSessions();
      unsubscribeStatus();
    };
  }, [isConnected]);

  const handleCreateSession = () => {
    if (activeStep < 3) {
      setActiveStep(prev => prev + 1);
      return;
    }

    const session: RobloxSession = {
      id: `session_${Date.now()}`,
      name: newSession.name!,
      description: newSession.description,
      status: 'draft',
      createdAt: new Date(),
      settings: newSession.settings!,
      content: newSession.content!,
      participants: {
        teacherId: currentUser.userId!,
        students: selectedStudents.map(id => ({
          id,
          name: `Student ${id}`,
          status: 'invited' as const
        }))
      },
      metrics: {
        totalPlayers: 0,
        activePlayers: 0,
        averageProgress: 0,
        completionRate: 0
      }
    };

    sendMessage(WebSocketMessageType.CREATE_SESSION, session);
    setSessions(prev => [...prev, session]);
    setCreateDialogOpen(false);
    resetNewSession();
    
    // Navigate to environment preview after creation
    navigate('/roblox/environment-preview', {
      state: {
        sessionId: session.id,
        sessionData: session,
        mode: 'setup'
      }
    });
  };

  const handleStartSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'start'
    });
    
    const session = sessions.find(s => s.id === sessionId);
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'active', startedAt: new Date() };
      }
      return s;
    }));
    
    // Navigate to Roblox Environment Preview with session data
    if (session) {
      navigate('/roblox/environment-preview', {
        state: {
          sessionId,
          sessionData: session,
          mode: 'live'
        }
      });
    }
  };

  const handlePauseSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'pause'
    });
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'paused' };
      }
      return s;
    }));
  };

  const handleStopSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'stop'
    });
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'completed', endedAt: new Date() };
      }
      return s;
    }));
  };

  const handleDeleteSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.DELETE_SESSION, { sessionId });
    setSessions(prev => prev.filter(s => s.id !== sessionId));
  };

  const handleDuplicateSession = (session: RobloxSession) => {
    const duplicated = {
      ...session,
      id: `session_${Date.now()}`,
      name: `${session.name} (Copy)`,
      status: 'draft' as const,
      createdAt: new Date(),
      startedAt: undefined,
      endedAt: undefined
    };
    
    sendMessage(WebSocketMessageType.CREATE_SESSION, duplicated);
    setSessions(prev => [...prev, duplicated]);
  };

  const handleApplyTemplate = (template: SessionTemplate) => {
    setSelectedTemplateId(template.id);
    setNewSession({
      ...newSession,
      settings: { ...template.settings },
      content: { ...template.content }
    });
  };

  const resetNewSession = () => {
    setNewSession({
      name: '',
      description: '',
      settings: {
        maxPlayers: 30,
        minPlayers: 1,
        accessType: 'public',
        allowLateJoin: true,
        allowRejoin: true,
        recordSession: true,
        enableChat: true,
        enableVoice: false
      },
      content: {
        subject: '',
        gradeLevel: 5,
        environmentType: 'classroom',
        objectives: [],
        hasQuiz: false
      }
    });
    setActiveStep(0);
    setSelectedStudents([]);
    setSelectedTemplateId(null);
  };

  const getSessionStatusColor = (status: RobloxSession['status']) => {
    switch (status) {
      case 'draft': return 'default';
      case 'ready': return 'info';
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'completed': return 'default';
      case 'archived': return 'default';
      default: return 'default';
    }
  };

  const generateAccessCode = () => {
    const code = Math.random().toString(36).substring(2, 8).toUpperCase();
    setNewSession(prev => ({
      ...prev,
      settings: {
        ...prev.settings!,
        accessCode: code
      }
    }));
  };

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <Card>
        <Card.Section p="md">
          <Group justify="space-between" align="center">
            <Group align="center">
              <IconDeviceGamepad color={theme.colors.blue[6]} size={32} />
              <Box>
                <Title order={3}>Session Manager</Title>
                <Text size="sm" c="dimmed">
                  Create and manage Roblox educational game sessions
                </Text>
              </Box>
            </Group>

            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => setCreateDialogOpen(true)}
            >
              New Session
            </Button>
          </Group>
        </Card.Section>
      </Card>

      {/* Sessions Grid */}
      <Grid gutter="md" style={{ flex: 1, overflow: 'auto' }}>
        {sessions.map((session) => (
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={session.id}>
            <Card
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                border: session.status === 'active' ? `2px solid ${theme.colors.green[6]}` : `1px solid ${theme.colors.gray[3]}`
              }}
            >
              <Card.Section p="md" style={{ flex: 1 }}>
                <Group justify="space-between" align="flex-start" mb="md">
                  <Box>
                    <Text size="lg" fw={600} mb="xs">
                      {session.name}
                    </Text>
                    <Badge
                      color={
                        getSessionStatusColor(session.status) === 'info' ? 'blue' :
                        getSessionStatusColor(session.status) === 'success' ? 'green' :
                        getSessionStatusColor(session.status) === 'warning' ? 'yellow' : 'gray'
                      }
                      size="sm"
                    >
                      {session.status}
                    </Badge>
                  </Box>

                  <Group gap="xs">
                    {session.settings.accessType === 'private' && (
                      <Tooltip label="Private Session">
                        <IconLock size={16} color={theme.colors.gray[6]} />
                      </Tooltip>
                    )}
                    {session.settings.recordSession && (
                      <Tooltip label="Recording Enabled">
                        <Box style={{ position: 'relative' }}>
                          <IconClock size={16} color={theme.colors.gray[6]} />
                          <Box
                            style={{
                              position: 'absolute',
                              top: -2,
                              right: -2,
                              width: 6,
                              height: 6,
                              backgroundColor: theme.colors.red[6],
                              borderRadius: '50%'
                            }}
                          />
                        </Box>
                      </Tooltip>
                    )}
                  </Group>
                </Group>

                {session.description && (
                  <Text size="sm" c="dimmed" mb="md">
                    {session.description}
                  </Text>
                )}

                <Grid gutter="xs" mb="md">
                  <Grid.Col span={6}>
                    <Text size="xs" c="dimmed">Subject</Text>
                    <Text size="sm">{session.content.subject}</Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="xs" c="dimmed">Grade</Text>
                    <Text size="sm">Level {session.content.gradeLevel}</Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="xs" c="dimmed">Environment</Text>
                    <Text size="sm">{session.content.environmentType}</Text>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <Text size="xs" c="dimmed">Players</Text>
                    <Text size="sm">
                      {session.metrics.activePlayers}/{session.settings.maxPlayers}
                    </Text>
                  </Grid.Col>
                </Grid>

                {session.participants.students.length > 0 && (
                  <Group align="center" mb="md">
                    <Avatar.Group spacing="sm">
                      {session.participants.students
                        .filter(s => s.status === 'active')
                        .slice(0, 4)
                        .map((student) => (
                          <Avatar key={student.id} size={24}>
                            {student.name[0]}
                          </Avatar>
                        ))}
                      {session.participants.students.filter(s => s.status === 'active').length > 4 && (
                        <Avatar size={24}>+{session.participants.students.filter(s => s.status === 'active').length - 4}</Avatar>
                      )}
                    </Avatar.Group>
                    <Text size="xs" c="dimmed">
                      {session.participants.students.filter(s => s.status === 'active').length} active
                    </Text>
                  </Group>
                )}

                {session.settings.timeLimit && (
                  <Alert color="blue" mt="md">
                    <Text size="xs">
                      {session.settings.timeLimit} minute time limit
                    </Text>
                  </Alert>
                )}
              </Card.Section>

              <Divider />

              <Card.Section p="md">
                <Group>
                  {session.status === 'draft' && (
                    <>
                      <Button
                        size="sm"
                        leftSection={<IconEdit size={16} />}
                        onClick={() => {
                          setSelectedSession(session);
                          setSettingsDialogOpen(true);
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        color="green"
                        leftSection={<IconPlayerPlay size={16} />}
                        onClick={() => handleStartSession(session.id)}
                      >
                        Start
                      </Button>
                    </>
                  )}

                  {session.status === 'active' && (
                    <>
                      <Button
                        size="sm"
                        color="yellow"
                        leftSection={<IconPlayerPause size={16} />}
                        onClick={() => handlePauseSession(session.id)}
                      >
                        Pause
                      </Button>
                      <Button
                        size="sm"
                        color="red"
                        leftSection={<IconPlayerStop size={16} />}
                        onClick={() => handleStopSession(session.id)}
                      >
                        Stop
                      </Button>
                    </>
                  )}

                  {session.status === 'paused' && (
                    <Button
                      size="sm"
                      color="green"
                      leftSection={<IconPlayerPlay size={16} />}
                      onClick={() => handleStartSession(session.id)}
                    >
                      Resume
                    </Button>
                  )}

                  <ActionIcon
                    size="sm"
                    onClick={() => handleDuplicateSession(session)}
                  >
                    <IconCopy size={16} />
                  </ActionIcon>

                  <ActionIcon
                    size="sm"
                    onClick={() => {
                      setSelectedSession(session);
                      setInviteDialogOpen(true);
                    }}
                  >
                    <IconShare size={16} />
                  </ActionIcon>

                  {(session.status === 'draft' || session.status === 'completed') && (
                    <ActionIcon
                      size="sm"
                      color="red"
                      onClick={() => handleDeleteSession(session.id)}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  )}
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
        ))}
      </Grid>

      {/* Create Session Dialog */}
      <Modal
        opened={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        title="Create New Session"
        size="lg"
      >
        <Stepper active={activeStep} orientation="vertical">
          <Stepper.Step label="Basic Information">
            <Stack gap="md" mt="md">
              <TextInput
                label="Session Name"
                value={newSession.name}
                onChange={(event) => setNewSession({ ...newSession, name: event.currentTarget.value })}
              />
              <Textarea
                label="Description (Optional)"
                rows={3}
                value={newSession.description}
                onChange={(event) => setNewSession({ ...newSession, description: event.currentTarget.value })}
              />

              <Box>
                <Text size="sm" fw={600} mb="sm">
                  Quick Templates
                </Text>
                <Group gap="xs" wrap="wrap">
                  {SESSION_TEMPLATES.map((template) => (
                    <Badge
                      key={template.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleApplyTemplate(template)}
                      color={selectedTemplateId === template.id ? 'blue' : 'gray'}
                      variant={selectedTemplateId === template.id ? 'filled' : 'outline'}
                    >
                      {template.name}
                    </Badge>
                  ))}
                </Group>
              </Box>
            </Stack>
          </Stepper.Step>

          <Stepper.Step label="Content Settings">
            <Grid gutter="md" mt="md">
              <Grid.Col span={6}>
                <Select
                  label="Subject"
                  value={newSession.content?.subject}
                  onChange={(value) => setNewSession({
                    ...newSession,
                    content: { ...newSession.content!, subject: value || '' }
                  })}
                  data={[
                    { value: 'Mathematics', label: 'Mathematics' },
                    { value: 'Science', label: 'Science' },
                    { value: 'English', label: 'English' },
                    { value: 'History', label: 'History' },
                    { value: 'Geography', label: 'Geography' }
                  ]}
                />
              </Grid.Col>

              <Grid.Col span={6}>
                <Select
                  label="Grade Level"
                  value={newSession.content?.gradeLevel?.toString()}
                  onChange={(value) => setNewSession({
                    ...newSession,
                    content: { ...newSession.content!, gradeLevel: Number(value) }
                  })}
                  data={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(grade => ({
                    value: grade.toString(),
                    label: `Grade ${grade}`
                  }))}
                />
              </Grid.Col>

              <Grid.Col span={12}>
                <Select
                  label="Environment Type"
                  value={newSession.content?.environmentType}
                  onChange={(value) => setNewSession({
                    ...newSession,
                    content: { ...newSession.content!, environmentType: value || '' }
                  })}
                  data={[
                    { value: 'classroom', label: 'Classroom' },
                    { value: 'laboratory', label: 'Laboratory' },
                    { value: 'outdoor', label: 'Outdoor' },
                    { value: 'space_station', label: 'Space Station' },
                    { value: 'underwater', label: 'Underwater' },
                    { value: 'historical', label: 'Historical' }
                  ]}
                />
              </Grid.Col>

              <Grid.Col span={12}>
                <Group align="center">
                  <Text size="sm">Include Quiz</Text>
                  <Switch
                    checked={newSession.content?.hasQuiz}
                    onChange={(event) => setNewSession({
                      ...newSession,
                      content: { ...newSession.content!, hasQuiz: event.currentTarget.checked }
                    })}
                  />
                </Group>
              </Grid.Col>
            </Grid>
          </Stepper.Step>

          <Stepper.Step label="Session Settings">
            <Stack gap="md" mt="md">
              <Box>
                <Text size="sm" mb="sm">Access Type</Text>
                <Radio.Group
                  value={newSession.settings?.accessType}
                  onChange={(value) => setNewSession({
                    ...newSession,
                    settings: { ...newSession.settings!, accessType: value as any }
                  })}
                >
                  <Group>
                    <Radio value="public" label="Public" />
                    <Radio value="private" label="Private" />
                    <Radio value="invite-only" label="Invite Only" />
                  </Group>
                </Radio.Group>
              </Box>

              {newSession.settings?.accessType === 'private' && (
                <TextInput
                  label="Access Code"
                  value={newSession.settings?.accessCode}
                  onChange={(event) => setNewSession({
                    ...newSession,
                    settings: { ...newSession.settings!, accessCode: event.currentTarget.value }
                  })}
                  rightSection={
                    <Button size="xs" onClick={generateAccessCode}>
                      Generate
                    </Button>
                  }
                />
              )}

              <Grid gutter="md">
                <Grid.Col span={6}>
                  <Text size="sm" mb="sm">Max Players: {newSession.settings?.maxPlayers}</Text>
                  <Slider
                    value={newSession.settings?.maxPlayers}
                    onChange={(value) => setNewSession({
                      ...newSession,
                      settings: { ...newSession.settings!, maxPlayers: value }
                    })}
                    min={1}
                    max={50}
                    step={5}
                    marks
                  />
                </Grid.Col>

                <Grid.Col span={6}>
                  <Text size="sm" mb="sm">Time Limit (minutes): {newSession.settings?.timeLimit || 'None'}</Text>
                  <Slider
                    value={newSession.settings?.timeLimit || 0}
                    onChange={(value) => setNewSession({
                      ...newSession,
                      settings: { ...newSession.settings!, timeLimit: value || undefined }
                    })}
                    min={0}
                    max={120}
                    step={15}
                    marks
                  />
                </Grid.Col>
              </Grid>

              <Stack gap="xs">
                <Checkbox
                  label="Allow Late Join"
                  checked={newSession.settings?.allowLateJoin}
                  onChange={(event) => setNewSession({
                    ...newSession,
                    settings: { ...newSession.settings!, allowLateJoin: event.currentTarget.checked }
                  })}
                />
                <Checkbox
                  label="Record Session"
                  checked={newSession.settings?.recordSession}
                  onChange={(event) => setNewSession({
                    ...newSession,
                    settings: { ...newSession.settings!, recordSession: event.currentTarget.checked }
                  })}
                />
                <Checkbox
                  label="Enable Chat"
                  checked={newSession.settings?.enableChat}
                  onChange={(event) => setNewSession({
                    ...newSession,
                    settings: { ...newSession.settings!, enableChat: event.currentTarget.checked }
                  })}
                />
              </Stack>
            </Stack>
          </Stepper.Step>

          <Stepper.Step label="Invite Students" description="Optional">
            <Stack gap="md" mt="md">
              <MultiSelect
                label="Search students..."
                placeholder="Type to search"
                data={['student1', 'student2', 'student3']} // Would be fetched from API
                value={selectedStudents}
                onChange={setSelectedStudents}
                searchable
              />

              <Alert color="blue">
                <Text size="sm" fw={600}>Note</Text>
                <Text size="sm">You can also invite students after creating the session</Text>
              </Alert>
            </Stack>
          </Stepper.Step>
        </Stepper>

        <Group justify="flex-end" mt="lg">
          <Button variant="outline" onClick={() => {
            setCreateDialogOpen(false);
            resetNewSession();
          }}>
            Cancel
          </Button>
          {activeStep > 0 && (
            <Button variant="outline" onClick={() => setActiveStep(prev => prev - 1)}>
              Back
            </Button>
          )}
          <Button onClick={handleCreateSession}>
            {activeStep < 3 ? 'Next' : 'Create Session'}
          </Button>
        </Group>
      </Modal>

      {/* Empty State */}
      {sessions.length === 0 && (
        <Box
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '16px'
          }}
        >
          <IconDeviceGamepad size={64} color={theme.colors.gray[4]} />
          <Text size="lg" c="dimmed">
            No sessions yet
          </Text>
          <Text size="sm" c="dimmed">
            Create your first educational game session
          </Text>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Session
          </Button>
        </Box>
      )}
    </Box>
  );
};