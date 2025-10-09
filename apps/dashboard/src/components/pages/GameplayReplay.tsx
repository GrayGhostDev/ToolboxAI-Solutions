import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  Button,
  Stack,
  ActionIcon,
  Progress,
  Badge,
  Alert,
  Slider,
  Select,
  Paper,
  List,
  Divider,
  Tabs,
  Avatar,
  Grid,
  Group,
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerSkipForward,
  IconPlayerSkipBack,
  IconReload,
  IconMaximize,
  IconTrophy,
  IconStarFilled,
  IconTrendingUp,
  IconSchool,
  IconCircleCheck,
  IconAlertTriangle,
  IconDeviceGamepad,
  IconBulb,
  IconDownload,
  IconShare,
  IconCalendar,
} from '@tabler/icons-react';
import { useAppSelector } from '../../store';

interface GameplaySession {
  id: string;
  studentName: string;
  studentAvatar: string;
  worldName: string;
  worldThumbnail: string;
  date: Date;
  duration: number; // in seconds
  highlights: Highlight[];
  achievements: Achievement[];
  interactions: Interaction[];
  progress: ProgressPoint[];
  overallScore: number;
  xpEarned: number;
  masteryConcepts: string[];
}

interface Highlight {
  id: string;
  timestamp: number; // seconds from start
  type: 'achievement' | 'milestone' | 'struggle' | 'breakthrough' | 'collaboration';
  title: string;
  description: string;
  thumbnailUrl?: string;
  importance: 'low' | 'medium' | 'high';
}

interface Achievement {
  id: string;
  name: string;
  icon: string;
  timestamp: number;
  xpReward: number;
}

interface Interaction {
  id: string;
  type: 'npc_dialogue' | 'puzzle_solve' | 'quiz_complete' | 'peer_help';
  timestamp: number;
  details: string;
  outcome: 'success' | 'partial' | 'retry';
}

interface ProgressPoint {
  timestamp: number;
  concept: string;
  mastery: number; // 0-100
}

