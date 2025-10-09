import React, { useState, useEffect } from "react";
import {
  Box,
  Text,
  Grid,
  Card,
  Button,
  Badge,
  Progress,
  Tabs,
  Modal,
  TextInput,
  Select,
  ActionIcon,
  Tooltip,
  Alert,
  Paper,
  List,
  Divider,
  SegmentedControl,
  Skeleton,
  Avatar,
  Group,
  Stack,
  Container,
  Title,
  Center
} from '@mantine/core';

import {
  IconTrophy,
  IconClock,
  IconCalendar,
  IconStar,
  IconTrendingUp,
  IconClipboardCheck,
  IconSchool,
  IconPalette,
  IconBarbell,
  IconUsers,
  IconCircleCheck,
  IconCircle,
  IconLock,
  IconLockOpen,
  IconPlus,
  IconEdit,
  IconTrash,
  IconFilter,
  IconArrowsSort,
  IconRefresh,
  IconPlayerPlay,
  IconDots,
  IconInfoCircle,
  IconCoin,
  IconGift,
  IconFlame,
  IconSparkles,
  IconConfetti,
  IconAward,
  IconGauge,
  IconBrain,
  IconUsersGroup,
  IconCalendarTime,
  IconFlag,
} from "@tabler/icons-react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../../store";
import { Mission, MissionProgress, Challenge } from "../../types/api";
import { useApiCall, useApiCallOnMount } from "../../hooks/useApiCall";
const categoryIcons = {
  academic: <IconSchool />,
  social: <IconUsers />,
  creativity: <IconPalette />,
  physical: <IconBarbell />,
  community: <IconUsersGroup />,
};
const difficultyColors = {
  easy: "green",
  medium: "yellow",
  hard: "red",
  expert: "violet",
} as const;
const typeColors = {
  daily: "#4CAF50",
  weekly: "#2196F3",
  monthly: "#FF9800",
  special: "#9C27B0",
  custom: "#607D8B",
};
const challengeTypeIcons = {
  speed: <IconGauge />,
  accuracy: <IconBrain />,
  creativity: <IconPalette />,
  collaboration: <IconUsersGroup />,
  endurance: <IconCalendarTime />,
};
const Missions: React.FunctionComponent<Record<string, any>> = () => {
  const dispatch = useDispatch();
  const { role, userId } = useSelector((state: RootState) => state.user);
  const { xp, level } = useSelector((state: RootState) => state.gamification);
  const [activeTab, setActiveTab] = useState(0);
  const [missionProgress, setMissionProgress] = useState<Map<string, MissionProgress>>(new Map());

  // Fetch missions from API
  const { data: missionsData, loading: missionsLoading, error: missionsError, refetch: refetchMissions } = useApiCallOnMount(
    null,
    { mockEndpoint: '/student/missions', showNotification: false }
  );

  // Fetch challenges from API
  const { data: challengesData, loading: challengesLoading, error: challengesError, refetch: refetchChallenges } = useApiCallOnMount(
    null,
    { mockEndpoint: '/student/challenges', showNotification: false }
  );

  // API hooks for mutations
  const { execute: startMissionApi } = useApiCall();
  const { execute: claimRewardApi } = useApiCall();
  const { execute: joinChallengeApi } = useApiCall();

  const missions: Mission[] = (missionsData as Mission[]) || [];
  const challenges: Challenge[] = (challengesData as Challenge[]) || [];
  const loading = missionsLoading || challengesLoading;
  const [challengeFilter, setChallengeFilter] = useState<"all" | "upcoming" | "active" | "completed">("active");
  const [missionFilter, setMissionFilter] = useState<"all" | "daily" | "weekly" | "monthly" | "special">("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null);
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [missionDetailsOpen, setMissionDetailsOpen] = useState(false);
  const [challengeDetailsOpen, setChallengeDetailsOpen] = useState(false);

  // Load mission progress when missions data is available
  useEffect(() => {
    if (missionsData && Array.isArray(missionsData)) {
      // Extract progress from missions if it's embedded
      const progressMap = new Map<string, MissionProgress>();
      // If progress is separate, we'd fetch it here
      // For now, we'll check if missions have embedded progress
      (missionsData as any[]).forEach(mission => {
        if (mission.progress) {
          progressMap.set(mission.id, mission.progress);
        }
      });
      setMissionProgress(progressMap);
    }
  }, [missionsData]);
  const handleStartMission = async (mission: Mission) => {
    try {
      const response = await startMissionApi('POST', `/student/missions/${mission.id}/start`, {
        missionId: mission.id,
        studentId: userId,
      });

      if (response) {
        const newProgress: MissionProgress = response as MissionProgress;
        setMissionProgress(prev => new Map(prev).set(mission.id, newProgress));
        // Optionally refetch missions to get updated state
        refetchMissions();
      }
    } catch (error) {
      console.error("Failed to start mission:", error);
    }
  };
  const handleClaimReward = async (mission: Mission) => {
    try {
      const response = await claimRewardApi('POST', `/student/missions/${mission.id}/claim`, {
        missionId: mission.id,
        studentId: userId,
      });

      if (response) {
        const updatedProgress = response as MissionProgress;
        setMissionProgress(prev => new Map(prev).set(mission.id, updatedProgress));
        // Optionally refetch to get updated XP/level
        refetchMissions();
      }
    } catch (error) {
      console.error("Failed to claim reward:", error);
    }
  };
  const handleJoinChallenge = async (challenge: Challenge) => {
    try {
      const response = await joinChallengeApi('POST', `/student/challenges/${challenge.id}/join`, {
        challengeId: challenge.id,
        studentId: userId,
      });

      if (response) {
        // Refetch challenges to get updated participant list
        refetchChallenges();
      }
    } catch (error) {
      console.error("Failed to join challenge:", error);
    }
  };
  const renderMissionCard = (mission: Mission) => {
    const progress = missionProgress.get(mission.id);
    const isStarted = !!progress;
    const isCompleted = progress?.status === "completed";
    const isClaimed = progress?.status === "claimed";
    return (
      <Card
        key={mission.id}
        style={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          borderTop: `4px solid ${typeColors[mission.type]}`,
          opacity: isClaimed ? 0.7 : 1,
        }}
        padding="md"
      >
        <Box style={{ flexGrow: 1 }}>
          <Group justify="space-between" align="flex-start" mb="xs">
            <Group gap="xs" align="center">
              {categoryIcons[mission.category]}
              <Badge
                size="sm"
                style={{ backgroundColor: typeColors[mission.type], color: "white" }}
              >
                {mission.type}
              </Badge>
              <Badge
                size="sm"
                color={difficultyColors[mission.difficulty]}
              >
                {mission.difficulty}
              </Badge>
            </Group>
            {mission.isRepeatable && (
              <Tooltip label="Repeatable Mission">
                <IconRefresh size={16} />
              </Tooltip>
            )}
          </Group>
          <Title order={4} mb="xs">
            {mission.title}
          </Title>
          <Text size="sm" c="dimmed" mb="md">
            {mission.description}
          </Text>
          <Group gap="xs" my="md">
            <IconCoin />
            <Text size="lg" fw={600} c="blue">
              {mission.xpReward} XP
            </Text>
            {mission.badgeReward && (
              <>
                <IconAward />
                <Text size="sm">+ Badge</Text>
              </>
            )}
          </Group>
          {isStarted && progress && (
            <Box mb="md">
              <Group justify="space-between" mb="xs">
                <Text size="sm">Progress</Text>
                <Text size="sm">{Math.round(progress.progress)}%</Text>
              </Group>
              <Progress
                value={progress.progress}
                size="md"
              />
            </Box>
          )}
          <List spacing="xs" size="sm">
            {mission.requirements.map((req) => {
              const reqProgress = progress?.requirementsProgress.find(
                rp => rp.requirementId === req.id
              );
              const current = reqProgress?.current || 0;
              const completed = reqProgress?.completed || false;
              return (
                <List.Item
                  key={req.id}
                  icon={completed ? (
                    <IconCircleCheck color="green" size={16} />
                  ) : (
                    <IconCircle size={16} />
                  )}
                >
                  <Box>
                    <Text size="sm">{req.description}</Text>
                    <Text size="xs" c="dimmed">{current} / {req.target}</Text>
                  </Box>
                </List.Item>
              );
            })}
          </List>
          {mission.endDate && (
            <Alert color="blue" mt="md">
              <Text size="xs">
                Ends: {new Date(mission.endDate).toLocaleDateString()}
              </Text>
            </Alert>
          )}
        </Box>
        <Box pt={0} mt="md">
          {!isStarted && (
            <Button
              fullWidth
              leftSection={<IconPlayerPlay />}
              onClick={() => handleStartMission(mission)}
            >
              Start Mission
            </Button>
          )}
          {isStarted && !isCompleted && !isClaimed && (
            <Button
              fullWidth
              variant="outline"
              onClick={() => {
                setSelectedMission(mission);
                setMissionDetailsOpen(true);
              }}
            >
              View Details
            </Button>
          )}
          {isCompleted && !isClaimed && (
            <Button
              fullWidth
              color="green"
              leftSection={<IconConfetti />}
              onClick={() => handleClaimReward(mission)}
            >
              Claim Reward
            </Button>
          )}
          {isClaimed && (
            <Button fullWidth disabled leftSection={<IconCircleCheck />}>
              Claimed
            </Button>
          )}
        </Box>
      </Card>
    );
  };
  const renderChallengeCard = (challenge: Challenge) => {
    const isParticipant = challenge.participants.includes(userId || "");
    const timeUntilStart = new Date(challenge.startTime).getTime() - Date.now();
    const timeUntilEnd = new Date(challenge.endTime).getTime() - Date.now();
    return (
      <Card key={challenge.id} style={{ height: "100%" }} padding="md">
        <Group justify="space-between" align="flex-start" mb="md">
          <Group gap="xs" align="center">
            {challengeTypeIcons[challenge.type]}
            <Title order={4}>{challenge.title}</Title>
          </Group>
          <Badge
            size="sm"
            color={
              challenge.status === "active" ? "green" :
              challenge.status === "upcoming" ? "yellow" : "gray"
            }
          >
            {challenge.status}
          </Badge>
        </Group>
        <Text size="sm" c="dimmed" mb="md">
          {challenge.description}
        </Text>
        <Box my="md">
          <Text size="xs" c="dimmed">
            {challenge.status === "upcoming" && `Starts in ${Math.ceil(timeUntilStart / (1000 * 60 * 60 * 24))} days`}
            {challenge.status === "active" && `Ends in ${Math.ceil(timeUntilEnd / (1000 * 60 * 60 * 24))} days`}
            {challenge.status === "completed" && "Challenge ended"}
          </Text>
        </Box>
        <Group gap="xs" mb="md">
          <IconUsers size={16} />
          <Text size="sm">
            {challenge.participants.length} participants
          </Text>
        </Group>
        {challenge.leaderboard && challenge.leaderboard.length > 0 && (
          <Box mb="md">
            <Text size="sm" fw={600} mb="xs">
              Current Leaders
            </Text>
            <List spacing="xs" size="sm">
              {challenge.leaderboard.slice(0, 3).map((entry) => (
                <List.Item
                  key={entry.studentId}
                  icon={
                    <Avatar size="sm" radius="xl">
                      {entry.rank}
                    </Avatar>
                  }
                >
                  <Box>
                    <Text size="sm">{entry.displayName}</Text>
                    <Text size="xs" c="dimmed">Score: {entry.score}</Text>
                  </Box>
                </List.Item>
              ))}
            </List>
          </Box>
        )}
        <Text size="sm" fw={600} mb="xs">
          Prizes
        </Text>
        <Group gap="xs" mb="md">
          {challenge.prizes.slice(0, 3).map((prize) => (
            <Badge
              key={prize.position}
              variant="outline"
              size="sm"
            >
              #{prize.position}: {prize.xpReward} XP
            </Badge>
          ))}
        </Group>
        <Box pt="md">
          {challenge.status === "upcoming" && !isParticipant && (
            <Button
              fullWidth
              leftSection={<IconFlag />}
              onClick={() => handleJoinChallenge(challenge)}
            >
              Join Challenge
            </Button>
          )}
          {challenge.status === "upcoming" && isParticipant && (
            <Button fullWidth disabled leftSection={<IconCircleCheck />}>
              Registered
            </Button>
          )}
          {challenge.status === "active" && (
            <Button
              fullWidth
              onClick={() => {
                setSelectedChallenge(challenge);
                setChallengeDetailsOpen(true);
              }}
            >
              {isParticipant ? "Submit Entry" : "View Details"}
            </Button>
          )}
          {challenge.status === "completed" && (
            <Button
              fullWidth
              variant="outline"
              onClick={() => {
                setSelectedChallenge(challenge);
                setChallengeDetailsOpen(true);
              }}
            >
              View Results
            </Button>
          )}
        </Box>
      </Card>
    );
  };
  const filteredMissions = missions.filter(mission => {
    if (missionFilter !== "all" && mission.type !== missionFilter) return false;
    if (categoryFilter !== "all" && mission.category !== categoryFilter) return false;
    return true;
  });
  const filteredChallenges = challenges.filter(challenge => {
    if (challengeFilter === "all") return true;
    return challenge.status === challengeFilter;
  });
  return (
    <Container size="xl">
      <Group justify="space-between" align="center" mb="xl">
        <Title order={2}>Missions & Challenges</Title>
        {(role === "teacher" || role === "admin") && (
          <Button
            leftSection={<IconPlus />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Mission
          </Button>
        )}
      </Group>
      <Paper p="md" mb="xl">
        <Grid>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Group gap="xs" align="center">
              <IconFlame color="red" />
              <Box>
                <Title order={3}>{xp}</Title>
                <Text size="xs" c="dimmed">
                  Total XP
                </Text>
              </Box>
            </Group>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Group gap="xs" align="center">
              <IconStar color="orange" />
              <Box>
                <Title order={3}>{level}</Title>
                <Text size="xs" c="dimmed">
                  Current Level
                </Text>
              </Box>
            </Group>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Group gap="xs" align="center">
              <IconClipboardCheck color="blue" />
              <Box>
                <Title order={3}>
                  {Array.from(missionProgress.values()).filter(p => p.status === "in_progress").length}
                </Title>
                <Text size="xs" c="dimmed">
                  Active Missions
                </Text>
              </Box>
            </Group>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Group gap="xs" align="center">
              <IconTrophy color="green" />
              <Box>
                <Title order={3}>
                  {Array.from(missionProgress.values()).filter(p => p.status === "completed" || p.status === "claimed").length}
                </Title>
                <Text size="xs" c="dimmed">
                  Completed
                </Text>
              </Box>
            </Group>
          </Grid.Col>
        </Grid>
      </Paper>
      <Tabs value={activeTab.toString()} onChange={(v) => setActiveTab(Number(v))} mb="xl">
        <Tabs.List>
          <Tabs.Tab value="0" leftSection={<IconClipboardCheck />}>
            Missions
          </Tabs.Tab>
          <Tabs.Tab value="1" leftSection={<IconTrophy />}>
            Challenges
          </Tabs.Tab>
          <Tabs.Tab value="2" leftSection={<IconClock />}>
            History
          </Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="0">
          <Group gap="md" mb="lg" wrap="nowrap">
            <SegmentedControl
              value={missionFilter}
              onChange={setMissionFilter}
              data={[
                { value: "all", label: "All" },
                { value: "daily", label: "Daily" },
                { value: "weekly", label: "Weekly" },
                { value: "monthly", label: "Monthly" },
                { value: "special", label: "Special" },
              ]}
              size="sm"
            />
            <Select
              placeholder="Category"
              value={categoryFilter}
              onChange={(value) => setCategoryFilter(value || "all")}
              data={[
                { value: "all", label: "All Categories" },
                { value: "academic", label: "Academic" },
                { value: "social", label: "Social" },
                { value: "creativity", label: "Creativity" },
                { value: "physical", label: "Physical" },
                { value: "community", label: "Community" },
              ]}
              size="sm"
              style={{ minWidth: 150 }}
            />
          </Group>
          <Grid>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={i}>
                  <Skeleton height={300} />
                </Grid.Col>
              ))
            ) : (
              filteredMissions.map((mission) => (
                <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={mission.id}>
                  {renderMissionCard(mission)}
                </Grid.Col>
              ))
            )}
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="1">
          <Group gap="md" mb="lg">
            <SegmentedControl
              value={challengeFilter}
              onChange={setChallengeFilter}
              data={[
                { value: "all", label: "All" },
                { value: "upcoming", label: "Upcoming" },
                { value: "active", label: "Active" },
                { value: "completed", label: "Completed" },
              ]}
              size="sm"
            />
          </Group>
          <Grid>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <Grid.Col span={{ base: 12, md: 6 }} key={i}>
                  <Skeleton height={250} />
                </Grid.Col>
              ))
            ) : (
              filteredChallenges.map((challenge) => (
                <Grid.Col span={{ base: 12, md: 6 }} key={challenge.id}>
                  {renderChallengeCard(challenge)}
                </Grid.Col>
              ))
            )}
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="2">
          <Paper p="lg">
            <Title order={4} mb="md">
              Mission History
            </Title>
            <List spacing="sm">
              {Array.from(missionProgress.values())
                .filter(p => p.status === "claimed")
                .map((progress) => {
                  const mission = missions.find(m => m.id === progress.missionId);
                  if (!mission) return null;
                  return (
                    <React.Fragment key={progress.id}>
                      <List.Item
                        icon={categoryIcons[mission.category]}
                      >
                        <Group justify="space-between" align="center">
                          <Box>
                            <Text fw={500}>{mission.title}</Text>
                            <Text size="sm" c="dimmed">
                              Completed on {new Date(progress.claimedAt!).toLocaleDateString()}
                            </Text>
                          </Box>
                          <Badge color="green">+{mission.xpReward} XP</Badge>
                        </Group>
                      </List.Item>
                      <Divider />
                    </React.Fragment>
                  );
                })}
            </List>
          </Paper>
        </Tabs.Panel>
      </Tabs>
      {/* Mission Details Modal */}
      <Modal
        opened={missionDetailsOpen}
        onClose={() => setMissionDetailsOpen(false)}
        title={selectedMission?.title}
        size="sm"
      >
        {selectedMission && (
          <Stack gap="md">
            <Text>
              {selectedMission.description}
            </Text>
            {/* Add more mission details here */}
            <Group justify="flex-end">
              <Button onClick={() => setMissionDetailsOpen(false)}>Close</Button>
            </Group>
          </Stack>
        )}
      </Modal>

      {/* Challenge Details Modal */}
      <Modal
        opened={challengeDetailsOpen}
        onClose={() => setChallengeDetailsOpen(false)}
        title={selectedChallenge?.title}
        size="md"
      >
        {selectedChallenge && (
          <Stack gap="md">
            <Text>
              {selectedChallenge.description}
            </Text>
            {/* Add challenge submission form or results here */}
            <Group justify="flex-end">
              <Button onClick={() => setChallengeDetailsOpen(false)}>Close</Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Container>
  );
};
export default Missions;