import { useState } from "react";
import {
  Box,
  Card,
  Text,
  Button,
  Grid,
  Stack,
  Badge,
  Avatar,
  Paper,
  ActionIcon,
  Divider,
  Alert,
  Progress,
  Group,
  Title,
  Container,
  Center
} from '@mantine/core';

import {
  IconDeviceGamepad2,
  IconPlayerPlay,
  IconStars,
  IconClock,
  IconUsers,
  IconTrophy,
  IconRefresh,
} from "@tabler/icons-react";
import { useAppSelector } from "../../../store";
interface RobloxWorld {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  playerCount: number;
  difficulty: "Easy" | "Medium" | "Hard";
  subject: string;
  estimatedTime: number;
  xpReward: number;
  badges: string[];
  isLocked: boolean;
  completionRate: number;
}
export default function Play() {
  const user = useAppSelector((s) => s.user);
  const userXP = useAppSelector((s) => s.gamification.xp);
  const [worlds, setWorlds] = useState<RobloxWorld[]>([
    {
      id: "1",
      name: "Math Adventure Island",
      description: "Explore mathematical concepts through exciting quests and puzzles",
      thumbnailUrl: "",
      playerCount: 156,
      difficulty: "Easy",
      subject: "Mathematics",
      estimatedTime: 25,
      xpReward: 100,
      badges: ["Math Explorer", "Problem Solver"],
      isLocked: false,
      completionRate: 85,
    },
    {
      id: "2",
      name: "Science Laboratory",
      description: "Conduct virtual experiments and discover scientific principles",
      thumbnailUrl: "",
      playerCount: 89,
      difficulty: "Medium",
      subject: "Science",
      estimatedTime: 35,
      xpReward: 150,
      badges: ["Scientist", "Experimenter"],
      isLocked: false,
      completionRate: 72,
    },
    {
      id: "3",
      name: "History Time Machine",
      description: "Travel through time and experience historical events firsthand",
      thumbnailUrl: "",
      playerCount: 67,
      difficulty: "Medium",
      subject: "History",
      estimatedTime: 40,
      xpReward: 175,
      badges: ["Time Traveler", "Historian"],
      isLocked: false,
      completionRate: 68,
    },
    {
      id: "4",
      name: "Advanced Physics Simulator",
      description: "Master complex physics concepts in an interactive environment",
      thumbnailUrl: "",
      playerCount: 23,
      difficulty: "Hard",
      subject: "Physics",
      estimatedTime: 60,
      xpReward: 250,
      badges: ["Physics Master", "Theory Expert"],
      isLocked: true,
      completionRate: 45,
    },
  ]);
  const [loading, setLoading] = useState(false);
  const handleJoinWorld = async (worldId: string) => {
    setLoading(true);
    try {
      // TODO: Implement API call to get Roblox join URL
      // const joinUrl = await getRobloxJoinUrl(worldId);
      // window.open(joinUrl, '_blank');
      console.log(`Joining world ${worldId}`);
    } catch (error) {
      console.error("Failed to join world:", error);
    } finally {
      setLoading(false);
    }
  };
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Easy": return "success";
      case "Medium": return "warning";
      case "Hard": return "error";
      default: return "default";
    }
  };
  const getSubjectColor = (subject: string) => {
    switch (subject) {
      case "Mathematics": return "#1976d2";
      case "Science": return "#2e7d32";
      case "History": return "#ed6c02";
      case "Physics": return "#9c27b0";
      default: return "#666";
    }
  };
  return (
    <Container size="xl">
      <Group justify="space-between" align="center" mb="xl">
        <Box>
          <Title order={2} fw={600}>
            Roblox Learning Worlds
          </Title>
          <Text size="md" c="dimmed">
            Learn through immersive gaming experiences
          </Text>
        </Box>
        <ActionIcon onClick={() => window.location.reload()}>
          <IconRefresh />
        </ActionIcon>
      </Group>
      {/* Current Session Info */}
      {user && (
        <Alert color="blue" mb="xl">
          <Text size="sm">
            Welcome back, <strong>{user.displayName}</strong>!
            You currently have <strong>{userXP} XP</strong> and are Level <strong>{Math.floor(userXP / 100) + 1}</strong>.
          </Text>
        </Alert>
      )}
      <Grid>
        {worlds.map((world) => (
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={world.id}>
            <Card
              style={{
                height: "100%",
                opacity: world.isLocked ? 0.6 : 1,
                transition: "transform 0.2s",
              }}
              styles={{
                root: {
                  "&:hover": {
                    transform: world.isLocked ? "none" : "translateY(-4px)",
                  },
                },
              }}
              padding="md"
            >
              <Box
                style={{
                  height: 120,
                  background: `linear-gradient(135deg, ${getSubjectColor(world.subject)}22 0%, ${getSubjectColor(world.subject)}44 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                  borderRadius: 8,
                  marginBottom: 16,
                }}
              >
                <IconDeviceGamepad2 size={48} color={getSubjectColor(world.subject)} />
                {world.isLocked && (
                  <Badge
                    size="sm"
                    style={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                    }}
                  >
                    Locked
                  </Badge>
                )}
              </Box>
              <Title order={4} fw={600} mb="xs">
                {world.name}
              </Title>
              <Text size="sm" c="dimmed" mb="md">
                {world.description}
              </Text>
              <Stack gap="md">
                <Group gap="xs" wrap="wrap">
                  <Badge
                    size="sm"
                    color={getDifficultyColor(world.difficulty)}
                  >
                    {world.difficulty}
                  </Badge>
                  <Badge
                    size="sm"
                    variant="outline"
                  >
                    {world.subject}
                  </Badge>
                </Group>
                <Stack gap="xs">
                  <Group justify="space-between" align="center">
                    <Text size="xs" c="dimmed">
                      Completion Rate
                    </Text>
                    <Text size="xs" fw={600}>
                      {world.completionRate}%
                    </Text>
                  </Group>
                  <Progress
                    value={world.completionRate}
                    size="sm"
                    radius="md"
                  />
                </Stack>
                <Divider />
                <Stack gap="xs">
                  <Group gap="xs" align="center">
                    <IconClock size={16} />
                    <Text size="xs">
                      ~{world.estimatedTime} minutes
                    </Text>
                  </Group>
                  <Group gap="xs" align="center">
                    <IconUsers size={16} />
                    <Text size="xs">
                      {world.playerCount} players online
                    </Text>
                  </Group>
                  <Group gap="xs" align="center">
                    <IconStars size={16} />
                    <Text size="xs">
                      +{world.xpReward} XP reward
                    </Text>
                  </Group>
                </Stack>
                {world.badges.length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Text size="xs" c="dimmed" mb="xs">
                        Available Badges:
                      </Text>
                      <Group gap="xs" wrap="wrap">
                        {world.badges.map((badge, index) => (
                          <Badge
                            key={index}
                            size="sm"
                            variant="outline"
                            color="violet"
                          >
                            {badge}
                          </Badge>
                        ))}
                      </Group>
                    </Box>
                  </>
                )}
                <Button
                  fullWidth
                  size="md"
                  leftSection={<IconPlayerPlay />}
                  onClick={() => handleJoinWorld(world.id)}
                  disabled={world.isLocked || loading}
                  style={{
                    borderRadius: 8,
                    fontWeight: 600,
                    padding: "12px 16px",
                  }}
                >
                  {world.isLocked ? "Unlock Required" : "Join World"}
                </Button>
              </Stack>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
      {/* Quick Tips */}
      <Card mt="xl" padding="md">
        <Title order={4} mb="md">
          Gaming Tips for Learning
        </Title>
        <Grid>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Group gap="md">
              <IconTrophy color="blue" />
              <Box>
                <Text fw={500}>Earn XP</Text>
                <Text size="xs" c="dimmed">
                  Complete lessons and challenges to gain experience points
                </Text>
              </Box>
            </Group>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Group gap="md">
              <IconStars color="violet" />
              <Box>
                <Text fw={500}>Collect Badges</Text>
                <Text size="xs" c="dimmed">
                  Achieve specific goals to unlock special badges
                </Text>
              </Box>
            </Group>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Group gap="md">
              <IconUsers color="green" />
              <Box>
                <Text fw={500}>Play Together</Text>
                <Text size="xs" c="dimmed">
                  Join friends in multiplayer learning experiences
                </Text>
              </Box>
            </Group>
          </Grid.Col>
        </Grid>
      </Card>
    </Container>
  );
}