export default function GameplayReplay() {
  const user = useAppSelector((s) => s.user);
  const [selectedChild, setSelectedChild] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [sessions, setSessions] = useState<GameplaySession[]>([]);
  const [currentSession, setCurrentSession] = useState<GameplaySession | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [activeTab, setActiveTab] = useState<string | null>('0');
  const [selectedHighlight, setSelectedHighlight] = useState<string | null>(null);

  // Mock data for children (in real app, fetch from API)
  const children = [
    { id: '1', name: 'Emma Johnson', avatar: '', grade: 5 },
    { id: '2', name: 'Alex Johnson', avatar: '', grade: 3 },
  ];

  // Load mock sessions
  useEffect(() => {
    // Mock gameplay sessions
    const mockSessions: GameplaySession[] = [
      {
        id: '1',
        studentName: 'Emma Johnson',
        studentAvatar: '',
        worldName: 'Math Adventure Island',
        worldThumbnail: '',
        date: new Date(),
        duration: 1800, // 30 minutes
        highlights: [
          {
            id: 'h1',
            timestamp: 120,
            type: 'achievement',
            title: 'First Puzzle Solved!',
            description: 'Emma solved the fraction puzzle on her first try',
            importance: 'high',
          },
          {
            id: 'h2',
            timestamp: 450,
            type: 'breakthrough',
            title: 'Mastered Multiplication',
            description: 'Completed all multiplication challenges with 100% accuracy',
            importance: 'high',
          },
          {
            id: 'h3',
            timestamp: 780,
            type: 'collaboration',
            title: 'Helped a Classmate',
            description: 'Emma assisted another student with a difficult problem',
            importance: 'medium',
          },
          {
            id: 'h4',
            timestamp: 1200,
            type: 'struggle',
            title: 'Division Challenge',
            description: 'Took 3 attempts but persevered through the division section',
            importance: 'medium',
          },
          {
            id: 'h5',
            timestamp: 1650,
            type: 'milestone',
            title: 'Level Complete!',
            description: 'Finished Level 3 with a score of 95%',
            importance: 'high',
          },
        ],
        achievements: [
          { id: 'a1', name: 'Problem Solver', icon: '🧩', timestamp: 120, xpReward: 50 },
          { id: 'a2', name: 'Math Master', icon: '🎓', timestamp: 450, xpReward: 100 },
          { id: 'a3', name: 'Team Player', icon: '🤝', timestamp: 780, xpReward: 75 },
        ],
        interactions: [
          {
            id: 'i1',
            type: 'npc_dialogue',
            timestamp: 60,
            details: 'Spoke with Professor Math about fractions',
            outcome: 'success',
          },
          {
            id: 'i2',
            type: 'puzzle_solve',
            timestamp: 120,
            details: 'Fraction puzzle completed',
            outcome: 'success',
          },
          {
            id: 'i3',
            type: 'quiz_complete',
            timestamp: 900,
            details: 'Mid-level quiz: 9/10 correct',
            outcome: 'success',
          },
          {
            id: 'i4',
            type: 'peer_help',
            timestamp: 780,
            details: 'Helped Alex with multiplication',
            outcome: 'success',
          },
        ],
        progress: [
          { timestamp: 0, concept: 'Fractions', mastery: 60 },
          { timestamp: 300, concept: 'Fractions', mastery: 75 },
          { timestamp: 600, concept: 'Multiplication', mastery: 80 },
          { timestamp: 900, concept: 'Multiplication', mastery: 95 },
          { timestamp: 1200, concept: 'Division', mastery: 70 },
          { timestamp: 1500, concept: 'Division', mastery: 85 },
        ],
        overallScore: 95,
        xpEarned: 225,
        masteryConcepts: ['Fractions', 'Multiplication', 'Problem Solving'],
      },
      {
        id: '2',
        studentName: 'Emma Johnson',
        studentAvatar: '',
        worldName: 'Science Laboratory',
        worldThumbnail: '',
        date: new Date(Date.now() - 86400000), // Yesterday
        duration: 2400, // 40 minutes
        highlights: [
          {
            id: 'h6',
            timestamp: 180,
            type: 'achievement',
            title: 'Experiment Success!',
            description: 'Completed the chemical reaction experiment perfectly',
            importance: 'high',
          },
        ],
        achievements: [
          { id: 'a4', name: 'Scientist', icon: '🔬', timestamp: 180, xpReward: 75 },
        ],
        interactions: [
          {
            id: 'i5',
            type: 'npc_dialogue',
            timestamp: 100,
            details: 'Learned about chemical reactions from Dr. Science',
            outcome: 'success',
          },
        ],
        progress: [
          { timestamp: 0, concept: 'Chemistry', mastery: 50 },
          { timestamp: 1200, concept: 'Chemistry', mastery: 85 },
        ],
        overallScore: 88,
        xpEarned: 175,
        masteryConcepts: ['Chemistry', 'Scientific Method'],
      },
    ];

    setSessions(mockSessions);
    if (mockSessions.length > 0) {
      setCurrentSession(mockSessions[0]);
    }
  }, [selectedChild, selectedDate]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (newTime: number) => {
    setCurrentTime(newTime);
  };

  const jumpToHighlight = (timestamp: number) => {
    setCurrentTime(timestamp);
    setIsPlaying(true);
  };

  const getHighlightIcon = (type: Highlight['type']) => {
    switch (type) {
      case 'achievement':
        return <IconTrophy size={20} color="var(--mantine-color-yellow-6)" />;
      case 'milestone':
        return <IconStarFilled size={20} color="var(--mantine-color-blue-6)" />;
      case 'breakthrough':
        return <IconTrendingUp size={20} color="var(--mantine-color-green-6)" />;
      case 'struggle':
        return <IconAlertTriangle size={20} color="var(--mantine-color-red-6)" />;
      case 'collaboration':
        return <IconSchool size={20} color="var(--mantine-color-grape-6)" />;
      default:
        return <IconCircleCheck size={20} />;
    }
  };

  // Simulate playback
  useEffect(() => {
    if (isPlaying && currentSession && currentTime < currentSession.duration) {
      const timer = setTimeout(() => {
        setCurrentTime((prev) => Math.min(prev + playbackSpeed, currentSession.duration));
      }, 1000 / playbackSpeed);
      return () => clearTimeout(timer);
    } else if (currentTime >= (currentSession?.duration || 0)) {
      setIsPlaying(false);
    }
  }, [isPlaying, currentTime, playbackSpeed, currentSession]);

  if (!currentSession) {
    return (
      <Box>
        <Text size="xl" fw={600} mb="md">
          Gameplay Replay
        </Text>
        <Alert color="blue">
          Select a child and date to view their gameplay sessions
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Group justify="space-between" align="center" mb="md">
        <Text size="xl" fw={600}>
          Gameplay Replay
        </Text>
        <Group gap="sm">
          <Select
            placeholder="Select Child"
            value={selectedChild}
            onChange={(value) => setSelectedChild(value || '')}
            data={children.map((child) => ({
              value: child.id,
              label: child.name,
            }))}
            style={{ minWidth: 150 }}
            size="sm"
          />
          <DatePickerInput
            placeholder="Select Date"
            value={selectedDate}
            onChange={(date) => date && setSelectedDate(date)}
            size="sm"
            leftSection={<IconCalendar size={16} />}
          />
        </Group>
      </Group>

      <Grid gutter="md">
        {/* Video Player Area */}
        <Grid.Col span={{ base: 12, lg: 8 }}>
          <Card>
            <Box
              style={{
                position: 'relative',
                paddingTop: '56.25%', // 16:9 aspect ratio
                backgroundColor: 'black',
                borderRadius: 4,
                overflow: 'hidden',
              }}
            >
              {/* Replay Visualization */}
              <Box
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                <Stack align="center" gap="sm">
                  <IconDeviceGamepad size={80} color="white" style={{ opacity: 0.8 }} />
                  <Text size="lg" c="white">
                    {currentSession.worldName}
                  </Text>
                  <Text c="white" style={{ opacity: 0.9 }}>
                    {formatTime(currentTime)} / {formatTime(currentSession.duration)}
                  </Text>
                </Stack>
              </Box>

              {/* Highlight Markers on Timeline */}
              <Box
                style={{
                  position: 'absolute',
                  bottom: 80,
                  left: 0,
                  right: 0,
                  height: 4,
                  backgroundColor: 'rgba(255,255,255,0.3)',
                }}
              >
                {currentSession.highlights.map((highlight) => (
                  <Box
                    key={highlight.id}
                    style={{
                      position: 'absolute',
                      left: `${(highlight.timestamp / currentSession.duration) * 100}%`,
                      top: -6,
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor:
                        highlight.importance === 'high'
                          ? 'var(--mantine-color-yellow-6)'
                          : highlight.importance === 'medium'
                          ? 'var(--mantine-color-blue-6)'
                          : 'var(--mantine-color-gray-6)',
                      cursor: 'pointer',
                      transition: 'transform 0.2s',
                    }}
                    onClick={() => jumpToHighlight(highlight.timestamp)}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.3)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                  />
                ))}
              </Box>
            </Box>

            {/* Player Controls */}
            <Card.Section p="md">
              <Stack gap="sm">
                <Slider
                  value={currentTime}
                  max={currentSession.duration}
                  onChange={handleSeek}
                  style={{ width: '100%' }}
                />
                <Group justify="center" gap="sm">
                  <ActionIcon onClick={() => handleSeek(Math.max(0, currentTime - 30))} size="lg">
                    <IconPlayerSkipBack size={20} />
                  </ActionIcon>
                  <ActionIcon
                    onClick={handlePlayPause}
                    size="xl"
                    color="blue"
                    variant="filled"
                  >
                    {isPlaying ? <IconPlayerPause size={24} /> : <IconPlayerPlay size={24} />}
                  </ActionIcon>
                  <ActionIcon
                    onClick={() => handleSeek(Math.min(currentSession.duration, currentTime + 30))}
                    size="lg"
                  >
                    <IconPlayerSkipForward size={20} />
                  </ActionIcon>
                  <ActionIcon onClick={() => handleSeek(0)} size="lg">
                    <IconReload size={20} />
                  </ActionIcon>
                  <Select
                    value={playbackSpeed.toString()}
                    onChange={(value) => setPlaybackSpeed(Number(value))}
                    data={[
                      { value: '0.5', label: '0.5x' },
                      { value: '1', label: '1x' },
                      { value: '1.5', label: '1.5x' },
                      { value: '2', label: '2x' },
                    ]}
                    size="sm"
                    style={{ width: 80, marginLeft: 'auto' }}
                  />
                  <ActionIcon size="lg">
                    <IconDownload size={20} />
                  </ActionIcon>
                  <ActionIcon size="lg">
                    <IconShare size={20} />
                  </ActionIcon>
                  <ActionIcon size="lg">
                    <IconMaximize size={20} />
                  </ActionIcon>
                </Group>
              </Stack>
            </Card.Section>
          </Card>

          {/* Session Tabs */}
          <Card mt="md">
            <Tabs value={activeTab} onChange={setActiveTab}>
              <Tabs.List>
                <Tabs.Tab value="0">Highlights</Tabs.Tab>
                <Tabs.Tab value="1">Progress</Tabs.Tab>
                <Tabs.Tab value="2">Interactions</Tabs.Tab>
                <Tabs.Tab value="3">Achievements</Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="0" pt="md">
                <List spacing={0}>
                  {currentSession.highlights.map((highlight, index) => (
                    <React.Fragment key={highlight.id}>
                      <List.Item
                        onClick={() => {
                          setSelectedHighlight(highlight.id);
                          jumpToHighlight(highlight.timestamp);
                        }}
                        style={{
                          cursor: 'pointer',
                          padding: '12px',
                          backgroundColor: selectedHighlight === highlight.id ? 'var(--mantine-color-gray-1)' : undefined,
                        }}
                        icon={getHighlightIcon(highlight.type)}
                      >
                        <Group justify="space-between">
                          <Box style={{ flex: 1 }}>
                            <Text fw={500}>{highlight.title}</Text>
                            <Group gap="xs">
                              <Text size="xs">{formatTime(highlight.timestamp)}</Text>
                              <Text size="xs" c="dimmed">• {highlight.description}</Text>
                            </Group>
                          </Box>
                          <Badge
                            size="sm"
                            color={
                              highlight.importance === 'high'
                                ? 'red'
                                : highlight.importance === 'medium'
                                ? 'yellow'
                                : 'gray'
                            }
                          >
                            {highlight.importance}
                          </Badge>
                        </Group>
                      </List.Item>
                      {index < currentSession.highlights.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Tabs.Panel>

              <Tabs.Panel value="1" pt="md">
                <Box>
                  <Text size="lg" fw={500} mb="md">
                    Concept Mastery Progress
                  </Text>
                  {Array.from(new Set(currentSession.progress.map((p) => p.concept))).map(
                    (concept) => {
                      const conceptProgress = currentSession.progress.filter(
                        (p) => p.concept === concept
                      );
                      const initial = conceptProgress[0]?.mastery || 0;
                      const final = conceptProgress[conceptProgress.length - 1]?.mastery || 0;
                      const improvement = final - initial;

                      return (
                        <Box key={concept} mb="md">
                          <Group justify="space-between" mb="xs">
                            <Text size="sm">{concept}</Text>
                            <Group gap="xs">
                              <Badge
                                size="sm"
                                color={final >= 80 ? 'green' : 'gray'}
                              >
                                {final}%
                              </Badge>
                              {improvement > 0 && (
                                <Badge
                                  size="sm"
                                  color="green"
                                  variant="outline"
                                >
                                  +{improvement}%
                                </Badge>
                              )}
                            </Group>
                          </Group>
                          <Progress value={final} />
                        </Box>
                      );
                    }
                  )}
                </Box>
              </Tabs.Panel>

              <Tabs.Panel value="2" pt="md">
                <List spacing={0}>
                  {currentSession.interactions.map((interaction, index) => (
                    <React.Fragment key={interaction.id}>
                      <List.Item style={{ padding: '12px' }}>
                        <Box>
                          <Text>{interaction.details}</Text>
                          <Group gap="xs" mt="xs">
                            <Text size="xs">{formatTime(interaction.timestamp)}</Text>
                            <Badge
                              size="sm"
                              color={interaction.outcome === 'success' ? 'green' : 'yellow'}
                            >
                              {interaction.outcome}
                            </Badge>
                          </Group>
                        </Box>
                      </List.Item>
                      {index < currentSession.interactions.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Tabs.Panel>

              <Tabs.Panel value="3" pt="md">
                <List spacing={0}>
                  {currentSession.achievements.map((achievement, index) => (
                    <React.Fragment key={achievement.id}>
                      <List.Item
                        icon={<Text size="xl">{achievement.icon}</Text>}
                        style={{ padding: '12px' }}
                      >
                        <Group justify="space-between">
                          <Box>
                            <Text fw={500}>{achievement.name}</Text>
                            <Text size="xs" c="dimmed">{formatTime(achievement.timestamp)}</Text>
                          </Box>
                          <Badge color="blue">+{achievement.xpReward} XP</Badge>
                        </Group>
                      </List.Item>
                      {index < currentSession.achievements.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Tabs.Panel>
            </Tabs>
          </Card>
        </Grid.Col>

        {/* Session Info Sidebar */}
        <Grid.Col span={{ base: 12, lg: 4 }}>
          {/* Session Overview */}
          <Card>
            <Text size="lg" fw={500} mb="md">
              Session Overview
            </Text>
            <Stack gap="md">
              <Paper p="md" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                <Group>
                  <Avatar src={currentSession.studentAvatar} radius="xl">
                    {currentSession.studentName[0]}
                  </Avatar>
                  <Box>
                    <Text fw={500}>
                      {currentSession.studentName}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {currentSession.date.toLocaleDateString()}
                    </Text>
                  </Box>
                </Group>
              </Paper>

              <Stack gap="xs">
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    Duration
                  </Text>
                  <Text size="sm" fw={600}>
                    {formatTime(currentSession.duration)}
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    Overall Score
                  </Text>
                  <Badge
                    size="sm"
                    color={currentSession.overallScore >= 90 ? 'green' : 'blue'}
                  >
                    {currentSession.overallScore}%
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    XP Earned
                  </Text>
                  <Text size="sm" fw={600} c="blue">
                    +{currentSession.xpEarned} XP
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    Achievements
                  </Text>
                  <Text size="sm" fw={600}>
                    {currentSession.achievements.length}
                  </Text>
                </Group>
              </Stack>

              <Divider />

              <Box>
                <Text fw={500} mb="xs">
                  Mastered Concepts
                </Text>
                <Group gap="xs">
                  {currentSession.masteryConcepts.map((concept) => (
                    <Badge key={concept} size="sm" variant="outline">
                      {concept}
                    </Badge>
                  ))}
                </Group>
              </Box>
            </Stack>
          </Card>

          {/* Other Sessions */}
          <Card mt="md">
            <Text size="lg" fw={500} mb="md">
              Other Sessions Today
            </Text>
            <List spacing={0}>
              {sessions.slice(0, 3).map((session) => (
                <List.Item
                  key={session.id}
                  onClick={() => setCurrentSession(session)}
                  style={{
                    cursor: 'pointer',
                    padding: '12px',
                    backgroundColor: session.id === currentSession.id ? 'var(--mantine-color-gray-1)' : undefined,
                  }}
                  icon={<IconDeviceGamepad size={20} />}
                >
                  <Box>
                    <Text fw={500}>{session.worldName}</Text>
                    <Text size="xs" c="dimmed">
                      {formatTime(session.duration)} • {session.xpEarned} XP
                    </Text>
                  </Box>
                </List.Item>
              ))}
            </List>
          </Card>

          {/* Insights */}
          <Card mt="md">
            <Group mb="md">
              <IconBulb size={20} />
              <Text size="lg" fw={500}>AI Insights</Text>
            </Group>
            <Stack gap="sm">
              <Alert color="green">
                Emma showed excellent problem-solving skills, particularly in the multiplication
                section.
              </Alert>
              <Alert color="blue">
                Consider more division practice. Emma needed multiple attempts but showed good
                perseverance.
              </Alert>
              <Alert color="yellow">
                Emma spent 5 minutes on one problem. This might indicate the need for additional
                support in this area.
              </Alert>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
}
