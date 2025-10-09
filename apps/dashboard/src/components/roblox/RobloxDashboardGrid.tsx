/**
 * Roblox Dashboard Grid Component
 *
 * Displays a grid of 3D icons and interactive elements
 * with futuristic animations and hover effects
 */

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  Text,
  Box,
  Group,
  Badge,
  Progress,
  ActionIcon,
  Tooltip,
  Transition,
  useMantineTheme,
  rem
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconRefresh,
  IconStar,
  IconTrophy,
  IconTrendingUp,
  IconSchool,
  IconDeviceGamepad,
  IconBrain,
  IconUsers,
  IconDeviceGamepad,
  IconSparkles
} from '@tabler/icons-react';
import { Roblox3DIcon } from './Roblox3DIcon';

interface DashboardItem {
  id: string;
  name: string;
  type: 'education' | 'gaming' | 'tool' | 'achievement';
  category: string;
  level: number;
  isUnlocked: boolean;
  progress: number;
  maxProgress: number;
  description: string;
  icon: string;
  isActive: boolean;
  lastUsed?: Date;
}

interface RobloxDashboardGridProps {
  items: DashboardItem[];
  onItemClick?: (item: DashboardItem) => void;
  onItemPlay?: (item: DashboardItem) => void;
  onItemPause?: (item: DashboardItem) => void;
  onItemRefresh?: (item: DashboardItem) => void;
}

const SAMPLE_ITEMS: DashboardItem[] = [
  {
    id: '1',
    name: 'ABC_CUBE',
    type: 'education',
    category: 'Language',
    level: 3,
    isUnlocked: true,
    progress: 75,
    maxProgress: 100,
    description: 'Learn the alphabet with interactive 3D cubes',
    icon: 'ABC_CUBE',
    isActive: true,
    lastUsed: new Date()
  },
  {
    id: '2',
    name: 'MATH_BOARD',
    type: 'education',
    category: 'Mathematics',
    level: 2,
    isUnlocked: true,
    progress: 45,
    maxProgress: 100,
    description: 'Solve math problems on the interactive board',
    icon: 'BOARD',
    isActive: false,
    lastUsed: new Date(Date.now() - 3600000)
  },
  {
    id: '3',
    name: 'SPACE_QUIZ',
    type: 'education',
    category: 'Science',
    level: 4,
    isUnlocked: true,
    progress: 90,
    maxProgress: 100,
    description: 'Test your knowledge about space and planets',
    icon: 'LIGHT_BULB',
    isActive: false,
    lastUsed: new Date(Date.now() - 7200000)
  },
  {
    id: '4',
    name: 'SPORTS_CHALLENGE',
    type: 'gaming',
    category: 'Physical Education',
    level: 1,
    isUnlocked: true,
    progress: 20,
    maxProgress: 100,
    description: 'Complete physical challenges and sports activities',
    icon: 'BASKETBALL',
    isActive: false,
    lastUsed: new Date(Date.now() - 86400000)
  },
  {
    id: '5',
    name: 'ART_STUDIO',
    type: 'tool',
    category: 'Creative Arts',
    level: 2,
    isUnlocked: true,
    progress: 60,
    maxProgress: 100,
    description: 'Create digital art with brushes and colors',
    icon: 'CRAYON',
    isActive: false,
    lastUsed: new Date(Date.now() - 172800000)
  },
  {
    id: '6',
    name: 'ACHIEVEMENT_HALL',
    type: 'achievement',
    category: 'Recognition',
    level: 5,
    isUnlocked: true,
    progress: 100,
    maxProgress: 100,
    description: 'View all your earned achievements and badges',
    icon: 'TROPHY',
    isActive: false,
    lastUsed: new Date(Date.now() - 259200000)
  }
];

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'education': return IconSchool;
    case 'gaming': return IconDeviceGamepad;
    case 'tool': return IconBrain;
    case 'achievement': return IconTrophy;
    default: return IconSparkles;
  }
};

const getTypeColor = (type: string, theme: any) => {
  switch (type) {
    case 'education': return theme.colors.blue[6];
    case 'gaming': return theme.colors.violet[6];
    case 'tool': return theme.colors.cyan[6];
    case 'achievement': return theme.colors.yellow[6];
    default: return theme.colors.gray[5];
  }
};

