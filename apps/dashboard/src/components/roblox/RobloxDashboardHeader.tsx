/**
 * Roblox Dashboard Header Component
 * 
 * Futuristic header with character avatars, notifications, and navigation
 * designed for kids with engaging animations and effects
 */

import React, { useState, useEffect } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import Stack from '@mui/material/Stack';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Divider from '@mui/material/Divider';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import Fade from '@mui/material/Fade';
import Slide from '@mui/material/Slide';
import Zoom from '@mui/material/Zoom';
import Zoom from '@mui/material/Zoom';
import {
  Notifications,
  Settings,
  Help,
  AccountCircle,
  RocketLaunch,
  Star,
  EmojiEvents,
  AutoAwesome,
  Menu as MenuIcon,
  Close
} from '@mui/icons-material';
import { RobloxCharacterAvatar } from './RobloxCharacterAvatar';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'achievement' | 'level_up' | 'new_content' | 'reminder';
  timestamp: Date;
  isRead: boolean;
}

interface RobloxDashboardHeaderProps {
  title?: string;
  subtitle?: string;
  onMenuClick?: () => void;
  onNotificationClick?: (notification: Notification) => void;
  onSettingsClick?: () => void;
  onHelpClick?: () => void;
  onProfileClick?: () => void;
}

const SAMPLE_CHARACTERS = [
  {
    name: 'Astro Explorer',
    type: 'astronaut' as const,
    level: 5,
    xp: 1250,
    achievements: ['Space Walker', 'Quiz Master'],
    isActive: true,
    imagePath: '/images/characters/PNG/Astronauto (variation)/01.png'
  },
  {
    name: 'Alien Buddy',
    type: 'alien' as const,
    level: 3,
    xp: 800,
    achievements: ['First Contact'],
    isActive: false,
    imagePath: '/images/characters/PNG/Aliens/back.png'
  }
];

const SAMPLE_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    title: 'Level Up! 🎉',
    message: 'You reached Level 5! New features unlocked!',
    type: 'level_up',
    timestamp: new Date(),
    isRead: false
  },
  {
    id: '2',
    title: 'Achievement Unlocked! ⭐',
    message: 'Space Walker - Complete 10 space missions',
    type: 'achievement',
    timestamp: new Date(Date.now() - 3600000),
    isRead: false
  },
  {
    id: '3',
    title: 'New Content Available! 🚀',
    message: 'Check out the new math challenges!',
    type: 'new_content',
    timestamp: new Date(Date.now() - 7200000),
    isRead: true
  }
];

