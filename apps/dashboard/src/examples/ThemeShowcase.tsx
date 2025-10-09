import { Box, Text, Paper, Stack, Grid, Avatar, Divider, Group } from '@mantine/core';
/**
 * Theme Showcase Component
 *
 * Demonstrates the Roblox-inspired design system components and features.
 * This component serves as both documentation and testing for the theme system.
 */

import React from 'react';
import { IconBell, IconTrophy, IconSchool, IconSettings, IconSpeed, IconStar, IconDeviceGamepad } from '@tabler/icons-react';
import {
  IconHome, IconUser, IconSettings, IconLogout, IconChevronDown,
  IconChevronUp, IconChevronLeft, IconChevronRight, IconMenu,
  IconX, IconCheck, IconPlus, IconMinus, IconEdit, IconTrash,
  IconSearch, IconFilter, IconDownload, IconUpload, IconEye,
  IconEyeOff, IconBell, IconMessage, IconStar, IconHeart,
  IconShare, IconRefresh, IconLogin, IconSchool, IconBook,
  IconChartBar, IconPalette, IconMoon, IconSun, IconPlayerPlay,
  IconPlayerPause, IconPlayerStop, IconVolume, IconVolumeOff,
  IconInfoCircle, IconAlertTriangle, IconX, IconCircleCheck,
  IconArrowLeft, IconArrowRight, IconSend, IconDeviceFloppy,
  IconPrinter, IconHelp, IconHelpCircle, IconLock, IconLockOpen,
  IconMail, IconPhone, IconMapPin, IconMap, IconCalendar, IconClock,
  IconWifi, IconWifiOff, IconBluetooth, IconBattery, IconCamera,
  IconMicrophone, IconMicrophoneOff, IconVideo, IconVideoOff,
  IconPhoto, IconPaperclip, IconCloud, IconCloudUpload,
  IconCloudDownload, IconFolder, IconFolderOpen, IconFolderPlus,
  IconFile, IconFileText, IconClipboard, IconBan, IconFlag,
  IconBookmark, IconShoppingCart, IconUserCircle, IconMoodSmile,
  IconMoodSad, IconThumbUp, IconThumbDown, IconMessages,
  IconMessageQuestion, IconSpeakerphone, IconBellRinging,
  IconBellOff, IconCalendarEvent, IconCalendarStats, IconAlarm,
  IconAlarmOff, IconHistory, IconRefreshOff, IconRefreshAlert,
  IconDashboard, IconUsers, IconDotsVertical, IconDots,
  IconReportAnalytics
} from '@tabler/icons-react';
import {
  RobloxCard,
  RobloxButton,
  RobloxChip,
  XPProgressBar,
  RobloxFAB,
  RobloxAvatar,
  AchievementBadge,
  RobloxNotificationCard,
  RobloxSkeleton,
  GameContainer,
  ThemeSwitcher,
  useThemeContext
} from '../theme';

const ThemeShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const { isDark, mode } = useThemeContext();

  return (
    <Box style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <Box style={{ marginBottom: 48, textAlign: 'center' }}>
        <Text size="xl" fw={600} mb="md">
          Roblox Theme Showcase
        </Text>
        <Text size="md" c="dimmed" mb="md">
          Current theme: {mode} mode ({isDark ? 'dark' : 'light'})
        </Text>
        <Box style={{ marginTop: 16 }}>
          <ThemeSwitcher variant="menu" showLabel />
        </Box>
      </Box>

      <Grid>
        {/* Buttons Section */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Buttons
              </Text>
              <Stack gap="sm">
                <RobloxButton variant="filled" size="lg">
                  Primary Button
                </RobloxButton>
                <RobloxButton variant="outline">
                  Secondary Button
                </RobloxButton>
                <RobloxButton variant="subtle">
                  Text Button
                </RobloxButton>
                <RobloxButton variant="filled" disabled>
                  Disabled Button
                </RobloxButton>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Chips Section */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Gamification Chips
              </Text>
              <Group gap="sm" style={{ flexWrap: 'wrap' }}>
                <RobloxChip label="Common" rarity="common" />
                <RobloxChip label="Rare" rarity="rare" />
                <RobloxChip label="Epic" rarity="epic" />
                <RobloxChip label="Legendary" rarity="legendary" />
              </Group>
              <Box mt="sm">
                <RobloxChip
                  label="Level 25"
                  icon={<IconTrophy />}
                  variant="filled"
                />
                <RobloxChip
                  label="Pro Player"
                  icon={<IconStar />}
                  variant="outline"
                  style={{ marginLeft: 8 }}
                />
              </Box>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Progress Bars */}
        <Grid.Col span={12}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                XP Progress Bars
              </Text>
              <Stack gap="lg">
                <Box>
                  <Text size="sm" mb="xs">
                    Level 1 - Beginner (25% XP)
                  </Text>
                  <XPProgressBar value={25} level={1} />
                </Box>
                <Box>
                  <Text size="sm" mb="xs">
                    Level 15 - Intermediate (65% XP)
                  </Text>
                  <XPProgressBar value={65} level={15} />
                </Box>
                <Box>
                  <Text size="sm" mb="xs">
                    Level 50 - Expert (90% XP)
                  </Text>
                  <XPProgressBar value={90} level={50} />
                </Box>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Avatars Section */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Gaming Avatars
              </Text>
              <Group gap="lg" align="center">
                <RobloxAvatar level={1} isOnline>
                  <Avatar size="lg">
                    <IconDeviceGamepad />
                  </Avatar>
                </RobloxAvatar>
                <RobloxAvatar level={25} isOnline={false}>
                  <Avatar size="lg">
                    <IconSchool />
                  </Avatar>
                </RobloxAvatar>
                <AchievementBadge badgeContent="!" achievement="gold">
                  <RobloxAvatar level={100} isOnline>
                    <Avatar size="lg">
                      <IconStar />
                    </Avatar>
                  </RobloxAvatar>
                </AchievementBadge>
              </Group>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Notifications */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <Stack gap="sm">
            <RobloxNotificationCard severity="success">
              <Box style={{ padding: 8 }}>
                <Text size="md" mb="xs">
                  Achievement Unlocked!
                </Text>
                <Text size="sm">
                  You've completed your first lesson!
                </Text>
              </Box>
            </RobloxNotificationCard>

            <RobloxNotificationCard severity="info">
              <Box style={{ padding: 8 }}>
                <Text size="md" mb="xs">
                  New Content Available
                </Text>
                <Text size="sm">
                  Check out the latest math challenges.
                </Text>
              </Box>
            </RobloxNotificationCard>

            <RobloxNotificationCard severity="warning">
              <Box style={{ padding: 8 }}>
                <Text size="md" mb="xs">
                  Assignment Due Soon
                </Text>
                <Text size="sm">
                  You have 2 days left to submit.
                </Text>
              </Box>
            </RobloxNotificationCard>
          </Stack>
        </Grid.Col>

        {/* Game Container */}
        <Grid.Col span={12}>
          <GameContainer>
            <Text size="xl" ta="center" mb="md">
              Welcome to the Learning Arena!
            </Text>
            <Text size="md" ta="center" mb="xl">
              Embark on your educational journey with gamified learning experiences.
            </Text>

            <Group justify="center" gap="xl">
              <Box ta="center">
                <RobloxFAB>
                  <IconSpeed />
                </RobloxFAB>
                <Text size="sm" mt="xs">
                  Quick Start
                </Text>
              </Box>
              <Box ta="center">
                <RobloxFAB>
                  <IconTrophy />
                </RobloxFAB>
                <Text size="sm" mt="xs">
                  Achievements
                </Text>
              </Box>
              <Box ta="center">
                <RobloxFAB>
                  <IconSchool />
                </RobloxFAB>
                <Text size="sm" mt="xs">
                  Courses
                </Text>
              </Box>
            </Group>
          </GameContainer>
        </Grid.Col>

        {/* Loading States */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Loading States
              </Text>
              <Stack gap="sm">
                <RobloxSkeleton width="60%" height={32} />
                <RobloxSkeleton width="80%" height={24} />
                <RobloxSkeleton width="40%" height={24} />
                <RobloxSkeleton width="100%" height={120} />
              </Stack>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Text */}
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Text
              </Text>
              <Stack gap="xs">
                <Text size="2.5rem" fw={700}>Heading 1</Text>
                <Text size="2rem" fw={600}>Heading 2</Text>
                <Text size="1.75rem" fw={600}>Heading 3</Text>
                <Text size="1.5rem" fw={500}>Heading 4</Text>
                <Text size="1.25rem" fw={500}>Heading 5</Text>
                <Text size="1rem" fw={500}>Heading 6</Text>
                <Text size="md">
                  Body 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </Text>
                <Text size="sm" c="dimmed">
                  Body 2: Secondary text with proper contrast.
                </Text>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid.Col>

        {/* Animation Classes */}
        <Grid.Col span={12}>
          <RobloxCard>
            <Box style={{ padding: 16 }}>
              <Text size="lg" mb="md">
                Animation Classes
              </Text>
              <Text size="sm" c="dimmed" mb="md">
                Hover over elements to see animations in action.
              </Text>
              <Group gap="sm" mt="sm">
                <Paper
                  className="roblox-pulse"
                  style={{ padding: 8, textAlign: 'center', minWidth: 100 }}
                >
                  <Text size="sm">Pulse</Text>
                </Paper>
                <Paper
                  className="roblox-float"
                  style={{ padding: 8, textAlign: 'center', minWidth: 100 }}
                >
                  <Text size="sm">Float</Text>
                </Paper>
                <Paper
                  className="roblox-glow"
                  style={{ padding: 8, textAlign: 'center', minWidth: 100 }}
                >
                  <Text size="sm">Glow</Text>
                </Paper>
                <Paper
                  className="roblox-shimmer"
                  style={{ padding: 8, textAlign: 'center', minWidth: 100 }}
                >
                  <Text size="sm">Shimmer</Text>
                </Paper>
              </Group>
            </Box>
          </RobloxCard>
        </Grid.Col>
      </Grid>

      {/* Footer */}
      <Box style={{ marginTop: 48, textAlign: 'center' }}>
        <Divider style={{ marginBottom: 24 }} />
        <Text size="sm" c="dimmed">
          Roblox-Inspired Design System for ToolBoxAI Educational Platform
        </Text>
      </Box>
    </Box>
  );
};

export default ThemeShowcase;
