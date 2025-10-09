import { Box, Button, Text, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../utils/mui-imports';
/**
 * Theme Showcase Component
 *
 * Demonstrates the Roblox-inspired design system components and features.
 * This component serves as both documentation and testing for the theme system.
 */

import React from 'react';
import { IconBell, IconEmojiEvents, IconSchool, IconSettings, IconSpeed, IconStar, IconVideogameAsset } from '@tabler/icons-react';
import {
  IconHome, IconUser, IconSettings, IconLogout, IconChevronDown,
  IconChevronUp, IconChevronLeft, IconChevronRight, IconMenu,
  IconX, IconCheck, IconPlus, IconMinus, IconEdit, IconTrash,
  IconSearch, IconFilter, IconDownload, IconUpload, IconEye,
  IconEyeOff, IconBell, IconMessage, IconStar, IconHeart,
  IconShare, IconRefresh, IconLogin, IconSchool, IconBook,
  IconChartBar, IconPalette, IconMoon, IconSun, IconPlayerPlay,
  IconPlayerPause, IconPlayerStop, IconVolume, IconVolumeOff,
  IconInfoCircle, IconAlertTriangle, IconCircleX, IconCircleCheck,
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
    <Box style={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box style={{ mb: 6, textAlign: 'center' }}>
        <Text order={2} component="h1" gutterBottom>
          Roblox Theme Showcase
        </Text>
        <Text order={6} color="text.secondary" gutterBottom>
          Current theme: {mode} mode ({isDark ? 'dark' : 'light'})
        </Text>
        <Box style={{ mt: 2 }}>
          <ThemeSwitcher variant="menu" showLabel />
        </Box>
      </Box>

      <SimpleGrid spacing={4}>
        {/* Buttons Section */}
        <Box xs={12} md={6}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Buttons
              </Text>
              <Stack gap={2}>
                <RobloxButton variant="filled" size="large">
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
        </SimpleGrid>

        {/* Chips Section */}
        <Box xs={12} md={6}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Gamification Chips
              </Text>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <RobloxChip label="Common" rarity="common" />
                <RobloxChip label="Rare" rarity="rare" />
                <RobloxChip label="Epic" rarity="epic" />
                <RobloxChip label="Legendary" rarity="legendary" />
              </Stack>
              <Box style={{ mt: 2 }}>
                <RobloxChip
                  label="Level 25"
                  icon={<IconEmojiEvents />}
                  variant="filled"
                />
                <RobloxChip
                  label="Pro Player"
                  icon={<IconStar />}
                  variant="outline"
                  style={{ ml: 1 }}
                />
              </Box>
            </Box>
          </RobloxCard>
        </SimpleGrid>

        {/* Progress Bars */}
        <Box xs={12}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                XP Progress Bars
              </Text>
              <Stack gap={3}>
                <Box>
                  <Text size="sm" gutterBottom>
                    Level 1 - Beginner (25% XP)
                  </Text>
                  <XPProgressBar value={25} level={1} />
                </Box>
                <Box>
                  <Text size="sm" gutterBottom>
                    Level 15 - Intermediate (65% XP)
                  </Text>
                  <XPProgressBar value={65} level={15} />
                </Box>
                <Box>
                  <Text size="sm" gutterBottom>
                    Level 50 - Expert (90% XP)
                  </Text>
                  <XPProgressBar value={90} level={50} />
                </Box>
              </Stack>
            </Box>
          </RobloxCard>
        </SimpleGrid>

        {/* Avatars Section */}
        <Box xs={12} md={6}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Gaming Avatars
              </Text>
              <Stack direction="row" spacing={3} alignItems="center">
                <RobloxAvatar level={1} isOnline>
                  <Avatar style={{ width: 56, height: 56 }}>
                    <IconVideogameAsset />
                  </Avatar>
                </RobloxAvatar>
                <RobloxAvatar level={25} isOnline={false}>
                  <Avatar style={{ width: 56, height: 56 }}>
                    <IconSchool />
                  </Avatar>
                </RobloxAvatar>
                <AchievementBadge badgeContent="!" achievement="gold">
                  <RobloxAvatar level={100} isOnline>
                    <Avatar style={{ width: 56, height: 56 }}>
                      <IconStar />
                    </Avatar>
                  </RobloxAvatar>
                </AchievementBadge>
              </Stack>
            </Box>
          </RobloxCard>
        </SimpleGrid>

        {/* IconBell */}
        <Box xs={12} md={6}>
          <Stack gap={2}>
            <RobloxNotificationCard severity="success">
              <Box style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  Achievement Unlocked!
                </Text>
                <Text size="sm">
                  You've completed your first lesson!
                </Text>
              </Box>
            </RobloxNotificationCard>
            
            <RobloxNotificationCard severity="info">
              <Box style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  New Content Available
                </Text>
                <Text size="sm">
                  Check out the latest math challenges.
                </Text>
              </Box>
            </RobloxNotificationCard>
            
            <RobloxNotificationCard severity="warning">
              <Box style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  Assignment Due Soon
                </Text>
                <Text size="sm">
                  You have 2 days left to submit.
                </Text>
              </Box>
            </RobloxNotificationCard>
          </Stack>
        </SimpleGrid>

        {/* Game Container */}
        <Box xs={12}>
          <GameContainer>
            <Text order={4} component="h2" gutterBottom align="center">
              Welcome to the Learning Arena!
            </Text>
            <Text size="md" align="center" style={{ mb: 4 }}>
              Embark on your educational journey with gamified learning experiences.
            </Text>
            
            <SimpleGrid spacing={3} justifyContent="center">
              <Box>
                <Box style={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <IconSpeed />
                  </RobloxFAB>
                  <Text size="sm" style={{ mt: 1 }}>
                    Quick Start
                  </Text>
                </Box>
              </SimpleGrid>
              <Box>
                <Box style={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <IconEmojiEvents />
                  </RobloxFAB>
                  <Text size="sm" style={{ mt: 1 }}>
                    Achievements
                  </Text>
                </Box>
              </SimpleGrid>
              <Box>
                <Box style={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <IconSchool />
                  </RobloxFAB>
                  <Text size="sm" style={{ mt: 1 }}>
                    Courses
                  </Text>
                </Box>
              </SimpleGrid>
            </SimpleGrid>
          </GameContainer>
        </SimpleGrid>

        {/* Loading States */}
        <Box xs={12} md={6}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Loading States
              </Text>
              <Stack gap={2}>
                <RobloxSkeleton width="60%" height={32} />
                <RobloxSkeleton width="80%" height={24} />
                <RobloxSkeleton width="40%" height={24} />
                <RobloxSkeleton width="100%" height={120} />
              </Stack>
            </Box>
          </RobloxCard>
        </SimpleGrid>

        {/* Text */}
        <Box xs={12} md={6}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Text
              </Text>
              <Stack gap={1}>
                <Text order={1}>Heading 1</Text>
                <Text order={2}>Heading 2</Text>
                <Text order={3}>Heading 3</Text>
                <Text order={4}>Heading 4</Text>
                <Text order={5}>Heading 5</Text>
                <Text order={6}>Heading 6</Text>
                <Text size="md">
                  Body 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </Text>
                <Text size="sm" color="text.secondary">
                  Body 2: Secondary text with proper contrast.
                </Text>
              </Stack>
            </Box>
          </RobloxCard>
        </SimpleGrid>

        {/* Animation Classes */}
        <Box xs={12}>
          <RobloxCard>
            <Box style={{ p: 3 }}>
              <Text order={5} gutterBottom>
                Animation Classes
              </Text>
              <Text size="sm" color="text.secondary" gutterBottom>
                Hover over elements to see animations in action.
              </Text>
              <SimpleGrid spacing={2} style={{ mt: 2 }}>
                <Box>
                  <Paper 
                    className="roblox-pulse"
                    style={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Text size="sm">Pulse</Text>
                  </Paper>
                </SimpleGrid>
                <Box>
                  <Paper 
                    className="roblox-float"
                    style={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Text size="sm">Float</Text>
                  </Paper>
                </SimpleGrid>
                <Box>
                  <Paper 
                    className="roblox-glow"
                    style={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Text size="sm">Glow</Text>
                  </Paper>
                </SimpleGrid>
                <Box>
                  <Paper 
                    className="roblox-shimmer"
                    style={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Text size="sm">Shimmer</Text>
                  </Paper>
                </SimpleGrid>
              </SimpleGrid>
            </Box>
          </RobloxCard>
        </SimpleGrid>
      </SimpleGrid>

      {/* Footer */}
      <Box style={{ mt: 6, textAlign: 'center' }}>
        <Divider style={{ mb: 3 }} />
        <Text size="sm" color="text.secondary">
          Roblox-Inspired Design System for ToolBoxAI Educational Platform
        </Text>
      </Box>
    </Box>
  );
};

export default ThemeShowcase;
