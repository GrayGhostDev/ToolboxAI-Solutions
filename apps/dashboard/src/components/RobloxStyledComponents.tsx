import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../utils/mui-imports';
/**
 * Roblox-Styled Components
 *
 * Pre-built components with Roblox theming and gamification elements.
 */
import React from 'react';
import { designTokens } from '..//designTokens';
// Roblox brand colors
const ROBLOX_RED = '#E2231A';
const ROBLOX_RED_DARK = '#B71C15';
const ROBLOX_GRAY = '#393B3D';
const ROBLOX_WHITE = '#FFFFFF';
// Animations
const robloxPulse = keyframes`
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
`;
const robloxGlow = keyframes`
  0%, 100% {
    box-shadow: 0 0 5px rgba(226, 35, 26, 0.25);
  }
  50% {
    box-shadow: 0 0 20px rgba(226, 35, 26, 0.5);
  }
`;
const robloxShimmer = keyframes`
  0% {
    background-position: -200% center;
  }
  100% {
    background-position: 200% center;
  }
`;
const robloxFloat = keyframes`
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-8px);
  }
`;
// Enhanced Card with Roblox styling
export const RobloxCard = styled(Card)(({ theme }) => ({
  borderRadius: designTokens.borderRadius['2xl'],
  border: `2px solid ${theme.palette.divider}`,
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.background.paper, 0.8)})`
    : theme.palette.background.paper,
  boxShadow: '0 4px 12px rgba(226, 35, 26, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1)',
  transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: `linear-gradient(135deg, ${ROBLOX_RED}, ${ROBLOX_RED_DARK})`,
    borderRadius: `${designTokens.borderRadius['2xl']} ${designTokens.borderRadius['2xl']} 0 0`
  },
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    borderColor: alpha(ROBLOX_RED, 0.5)
  }
}));
// Gaming-style button
export const RobloxButton = styled(Button)(({ theme }) => ({
  borderRadius: designTokens.borderRadius.xl,
  fontWeight: designTokens.typography.fontWeight.bold,
  fontSize: designTokens.typography.fontSize.sm[0],
  textTransform: 'none',
  padding: `${designTokens.spacing[3]} ${designTokens.spacing[6]}`,
  position: 'relative',
  overflow: 'hidden',
  transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
  ...(variant === 'contained' && {
    background: `linear-gradient(135deg, ${ROBLOX_RED}, ${ROBLOX_RED_DARK})`,
    color: ROBLOX_WHITE,
    boxShadow: `0 2px 8px rgba(226, 35, 26, 0.2)`,
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: '-100%',
      width: '100%',
      height: '100%',
      background: `linear-gradient(90deg, transparent, ${alpha(ROBLOX_WHITE, 0.2)}, transparent)`,
      transition: `left ${designTokens.animation.duration.slow} ${designTokens.animation.easing.inOut}`
    },
    '&:hover': {
      transform: 'translateY(-2px) scale(1.02)',
      boxShadow: `0 8px 25px ${alpha(ROBLOX_RED, 0.4)}`,
      '&::before': {
        left: '100%'
      }
    },
    '&:active': {
      transform: 'translateY(0) scale(0.98)'
    }
  }),
  ...(variant === 'outlined' && {
    borderWidth: '2px',
    borderColor: ROBLOX_RED,
    color: ROBLOX_RED,
    '&:hover': {
      borderColor: ROBLOX_RED_DARK,
      backgroundColor: alpha(ROBLOX_RED, 0.1),
      transform: 'translateY(-1px)'
    }
  })
}));
// Gamification chip
export const RobloxChip = styled(Chip)(({ theme }) => {
  const rarity = 'common'; // Default rarity
  const colorMap = {
    common: '#10B981',
    rare: '#3B82F6',
    epic: '#8B5CF6',
    legendary: '#F59E0B'
  };
  const color = colorMap[rarity];
  return {
    borderRadius: designTokens.borderRadius.full,
    fontWeight: designTokens.typography.fontWeight.bold,
    fontSize: designTokens.typography.fontSize.xs[0],
    height: 'auto',
    padding: `${designTokens.spacing[1]} ${designTokens.spacing[3]}`,
    background: `linear-gradient(135deg, ${color}, ${alpha(color, 0.8)})`,
    color: ROBLOX_WHITE,
    border: `1px solid ${alpha(color, 0.3)}`,
    boxShadow: `0 2px 8px ${alpha(color, 0.3)}`,
    transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
    '&:hover': {
      transform: 'scale(1.05)',
      boxShadow: `0 4px 15px ${alpha(color, 0.5)}`,
      animation: `${robloxGlow} 1s ease-in-out`
    }
  };
});
// XP Progress bar
export const XPProgressBar = styled(LinearProgress)<{ level?: number }>(({ theme, level = 1 }) => ({
  height: 12,
  borderRadius: designTokens.borderRadius.full,
  backgroundColor: theme.palette.mode === 'dark'
    ? alpha(ROBLOX_GRAY, 0.3)
    : alpha(ROBLOX_GRAY, 0.1),
  '& .MuiLinearProgress-bar': {
    borderRadius: designTokens.borderRadius.full,
    background: 'linear-gradient(135deg, #8B5CF6, #F59E0B)',
    position: 'relative',
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(90deg, transparent, ${alpha(ROBLOX_WHITE, 0.3)}, transparent)`,
      backgroundSize: '200% 100%',
      animation: `${robloxShimmer} 2s infinite`
    }
  }
}));
// Floating action button with game-like effects
export const RobloxFAB = styled(IconButton)(({ theme }) => ({
  width: 56,
  height: 56,
  background: `linear-gradient(135deg, ${ROBLOX_RED}, ${ROBLOX_RED_DARK})`,
  color: ROBLOX_WHITE,
  borderRadius: designTokens.borderRadius.full,
  boxShadow: `0 2px 8px rgba(226, 35, 26, 0.2)`,
  transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
  '&:hover': {
    background: `linear-gradient(135deg, ${ROBLOX_RED_DARK}, ${ROBLOX_RED})`,
    transform: 'scale(1.1)',
    boxShadow: `0 8px 25px ${alpha(ROBLOX_RED, 0.4)}`,
    animation: `${robloxFloat} 2s ease-in-out infinite`
  },
  '&:active': {
    transform: 'scale(0.95)'
  }
}));
// Gaming avatar with level badge
export const RobloxAvatar = styled(Box)<{ level?: number; isOnline?: boolean }>(({ theme, level, isOnline }) => ({
  position: 'relative',
  display: 'inline-block',
  '& .MuiAvatar-root': {
    border: `3px solid ${ROBLOX_RED}`,
    boxShadow: `0 0 0 2px ${alpha(ROBLOX_RED, 0.2)}`,
    transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`
  },
  ...(isOnline && {
    '&::after': {
      content: '""',
      position: 'absolute',
      bottom: 0,
      right: 0,
      width: 12,
      height: 12,
      backgroundColor: '#22C55E',
      borderRadius: '50%',
      border: `2px solid ${theme.palette.background.paper}`,
      animation: `${robloxPulse} 2s infinite`
    }
  }),
  ...(level && {
    '&::before': {
      content: `"${level}"`,
      position: 'absolute',
      top: -8,
      left: -8,
      width: 24,
      height: 24,
      backgroundColor: '#F59E0B',
      color: ROBLOX_WHITE,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '10px',
      fontWeight: 'bold',
      border: `2px solid ${theme.palette.background.paper}`,
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
    }
  })
}));
// Achievement badge
export const AchievementBadge = styled(Badge)<{ achievement?: 'bronze' | 'silver' | 'gold' | 'diamond' }>(({ theme, achievement = 'bronze' }) => {
  const colors = {
    bronze: '#CD7F32',
    silver: '#C0C0C0',
    gold: '#F59E0B',
    diamond: '#B9F2FF'
  };
  const color = colors[achievement];
  return {
    '& .MuiBadge-badge': {
      backgroundColor: color,
      color: achievement === 'silver' ? ROBLOX_GRAY : ROBLOX_WHITE,
      fontWeight: designTokens.typography.fontWeight.bold,
      fontSize: designTokens.typography.fontSize.xs[0],
      minWidth: 20,
      height: 20,
      borderRadius: '50%',
      border: `2px solid ${theme.palette.background.paper}`,
      boxShadow: `0 0 10px ${alpha(color, 0.5)}`,
      animation: `${robloxPulse} 3s infinite`
    }
  };
});
// Notification card with Roblox styling
export const RobloxNotificationCard = styled(RobloxCard)<{ severity?: 'info' | 'success' | 'warning' | 'error' }>(({ theme, severity = 'info' }) => {
  const colors = {
    info: '#3B82F6',
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444'
  };
  const color = colors[severity];
  return {
    backgroundColor: alpha(color, 0.1),
    borderColor: alpha(color, 0.3),
    '&::before': {
      background: color
    }
  };
});
// Loading skeleton with Roblox theme
export const RobloxSkeleton = styled(Box)<{ width?: number | string; height?: number | string }>(({ theme, width = '100%', height = 20 }) => ({
  width,
  height,
  borderRadius: designTokens.borderRadius.md,
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(90deg, ${alpha(ROBLOX_GRAY, 0.2)} 25%, ${alpha(ROBLOX_GRAY, 0.3)} 50%, ${alpha(ROBLOX_GRAY, 0.2)} 75%)`
    : `linear-gradient(90deg, ${alpha(ROBLOX_GRAY, 0.1)} 25%, ${alpha(ROBLOX_GRAY, 0.2)} 50%, ${alpha(ROBLOX_GRAY, 0.1)} 75%)`,
  backgroundSize: '200% 100%',
  animation: `${robloxShimmer} 1.5s infinite`
}));
// Gamified container
export const GameContainer = styled(Box)(({ theme }) => ({
  background: theme.palette.mode === 'dark'
    ? `radial-gradient(circle at 20% 80%, ${alpha(ROBLOX_RED, 0.1)} 0%, transparent 50%), radial-gradient(circle at 80% 20%, ${alpha('#8B5CF6', 0.1)} 0%, transparent 50%)`
    : `radial-gradient(circle at 20% 80%, ${alpha(ROBLOX_RED, 0.05)} 0%, transparent 50%), radial-gradient(circle at 80% 20%, ${alpha('#8B5CF6', 0.05)} 0%, transparent 50%)`,
  borderRadius: designTokens.borderRadius['3xl'],
  padding: designTokens.spacing[6],
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `conic-gradient(from 0deg, transparent, ${alpha(ROBLOX_RED, 0.1)}, transparent)`,
    animation: `${robloxFloat} 10s linear infinite`,
    pointerEvents: 'none'
  }
}));
export default {
  RobloxCard,
  RobloxButton,
  RobloxChip,
  XPProgressBar,
  RobloxFAB,
  RobloxAvatar,
  AchievementBadge,
  RobloxNotificationCard,
  RobloxSkeleton,
  GameContainer
};