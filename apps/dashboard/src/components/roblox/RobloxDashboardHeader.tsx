/**
 * Roblox Dashboard Header Component
 *
 * Futuristic header with character avatars, notifications, and navigation
 * designed for kids with engaging animations and effects
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  ActionIcon,
  Badge,
  Group,
  Avatar,
  Menu,
  Divider,
  Transition,
  useMantineTheme,
  rem
} from '@mantine/core';
import {
  IconBell,
  IconSettings,
  IconHelp,
  IconUser,
  IconRocket,
  IconStar,
  IconTrophy,
  IconSparkles,
  IconMenu2,
  IconX
} from '@tabler/icons-react';
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
  const theme = useMantineTheme();
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
    <Box
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        background: `linear-gradient(135deg, ${theme.fn.rgba(theme.colors.blue[6], 0.9)}, ${theme.fn.rgba(theme.colors.violet[6], 0.9)})`,
        backdropFilter: 'blur(20px)',
        borderBottom: `2px solid ${theme.fn.rgba(theme.colors.blue[6], 0.3)}`,
        boxShadow: `0 8px 32px ${theme.fn.rgba(theme.colors.blue[6], 0.3)}`,
        padding: rem(16),
        minHeight: 80
      }}
    >
      <Group justify="space-between" align="center" h={64}>
        {/* Left Section - Menu & Title */}
        <Group align="center" style={{ flex: 1 }}>
          <ActionIcon
            size="lg"
            variant="subtle"
            color="white"
            onClick={onMenuClick}
            style={{
              background: theme.fn.rgba('#fff', 0.1),
              transition: 'all 0.3s ease'
            }}
            styles={{
              root: {
                '&:hover': {
                  background: theme.fn.rgba('#fff', 0.2),
                  transform: 'scale(1.1)',
                }
              }
            }}
          >
            <IconMenu2 size={24} />
          </ActionIcon>

          <Box style={{ flex: 1 }}>
            <Transition
              mounted={isAnimating}
              transition="fade"
              duration={1000}
            >
              {(styles) => (
                <Text
                  size="xl"
                  fw={800}
                  style={{
                    ...styles,
                    background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    marginBottom: rem(4)
                  }}
                >
                  {title}
                </Text>
              )}
            </Transition>

            <Transition
              mounted={isAnimating}
              transition="slide-up"
              duration={1500}
            >
              {(styles) => (
                <Text
                  size="lg"
                  style={{
                    ...styles,
                    color: theme.fn.rgba('#fff', 0.9),
                    fontWeight: 500
                  }}
                >
                  {subtitle}
                </Text>
              )}
            </Transition>
          </Box>
        </Group>

        {/* Center Section - Character Avatars */}
        <Box style={{ display: 'flex', alignItems: 'center', margin: `0 ${rem(32)}` }}>
          <Group spacing="md" align="center">
            {SAMPLE_CHARACTERS.map((character, index) => (
              <Transition
                key={character.name}
                mounted={isAnimating}
                transition="pop"
                duration={2000 + index * 200}
              >
                {(styles) => (
                  <Box style={styles}>
                    <RobloxCharacterAvatar
                      character={character}
                      size="medium"
                      animated={true}
                      onClick={() => console.log(`Selected ${character.name}`)}
                    />
                  </Box>
                )}
              </Transition>
            ))}
          </Group>
        </Box>

        {/* Right Section - Actions */}
        <Group spacing="xs" align="center">
          {/* Notifications */}
          <Menu
            shadow="md"
            width={300}
            position="bottom-end"
            opened={Boolean(notificationMenuAnchor)}
            onChange={(opened) => !opened && setNotificationMenuAnchor(null)}
          >
            <Menu.Target>
              <ActionIcon
                size="lg"
                variant="subtle"
                color="white"
                onClick={(e) => setNotificationMenuAnchor(e.currentTarget)}
                style={{
                  background: theme.fn.rgba('#fff', 0.1),
                  transition: 'all 0.3s ease'
                }}
                styles={{
                  root: {
                    '&:hover': {
                      background: theme.fn.rgba('#fff', 0.2),
                      transform: 'scale(1.1)',
                    }
                  }
                }}
              >
                <Badge count={unreadCount} color="red" size="sm">
                  <IconBell size={20} />
                </Badge>
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown
              style={{
                background: `linear-gradient(145deg, ${theme.colors.dark[6]}, ${theme.fn.rgba(theme.colors.blue[6], 0.05)})`,
                border: `1px solid ${theme.fn.rgba(theme.colors.blue[6], 0.2)}`,
                backdropFilter: 'blur(20px)',
                maxHeight: 400,
                overflow: 'auto'
              }}
            >
              <Box p="md" style={{ borderBottom: `1px solid ${theme.fn.rgba(theme.colors.gray[6], 0.1)}` }}>
                <Text size="lg" fw={600} c={theme.colors.blue[6]}>
                  Notifications
                </Text>
              </Box>

              {notifications.map((notification) => (
                <Menu.Item
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  style={{
                    padding: rem(16),
                    borderBottom: `1px solid ${theme.fn.rgba(theme.colors.gray[6], 0.1)}`,
                    background: notification.isRead ? 'transparent' : theme.fn.rgba(theme.colors.blue[6], 0.05),
                  }}
                >
                  <Box>
                    <Group spacing="xs" mb="xs">
                      <Text size="sm" fw={600}>
                        {notification.title}
                      </Text>
                      {!notification.isRead && (
                        <Box
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: theme.colors.blue[6]
                          }}
                        />
                      )}
                    </Group>
                    <Text size="sm" c="dimmed">
                      {notification.message}
                    </Text>
                    <Text size="xs" c="dimmed" mt="xs">
                      {notification.timestamp.toLocaleTimeString()}
                    </Text>
                  </Box>
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>

          {/* Settings */}
          <ActionIcon
            size="lg"
            variant="subtle"
            color="white"
            onClick={onSettingsClick}
            style={{
              background: theme.fn.rgba('#fff', 0.1),
              transition: 'all 0.3s ease'
            }}
            styles={{
              root: {
                '&:hover': {
                  background: theme.fn.rgba('#fff', 0.2),
                  transform: 'scale(1.1)',
                }
              }
            }}
          >
            <IconSettings size={20} />
          </ActionIcon>

          {/* Help */}
          <ActionIcon
            size="lg"
            variant="subtle"
            color="white"
            onClick={onHelpClick}
            style={{
              background: theme.fn.rgba('#fff', 0.1),
              transition: 'all 0.3s ease'
            }}
            styles={{
              root: {
                '&:hover': {
                  background: theme.fn.rgba('#fff', 0.2),
                  transform: 'scale(1.1)',
                }
              }
            }}
          >
            <IconHelp size={20} />
          </ActionIcon>

          {/* Profile */}
          <Menu
            shadow="md"
            width={200}
            position="bottom-end"
            opened={Boolean(profileMenuAnchor)}
            onChange={(opened) => !opened && setProfileMenuAnchor(null)}
          >
            <Menu.Target>
              <ActionIcon
                size="lg"
                variant="subtle"
                color="white"
                onClick={(e) => setProfileMenuAnchor(e.currentTarget)}
                style={{
                  background: theme.fn.rgba('#fff', 0.1),
                  transition: 'all 0.3s ease'
                }}
                styles={{
                  root: {
                    '&:hover': {
                      background: theme.fn.rgba('#fff', 0.2),
                      transform: 'scale(1.1)',
                    }
                  }
                }}
              >
                <IconUser size={20} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown
              style={{
                background: `linear-gradient(145deg, ${theme.colors.dark[6]}, ${theme.fn.rgba(theme.colors.blue[6], 0.05)})`,
                border: `1px solid ${theme.fn.rgba(theme.colors.blue[6], 0.2)}`,
                backdropFilter: 'blur(20px)'
              }}
            >
              <Menu.Item
                leftSection={<IconUser size={16} />}
                onClick={handleProfileClick}
              >
                Profile
              </Menu.Item>
              <Menu.Item
                leftSection={<IconSettings size={16} />}
                onClick={onSettingsClick}
              >
                Settings
              </Menu.Item>
              <Divider />
              <Menu.Item
                leftSection={<IconHelp size={16} />}
                onClick={onHelpClick}
              >
                Help & Support
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>

    </Box>
  );
};

export default RobloxDashboardHeader;
