import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import Slide from '@mui/material/Slide';
import Fade from '@mui/material/Fade';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Chip from '@mui/material/Chip';
import { styled, keyframes } from '@mui/material/styles';
import { 
  Close, 
  Notifications, 
  EmojiEvents, 
  School, 
  SportsEsports,
  Star,
  LocalFireDepartment
} from '@mui/icons-material';

interface Notification {
  id: string;
  type: 'achievement' | 'level_up' | 'xp_gain' | 'badge_earned' | 'mission_complete' | 'general';
  title: string;
  message: string;
  icon?: string;
  timestamp: Date;
  read: boolean;
  priority: 'low' | 'medium' | 'high';
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface RobloxNotificationSystemProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
  onRemove: (id: string) => void;
  onClearAll: () => void;
  maxVisible?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

// Animations
const slideInAnimation = keyframes`
  0% {
    transform: translateX(100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
`;

const bounceAnimation = keyframes`
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
`;

const glowAnimation = keyframes`
  0% {
    box-shadow: 0 0 5px currentColor;
  }
  50% {
    box-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
  }
  100% {
    box-shadow: 0 0 5px currentColor;
  }
`;

const NotificationContainer = styled(Box)(({ theme }) => ({
  position: 'fixed',
  top: 20,
  right: 20,
  zIndex: 9999,
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
  maxWidth: 400,
  width: '100%',
}));

const NotificationCard = styled(Box)(({ theme, notificationType, priority }: any) => {
  const typeColors = {
    achievement: theme.palette.success.main,
    level_up: theme.palette.primary.main,
    xp_gain: theme.palette.warning.main,
    badge_earned: theme.palette.secondary.main,
    mission_complete: theme.palette.info.main,
    general: theme.palette.grey[600]
  };

  const priorityStyles = {
    low: { borderLeft: `3px solid ${typeColors[notificationType]}` },
    medium: { 
      borderLeft: `4px solid ${typeColors[notificationType]}`,
      boxShadow: `0 0 10px ${alpha(typeColors[notificationType], 0.3)}`
    },
    high: { 
      borderLeft: `5px solid ${typeColors[notificationType]}`,
      boxShadow: `0 0 15px ${alpha(typeColors[notificationType], 0.5)}`,
      animation: `${glowAnimation} 2s ease-in-out infinite`
    }
  };

  return {
    background: `linear-gradient(135deg, ${theme.palette.background.paper}, ${alpha(typeColors[notificationType], 0.05)})`,
    borderRadius: 12,
    padding: 16,
    border: `1px solid ${alpha(typeColors[notificationType], 0.2)}`,
    backdropFilter: 'blur(10px)',
    animation: `${slideInAnimation} 0.3s ease-out`,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    cursor: 'pointer',
    position: 'relative',
    overflow: 'hidden',
    
    '&:hover': {
      transform: 'translateX(-5px) scale(1.02)',
      boxShadow: `0 8px 25px ${alpha(typeColors[notificationType], 0.4)}`,
    },
    
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(45deg, transparent, ${alpha(typeColors[notificationType], 0.1)}, transparent)`,
      transform: 'translateX(-100%)',
      transition: 'transform 0.6s ease',
    },
    
    '&:hover::before': {
      transform: 'translateX(100%)',
    },
    
    ...priorityStyles[priority]
  };
});

const NotificationIcon = styled(Box)(({ theme, notificationType }: any) => {
  const typeColors = {
    achievement: theme.palette.success.main,
    level_up: theme.palette.primary.main,
    xp_gain: theme.palette.warning.main,
    badge_earned: theme.palette.secondary.main,
    mission_complete: theme.palette.info.main,
    general: theme.palette.grey[600]
  };

  return {
    width: 40,
    height: 40,
    borderRadius: '50%',
    background: `linear-gradient(135deg, ${typeColors[notificationType]}, ${alpha(typeColors[notificationType], 0.7)})`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '1.2rem',
    boxShadow: `0 4px 12px ${alpha(typeColors[notificationType], 0.4)}`,
    animation: `${bounceAnimation} 0.6s ease-out`,
  };
});

const getNotificationIcon = (type: string) => {
  const iconMap: { [key: string]: React.ComponentType<any> } = {
    achievement: EmojiEvents,
    level_up: Star,
    xp_gain: LocalFireDepartment,
    badge_earned: School,
    mission_complete: SportsEsports,
    general: Notifications,
  };
  return iconMap[type] || Notifications;
};

export const RobloxNotificationSystem: React.FunctionComponent<RobloxNotificationSystemProps> = ({
  notifications,
  onMarkAsRead,
  onRemove,
  onClearAll,
  maxVisible = 5,
  position = 'top-right'
}) => {
  const theme = useTheme();
  const [visibleNotifications, setVisibleNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    const unreadNotifications = notifications
      .filter(n => !n.read)
      .sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      })
      .slice(0, maxVisible);
    
    setVisibleNotifications(unreadNotifications);
  }, [notifications, maxVisible]);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
    if (notification.action) {
      notification.action.onClick();
    }
  };

  const getPriorityChip = (priority: string) => {
    const priorityStyles = {
      low: { color: theme.palette.grey[500], label: 'Low' },
      medium: { color: theme.palette.warning.main, label: 'Medium' },
      high: { color: theme.palette.error.main, label: 'High' }
    };
    
    const style = priorityStyles[priority as keyof typeof priorityStyles];
    return (
      <Chip
        label={style.label}
        size="small"
        sx={{
          color: style.color,
          borderColor: style.color,
          backgroundColor: alpha(style.color, 0.1),
          fontWeight: 600,
          fontSize: '0.7rem',
          height: 20,
        }}
      />
    );
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <NotificationContainer sx={{
      [position.includes('left') ? 'left' : 'right']: 20,
      [position.includes('top') ? 'top' : 'bottom']: 20,
    }}>
      {visibleNotifications.map((notification, index) => {
        const IconComponent = getNotificationIcon(notification.type);
        
        return (
          <Slide
            key={notification.id}
            direction="left"
            in={true}
            timeout={300 + index * 100}
          >
            <NotificationCard
              notificationType={notification.type}
              priority={notification.priority}
              onClick={(e: React.MouseEvent) => () => handleNotificationClick(notification)}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <NotificationIcon notificationType={notification.type}>
                  <IconComponent />
                </NotificationIcon>
                
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: 700,
                        color: theme.palette.text.primary,
                        flex: 1,
                      }}
                    >
                      {notification.title}
                    </Typography>
                    {getPriorityChip(notification.priority)}
                  </Box>
                  
                  <Typography
                    variant="body2"
                    sx={{
                      color: theme.palette.text.secondary,
                      mb: 1,
                      lineHeight: 1.4,
                    }}
                  >
                    {notification.message}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography
                      variant="caption"
                      sx={{
                        color: theme.palette.text.disabled,
                        fontSize: '0.7rem',
                      }}
                    >
                      {notification.timestamp.toLocaleTimeString()}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {notification.action && (
                        <Chip
                          label={notification.action.label}
                          size="small"
                          onClick={(e: React.MouseEvent) => (e) => {
                            e.stopPropagation();
                            notification.action!.onClick();
                          }}
                          sx={{
                            backgroundColor: theme.palette.primary.main,
                            color: 'white',
                            fontSize: '0.7rem',
                            height: 20,
                            '&:hover': {
                              backgroundColor: theme.palette.primary.dark,
                            }
                          }}
                        />
                      )}
                      
                      <IconButton
                        size="small"
                        onClick={(e: React.MouseEvent) => (e) => {
                          e.stopPropagation();
                          onRemove(notification.id);
                        }}
                        sx={{
                          color: theme.palette.text.disabled,
                          '&:hover': {
                            color: theme.palette.error.main,
                            backgroundColor: alpha(theme.palette.error.main, 0.1),
                          }
                        }}
                      >
                        <Close fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              </Box>
            </NotificationCard>
          </Slide>
        );
      })}
      
      {notifications.length > maxVisible && (
        <Box sx={{ textAlign: 'center', mt: 1 }}>
          <Chip
            label={`+${notifications.length - maxVisible} more notifications`}
            onClick={(e: React.MouseEvent) => onClearAll}
            sx={{
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              color: theme.palette.primary.main,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.2),
              }
            }}
          />
        </Box>
      )}
    </NotificationContainer>
  );
};
