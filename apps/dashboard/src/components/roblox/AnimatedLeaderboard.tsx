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
  keyframes,
  rem
} from '@mantine/core';
// import { createStyles } from '@mantine/emotion'; // Removed - using inline styles instead
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

const slideIn = keyframes({
  'from': {
    opacity: 0,
    transform: 'translateX(-100%)'
  },
  'to': {
    opacity: 1,
    transform: 'translateX(0)'
  }
});

const glow = keyframes({
  '0%, 100%': { boxShadow: `0 0 20px ${robloxColors.gold}77` },
  '50%': { boxShadow: `0 0 40px ${robloxColors.gold}CC` }
});

const useStyles = createStyles((theme) => ({
  card: {
    background: `linear-gradient(135deg, ${robloxColors.dark} 0%, ${theme.fn.rgba(robloxColors.darkGray, 0.95)} 100%)`,
    border: `2px solid ${theme.fn.rgba(robloxColors.primary, 0.3)}`,
    borderRadius: rem(20),
    padding: theme.spacing.lg,
    position: 'relative',
    overflow: 'hidden',

    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: rem(4),
      background: `linear-gradient(90deg, ${robloxColors.primary}, ${robloxColors.secondary}, ${robloxColors.accent})`,
      animation: 'shimmer 3s linear infinite'
    }
  },
  leaderItem: {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing.md,
    borderRadius: rem(12),
    marginBottom: theme.spacing.sm,
    position: 'relative',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    animation: `${slideIn} 0.5s ease-out`,

    '&:hover': {
      transform: 'translateX(8px) scale(1.02)',
      boxShadow: `0 8px 24px ${theme.fn.rgba(robloxColors.primary, 0.3)}`
    }
  },
  leaderItemTop3: {
    background: (rank: number) => rank <= 3
      ? `linear-gradient(135deg, ${theme.fn.rgba(robloxColors.gold, rank === 1 ? 0.2 : rank === 2 ? 0.15 : 0.1)} 0%, ${theme.fn.rgba(robloxColors.dark, 0.9)} 100%)`
      : theme.fn.rgba(robloxColors.darkGray, 0.5),
    border: (rank: number) => `1px solid ${rank <= 3 ? theme.fn.rgba(robloxColors.gold, 0.3) : theme.fn.rgba(robloxColors.gray, 0.2)}`,

    '&:hover': {
      background: (rank: number) => rank <= 3
        ? `linear-gradient(135deg, ${theme.fn.rgba(robloxColors.gold, rank === 1 ? 0.3 : rank === 2 ? 0.25 : 0.2)} 0%, ${theme.fn.rgba(robloxColors.dark, 0.95)} 100%)`
        : theme.fn.rgba(robloxColors.darkGray, 0.7)
    }
  },
  leaderItemFirst: {
    animation: `${slideIn} 0.5s ease-out 0.1s both, ${glow} 2s ease-in-out infinite`
  },
  rankBadge: {
    width: 40,
    height: 40,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 800,
    fontSize: rem(20),
    position: 'relative'
  }
}));

const RankBadge: React.FC<{ rank: number }> = ({ rank }) => {
  const theme = useMantineTheme();
  const { classes } = useStyles();

  const getBadgeStyle = (rank: number) => {
    if (rank === 1) {
      return {
        background: `linear-gradient(135deg, ${robloxColors.gold} 0%, #FFD700 100%)`,
        color: '#fff',
        boxShadow: `0 4px 12px ${theme.fn.rgba(robloxColors.gold, 0.3)}`
      };
    } else if (rank === 2) {
      return {
        background: 'linear-gradient(135deg, #C0C0C0 0%, #B8B8B8 100%)',
        color: '#fff',
        boxShadow: `0 4px 12px ${theme.fn.rgba('#C0C0C0', 0.3)}`
      };
    } else if (rank === 3) {
      return {
        background: 'linear-gradient(135deg, #CD7F32 0%, #B87333 100%)',
        color: '#fff',
        boxShadow: `0 4px 12px ${theme.fn.rgba('#CD7F32', 0.3)}`
      };
    } else {
      return {
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
    <Box
      className={classes.rankBadge}
      style={getBadgeStyle(rank)}
    >
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
        backgroundColor: theme.fn.rgba(robloxColors.gray, 0.2)
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
  const theme = useMantineTheme();

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
  const { classes } = useStyles();
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

  return (
    <Card className={classes.card}>
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
          const defaultBorderColor = rank <= 3
            ? theme.fn.rgba(robloxColors.gold, 0.3)
            : theme.fn.rgba(robloxColors.gray, 0.2);
          const borderColor = isSelected ? robloxColors.primary : defaultBorderColor;
          const borderWidth = isSelected ? 2 : 1;

          return (
            <motion.div
              key={player.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              transition={{ delay: index * 0.05 }}
            >
              <Box
                className={`${classes.leaderItem} ${rank <= 3 ? classes.leaderItemTop3 : ''} ${rank === 1 ? classes.leaderItemFirst : ''}`}
                onClick={() => handlePlayerClick(player)}
                style={{
                  background: rank <= 3
                    ? `linear-gradient(135deg, ${theme.fn.rgba(robloxColors.gold, rank === 1 ? 0.2 : rank === 2 ? 0.15 : 0.1)} 0%, ${theme.fn.rgba(robloxColors.dark, 0.9)} 100%)`
                    : theme.fn.rgba(robloxColors.darkGray, 0.5),
                  border: `${borderWidth}px solid ${borderColor}`
                }}
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
                        backgroundColor: theme.fn.rgba(robloxColors.gold, 0.2),
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
