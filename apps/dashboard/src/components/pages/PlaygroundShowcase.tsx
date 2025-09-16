import React, { useState } from 'react';
import { Box, Container, Typography, Grid, Card, Button, Fab } from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import { motion } from 'framer-motion';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import SchoolIcon from '@mui/icons-material/School';
import SportsEsportsIcon from '@mui/icons-material/SportsEsports';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import StarIcon from '@mui/icons-material/Star';

// Import our new playful components
import { Roblox3DMetricCard } from '../roblox/Roblox3DMetricCard';
import { AnimatedLeaderboard } from '../roblox/AnimatedLeaderboard';
import { FloatingIslandNav } from '../roblox/FloatingIslandNav';
import { robloxColors } from '../../theme/robloxTheme';

// Animations
const rainbow = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
`;

const bounce = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
`;

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
`;

// Styled components
const RainbowBackground = styled(Box)({
  background: robloxColors.effects.rainbowGradient,
  backgroundSize: '400% 400%',
  animation: `${rainbow} 10s ease infinite`,
  minHeight: '100vh',
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.3) 0%, transparent 50%)',
    pointerEvents: 'none',
  },
});

const FloatingEmoji = styled(Box)<{ delay: number; left: string }>(({ delay, left }) => ({
  position: 'absolute',
  left,
  bottom: '-50px',
  fontSize: '3rem',
  animation: `${float} 15s linear ${delay}s infinite`,
  zIndex: 1,
  pointerEvents: 'none',
}));

const GlowingTitle = styled(Typography)({
  fontWeight: 900,
  fontSize: '4rem',
  textAlign: 'center',
  background: robloxColors.effects.electricGradient,
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  textShadow: `0 0 40px ${robloxColors.neon.electricBlue}`,
  animation: `${pulse} 2s ease-in-out infinite`,
  marginBottom: '2rem',
});

const FloatingCard = styled(Card)<{ delay?: number }>(({ delay = 0 }) => ({
  background: `linear-gradient(135deg, ${robloxColors.dark.background} 0%, ${robloxColors.dark.surface} 100%)`,
  border: `2px solid ${robloxColors.neon.electricBlue}`,
  borderRadius: '24px',
  padding: '24px',
  animation: `${bounce} 3s ease-in-out ${delay}s infinite`,
  boxShadow: `0 10px 40px ${robloxColors.neon.electricBlue}40`,
  '&:hover': {
    transform: 'scale(1.05)',
    boxShadow: `0 20px 60px ${robloxColors.neon.hotPink}60`,
  },
}));

const PlaygroundShowcase: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<number | null>(null);

  // Sample data for components
  const leaderboardPlayers = [
    { id: '1', name: 'CoolKid123', xp: 15420, level: 42, streak: 7, badges: 12, change: 'up' as const, changeValue: 2, isOnline: true },
    { id: '2', name: 'ProGamer456', xp: 14200, level: 40, streak: 5, badges: 10, change: 'up' as const, changeValue: 1, isOnline: true },
    { id: '3', name: 'StudyMaster', xp: 13800, level: 38, streak: 12, badges: 15, change: 'down' as const, changeValue: 1, isOnline: false },
    { id: '4', name: 'QuizChampion', xp: 12500, level: 35, streak: 3, badges: 8, change: 'same' as const, isOnline: true },
    { id: '5', name: 'MathWizard', xp: 11200, level: 32, streak: 9, badges: 11, change: 'up' as const, changeValue: 3, isOnline: false },
    { id: '6', name: 'ScienceGeek', xp: 10800, level: 30, streak: 6, badges: 7, change: 'down' as const, changeValue: 2, isOnline: true },
    { id: '7', name: 'BookWorm99', xp: 9500, level: 28, streak: 15, badges: 9, change: 'up' as const, changeValue: 1, isOnline: true },
  ];

  const metrics = [
    {
      title: 'Total XP Earned',
      value: 15420,
      icon: <StarIcon />,
      trend: { value: 23, direction: 'up' as const },
      color: robloxColors.neon.plasmaYellow,
      subtitle: 'Keep going! 580 XP to next level',
      format: 'number' as const,
    },
    {
      title: 'Lessons Completed',
      value: 142,
      icon: <SchoolIcon />,
      trend: { value: 15, direction: 'up' as const },
      color: robloxColors.neon.toxicGreen,
      subtitle: '28 more than last month!',
      format: 'number' as const,
    },
    {
      title: 'Win Rate',
      value: 87,
      icon: <EmojiEventsIcon />,
      trend: { value: 5, direction: 'up' as const },
      color: robloxColors.neon.hotPink,
      subtitle: 'Top 5% of all players!',
      format: 'percentage' as const,
    },
    {
      title: 'Study Time',
      value: 42,
      icon: <SportsEsportsIcon />,
      trend: { value: -3, direction: 'down' as const },
      color: robloxColors.neon.electricBlue,
      subtitle: 'This week',
      format: 'time' as const,
    },
  ];

  return (
    <RainbowBackground>
      {/* Floating emojis in background */}
      <FloatingEmoji delay={0} left="10%">🚀</FloatingEmoji>
      <FloatingEmoji delay={2} left="25%">⭐</FloatingEmoji>
      <FloatingEmoji delay={4} left="40%">🎮</FloatingEmoji>
      <FloatingEmoji delay={6} left="55%">🏆</FloatingEmoji>
      <FloatingEmoji delay={8} left="70%">💎</FloatingEmoji>
      <FloatingEmoji delay={10} left="85%">🌟</FloatingEmoji>

      <Container maxWidth="xl" sx={{ py: 4, position: 'relative', zIndex: 2 }}>
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <GlowingTitle variant="h1">
            🎮 EPIC GAMING DASHBOARD 🚀
          </GlowingTitle>

          <Typography
            variant="h4"
            sx={{
              textAlign: 'center',
              color: robloxColors.white,
              mb: 6,
              fontWeight: 600,
              textShadow: `2px 2px 4px rgba(0,0,0,0.5)`,
            }}
          >
            Where Learning Meets Gaming!
          </Typography>
        </motion.div>

        {/* Floating Island Navigation */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <FloatingCard delay={0}>
            <Typography
              variant="h5"
              sx={{
                color: robloxColors.neon.electricBlue,
                mb: 3,
                fontWeight: 700,
                textAlign: 'center',
              }}
            >
              🏝️ Choose Your Adventure Island! 🏝️
            </Typography>
            <FloatingIslandNav />
          </FloatingCard>
        </motion.div>

        {/* 3D Metric Cards */}
        <Box sx={{ mt: 4 }}>
          <Typography
            variant="h4"
            sx={{
              color: robloxColors.white,
              mb: 3,
              fontWeight: 700,
              textAlign: 'center',
              textShadow: `0 0 20px ${robloxColors.neon.hotPink}`,
            }}
          >
            ⚡ Your Epic Stats ⚡
          </Typography>

          <Grid container spacing={3}>
            {metrics.map((metric, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <motion.div
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Roblox3DMetricCard
                    {...metric}
                    onClick={() => setSelectedMetric(index)}
                    tooltip={`Click for more details about ${metric.title}`}
                  />
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Animated Leaderboard */}
        <Box sx={{ mt: 6 }}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <AnimatedLeaderboard
                  players={leaderboardPlayers}
                  title="🏆 ULTIMATE CHAMPIONS 🏆"
                  onPlayerClick={(player) => console.log('Clicked player:', player)}
                />
              </motion.div>
            </Grid>

            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
              >
                <FloatingCard delay={0.2}>
                  <Typography
                    variant="h5"
                    sx={{
                      color: robloxColors.neon.toxicGreen,
                      mb: 3,
                      fontWeight: 700,
                      textAlign: 'center',
                    }}
                  >
                    🎯 Daily Challenges 🎯
                  </Typography>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {['Complete 5 Math Problems', 'Win 3 Quiz Battles', 'Study for 30 Minutes', 'Help a Friend'].map((challenge, index) => (
                      <Button
                        key={index}
                        variant="contained"
                        fullWidth
                        sx={{
                          background: robloxColors.effects.electricGradient,
                          py: 2,
                          fontSize: '1.1rem',
                          fontWeight: 700,
                          borderRadius: '16px',
                          animation: `${pulse} ${2 + index * 0.2}s ease-in-out infinite`,
                          '&:hover': {
                            transform: 'scale(1.05)',
                            boxShadow: `0 10px 30px ${robloxColors.neon.hotPink}60`,
                          },
                        }}
                      >
                        {challenge}
                      </Button>
                    ))}
                  </Box>
                </FloatingCard>
              </motion.div>
            </Grid>
          </Grid>
        </Box>

        {/* Floating Action Buttons */}
        <Box
          sx={{
            position: 'fixed',
            bottom: 32,
            right: 32,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          <Fab
            color="primary"
            sx={{
              background: robloxColors.effects.fireGradient,
              animation: `${spin} 3s linear infinite`,
              '&:hover': {
                animation: 'none',
                transform: 'scale(1.2)',
              },
            }}
          >
            <RocketLaunchIcon />
          </Fab>
          <Fab
            sx={{
              background: robloxColors.effects.cosmicGradient,
              animation: `${bounce} 2s ease-in-out infinite`,
            }}
          >
            <AutoAwesomeIcon />
          </Fab>
        </Box>
      </Container>
    </RainbowBackground>
  );
};

export default PlaygroundShowcase;