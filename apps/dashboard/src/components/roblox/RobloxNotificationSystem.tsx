/**
 * Roblox Notification System Component
 *
 * Displays fun, engaging notifications for achievements, level ups, XP gains, etc.
 * Designed with a Roblox-inspired aesthetic for educational gaming experiences.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  ActionIcon,
  Group,
  useMantineTheme,
  rem
} from '@mantine/core';
import {
  IconX,
  IconTrophy,
  IconStar,
  IconCoin,
  IconBadge,
  IconTarget,
  IconBell
} from '@tabler/icons-react';

export type NotificationType =
  | 'achievement'
  | 'level_up'
  | 'xp_gain'
  | 'badge_earned'
  | 'mission_complete'
  | 'general';

export type NotificationPriority = 'low' | 'medium' | 'high';

export type NotificationPosition =
  | 'top-right'
  | 'top-left'
  | 'bottom-right'
  | 'bottom-left';

export interface RobloxNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  duration?: number;
  icon?: React.ReactNode;
}

interface NotificationCardProps {
  notification: RobloxNotification;
  onClose: (id: string) => void;
}

interface RobloxNotificationSystemProps {
  notifications: RobloxNotification[];
  position?: NotificationPosition;
  maxNotifications?: number;
  onNotificationClose?: (id: string) => void;
}

// Keyframe animations defined as CSS strings
const animations = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-5px);
    }
  }

  @keyframes glow {
    0%, 100% {
      box-shadow: 0 0 10px currentColor;
    }
    50% {
      box-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
    }
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%) skewX(-15deg);
    }
    100% {
      transform: translateX(200%) skewX(-15deg);
    }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'roblox-notification-system-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = animations;
    document.head.appendChild(style);
  }
}

const NotificationCard: React.FC<NotificationCardProps> = ({ notification, onClose }) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);

  const typeColors = {
    achievement: theme.colors.green[6],
    level_up: theme.colors.blue[6],
    xp_gain: theme.colors.yellow[6],
    badge_earned: theme.colors.violet[6],
    mission_complete: theme.colors.cyan[6],
    general: theme.colors.gray[6]
  };

  const typeIcons = {
    achievement: <IconTrophy size={24} />,
    level_up: <IconStar size={24} />,
    xp_gain: <IconCoin size={24} />,
    badge_earned: <IconBadge size={24} />,
    mission_complete: <IconTarget size={24} />,
    general: <IconBell size={24} />
  };

  const mainColor = typeColors[notification.type];

  const priorityStyles = {
    low: {
      borderLeft: `3px solid ${mainColor}`
    },
    medium: {
      borderLeft: `4px solid ${mainColor}`,
      boxShadow: `0 0 10px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.3)`
    },
    high: {
      borderLeft: `5px solid ${mainColor}`,
      boxShadow: `0 0 15px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.5)`,
      animation: 'glow 2s ease-in-out infinite'
    }
  };

  const cardStyle: React.CSSProperties = {
    position: 'relative',
    background: `linear-gradient(135deg, ${theme.colors.dark[6]}, rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.05))`,
    borderRadius: rem(12),
    padding: rem(16),
    marginBottom: rem(12),
    minWidth: 300,
    maxWidth: 400,
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    animation: 'slideIn 0.4s ease-out',
    overflow: 'hidden',
    transform: isHovered ? 'translateX(-5px) scale(1.02)' : 'none',
    ...priorityStyles[notification.priority]
  };

  const iconContainerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 48,
    height: 48,
    borderRadius: '50%',
    background: `linear-gradient(135deg, ${mainColor}, rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.7))`,
    color: 'white',
    boxShadow: `0 4px 12px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.4)`,
    animation: notification.priority === 'high' ? 'bounce 1s ease-in-out infinite' : 'none'
  };

  const shimmerOverlayStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
    pointerEvents: 'none',
    opacity: isHovered ? 1 : 0,
    animation: isHovered ? 'shimmer 2s infinite' : 'none',
    transition: 'opacity 0.3s ease'
  };

  return (
    <Box
      style={cardStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Group style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Group style={{ gap: rem(12), alignItems: 'flex-start', flex: 1 }}>
          <Box style={iconContainerStyle}>
            {notification.icon || typeIcons[notification.type]}
          </Box>

          <Box style={{ flex: 1 }}>
            <Text
              fw={700}
              size="lg"
              style={{
                color: mainColor,
                textShadow: `0 0 10px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.5)`,
                marginBottom: rem(4)
              }}
            >
              {notification.title}
            </Text>

            <Text
              size="sm"
              c="dimmed"
            >
              {notification.message}
            </Text>
          </Box>
        </Group>

        <ActionIcon
          variant="subtle"
          color="gray"
          onClick={() => onClose(notification.id)}
          style={{
            opacity: isHovered ? 1 : 0.6,
            transition: 'opacity 0.3s ease'
          }}
        >
          <IconX size={18} />
        </ActionIcon>
      </Group>

      {/* Shimmer effect overlay */}
      <Box style={shimmerOverlayStyle} />
    </Box>
  );
};

export const RobloxNotificationSystem: React.FC<RobloxNotificationSystemProps> = ({
  notifications,
  position = 'top-right',
  maxNotifications = 5,
  onNotificationClose
}) => {
  const [activeNotifications, setActiveNotifications] = useState<RobloxNotification[]>([]);

  useEffect(() => {
    setActiveNotifications(notifications.slice(0, maxNotifications));
  }, [notifications, maxNotifications]);

  useEffect(() => {
    const timers = activeNotifications
      .filter(n => n.duration)
      .map(notification => {
        return setTimeout(() => {
          handleClose(notification.id);
        }, notification.duration);
      });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [activeNotifications]);

  const handleClose = (id: string) => {
    setActiveNotifications(prev => prev.filter(n => n.id !== id));
    onNotificationClose?.(id);
  };

  const positionStyles = {
    'top-right': { top: 20, right: 20 },
    'top-left': { top: 20, left: 20 },
    'bottom-right': { bottom: 20, right: 20 },
    'bottom-left': { bottom: 20, left: 20 }
  };

  const containerStyle: React.CSSProperties = {
    position: 'fixed',
    ...positionStyles[position],
    zIndex: 9999,
    pointerEvents: 'none'
  };

  const notificationWrapperStyle: React.CSSProperties = {
    pointerEvents: 'auto'
  };

  return (
    <Box style={containerStyle}>
      <Box style={notificationWrapperStyle}>
        {activeNotifications.map(notification => (
          <NotificationCard
            key={notification.id}
            notification={notification}
            onClose={handleClose}
          />
        ))}
      </Box>
    </Box>
  );
};

export default RobloxNotificationSystem;