export const RobloxDashboardHeader: React.FunctionComponent<RobloxDashboardHeaderProps> = ({
  title = 'ToolBoxAI Space Station',
  subtitle = 'Your Learning Adventure Awaits!',
  onMenuClick,
  onNotificationClick,
  onSettingsClick,
  onHelpClick,
  onProfileClick
}) => {
  const theme = useTheme();
  const [notifications, setNotifications] = useState<Notification[]>(SAMPLE_NOTIFICATIONS);
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<null | HTMLElement>(null);
  const [profileMenuAnchor, setProfileMenuAnchor] = useState<null | HTMLElement>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  useEffect(() => {
    // Animate header elements on mount
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleNotificationClick = (notification: Notification) => {
    setNotifications(prev => 
      prev.map(n => n.id === notification.id ? { ...n, isRead: true } : n)
    );
    if (onNotificationClick) {
      onNotificationClick(notification);
    }
    setNotificationMenuAnchor(null);
  };

  const handleProfileClick = () => {
    if (onProfileClick) {
      onProfileClick();
    }
    setProfileMenuAnchor(null);
  };

  return (
    <AppBar
      position="sticky"
      sx={{
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.9)}, ${alpha(theme.palette.secondary.main, 0.9)})`,
        backdropFilter: 'blur(20px)',
        borderBottom: `2px solid ${alpha(theme.palette.primary.main, 0.3)}`,
        boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
      }}
    >
      <Toolbar sx={{ minHeight: 80, py: 1 }}>
        {/* Left Section - Menu & Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          <IconButton
            edge="start"
            color="inherit"
            onClick={(e: React.MouseEvent) => onMenuClick}
            sx={{
              mr: 2,
              p: 1,
              background: alpha('#fff', 0.1),
              '&:hover': {
                background: alpha('#fff', 0.2),
                transform: 'scale(1.1)',
              },
              transition: 'all 0.3s ease'
            }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ flex: 1 }}>
            <Fade in={isAnimating} timeout={1000}>
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  mb: 0.5
                }}
              >
                {title}
              </Typography>
            </Fade>
            
            <Slide in={isAnimating} direction="up" timeout={1500}>
              <Typography
                variant="subtitle1"
                sx={{
                  color: alpha('#fff', 0.9),
                  fontWeight: 500,
                  fontSize: '1.1rem'
                }}
              >
                {subtitle}
              </Typography>
            </Slide>
          </Box>
        </Box>

        {/* Center Section - Character Avatars */}
        <Box sx={{ display: 'flex', alignItems: 'center', mx: 4 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            {SAMPLE_CHARACTERS.map((character, index) => (
              <Zoom
                in={isAnimating}
                timeout={2000 + index * 200}
                key={character.name}
              >
                <Box>
                  <RobloxCharacterAvatar
                    character={character}
                    size="medium"
                    animated={true}
                    onClick={(e: React.MouseEvent) => () => console.log(`Selected ${character.name}`)}
                  />
                </Box>
              </Zoom>
            ))}
          </Stack>
        </Box>

        {/* Right Section - Actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notifications */}
          <IconButton
            color="inherit"
            onClick={(e: React.MouseEvent) => (e) => setNotificationMenuAnchor(e.currentTarget)}
            sx={{
              p: 1,
              background: alpha('#fff', 0.1),
              '&:hover': {
                background: alpha('#fff', 0.2),
                transform: 'scale(1.1)',
              },
              transition: 'all 0.3s ease'
            }}
          >
            <Badge badgeContent={unreadCount} color="error">
              <Notifications />
            </Badge>
          </IconButton>

          {/* Settings */}
          <IconButton
            color="inherit"
            onClick={(e: React.MouseEvent) => onSettingsClick}
            sx={{
              p: 1,
              background: alpha('#fff', 0.1),
              '&:hover': {
                background: alpha('#fff', 0.2),
                transform: 'scale(1.1)',
              },
              transition: 'all 0.3s ease'
            }}
          >
            <Settings />
          </IconButton>

          {/* Help */}
          <IconButton
            color="inherit"
            onClick={(e: React.MouseEvent) => onHelpClick}
            sx={{
              p: 1,
              background: alpha('#fff', 0.1),
              '&:hover': {
                background: alpha('#fff', 0.2),
                transform: 'scale(1.1)',
              },
              transition: 'all 0.3s ease'
            }}
          >
            <Help />
          </IconButton>

          {/* Profile */}
          <IconButton
            color="inherit"
            onClick={(e: React.MouseEvent) => (e) => setProfileMenuAnchor(e.currentTarget)}
            sx={{
              p: 1,
              background: alpha('#fff', 0.1),
              '&:hover': {
                background: alpha('#fff', 0.2),
                transform: 'scale(1.1)',
              },
              transition: 'all 0.3s ease'
            }}
          >
            <AccountCircle />
          </IconButton>
        </Box>
      </Toolbar>

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationMenuAnchor}
        open={Boolean(notificationMenuAnchor)}
        onClose={() => setNotificationMenuAnchor(null)}
        PaperProps={{
          sx: {
            background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
            backdropFilter: 'blur(20px)',
            minWidth: 300,
            maxHeight: 400,
            overflow: 'auto'
          }
        }}
      >
        <Box sx={{ p: 2, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
          <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
            Notifications
          </Typography>
        </Box>
        
        {notifications.map((notification) => (
          <MenuItem
            key={notification.id}
            onClick={(e: React.MouseEvent) => () => handleNotificationClick(notification)}
            sx={{
              py: 2,
              px: 2,
              borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              background: notification.isRead ? 'transparent' : alpha(theme.palette.primary.main, 0.05),
              '&:hover': {
                background: alpha(theme.palette.primary.main, 0.1),
              }
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {notification.title}
                </Typography>
                {!notification.isRead && (
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: theme.palette.primary.main
                    }}
                  />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary">
                {notification.message}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {notification.timestamp.toLocaleTimeString()}
              </Typography>
            </Box>
          </MenuItem>
        ))}
      </Menu>

      {/* Profile Menu */}
      <Menu
        anchorEl={profileMenuAnchor}
        open={Boolean(profileMenuAnchor)}
        onClose={() => setProfileMenuAnchor(null)}
        PaperProps={{
          sx: {
            background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
            backdropFilter: 'blur(20px)',
            minWidth: 200
          }
        }}
      >
        <MenuItem onClick={(e: React.MouseEvent) => handleProfileClick}>
          <AccountCircle sx={{ mr: 2 }} />
          Profile
        </MenuItem>
        <MenuItem onClick={(e: React.MouseEvent) => onSettingsClick}>
          <Settings sx={{ mr: 2 }} />
          Settings
        </MenuItem>
        <Divider />
        <MenuItem onClick={(e: React.MouseEvent) => onHelpClick}>
          <Help sx={{ mr: 2 }} />
          Help & Support
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default RobloxDashboardHeader;
