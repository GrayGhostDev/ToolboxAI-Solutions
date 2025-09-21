/**
 * Theme Showcase Component
 *
 * Demonstrates the Roblox-inspired design system components and features.
 * This component serves as both documentation and testing for the theme system.
 */

import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Avatar from '@mui/material/Avatar';
import Avatar from '@mui/material/Avatar';
import {
  Star,
  EmojiEvents,
  Speed,
  School,
  VideogameAsset,
  Notifications,
  Settings
} from '@mui/icons-material';
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
    <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 6, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Roblox Theme Showcase
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Current theme: {mode} mode ({isDark ? 'dark' : 'light'})
        </Typography>
        <Box sx={{ mt: 2 }}>
          <ThemeSwitcher variant="menu" showLabel />
        </Box>
      </Box>

      <Grid container spacing={4}>
        {/* Buttons Section */}
        <Grid item xs={12} md={6}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Buttons
              </Typography>
              <Stack spacing={2}>
                <RobloxButton variant="contained" size="large">
                  Primary Button
                </RobloxButton>
                <RobloxButton variant="outlined">
                  Secondary Button
                </RobloxButton>
                <RobloxButton variant="text">
                  Text Button
                </RobloxButton>
                <RobloxButton variant="contained" disabled>
                  Disabled Button
                </RobloxButton>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Chips Section */}
        <Grid item xs={12} md={6}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Gamification Chips
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <RobloxChip label="Common" rarity="common" />
                <RobloxChip label="Rare" rarity="rare" />
                <RobloxChip label="Epic" rarity="epic" />
                <RobloxChip label="Legendary" rarity="legendary" />
              </Stack>
              <Box sx={{ mt: 2 }}>
                <RobloxChip
                  label="Level 25"
                  icon={<EmojiEvents />}
                  variant="filled"
                />
                <RobloxChip
                  label="Pro Player"
                  icon={<Star />}
                  variant="outlined"
                  sx={{ ml: 1 }}
                />
              </Box>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Progress Bars */}
        <Grid item xs={12}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                XP Progress Bars
              </Typography>
              <Stack spacing={3}>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Level 1 - Beginner (25% XP)
                  </Typography>
                  <XPProgressBar value={25} level={1} />
                </Box>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Level 15 - Intermediate (65% XP)
                  </Typography>
                  <XPProgressBar value={65} level={15} />
                </Box>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Level 50 - Expert (90% XP)
                  </Typography>
                  <XPProgressBar value={90} level={50} />
                </Box>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Avatars Section */}
        <Grid item xs={12} md={6}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Gaming Avatars
              </Typography>
              <Stack direction="row" spacing={3} alignItems="center">
                <RobloxAvatar level={1} isOnline>
                  <Avatar sx={{ width: 56, height: 56 }}>
                    <VideogameAsset />
                  </Avatar>
                </RobloxAvatar>
                <RobloxAvatar level={25} isOnline={false}>
                  <Avatar sx={{ width: 56, height: 56 }}>
                    <School />
                  </Avatar>
                </RobloxAvatar>
                <AchievementBadge badgeContent="!" achievement="gold">
                  <RobloxAvatar level={100} isOnline>
                    <Avatar sx={{ width: 56, height: 56 }}>
                      <Star />
                    </Avatar>
                  </RobloxAvatar>
                </AchievementBadge>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <Stack spacing={2}>
            <RobloxNotificationCard severity="success">
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Achievement Unlocked!
                </Typography>
                <Typography variant="body2">
                  You've completed your first lesson!
                </Typography>
              </Box>
            </RobloxNotificationCard>
            
            <RobloxNotificationCard severity="info">
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  New Content Available
                </Typography>
                <Typography variant="body2">
                  Check out the latest math challenges.
                </Typography>
              </Box>
            </RobloxNotificationCard>
            
            <RobloxNotificationCard severity="warning">
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Assignment Due Soon
                </Typography>
                <Typography variant="body2">
                  You have 2 days left to submit.
                </Typography>
              </Box>
            </RobloxNotificationCard>
          </Stack>
        </Grid>

        {/* Game Container */}
        <Grid item xs={12}>
          <GameContainer>
            <Typography variant="h4" component="h2" gutterBottom align="center">
              Welcome to the Learning Arena!
            </Typography>
            <Typography variant="body1" align="center" sx={{ mb: 4 }}>
              Embark on your educational journey with gamified learning experiences.
            </Typography>
            
            <Grid container spacing={3} justifyContent="center">
              <Grid item>
                <Box sx={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <Speed />
                  </RobloxFAB>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Quick Start
                  </Typography>
                </Box>
              </Grid>
              <Grid item>
                <Box sx={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <EmojiEvents />
                  </RobloxFAB>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Achievements
                  </Typography>
                </Box>
              </Grid>
              <Grid item>
                <Box sx={{ textAlign: 'center' }}>
                  <RobloxFAB>
                    <School />
                  </RobloxFAB>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Courses
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </GameContainer>
        </Grid>

        {/* Loading States */}
        <Grid item xs={12} md={6}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Loading States
              </Typography>
              <Stack spacing={2}>
                <RobloxSkeleton width="60%" height={32} />
                <RobloxSkeleton width="80%" height={24} />
                <RobloxSkeleton width="40%" height={24} />
                <RobloxSkeleton width="100%" height={120} />
              </Stack>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Typography */}
        <Grid item xs={12} md={6}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Typography
              </Typography>
              <Stack spacing={1}>
                <Typography variant="h1">Heading 1</Typography>
                <Typography variant="h2">Heading 2</Typography>
                <Typography variant="h3">Heading 3</Typography>
                <Typography variant="h4">Heading 4</Typography>
                <Typography variant="h5">Heading 5</Typography>
                <Typography variant="h6">Heading 6</Typography>
                <Typography variant="body1">
                  Body 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Body 2: Secondary text with proper contrast.
                </Typography>
              </Stack>
            </Box>
          </RobloxCard>
        </Grid>

        {/* Animation Classes */}
        <Grid item xs={12}>
          <RobloxCard>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Animation Classes
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Hover over elements to see animations in action.
              </Typography>
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item>
                  <Paper 
                    className="roblox-pulse"
                    sx={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Typography variant="body2">Pulse</Typography>
                  </Paper>
                </Grid>
                <Grid item>
                  <Paper 
                    className="roblox-float"
                    sx={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Typography variant="body2">Float</Typography>
                  </Paper>
                </Grid>
                <Grid item>
                  <Paper 
                    className="roblox-glow"
                    sx={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Typography variant="body2">Glow</Typography>
                  </Paper>
                </Grid>
                <Grid item>
                  <Paper 
                    className="roblox-shimmer"
                    sx={{ p: 2, textAlign: 'center', minWidth: 100 }}
                  >
                    <Typography variant="body2">Shimmer</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </RobloxCard>
        </Grid>
      </Grid>

      {/* Footer */}
      <Box sx={{ mt: 6, textAlign: 'center' }}>
        <Divider sx={{ mb: 3 }} />
        <Typography variant="body2" color="text.secondary">
          Roblox-Inspired Design System for ToolBoxAI Educational Platform
        </Typography>
      </Box>
    </Box>
  );
};

export default ThemeShowcase;
