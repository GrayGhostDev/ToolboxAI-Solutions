import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Badge from '@mui/material/Badge';

import { styled, keyframes } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import StarIcon from '@mui/icons-material/Star';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { robloxColors } from '../..//robloxTheme';
import { motion, AnimatePresence } from 'framer-motion';
const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateX(-100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;
const glow = keyframes`
  0%, 100% { box-shadow: 0 0 20px ${alpha(robloxColors.gold, 0.5)}; }
  50% { box-shadow: 0 0 40px ${alpha(robloxColors.gold, 0.8)}; }
`;
const StyledCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(135deg, ${robloxColors.dark} 0%, ${alpha(robloxColors.darkGray, 0.95)} 100%)`,
  border: `2px solid ${alpha(robloxColors.primary, 0.3)}`,
  borderRadius: '20px',
  padding: theme.spacing(3),
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: `linear-gradient(90deg, ${robloxColors.primary}, ${robloxColors.secondary}, ${robloxColors.accent})`,
    animation: 'shimmer 3s linear infinite',
  },
}));
const LeaderItem = styled(Box)<{ rank: number }>(({ theme, rank }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(2),
  borderRadius: '12px',
  background: rank <= 3
    ? `linear-gradient(135deg, ${alpha(robloxColors.gold, rank === 1 ? 0.2 : rank === 2 ? 0.15 : 0.1)} 0%, ${alpha(robloxColors.dark, 0.9)} 100%)`
    : alpha(robloxColors.darkGray, 0.5),
  border: `1px solid ${rank <= 3 ? alpha(robloxColors.gold, 0.3) : alpha(robloxColors.gray, 0.2)}`,
  marginBottom: theme.spacing(1.5),
  position: 'relative',
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  animation: `${slideIn} 0.5s ease-out ${rank * 0.1}s both`,
  '&:hover': {
    transform: 'translateX(8px) scale(1.02)',
    background: rank <= 3
      ? `linear-gradient(135deg, ${alpha(robloxColors.gold, rank === 1 ? 0.3 : rank === 2 ? 0.25 : 0.2)} 0%, ${alpha(robloxColors.dark, 0.95)} 100%)`
      : alpha(robloxColors.darkGray, 0.7),
    boxShadow: `0 8px 24px ${alpha(rank <= 3 ? robloxColors.gold : robloxColors.primary, 0.3)}`,
  },
  ...(rank === 1 && {
    animation: `${slideIn} 0.5s ease-out 0.1s both, ${glow} 2s ease-in-out infinite`,
  }),
}));
const RankBadge = styled(Box)<{ rank: number }>(({ rank }) => ({
  width: 40,
  height: 40,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: rank === 1
    ? `linear-gradient(135deg, ${robloxColors.gold} 0%, ${robloxColors.yellow} 100%)`
    : rank === 2
    ? `linear-gradient(135deg, #C0C0C0 0%, #B8B8B8 100%)`
    : rank === 3
    ? `linear-gradient(135deg, #CD7F32 0%, #B87333 100%)`
    : `linear-gradient(135deg, ${robloxColors.darkGray} 0%, ${robloxColors.gray} 100%)`,
  color: rank <= 3 ? '#fff' : robloxColors.lightGray,
  fontWeight: 800,
  fontSize: rank <= 3 ? '1.2rem' : '1rem',
  boxShadow: rank <= 3 ? `0 4px 12px ${alpha(robloxColors.gold, 0.3)}` : 'none',
  position: 'relative',
  ...(rank <= 3 && {
    '&::after': {
      content: '""',
      position: 'absolute',
      top: '-2px',
      left: '-2px',
      right: '-2px',
      bottom: '-2px',
      borderRadius: '50%',
      background: `linear-gradient(135deg, ${robloxColors.gold} 0%, transparent 100%)`,
      zIndex: -1,
      opacity: 0.5,
    },
  }),
}));
const XPBar = styled(LinearProgress)(({ theme }) => ({
  height: 8,
  borderRadius: 4,
  backgroundColor: alpha(robloxColors.gray, 0.2),
  '& .MuiLinearProgress-bar': {
    borderRadius: 4,
    background: `linear-gradient(90deg, ${robloxColors.primary} 0%, ${robloxColors.secondary} 100%)`,
  },
}));
const StreakBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: robloxColors.error,
    color: '#fff',
    fontWeight: 700,
    minWidth: 24,
    height: 24,
    borderRadius: 12,
    fontSize: '0.75rem',
    animation: 'pulse 2s infinite',
  },
}));
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
  const [displayPlayers, setDisplayPlayers] = useState<LeaderboardPlayer[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  useEffect(() => {
    // Sort players by XP and limit display
    const sorted = [...players]
      .sort((a, b) => b.xp - a.xp)
      .slice(0, showTopOnly);
    setDisplayPlayers(sorted);
  }, [players, showTopOnly]);
  const getTrophyIcon = (rank: number) => {
    if (rank === 1) return <EmojiEventsIcon sx={{ color: robloxColors.gold }} />;
    if (rank === 2) return <EmojiEventsIcon sx={{ color: '#C0C0C0' }} />;
    if (rank === 3) return <EmojiEventsIcon sx={{ color: '#CD7F32' }} />;
    return null;
  };
  const handlePlayerClick = (player: LeaderboardPlayer) => {
    setSelectedPlayer(player.id);
    onPlayerClick?.(player);
  };
  return (
    <StyledCard>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 800,
            background: `linear-gradient(135deg, #fff 0%, ${robloxColors.accent} 100%)`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <EmojiEventsIcon sx={{ color: robloxColors.gold, fontSize: 32 }} />
          {title}
        </Typography>
        <Chip
          label="Live"
          size="small"
          sx={{
            backgroundColor: robloxColors.success,
            color: '#fff',
            fontWeight: 700,
            animation: 'pulse 2s infinite',
          }}
        />
      </Box>
      <AnimatePresence>
        {displayPlayers.map((player, index) => {
          const rank = index + 1;
          const xpProgress = (player.xp % 1000) / 10; // XP progress to next level
          return (
            <motion.div
              key={player.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              transition={{ delay: index * 0.05 }}
            >
              <LeaderItem
                rank={rank}
                onClick={(e: React.MouseEvent) => () => handlePlayerClick(player)}
                sx={{
                  border: selectedPlayer === player.id
                    ? `2px solid ${robloxColors.primary}`
                    : undefined,
                }}
              >
                <RankBadge rank={rank}>
                  {rank <= 3 ? getTrophyIcon(rank) : rank}
                </RankBadge>
                <Box sx={{ ml: 2, position: 'relative' }}>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                    sx={{
                      '& .MuiBadge-dot': {
                        backgroundColor: player.isOnline ? robloxColors.success : robloxColors.gray,
                        width: 12,
                        height: 12,
                        border: `2px solid ${robloxColors.dark}`,
                      },
                    }}
                  >
                    <Avatar
                      src={player.avatar}
                      sx={{
                        width: 48,
                        height: 48,
                        border: `2px solid ${rank <= 3 ? robloxColors.gold : robloxColors.gray}`,
                      }}
                    >
                      {player.name[0]}
                    </Avatar>
                  </Badge>
                </Box>
                <Box sx={{ flex: 1, ml: 2 }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                      variant="h6"
                      sx={{
                        color: '#fff',
                        fontWeight: 700,
                        fontSize: '1rem',
                      }}
                    >
                      {player.name}
                    </Typography>
                    {player.streak > 0 && (
                      <StreakBadge badgeContent={player.streak}>
                        <LocalFireDepartmentIcon
                          sx={{ color: robloxColors.error, fontSize: 20 }}
                        />
                      </StreakBadge>
                    )}
                  </Box>
                  <Box display="flex" alignItems="center" gap={2} mt={0.5}>
                    <Typography
                      variant="caption"
                      sx={{ color: robloxColors.lightGray }}
                    >
                      Level {player.level}
                    </Typography>
                    <Box sx={{ flex: 1, maxWidth: 100 }}>
                      <XPBar variant="determinate" value={xpProgress} />
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{ color: robloxColors.accent, fontWeight: 600 }}
                    >
                      {player.xp.toLocaleString()} XP
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {player.badges > 0 && (
                    <Chip
                      icon={<StarIcon />}
                      label={player.badges}
                      size="small"
                      sx={{
                        backgroundColor: alpha(robloxColors.gold, 0.2),
                        color: robloxColors.gold,
                        fontWeight: 700,
                      }}
                    />
                  )}
                  {player.change !== 'same' && (
                    <Tooltip
                      title={`${player.change === 'up' ? '+' : '-'}${player.changeValue || 0} positions`}
                    >
                      <TrendingUpIcon
                        sx={{
                          color: player.change === 'up' ? robloxColors.success : robloxColors.error,
                          transform: player.change === 'down' ? 'rotate(180deg)' : 'none',
                          fontSize: 20,
                        }}
                      />
                    </Tooltip>
                  )}
                </Box>
              </LeaderItem>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </StyledCard>
  );
};
export default AnimatedLeaderboard;