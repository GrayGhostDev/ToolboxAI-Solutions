import React, { useEffect, useState } from "react";
import {
  Card,
  Text,
  Box,
  Stack,
  Progress,
  Badge,
  Avatar,
  Button,
  ActionIcon,
  Tabs,
  Paper,
  Loader,
  Alert,
  Select,
  Tooltip,
  List,
  Divider,
  Grid,
  Group,
  Title,
  Container,
  RingProgress,
  Center
} from '@mantine/core';

import {
  IconTrendingUp,
  IconTrendingDown,
  IconTrophy,
  IconSchool,
  IconClock,
  IconCircleCheck,
  IconCircle,
  IconStar,
  IconFlame,
  IconBrain,
  IconCalendar,
  IconRefresh,
  IconDownload,
  IconChartBar,
  IconClipboardCheck,
} from "@tabler/icons-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";
import { useAppDispatch, useAppSelector } from "../../store";
import {
  fetchStudentProgress,
  fetchClassProgress,
  fetchLessonAnalytics,
  setFilters,
  setCurrentStudent,
  compareStudents,
  generateProgressReport,
  clearError,
} from "../../store/slices/progressSlice";

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1"];

export default function Progress() {
  const dispatch = useAppDispatch();
  const {
    studentProgress,
    classProgress,
    lessonAnalytics,
    currentStudentId,
    currentClassId,
    loading,
    error,
    filters,
    comparisons,
  } = useAppSelector((state) => state.progress);
  
  const user = useAppSelector((state) => state.user);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedSubject, setSelectedSubject] = useState<string>("all");
  const [timeRange, setTimeRange] = useState(30);
  
  // Fetch progress data on mount
  useEffect(() => {
    if (user.role === "student" && (user as any).userId) {
      dispatch(fetchStudentProgress({ studentId: (user as any).userId, daysBack: timeRange }));
    } else if (user.role === "teacher" && user.classIds?.[0]) {
      dispatch(fetchClassProgress({ classId: user.classIds[0], daysBack: timeRange }));
    }
  }, [dispatch, user, timeRange]);
  
  const currentProgress = currentStudentId ? studentProgress[currentStudentId] : null;
  const currentClass = currentClassId ? classProgress[currentClassId] : null;
  
  const handleRefresh = () => {
    if (currentStudentId) {
      dispatch(fetchStudentProgress({ studentId: currentStudentId, daysBack: timeRange }));
    }
    if (currentClassId) {
      dispatch(fetchClassProgress({ classId: currentClassId, daysBack: timeRange }));
    }
  };
  
  const handleExportReport = () => {
    if (currentStudentId) {
      dispatch(generateProgressReport({ studentId: currentStudentId, format: "pdf" }));
    }
  };
  
  const handleCompareStudents = (studentIds: string[]) => {
    dispatch(compareStudents(studentIds));
  };
  
  // Mock data for demonstration (will be replaced with real data from API)
  const mockXPData = [
    { date: "Mon", xp: 150 },
    { date: "Tue", xp: 230 },
    { date: "Wed", xp: 180 },
    { date: "Thu", xp: 290 },
    { date: "Fri", xp: 310 },
    { date: "Sat", xp: 250 },
    { date: "Sun", xp: 380 },
  ];
  
  const mockSubjectData = [
    { subject: "Math", mastery: 85, hours: 12 },
    { subject: "Science", mastery: 72, hours: 10 },
    { subject: "Language", mastery: 90, hours: 15 },
    { subject: "History", mastery: 68, hours: 8 },
    { subject: "Arts", mastery: 95, hours: 6 },
  ];
  
  const mockSkillData = [
    { skill: "Problem Solving", level: 85 },
    { skill: "Critical Thinking", level: 78 },
    { skill: "Creativity", level: 92 },
    { skill: "Collaboration", level: 88 },
    { skill: "Communication", level: 75 },
    { skill: "Digital Literacy", level: 95 },
  ];
  
  const mockBadges = [
    { id: "1", name: "Math Wizard", icon: "🧙", rarity: "epic", earned: true },
    { id: "2", name: "Speed Reader", icon: "📚", rarity: "rare", earned: true },
    { id: "3", name: "Science Explorer", icon: "🔬", rarity: "common", earned: true },
    { id: "4", name: "Perfect Week", icon: "⭐", rarity: "legendary", earned: false },
    { id: "5", name: "Team Player", icon: "🤝", rarity: "rare", earned: true },
    { id: "6", name: "Early Bird", icon: "🌅", rarity: "common", earned: true },
  ];
  
  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case "legendary": return "#FFD700";
      case "epic": return "#9B30FF";
      case "rare": return "#0099FF";
      default: return "#888888";
    }
  };
  
  if (loading && !currentProgress && !currentClass) {
    return (
      <Center style={{ minHeight: 400 }}>
        <Loader size="lg" />
      </Center>
    );
  }

  return (
    <Container size="xl">
      <Grid>
        {/* Header */}
        <Grid.Col span={12}>
          <Card padding="md">
            <Group justify="space-between" align="center">
              <Title order={3} fw={600}>
                Learning Progress
              </Title>
              <Group gap="md" align="center">
                <Select
                  placeholder="Time Range"
                  value={timeRange.toString()}
                  onChange={(value) => setTimeRange(Number(value))}
                  data={[
                    { value: "7", label: "Last Week" },
                    { value: "30", label: "Last Month" },
                    { value: "90", label: "Last 3 Months" },
                    { value: "365", label: "Last Year" },
                  ]}
                  size="sm"
                  style={{ minWidth: 120 }}
                />
                <ActionIcon onClick={handleRefresh} disabled={loading}>
                  <IconRefresh size={16} />
                </ActionIcon>
                <Button
                  variant="outline"
                  leftSection={<IconDownload />}
                  onClick={handleExportReport}
                  size="sm"
                >
                  Export Report
                </Button>
              </Group>
            </Group>
          </Card>
        </Grid.Col>

        {error && (
          <Grid.Col span={12}>
            <Alert color="red" onClose={() => dispatch(clearError())}>
              {error}
            </Alert>
          </Grid.Col>
        )}
      
        {/* Key Metrics */}
        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconFlame color="red" />
                <Text size="xs" c="dimmed">
                  Current Streak
                </Text>
              </Group>
              <Title order={2} fw={700}>
                7 Days
              </Title>
              <Badge color="green" size="sm">Personal Best!</Badge>
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconTrophy color="orange" />
                <Text size="xs" c="dimmed">
                  Total XP
                </Text>
              </Group>
              <Title order={2} fw={700}>
                2,450
              </Title>
              <Group gap="xs" align="center">
                <IconTrendingUp color="green" size={16} />
                <Text size="xs" c="green">
                  +320 this week
                </Text>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconSchool color="blue" />
                <Text size="xs" c="dimmed">
                  Lessons Completed
                </Text>
              </Group>
              <Title order={2} fw={700}>
                42/50
              </Title>
              <Progress value={84} color="blue" />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="md">
              <Group gap="xs" align="center">
                <IconBrain color="violet" />
                <Text size="xs" c="dimmed">
                  Skill Level
                </Text>
              </Group>
              <Title order={2} fw={700}>
                Level 12
              </Title>
              <Text size="xs" c="dimmed">
                450 XP to Level 13
              </Text>
            </Stack>
          </Card>
        </Grid.Col>
      
        {/* Charts Section */}
        <Grid.Col span={12}>
          <Card padding="md">
            <Tabs value={activeTab.toString()} onChange={(v) => setActiveTab(Number(v))} mb="xl">
              <Tabs.List>
                <Tabs.Tab value="0">XP Progress</Tabs.Tab>
                <Tabs.Tab value="1">Subject Mastery</Tabs.Tab>
                <Tabs.Tab value="2">Skills Radar</Tabs.Tab>
                <Tabs.Tab value="3">Achievements</Tabs.Tab>
              </Tabs.List>
            
              <Tabs.Panel value="0">
                <Box>
                  <Title order={4} mb="md">
                    Weekly XP Progress
                  </Title>
                  <div style={{ width: "100%", height: 300 }}>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={mockXPData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <ChartTooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="xp"
                          stroke="#8884d8"
                          strokeWidth={2}
                          dot={{ fill: "#8884d8" }}
                          activeDot={{ r: 8 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Box>
              </Tabs.Panel>

              <Tabs.Panel value="1">
                <Box>
                  <Title order={4} mb="md">
                    Subject Mastery & Time Spent
                  </Title>
                  <div style={{ width: "100%", height: 300 }}>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={mockSubjectData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="subject" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                        <ChartTooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="mastery" fill="#8884d8" name="Mastery %" />
                        <Bar yAxisId="right" dataKey="hours" fill="#82ca9d" name="Hours" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  <Grid mt="xl">
                    {mockSubjectData.map((subject) => (
                      <Grid.Col key={subject.subject} span={{ base: 12, sm: 6, md: 3 }}>
                        <Paper p="md" style={{ textAlign: "center" }}>
                          <Text size="sm" fw={600} mb="md">
                            {subject.subject}
                          </Text>
                          <Center>
                            <RingProgress
                              size={80}
                              thickness={8}
                              sections={[
                                {
                                  value: subject.mastery,
                                  color: subject.mastery >= 80 ? "green" : subject.mastery >= 60 ? "yellow" : "red"
                                }
                              ]}
                              label={
                                <Text size="xs" ta="center">
                                  {subject.mastery}%
                                </Text>
                              }
                            />
                          </Center>
                        </Paper>
                      </Grid.Col>
                    ))}
                  </Grid>
                </Box>
              </Tabs.Panel>

              <Tabs.Panel value="2">
                <Box>
                  <Title order={4} mb="md">
                    Skills Development
                  </Title>
                  <div style={{ width: "100%", height: 400 }}>
                    <ResponsiveContainer width="100%" height={400}>
                      <RadarChart data={mockSkillData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="skill" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <Radar
                          name="Skill Level"
                          dataKey="level"
                          stroke="#8884d8"
                          fill="#8884d8"
                          fillOpacity={0.6}
                        />
                        <Legend />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </Box>
              </Tabs.Panel>

              <Tabs.Panel value="3">
                <Box>
                  <Title order={4} mb="md">
                    Badges & Achievements
                  </Title>
                  <Grid>
                    {mockBadges.map((badge) => (
                      <Grid.Col key={badge.id} span={{ base: 6, sm: 4, md: 2 }}>
                        <Paper
                          p="md"
                          style={{
                            textAlign: "center",
                            opacity: badge.earned ? 1 : 0.5,
                            border: `2px solid ${badge.earned ? getRarityColor(badge.rarity) : '#ddd'}`,
                            position: "relative",
                          }}
                        >
                          {badge.earned && (
                            <IconCircleCheck
                              style={{
                                position: "absolute",
                                top: 8,
                                right: 8,
                                color: "green",
                              }}
                              size={20}
                            />
                          )}
                          <Text size={32} mb="xs">
                            {badge.icon}
                          </Text>
                          <Text size="sm" fw={500}>
                            {badge.name}
                          </Text>
                          <Badge
                            size="sm"
                            mt="xs"
                            style={{
                              backgroundColor: getRarityColor(badge.rarity),
                              color: "white",
                            }}
                          >
                            {badge.rarity}
                          </Badge>
                        </Paper>
                      </Grid.Col>
                    ))}
                  </Grid>

                  <Group justify="space-between" align="center" mt="xl">
                    <Text size="sm" c="dimmed">
                      Earned: {mockBadges.filter(b => b.earned).length} / {mockBadges.length}
                    </Text>
                    <Progress
                      value={(mockBadges.filter(b => b.earned).length / mockBadges.length) * 100}
                      style={{ width: 200 }}
                    />
                  </Group>
                </Box>
              </Tabs.Panel>
            </Tabs>
          </Card>
        </Grid.Col>
      
        {/* Recent Activity */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md">
            <Title order={4} mb="md" fw={600}>
              Recent Achievements
            </Title>
            <List spacing="sm">
              {[
                { title: "Completed Math Chapter 5", xp: 150, time: "2 hours ago", icon: "📐" },
                { title: "Perfect Score on Science Quiz", xp: 200, time: "Yesterday", icon: "🔬" },
                { title: "7-Day Streak Achieved", xp: 100, time: "2 days ago", icon: "🔥" },
                { title: "Helped 3 Classmates", xp: 75, time: "3 days ago", icon: "🤝" },
              ].map((activity, index) => (
                <React.Fragment key={index}>
                  <List.Item
                    icon={
                      <Avatar size="sm" style={{ backgroundColor: "var(--mantine-primary-color-light)" }}>
                        {activity.icon}
                      </Avatar>
                    }
                  >
                    <Group justify="space-between" align="center">
                      <Box>
                        <Text fw={500}>{activity.title}</Text>
                        <Text size="sm" c="dimmed">{activity.time}</Text>
                      </Box>
                      <Badge color="green" size="sm">
                        +{activity.xp} XP
                      </Badge>
                    </Group>
                  </List.Item>
                  {index < 3 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Card>
        </Grid.Col>

        {/* Improvement Suggestions */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md">
            <Title order={4} mb="md" fw={600}>
              Recommended Focus Areas
            </Title>
            <Stack gap="md">
              {[
                {
                  subject: "History",
                  reason: "Below average performance",
                  action: "Review Chapter 3-4",
                  improvement: "+15%",
                },
                {
                  subject: "Science",
                  reason: "Upcoming test",
                  action: "Practice lab exercises",
                  improvement: "+10%",
                },
                {
                  subject: "Math",
                  reason: "Strong foundation",
                  action: "Try advanced problems",
                  improvement: "Challenge",
                },
              ].map((suggestion, index) => (
                <Paper key={index} p="md">
                  <Group justify="space-between" align="center">
                    <Box>
                      <Text fw={600} size="sm">
                        {suggestion.subject}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {suggestion.reason}
                      </Text>
                      <Text size="sm" mt="xs">
                        {suggestion.action}
                      </Text>
                    </Box>
                    <Badge
                      color={suggestion.improvement === "Challenge" ? "blue" : "green"}
                      variant="outline"
                    >
                      {suggestion.improvement}
                    </Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  );
}