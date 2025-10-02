import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  ActionIcon,
  Badge,
  Group,
  Transition,
  useMantineTheme,
  keyframes,
  rem
} from '@mantine/core';
// import { createStyles } from '@mantine/emotion'; // Removed - using inline styles instead
import {
  IconX,
  IconBell,
  IconTrophy,
  IconSchool,
  IconDeviceGamepad2,
  IconStar,
  IconFlame
} from '@tabler/icons-react';

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
const slideInAnimation = keyframes({
  '0%': {
    transform: 'translateX(100%)',
    opacity: 0
  },
  '100%': {
    transform: 'translateX(0)',
    opacity: 1
  }
});

const bounceAnimation = keyframes({
  '0%, 20%, 50%, 80%, 100%': {
    transform: 'translateY(0)'
  },
  '40%': {
    transform: 'translateY(-10px)'
  },
  '60%': {
    transform: 'translateY(-5px)'
  }
});

const glowAnimation = keyframes({
  '0%': {
    boxShadow: '0 0 5px currentColor'
  },
  '50%': {
    boxShadow: '0 0 20px currentColor, 0 0 30px currentColor'
  },
  '100%': {
    boxShadow: '0 0 5px currentColor'
  }
});

interface NotificationStyleOptions {
  notificationType: string;
  priority: string;
}

