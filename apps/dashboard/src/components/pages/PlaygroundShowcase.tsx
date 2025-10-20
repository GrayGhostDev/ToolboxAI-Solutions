import {
  Box, Button, Text, Paper, Stack, Grid, Container, ActionIcon, Avatar, Card,
  List, Divider, TextInput, Select, Chip, Badge, Alert, Loader, Progress,
  Modal, Menu, Tooltip, Checkbox, Switch, Slider, Autocomplete, Skeleton,
  Table, Group, FloatingButton
} from '@mantine/core';
import {
  IconStar, IconSchool, IconDeviceGamepad, IconRocketLaunch, IconSparkles,
  IconTrophy
} from '@tabler/icons-react';
import React, { useState } from 'react';
import { motion } from 'framer-motion';

// Roblox-themed components temporarily disabled for Vercel build
// import { Roblox3DMetricCard } from '../roblox/Roblox3DMetricCard';
// import { AnimatedLeaderboard } from '../roblox/AnimatedLeaderboard';
// import { FloatingIslandNav } from '../roblox/FloatingIslandNav';
import { useMantineTheme } from '@mantine/core';

const PlaygroundShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const [selectedMetric, setSelectedMetric] = useState<number | null>(null);

  // Sample data for components
  const leaderboardPlayers = [
    { id: '1', name: 'CoolKid123', xp: 15420, level: 42, streak: 7, badges: 12, change: 'up' as const, changeValue: 2, isOnline: true },
    { id: '2', name: 'ProGamer456', xp: 14200, level: 40, streak: 5, badges: 10, change: 'up' as const, changeValue: 1, isOnline: true },
    { id: '3', name: 'StudyMaster', xp: 13800, level: 38, streak: 12, badges: 15, change: 'down' as const, changeValue: 1, isOnline: false },
    { id: '4', name: 'QuizChampion', xp: 12500, level: 35, streak: 3, badges: 8, change: 'same' as const, isOnline: true },
    { id: '5', name: 'MathWizard', xp: 11200, level: 32, streak: 9, badges: 11, change: 'up' as const, changeValue: 3, isOnline: false },
    { id: '6', name: 'ScienceGeek', xp: 10800, level: 30, streak: 6, badges: 7, change: 'down' as const, changeValue: 2, isOnline: true },
    { id: '7', name: 'BookWorm99', xp: 9500, level: 28, streak: 15, badges: 9, change: 'up' as const, changeValue: 1, isOnline: true },
  ];

  const metrics = [
    {
      title: 'Total XP Earned',
      value: 15420,
      icon: <IconStar />,
      trend: { value: 23, direction: 'up' as const },
      color: theme.colors.yellow[6],
      subtitle: 'Keep going! 580 XP to next level',
      format: 'number' as const,
    },
    {
      title: 'Lessons Completed',
      value: 142,
      icon: <IconSchool />,
      trend: { value: 15, direction: 'up' as const },
      color: theme.colors.green[6],
      subtitle: '28 more than last month!',
      format: 'number' as const,
    },
    {
      title: 'Win Rate',
      value: 87,
      icon: <IconTrophy />,
      trend: { value: 5, direction: 'up' as const },
      color: theme.colors.violet[6],
      subtitle: 'Top 5% of all players!',
      format: 'percentage' as const,
    },
    {
      title: 'Study Time',
      value: 42,
      icon: <IconDeviceGamepad />,
      trend: { value: -3, direction: 'down' as const },
      color: theme.colors.blue[6],
      subtitle: 'This week',
      format: 'time' as const,
    },
  ];

  return (
    <Box
      style={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${theme.colors.violet[9]}, ${theme.colors.blue[9]}, ${theme.colors.pink[9]})`,
        backgroundSize: '400% 400%',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Floating emojis in background */}
      <Box style={{ position: 'absolute', left: '10%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear infinite' }}>🚀</Box>
      <Box style={{ position: 'absolute', left: '25%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear 2s infinite' }}>⭐</Box>
      <Box style={{ position: 'absolute', left: '40%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear 4s infinite' }}>🎮</Box>
      <Box style={{ position: 'absolute', left: '55%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear 6s infinite' }}>🏆</Box>
      <Box style={{ position: 'absolute', left: '70%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear 8s infinite' }}>💎</Box>
      <Box style={{ position: 'absolute', left: '85%', bottom: '-50px', fontSize: '3rem', zIndex: 1, pointerEvents: 'none', animation: 'float 15s linear 10s infinite' }}>🌟</Box>

      <Container size="xl" py="xl" style={{ position: 'relative', zIndex: 2 }}>
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <Text
            size="4rem"
            fw={900}
            ta="center"
            mb="xl"
            style={{
              background: `linear-gradient(135deg, ${theme.colors.blue[4]}, ${theme.colors.violet[4]})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            🎮 EPIC GAMING DASHBOARD 🚀
          </Text>

          <Text
            size="lg"
            ta="center"
            c="white"
            mb="3xl"
            fw={600}
            style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.5)' }}
          >
            Where Learning Meets Gaming!
          </Text>
        </motion.div>

        {/* Floating Island Navigation */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card
            withBorder
            radius="xl"
            mb="xl"
            style={{
              background: `linear-gradient(135deg, ${theme.colors.dark[7]}, ${theme.colors.dark[6]})`,
              border: `2px solid ${theme.colors.blue[6]}`,
              padding: 24
            }}
          >
            <Text
              size="lg"
              fw={700}
              ta="center"
              mb="lg"
              c={theme.colors.blue[4]}
            >
              🏝️ Choose Your Adventure Island! 🏝️
            </Text>
            <Alert color="blue" variant="light">Island navigation being optimized for deployment.</Alert>
          </Card>
        </motion.div>

        {/* 3D Metric Cards */}
        <Box mt="xl">
          <Text
            size="xl"
            fw={700}
            ta="center"
            mb="lg"
            c="white"
            style={{ textShadow: `0 0 20px ${theme.colors.violet[6]}` }}
          >
            ⚡ Your Epic Stats ⚡
          </Text>

          <Grid gutter="md">
            {metrics.map((metric, index) => (
              <Grid.Col span={{ base: 12, sm: 6, md: 3 }} key={index}>
                <motion.div
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card
                    withBorder
                    radius="md"
                    onClick={() => setSelectedMetric(index)}
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.dark[7]}, ${theme.colors.dark[6]})`,
                      border: `2px solid ${metric.color}`,
                      padding: 16,
                      cursor: 'pointer',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <Group align="center" gap="md" mb="xs">
                      {metric.icon}
                      <Text size="sm" fw={600} c={metric.color}>{metric.title}</Text>
                    </Group>
                    <Text size="2rem" fw={800} c="white">{metric.value}</Text>
                    <Text size="xs" c="dimmed">{metric.subtitle}</Text>
                  </Card>
                </motion.div>
              </Grid.Col>
            ))}
          </Grid>
        </Box>

        {/* Animated Leaderboard */}
        <Box mt="3xl">
          <Grid gutter="xl">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <Card
                  withBorder
                  radius="xl"
                  style={{
                    background: `linear-gradient(135deg, ${theme.colors.dark[7]}, ${theme.colors.violet[9]})`,
                    border: `2px solid ${theme.colors.violet[6]}`,
                    padding: 24
                  }}
                >
                  <Text size="lg" fw={700} ta="center" mb="lg" c={theme.colors.green[4]}>
                    🏆 ULTIMATE CHAMPIONS 🏆
                  </Text>
                  <Stack gap="sm">
                    {leaderboardPlayers.slice(0, 5).map((player, idx) => (
                      <Button
                        key={player.id}
                        fullWidth
                        variant="filled"
                        style={{
                          background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                          justifyContent: 'flex-start'
                        }}
                        onClick={() => console.log('Clicked player:', player)}
                      >
                        #{idx + 1} {player.name} - {player.xp} XP
                      </Button>
                    ))}
                  </Stack>
                </Card>
              </motion.div>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <motion.div
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
              >
                <Card
                  withBorder
                  radius="xl"
                  style={{
                    background: `linear-gradient(135deg, ${theme.colors.dark[7]}, ${theme.colors.violet[9]})`,
                    border: `2px solid ${theme.colors.violet[6]}`,
                    padding: 24
                  }}
                >
                  <Text
                    size="lg"
                    fw={700}
                    ta="center"
                    mb="lg"
                    c={theme.colors.green[4]}
                  >
                    🎯 Daily Challenges 🎯
                  </Text>

                  <Stack gap="md">
                    {['Complete 5 Math Problems', 'Win 3 Quiz Battles', 'Study for 30 Minutes', 'Help a Friend'].map((challenge, index) => (
                      <Button
                        key={index}
                        fullWidth
                        size="lg"
                        style={{
                          background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                          borderRadius: 16,
                          transition: 'all 0.3s ease'
                        }}
                      >
                        {challenge}
                      </Button>
                    ))}
                  </Stack>
                </Card>
              </motion.div>
            </Grid.Col>
          </Grid>
        </Box>

        {/* Floating Action Buttons */}
        <Box
          style={{
            position: 'fixed',
            bottom: 32,
            right: 32,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <ActionIcon
            size="xl"
            radius="xl"
            style={{
              background: `linear-gradient(135deg, ${theme.colors.orange[6]}, ${theme.colors.red[6]})`,
              animation: 'spin 3s linear infinite'
            }}
          >
            <IconRocketLaunch />
          </ActionIcon>
          <ActionIcon
            size="xl"
            radius="xl"
            style={{
              background: `linear-gradient(135deg, ${theme.colors.violet[6]}, ${theme.colors.pink[6]})`,
              animation: 'bounce 2s ease-in-out infinite'
            }}
          >
            <IconSparkles />
          </ActionIcon>
        </Box>
      </Container>
    </Box>
  );
};

export default PlaygroundShowcase;