export const RobloxDashboardGrid: React.FunctionComponent<RobloxDashboardGridProps> = ({
  items = SAMPLE_ITEMS,
  onItemClick,
  onItemPlay,
  onItemPause,
  onItemRefresh
}) => {
  const theme = useMantineTheme();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleItemClick = (item: DashboardItem) => {
    if (onItemClick) {
      onItemClick(item);
    }
  };

  const handleItemPlay = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemPlay) {
      onItemPlay(item);
    }
  };

  const handleItemPause = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemPause) {
      onItemPause(item);
    }
  };

  const handleItemRefresh = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemRefresh) {
      onItemRefresh(item);
    }
  };

  return (
    <Box p="lg">
      <Transition
        mounted={isAnimating}
        transition="fade"
        duration={1000}
      >
        {(styles) => (
          <Text
            size="xl"
            fw={700}
            ta="center"
            mb="lg"
            style={{
              ...styles,
              background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            Your Learning Tools
          </Text>
        )}
      </Transition>

      <Grid>
        {items.map((item, index) => {
          const TypeIcon = getTypeIcon(item.type);
          const typeColor = getTypeColor(item.type, theme);
          const progressPercentage = (item.progress / item.maxProgress) * 100;

          return (
            <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 3 }} key={item.id}>
              <Transition
                mounted={isAnimating}
                transition="pop"
                duration={1000 + index * 200}
              >
                {(styles) => (
                  <Card
                    style={{
                      ...styles,
                      height: '100%',
                      background: `linear-gradient(145deg, ${theme.colors.dark[6]}, ${theme.fn.rgba(typeColor, 0.05)})`,
                      border: `2px solid ${theme.fn.rgba(typeColor, 0.2)}`,
                      borderRadius: rem(12),
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      cursor: item.isUnlocked ? 'pointer' : 'default',
                      transform: hoveredItem === item.id ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
                      boxShadow: hoveredItem === item.id
                        ? `0 20px 40px ${theme.fn.rgba(typeColor, 0.3)}`
                        : `0 8px 25px ${theme.fn.rgba(typeColor, 0.1)}`
                    }}
                    onMouseEnter={() => setHoveredItem(item.id)}
                    onMouseLeave={() => setHoveredItem(null)}
                    onClick={() => handleItemClick(item)}
                    p="lg"
                  >
                    {/* Header with icon and actions */}
                    <Group justify="space-between" align="flex-start" mb="md">
                      <Group align="center" spacing="md">
                        <Roblox3DIcon
                          icon={{
                            name: item.icon,
                            type: item.type,
                            category: item.category,
                            level: item.level,
                            isUnlocked: item.isUnlocked,
                            imagePath: '',
                            description: item.description
                          }}
                          size="large"
                          animated={true}
                        />
                        <Box>
                          <Text size="lg" fw={600} mb="xs">
                            {item.name.replace(/_/g, ' ')}
                          </Text>
                          <Badge
                            size="sm"
                            style={{
                              background: `linear-gradient(135deg, ${typeColor}, ${theme.fn.rgba(typeColor, 0.7)})`,
                              color: 'white'
                            }}
                          >
                            {item.category}
                          </Badge>
                        </Box>
                      </Group>

                      {/* Action buttons */}
                      <Group spacing="xs">
                        {item.isActive ? (
                          <Tooltip label="Pause">
                            <ActionIcon
                              size="sm"
                              onClick={(e) => handleItemPause(item, e)}
                              style={{
                                color: theme.colors.yellow[6],
                                background: theme.fn.rgba(theme.colors.yellow[6], 0.1)
                              }}
                              styles={{
                                root: {
                                  '&:hover': {
                                    background: theme.fn.rgba(theme.colors.yellow[6], 0.2)
                                  }
                                }
                              }}
                            >
                              <IconPlayerPause size={16} />
                            </ActionIcon>
                          </Tooltip>
                        ) : (
                          <Tooltip label="Play">
                            <ActionIcon
                              size="sm"
                              onClick={(e) => handleItemPlay(item, e)}
                              style={{
                                color: theme.colors.green[6],
                                background: theme.fn.rgba(theme.colors.green[6], 0.1)
                              }}
                              styles={{
                                root: {
                                  '&:hover': {
                                    background: theme.fn.rgba(theme.colors.green[6], 0.2)
                                  }
                                }
                              }}
                            >
                              <IconPlayerPlay size={16} />
                            </ActionIcon>
                          </Tooltip>
                        )}

                        <Tooltip label="Refresh">
                          <ActionIcon
                            size="sm"
                            onClick={(e) => handleItemRefresh(item, e)}
                            style={{
                              color: theme.colors.cyan[6],
                              background: theme.fn.rgba(theme.colors.cyan[6], 0.1)
                            }}
                            styles={{
                              root: {
                                '&:hover': {
                                  background: theme.fn.rgba(theme.colors.cyan[6], 0.2)
                                }
                              }
                            }}
                          >
                            <IconRefresh size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Group>

                    {/* Description */}
                    <Text
                      size="sm"
                      c="dimmed"
                      mb="md"
                      style={{ flex: 1 }}
                    >
                      {item.description}
                    </Text>

                    {/* Progress section */}
                    <Box mb="md">
                      <Group justify="space-between" align="center" mb="xs">
                        <Text size="sm" fw={600}>
                          Progress
                        </Text>
                        <Text size="sm" c="dimmed">
                          {item.progress}/{item.maxProgress}
                        </Text>
                      </Group>
                      <Progress
                        value={progressPercentage}
                        size="sm"
                        radius="md"
                        style={{
                          background: theme.fn.rgba(typeColor, 0.1)
                        }}
                        styles={{
                          bar: {
                            background: `linear-gradient(90deg, ${typeColor}, ${theme.fn.rgba(typeColor, 0.7)})`,
                            borderRadius: rem(4)
                          }
                        }}
                      />
                    </Box>

                    {/* Level and status */}
                    <Group justify="space-between" align="center">
                      <Group spacing="xs" align="center">
                        <TypeIcon size={16} color={typeColor} />
                        <Text size="sm" fw={600}>
                          Level {item.level}
                        </Text>
                      </Group>

                      {item.isActive && (
                        <Badge
                          size="sm"
                          style={{
                            background: `linear-gradient(135deg, ${theme.colors.green[6]}, ${theme.fn.rgba(theme.colors.green[6], 0.7)})`,
                            color: 'white',
                            animation: 'pulse 2s infinite'
                          }}
                        >
                          Active
                        </Badge>
                      )}
                    </Group>
                  </Card>
                )}
              </Transition>
            </Grid.Col>
          );
        })}
      </Grid>
    </Box>
  );
};

export default RobloxDashboardGrid;