const useStyles = createStyles((theme, { notificationType, priority }: NotificationStyleOptions) => {
  const typeColors = {
    achievement: theme.colors.green[6],
    level_up: theme.colors.blue[6],
    xp_gain: theme.colors.yellow[6],
    badge_earned: theme.colors.violet[6],
    mission_complete: theme.colors.cyan[6],
    general: theme.colors.gray[6]
  };

  const priorityStyles = {
    low: { borderLeft: `3px solid ${typeColors[notificationType as keyof typeof typeColors]}` },
    medium: {
      borderLeft: `4px solid ${typeColors[notificationType as keyof typeof typeColors]}`,
      boxShadow: `0 0 10px ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.3)}`
    },
    high: {
      borderLeft: `5px solid ${typeColors[notificationType as keyof typeof typeColors]}`,
      boxShadow: `0 0 15px ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.5)}`,
      animation: `${glowAnimation} 2s ease-in-out infinite`
    }
  };

  return {
    container: {
      position: 'fixed',
      top: 20,
      right: 20,
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: rem(12),
      maxWidth: 400,
      width: '100%'
    },
    card: {
      background: `linear-gradient(135deg, ${theme.colors.dark[6]}, ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.05)})`,
      borderRadius: rem(12),
      padding: rem(16),
      border: `1px solid ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.2)}`,
      backdropFilter: 'blur(10px)',
      animation: `${slideInAnimation} 0.3s ease-out`,
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      cursor: 'pointer',
      position: 'relative',
      overflow: 'hidden',
      ...priorityStyles[priority as keyof typeof priorityStyles],

      '&:hover': {
        transform: 'translateX(-5px) scale(1.02)',
        boxShadow: `0 8px 25px ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.4)}`
      },

      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(45deg, transparent, ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.1)}, transparent)`,
        transform: 'translateX(-100%)',
        transition: 'transform 0.6s ease'
      },

      '&:hover::before': {
        transform: 'translateX(100%)'
      }
    },
    iconContainer: {
      width: 40,
      height: 40,
      borderRadius: '50%',
      background: `linear-gradient(135deg, ${typeColors[notificationType as keyof typeof typeColors]}, ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.7)})`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      boxShadow: `0 4px 12px ${theme.fn.rgba(typeColors[notificationType as keyof typeof typeColors], 0.4)}`,
      animation: `${bounceAnimation} 0.6s ease-out`
    }
  };
});

const getNotificationIcon = (type: string) => {
  const iconMap: Record<string, React.ComponentType<any>> = {
    achievement: IconTrophy,
    level_up: IconStar,
    xp_gain: IconFlame,
    badge_earned: IconSchool,
    mission_complete: IconDeviceGamepad2,
    general: IconBell,
  };
  return iconMap[type] || IconBell;
};

interface NotificationCardProps {
  notification: Notification;
  index: number;
  onRemove: (id: string) => void;
  onClick: (notification: Notification) => void;
  priorityBadge: React.ReactNode;
}

export const NotificationCard = ({
  notification,
  index,
  onRemove,
  onClick,
  priorityBadge,
}: NotificationCardProps) => {
  const { classes } = useStyles({ notificationType: notification.type, priority: notification.priority });
  const theme = useMantineTheme();
  const IconComponent = getNotificationIcon(notification.type);

  return (
    <Transition mounted transition="slide-left" duration={300 + index * 100}>
      {(styles) => (
        <Box
          className={classes.card}
          style={styles}
          onClick={() => onClick(notification)}
        >
          <Group spacing="md" align="flex-start">
            <Box className={classes.iconContainer}>
              <IconComponent size={20} />
            </Box>

            <Box style={{ flex: 1, minWidth: 0 }}>
              <Group spacing="xs" mb="xs" align="center">
                <Text size="sm" fw={700} style={{ flex: 1 }}>
                  {notification.title}
                </Text>
                {priorityBadge}
              </Group>

              <Text size="sm" c="dimmed" mb="xs" style={{ lineHeight: 1.4 }}>
                {notification.message}
              </Text>

              <Group justify="space-between" align="center">
                <Text size="xs" c="dimmed">
                  {notification.timestamp.toLocaleTimeString()}
                </Text>

                <Group spacing="xs">
                  {notification.action && (
                    <Badge
                      size="sm"
                      variant="filled"
                      style={{
                        cursor: 'pointer',
                        backgroundColor: theme.colors.blue[6],
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        notification.action?.onClick();
                      }}
                    >
                      {notification.action.label}
                    </Badge>
                  )}

                  <ActionIcon
                    size="sm"
                    variant="subtle"
                    c="dimmed"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemove(notification.id);
                    }}
                    styles={{
                      root: {
                        '&:hover': {
                          color: theme.colors.red[6],
                          backgroundColor: theme.fn.rgba(theme.colors.red[6], 0.1),
                        },
                      },
                    }}
                  >
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
              </Group>
            </Box>
          </Group>
        </Box>
      )}
    </Transition>
  );
};

export const RobloxNotificationSystem: React.FunctionComponent<RobloxNotificationSystemProps> = ({
  notifications,
  onMarkAsRead,
  onRemove,
  onClearAll,
  maxVisible = 5,
  position = 'top-right'
}) => {
  const theme = useMantineTheme();
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

  const getPriorityBadge = (priority: string) => {
    const priorityStyles = {
      low: { color: theme.colors.gray[5], label: 'Low' },
      medium: { color: theme.colors.yellow[6], label: 'Medium' },
      high: { color: theme.colors.red[6], label: 'High' }
    };

    const style = priorityStyles[priority as keyof typeof priorityStyles];
    return (
      <Badge
        size="sm"
        variant="outline"
        style={{
          color: style.color,
          borderColor: style.color,
          backgroundColor: theme.fn.rgba(style.color, 0.1)
        }}
      >
        {style.label}
      </Badge>
    );
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <Box
      style={{
        position: 'fixed',
        [position.includes('left') ? 'left' : 'right']: 20,
        [position.includes('top') ? 'top' : 'bottom']: 20,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: rem(12),
        maxWidth: 400,
        width: '100%'
      }}
    >
      {visibleNotifications.map((notification, index) => (
        <NotificationCard
          key={notification.id}
          notification={notification}
          index={index}
          onRemove={onRemove}
          onClick={handleNotificationClick}
          priorityBadge={getPriorityBadge(notification.priority)}
        />
      ))}

      {notifications.length > maxVisible && (
        <Box ta="center" mt="xs">
          <Badge
            size="lg"
            variant="outline"
            style={{
              cursor: 'pointer',
              backgroundColor: theme.fn.rgba(theme.colors.blue[6], 0.1),
              color: theme.colors.blue[6],
              border: `1px solid ${theme.fn.rgba(theme.colors.blue[6], 0.3)}`
            }}
            onClick={onClearAll}
          >
            +{notifications.length - maxVisible} more notifications
          </Badge>
        </Box>
      )}
    </Box>
  );
};
