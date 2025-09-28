import * as React from "react";
import {
  Card,
  Text,
  Title,
  Table,
  Avatar,
  Stack,
  Badge,
  SegmentedControl,
  TextInput,
  Box,
  Group,
  SimpleGrid,
  Paper,
  Progress,
  ActionIcon,
  Tooltip,
  ScrollArea
} from '@mantine/core';
import {
  IconSearch,
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconTrophy,
  IconFlame,
  IconStar,
  IconMedal,
  IconCrown
} from '@tabler/icons-react';
import { useEffect } from "react";
import { useAppSelector, useAppDispatch } from "../../store";
import { fetchLeaderboard, setLeaderboard } from "../../store/slices/gamificationSlice";
import { pusherService } from "../../services/pusher";
import { WebSocketMessageType } from "../../types/websocket";

export default function Leaderboard() {
  const dispatch = useAppDispatch();
  const currentUserId = useAppSelector((s) => s.user.userId);
  const currentClassId = useAppSelector((s) => s.user.classIds?.[0]);
  const { leaderboard, loading } = useAppSelector((s) => s.gamification);

  const [timeframe, setTimeframe] = React.useState<"daily" | "weekly" | "monthly" | "all">("weekly");
  const [searchTerm, setSearchTerm] = React.useState("");

  // Fetch leaderboard on mount and when timeframe changes
  useEffect(() => {
    if (currentClassId) {
      dispatch(fetchLeaderboard({ classId: currentClassId, timeframe }));
    }
  }, [dispatch, currentClassId, timeframe]);

  // Setup Pusher listeners for real-time updates
  useEffect(() => {
    // Request initial leaderboard from realtime channel via server-triggered event
    void pusherService.send(WebSocketMessageType.REQUEST_LEADERBOARD, { classId: currentClassId }, { channel: 'public' });

    // Unified handler for all public channel messages
    const handlePublicLeaderboardMessage = (message: any) => {
      switch (message.type) {
        case WebSocketMessageType.LEADERBOARD_UPDATE: {
          dispatch(setLeaderboard(message.data));
          break;
        }
        case WebSocketMessageType.XP_GAINED: {
          // Refresh leaderboard when someone gains XP
          dispatch(fetchLeaderboard({ classId: currentClassId, timeframe }));
          break;
        }
      }
    };

    // Single subscription to public channel
    const subscriptionId = pusherService.subscribe(
      'public',
      handlePublicLeaderboardMessage,
      (msg) =>
        msg.type === WebSocketMessageType.LEADERBOARD_UPDATE ||
        msg.type === WebSocketMessageType.XP_GAINED ||
        msg.type === WebSocketMessageType.BADGE_EARNED
    );

    // Cleanup
    return () => {
      pusherService.unsubscribe(subscriptionId);
    };
  }, [dispatch, currentClassId, timeframe]);

  const handleTimeframeChange = (value: string | null) => {
    if (value) {
      setTimeframe(value as "daily" | "weekly" | "monthly" | "all");
    }
  };

  // Filter leaderboard based on search term
  const filteredLeaderboard = React.useMemo(() => {
    if (!leaderboard) return [];
    if (!searchTerm) return leaderboard;

    return leaderboard.filter(entry =>
      entry.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.username?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [leaderboard, searchTerm]);

  // Get rank icon
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <IconCrown size={20} color="gold" />;
      case 2:
        return <IconMedal size={20} color="silver" />;
      case 3:
        return <IconMedal size={20} color="#CD7F32" />;
      default:
        return <IconStar size={16} color="gray" />;
    }
  };

  // Get trend icon
  const getTrendIcon = (trend: number) => {
    if (trend > 0) return <IconTrendingUp size={16} color="green" />;
    if (trend < 0) return <IconTrendingDown size={16} color="red" />;
    return <IconMinus size={16} color="gray" />;
  };

  return (
    <Box p="xl">
      <Stack gap="lg">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Title order={2}>
            <Group gap="sm">
              <IconTrophy size={28} color="var(--mantine-color-yellow-6)" />
              Class Leaderboard
            </Group>
          </Title>

          <Group gap="md">
            <SegmentedControl
              value={timeframe}
              onChange={handleTimeframeChange}
              data={[
                { label: 'Daily', value: 'daily' },
                { label: 'Weekly', value: 'weekly' },
                { label: 'Monthly', value: 'monthly' },
                { label: 'All Time', value: 'all' }
              ]}
            />
          </Group>
        </Group>

        {/* Search and Stats */}
        <Group justify="space-between">
          <TextInput
            placeholder="Search students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftSection={<IconSearch size={16} />}
            style={{ minWidth: 300 }}
          />

          <Group gap="md">
            <Paper p="sm" withBorder>
              <Group gap="xs">
                <IconFlame size={16} color="orange" />
                <Text size="sm" fw={500}>
                  {filteredLeaderboard.length} Students
                </Text>
              </Group>
            </Paper>
          </Group>
        </Group>

        {/* Top 3 Podium */}
        {filteredLeaderboard.length >= 3 && (
          <Card withBorder>
            <Card.Section p="md" withBorder>
              <Title order={4} ta="center">🏆 Top Performers</Title>
            </Card.Section>

            <SimpleGrid cols={3} p="md">
              {filteredLeaderboard.slice(0, 3).map((entry, index) => (
                <Paper key={entry.userId} p="md" withBorder ta="center">
                  <Stack gap="sm" align="center">
                    {getRankIcon(index + 1)}
                    <Avatar
                      src={entry.avatarUrl}
                      alt={entry.displayName}
                      size="lg"
                      style={{
                        border: index === 0 ? '3px solid gold' :
                               index === 1 ? '3px solid silver' :
                               '3px solid #CD7F32'
                      }}
                    />
                    <Stack gap={4} align="center">
                      <Text fw={600} size="sm">{entry.displayName}</Text>
                      <Text size="xl" fw={700} c={
                        index === 0 ? 'yellow' :
                        index === 1 ? 'gray' :
                        'orange'
                      }>
                        {entry.totalXP.toLocaleString()} XP
                      </Text>
                      <Badge variant="outline" size="sm">
                        Level {entry.level}
                      </Badge>
                    </Stack>
                  </Stack>
                </Paper>
              ))}
            </SimpleGrid>
          </Card>
        )}

        {/* Full Leaderboard Table */}
        <Card withBorder>
          <Card.Section p="md" withBorder>
            <Title order={4}>Full Rankings</Title>
          </Card.Section>

          <ScrollArea>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Rank</Table.Th>
                  <Table.Th>Student</Table.Th>
                  <Table.Th>Level</Table.Th>
                  <Table.Th>XP</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Trend</Table.Th>
                  <Table.Th>Badges</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {loading ? (
                  <Table.Tr>
                    <Table.Td colSpan={7}>
                      <Text ta="center" py="xl" c="dimmed">
                        Loading leaderboard...
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                ) : filteredLeaderboard.length === 0 ? (
                  <Table.Tr>
                    <Table.Td colSpan={7}>
                      <Text ta="center" py="xl" c="dimmed">
                        No students found
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                ) : (
                  filteredLeaderboard.map((entry, index) => (
                    <Table.Tr
                      key={entry.userId}
                      style={{
                        backgroundColor: entry.userId === currentUserId ?
                          'var(--mantine-color-blue-0)' : undefined
                      }}
                    >
                      <Table.Td>
                        <Group gap="xs">
                          {getRankIcon(index + 1)}
                          <Text fw={600}>#{index + 1}</Text>
                        </Group>
                      </Table.Td>

                      <Table.Td>
                        <Group gap="sm">
                          <Avatar
                            src={entry.avatarUrl}
                            alt={entry.displayName}
                            size="sm"
                          />
                          <Stack gap={2}>
                            <Text fw={500} size="sm">{entry.displayName}</Text>
                            {entry.username && (
                              <Text size="xs" c="dimmed">@{entry.username}</Text>
                            )}
                          </Stack>
                        </Group>
                      </Table.Td>

                      <Table.Td>
                        <Badge variant="outline" color="blue">
                          Level {entry.level}
                        </Badge>
                      </Table.Td>

                      <Table.Td>
                        <Text fw={600}>{entry.totalXP.toLocaleString()}</Text>
                      </Table.Td>

                      <Table.Td>
                        <Stack gap={4}>
                          <Progress
                            value={entry.progressPercentage}
                            size="sm"
                            color="blue"
                          />
                          <Text size="xs" c="dimmed">
                            {entry.progressPercentage}% complete
                          </Text>
                        </Stack>
                      </Table.Td>

                      <Table.Td>
                        <Group gap="xs">
                          {getTrendIcon(entry.weeklyChange || 0)}
                          <Text
                            size="sm"
                            c={
                              (entry.weeklyChange || 0) > 0 ? 'green' :
                              (entry.weeklyChange || 0) < 0 ? 'red' : 'gray'
                            }
                          >
                            {entry.weeklyChange > 0 ? '+' : ''}{entry.weeklyChange || 0}
                          </Text>
                        </Group>
                      </Table.Td>

                      <Table.Td>
                        <Group gap="xs">
                          {entry.badges?.slice(0, 3).map((badge, i) => (
                            <Tooltip key={i} label={badge.name}>
                              <Badge size="xs" variant="filled" color="yellow">
                                {badge.emoji || '🏆'}
                              </Badge>
                            </Tooltip>
                          ))}
                          {(entry.badges?.length || 0) > 3 && (
                            <Badge size="xs" variant="outline">
                              +{(entry.badges?.length || 0) - 3}
                            </Badge>
                          )}
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))
                )}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Card>

        {/* Current User Highlight */}
        {currentUserId && (
          <Alert color="blue" title="Your Position">
            <Text size="sm">
              {(() => {
                const userIndex = filteredLeaderboard.findIndex(entry => entry.userId === currentUserId);
                if (userIndex === -1) return "You're not in the current leaderboard";
                return `You're ranked #${userIndex + 1} with ${filteredLeaderboard[userIndex].totalXP.toLocaleString()} XP`;
              })()}
            </Text>
          </Alert>
        )}
      </Stack>
    </Box>
  );
}
