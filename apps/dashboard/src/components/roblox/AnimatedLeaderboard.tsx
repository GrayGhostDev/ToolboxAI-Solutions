import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  Avatar,
  Badge,
  Progress,
  ActionIcon,
  Tooltip,
  Group,
  useMantineTheme,
  rem
} from '@mantine/core';
import {
  IconTrophy,
  IconStar,
  IconFlame,
  IconTrendingUp
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';

// Roblox color constants
const robloxColors = {
  primary: '#00A2FF',
  secondary: '#7C3AED',
  accent: '#F59E0B',
  dark: '#1F2937',
  darkGray: '#374151',
  gray: '#6B7280',
  lightGray: '#D1D5DB',
  success: '#10B981',
  error: '#EF4444',
  gold: '#F59E0B'
};

// Keyframe animations defined as CSS strings
const animations = `
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes glow {
    0%, 100% {
      box-shadow: 0 0 20px ${robloxColors.gold}77;
    }
    50% {
      box-shadow: 0 0 40px ${robloxColors.gold}CC;
    }
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.05);
      opacity: 0.9;
    }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'animated-leaderboard-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = animations;
    document.head.appendChild(style);
  }
}

const RankBadge: React.FC<{ rank: number }> = ({ rank }) => {
  const theme = useMantineTheme();

  const getBadgeStyle = (rank: number): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      width: 40,
      height: 40,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 800,
      fontSize: rem(20),
      position: 'relative'
    };

    if (rank === 1) {
      return {
        ...baseStyle,
        background: 'linear-gradient(135deg, #F59E0B 0%, #FFD700 100%)',
        color: '#fff',
        boxShadow: `0 4px 12px rgba(${parseInt(robloxColors.gold.slice(1,3), 16)}, ${parseInt(robloxColors.gold.slice(3,5), 16)}, ${parseInt(robloxColors.gold.slice(5,7), 16)}, 0.3)`
      };
    } else if (rank === 2) {
      return {
        ...baseStyle,
        background: 'linear-gradient(135deg, #C0C0C0 0%, #B8B8B8 100%)',
        color: '#fff',
        boxShadow: '0 4px 12px rgba(192, 192, 192, 0.3)'
      };
    } else if (rank === 3) {
      return {
        ...baseStyle,
        background: 'linear-gradient(135deg, #CD7F32 0%, #B87333 100%)',
        color: '#fff',
        boxShadow: '0 4px 12px rgba(205, 127, 50, 0.3)'
      };
    } else {
      return {
        ...baseStyle,
        background: `linear-gradient(135deg, ${robloxColors.darkGray} 0%, ${robloxColors.gray} 100%)`,
        color: robloxColors.lightGray
      };
    }
  };

  const getTrophyIcon = (rank: number) => {
    if (rank === 1) return <IconTrophy size={20} color={robloxColors.gold} />;
    if (rank === 2) return <IconTrophy size={20} color="#C0C0C0" />;
    if (rank === 3) return <IconTrophy size={20} color="#CD7F32" />;
    return rank;
  };

  return (
    <Box style={getBadgeStyle(rank)}>
      {getTrophyIcon(rank)}
    </Box>
  );
};

const XPBar: React.FC<{ value: number }> = ({ value }) => {
  const theme = useMantineTheme();

  return (
    <Progress
      value={value}
      size="sm"
      radius="md"
      style={{
        backgroundColor: `rgba(${parseInt(robloxColors.gray.slice(1,3), 16)}, ${parseInt(robloxColors.gray.slice(3,5), 16)}, ${parseInt(robloxColors.gray.slice(5,7), 16)}, 0.2)`
      }}
      styles={{
        bar: {
          background: `linear-gradient(90deg, ${robloxColors.primary} 0%, ${robloxColors.secondary} 100%)`
        }
      }}
    />
  );
};

const StreakBadge: React.FC<{ streak: number }> = ({ streak }) => {
  return (
    <Badge
      size="sm"
      style={{
        backgroundColor: robloxColors.error,
        color: '#fff',
        fontWeight: 700,
        animation: 'pulse 2s infinite'
      }}
    >
      {streak}
    </Badge>
  );
};

interface LeaderboardPlayer {
  id: string;
  name: string;
  avatar?: string;
  xp: number;
  level: number;
  streak: number;
  badges: number;
  change: 'up' | 'down' | 'same';
  changeValue?: number;
  isOnline?: boolean;
}

interface AnimatedLeaderboardProps {
  players: LeaderboardPlayer[];
  title?: string;
  showTopOnly?: number;
  onPlayerClick?: (player: LeaderboardPlayer) => void;
}

export const AnimatedLeaderboard: React.FunctionComponent<AnimatedLeaderboardProps> = ({
  players,
  title = 'Leaderboard',
  showTopOnly = 10,
  onPlayerClick,
}) => {
  const theme = useMantineTheme();
  const [displayPlayers, setDisplayPlayers] = useState<LeaderboardPlayer[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);

  useEffect(() => {
    // Sort players by XP and limit display
    const sorted = [...players]
      .sort((a, b) => b.xp - a.xp)
      .slice(0, showTopOnly);
    setDisplayPlayers(sorted);
  }, [players, showTopOnly]);

  const handlePlayerClick = (player: LeaderboardPlayer) => {
    setSelectedPlayer(player.id);
    onPlayerClick?.(player);
  };

  const cardStyle: React.CSSProperties = {
    background: `linear-gradient(135deg, ${robloxColors.dark} 0%, rgba(${parseInt(robloxColors.darkGray.slice(1,3), 16)}, ${parseInt(robloxColors.darkGray.slice(3,5), 16)}, ${parseInt(robloxColors.darkGray.slice(5,7), 16)}, 0.95) 100%)`,
    border: `2px solid rgba(${parseInt(robloxColors.primary.slice(1,3), 16)}, ${parseInt(robloxColors.primary.slice(3,5), 16)}, ${parseInt(robloxColors.primary.slice(5,7), 16)}, 0.3)`,
    borderRadius: rem(20),
    padding: theme.spacing.lg,
    position: 'relative',
    overflow: 'hidden'
  };

  const topBorderStyle: React.CSSProperties = {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: rem(4),
    background: `linear-gradient(90deg, ${robloxColors.primary}, ${robloxColors.secondary}, ${robloxColors.accent})`,
    animation: 'shimmer 3s linear infinite'
  };

  const getLeaderItemStyle = (rank: number, isFirst: boolean, isSelected: boolean): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      display: 'flex',
      alignItems: 'center',
      padding: theme.spacing.md,
      borderRadius: rem(12),
      marginBottom: theme.spacing.sm,
      position: 'relative',
      transition: 'all 0.3s ease',
      cursor: 'pointer',
      animation: isFirst ? 'slideIn 0.5s ease-out 0.1s both, glow 2s ease-in-out infinite' : 'slideIn 0.5s ease-out'
    };

    const background = rank <= 3
      ? `linear-gradient(135deg, rgba(${parseInt(robloxColors.gold.slice(1,3), 16)}, ${parseInt(robloxColors.gold.slice(3,5), 16)}, ${parseInt(robloxColors.gold.slice(5,7), 16)}, ${rank === 1 ? 0.2 : rank === 2 ? 0.15 : 0.1}) 0%, rgba(${parseInt(robloxColors.dark.slice(1,3), 16)}, ${parseInt(robloxColors.dark.slice(3,5), 16)}, ${parseInt(robloxColors.dark.slice(5,7), 16)}, 0.9) 100%)`
      : `rgba(${parseInt(robloxColors.darkGray.slice(1,3), 16)}, ${parseInt(robloxColors.darkGray.slice(3,5), 16)}, ${parseInt(robloxColors.darkGray.slice(5,7), 16)}, 0.5)`;

    const defaultBorderColor = rank <= 3
      ? `rgba(${parseInt(robloxColors.gold.slice(1,3), 16)}, ${parseInt(robloxColors.gold.slice(3,5), 16)}, ${parseInt(robloxColors.gold.slice(5,7), 16)}, 0.3)`
      : `rgba(${parseInt(robloxColors.gray.slice(1,3), 16)}, ${parseInt(robloxColors.gray.slice(3,5), 16)}, ${parseInt(robloxColors.gray.slice(5,7), 16)}, 0.2)`;

    const borderColor = isSelected ? robloxColors.primary : defaultBorderColor;
    const borderWidth = isSelected ? 2 : 1;

    return {
      ...baseStyle,
      background,
      border: `${borderWidth}px solid ${borderColor}`
    };
  };

  return (
    <Card style={cardStyle}>
      {/* Top gradient border */}
      <Box style={topBorderStyle} />

      <Group justify="space-between" mb="lg">
        <Text
          size="xl"
          fw={800}
          style={{
            background: `linear-gradient(135deg, #fff 0%, ${robloxColors.accent} 100%)`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}
        >
          <Group spacing="xs">
            <IconTrophy size={32} color={robloxColors.gold} />
            {title}
          </Group>
        </Text>
        <Badge
          size="sm"
          style={{
            backgroundColor: robloxColors.success,
            color: '#fff',
            fontWeight: 700,
            animation: 'pulse 2s infinite'
          }}
        >
          Live
        </Badge>
      </Group>

      <AnimatePresence>
        {displayPlayers.map((player, index) => {
          const rank = index + 1;
          const xpProgress = (player.xp % 1000) / 10; // XP progress to next level
          const isSelected = selectedPlayer === player.id;
          const isFirst = rank === 1;

          return (
            <motion.div
              key={player.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              transition={{ delay: index * 0.05 }}
            >
              <Box
                style={getLeaderItemStyle(rank, isFirst, isSelected)}
                onClick={() => handlePlayerClick(player)}
              >
                <RankBadge rank={rank} />

                <Box ml="md" style={{ position: 'relative' }}>
                  <Badge
                    variant="dot"
                    style={{
                      backgroundColor: player.isOnline ? robloxColors.success : robloxColors.gray,
                      width: 12,
                      height: 12,
                      border: `2px solid ${robloxColors.dark}`
                    }}
                  >
                    <Avatar
                      src={player.avatar}
                      size="md"
                      style={{
                        border: `2px solid ${rank <= 3 ? robloxColors.gold : robloxColors.gray}`
                      }}
                    >
                      {player.name[0]}
                    </Avatar>
                  </Badge>
                </Box>

                <Box style={{ flex: 1, marginLeft: rem(16) }}>
                  <Group spacing="xs" mb="xs">
                    <Text
                      size="lg"
                      fw={700}
                      c="white"
                    >
                      {player.name}
                    </Text>
                    {player.streak > 0 && (
                      <Group spacing="xs">
                        <IconFlame size={20} color={robloxColors.error} />
                        <StreakBadge streak={player.streak} />
                      </Group>
                    )}
                  </Group>
                  <Group spacing="md" mt="xs">
                    <Text
                      size="xs"
                      c={robloxColors.lightGray}
                    >
                      Level {player.level}
                    </Text>
                    <Box style={{ flex: 1, maxWidth: 100 }}>
                      <XPBar value={xpProgress} />
                    </Box>
                    <Text
                      size="xs"
                      fw={600}
                      style={{ color: robloxColors.accent }}
                    >
                      {player.xp.toLocaleString()} XP
                    </Text>
                  </Group>
                </Box>

                <Group spacing="xs">
                  {player.badges > 0 && (
                    <Badge
                      leftSection={<IconStar size={14} />}
                      size="sm"
                      style={{
                        backgroundColor: `rgba(${parseInt(robloxColors.gold.slice(1,3), 16)}, ${parseInt(robloxColors.gold.slice(3,5), 16)}, ${parseInt(robloxColors.gold.slice(5,7), 16)}, 0.2)`,
                        color: robloxColors.gold,
                        fontWeight: 700
                      }}
                    >
                      {player.badges}
                    </Badge>
                  )}
                  {player.change !== 'same' && (
                    <Tooltip
                      label={`${player.change === 'up' ? '+' : '-'}${player.changeValue || 0} positions`}
                    >
                      <ActionIcon
                        variant="subtle"
                        size="sm"
                        style={{
                          color: player.change === 'up' ? robloxColors.success : robloxColors.error,
                          transform: player.change === 'down' ? 'rotate(180deg)' : 'none'
                        }}
                      >
                        <IconTrendingUp size={20} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Group>
              </Box>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </Card>
  );
};

export default AnimatedLeaderboard;
