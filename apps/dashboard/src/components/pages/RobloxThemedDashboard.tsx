/**
 * Roblox Themed Dashboard
 * 
 * Main dashboard component that combines all Roblox-themed elements
 * with futuristic design, character integration, and 3D icons
 */
import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Avatar from '@mui/material/Avatar';
import Badge from '@mui/material/Badge';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Fade from '@mui/material/Fade';
import Slide from '@mui/material/Slide';
import Zoom from '@mui/material/Zoom';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import {
  RocketLaunch,
  Star,
  EmojiEvents,
  TrendingUp,
  School,
  SportsEsports,
  Psychology,
  Groups,
  Games,
  AutoAwesome,
  PlayArrow,
  Pause,
  Refresh
} from '@mui/icons-material';
import { ThemeProvider } from '@mui/material/styles';
import { robloxTheme } from '../..//robloxTheme';
import RobloxDashboardHeader from '../roblox/RobloxDashboardHeader';
import RobloxDashboardGrid from '../roblox/RobloxDashboardGrid';
import RobloxCharacterAvatar from '../roblox/RobloxCharacterAvatar';
interface RobloxThemedDashboardProps {
  onNavigate?: (path: string) => void;
  onItemClick?: (item: any) => void;
}
export const RobloxThemedDashboard: React.FunctionComponent<RobloxThemedDashboardProps> = ({
  onNavigate,
  onItemClick
}) => {
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [activeItems, setActiveItems] = useState<Set<string>>(new Set());
  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 2000);
    return () => clearTimeout(timer);
  }, []);
  const handleItemPlay = (item: any) => {
    setActiveItems(prev => new Set([...prev, item.id]));
    console.log(`Playing ${item.name}`);
  };
  const handleItemPause = (item: any) => {
    setActiveItems(prev => {
      const newSet = new Set(prev);
      newSet.delete(item.id);
      return newSet;
    });
    console.log(`Paused ${item.name}`);
  };
  const handleItemRefresh = (item: any) => {
    console.log(`Refreshing ${item.name}`);
  };
  const handleItemClick = (item: any) => {
    if (onItemClick) {
      onItemClick(item);
    }
    console.log(`Clicked ${item.name}`);
  };
  if (isLoading) {
    return (
      <ThemeProvider theme={robloxTheme}>
        <Box
          sx={{
            minHeight: '100vh',
            background: `linear-gradient(135deg, ${robloxTheme.palette.background.default}, ${alpha(robloxTheme.palette.primary.main, 0.1)})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: 3
          }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${robloxTheme.palette.primary.main}, ${robloxTheme.palette.secondary.main})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'spin 2s linear infinite',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' }
              }
            }}
          >
            <RocketLaunch sx={{ fontSize: 40, color: 'white' }} />
          </Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: `linear-gradient(135deg, ${robloxTheme.palette.primary.main}, ${robloxTheme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Loading Space Station...
          </Typography>
        </Box>
      </ThemeProvider>
    );
  }
  return (
    <ThemeProvider theme={robloxTheme}>
      <Box
        sx={{
          minHeight: '100vh',
          background: `linear-gradient(135deg, ${robloxTheme.palette.background.default}, ${alpha(robloxTheme.palette.primary.main, 0.05)})`,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Animated background elements */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `
              radial-gradient(circle at 20% 80%, ${alpha(robloxTheme.palette.primary.main, 0.1)} 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, ${alpha(robloxTheme.palette.secondary.main, 0.1)} 0%, transparent 50%),
              radial-gradient(circle at 40% 40%, ${alpha(robloxTheme.palette.info.main, 0.05)} 0%, transparent 50%)
            `,
            animation: 'float 20s ease-in-out infinite',
            '@keyframes float': {
              '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
              '50%': { transform: 'translateY(-20px) rotate(180deg)' }
            }
          }}
        />
        {/* Main content */}
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          {/* Header */}
          <RobloxDashboardHeader
            title="ToolBoxAI Space Station"
            subtitle="Your Learning Adventure Awaits!"
            onMenuClick={() => console.log('Menu clicked')}
            onNotificationClick={(e: React.MouseEvent) => (notification) => console.log('Notification clicked:', notification)}
            onSettingsClick={() => console.log('Settings clicked')}
            onHelpClick={() => console.log('Help clicked')}
            onProfileClick={() => console.log('Profile clicked')}
          />
          {/* Main dashboard content */}
          <Container maxWidth="xl" sx={{ py: 4 }}>
            {/* Welcome section */}
            <Fade in={true} timeout={1000}>
              <Card
                sx={{
                  mb: 4,
                  background: `linear-gradient(145deg, ${robloxTheme.palette.background.paper}, ${alpha(robloxTheme.palette.primary.main, 0.05)})`,
                  border: `2px solid ${alpha(robloxTheme.palette.primary.main, 0.2)}`,
                  borderRadius: 3,
                  overflow: 'hidden',
                  position: 'relative'
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Grid container spacing={4} alignItems="center">
                    <Grid item xs={12} md={8}>
                      <Typography
                        variant="h3"
                        sx={{
                          fontWeight: 800,
                          mb: 2,
                          background: `linear-gradient(135deg, ${robloxTheme.palette.primary.main}, ${robloxTheme.palette.secondary.main})`,
                          backgroundClip: 'text',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                        }}
                      >
                        Welcome to Your Learning Universe! 🚀
                      </Typography>
                      <Typography
                        variant="h6"
                        sx={{
                          color: robloxTheme.palette.text.secondary,
                          mb: 3,
                          lineHeight: 1.6
                        }}
                      >
                        Explore, learn, and grow with our interactive 3D tools and characters. 
                        Your space adventure begins here!
                      </Typography>
                      <Stack direction="row" spacing={2} flexWrap="wrap">
                        <Chip
                          icon={<Star />}
                          label="Level 5 Explorer"
                          sx={{
                            background: `linear-gradient(135deg, ${robloxTheme.palette.warning.main}, ${alpha(robloxTheme.palette.warning.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                        <Chip
                          icon={<EmojiEvents />}
                          label="12 Achievements"
                          sx={{
                            background: `linear-gradient(135deg, ${robloxTheme.palette.secondary.main}, ${alpha(robloxTheme.palette.secondary.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                        <Chip
                          icon={<TrendingUp />}
                          label="85% Progress"
                          sx={{
                            background: `linear-gradient(135deg, ${robloxTheme.palette.success.main}, ${alpha(robloxTheme.palette.success.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                      </Stack>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <RobloxCharacterAvatar
                          character={{
                            name: 'Astro Explorer',
                            type: 'astronaut',
                            level: 5,
                            xp: 1250,
                            achievements: ['Space Walker', 'Quiz Master', 'Art Creator'],
                            isActive: true,
                            imagePath: '/images/characters/PNG/Astronauto (variation)/01.png'
                          }}
                          size="large"
                          animated={true}
                          onClick={(e: React.MouseEvent) => () => console.log('Character clicked')}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Fade>
            {/* Dashboard Grid */}
            <RobloxDashboardGrid
              onItemClick={handleItemClick}
              onItemPlay={handleItemPlay}
              onItemPause={handleItemPause}
              onItemRefresh={handleItemRefresh}
            />
            {/* Quick Actions */}
            <Fade in={true} timeout={2000}>
              <Card
                sx={{
                  mt: 4,
                  background: `linear-gradient(145deg, ${robloxTheme.palette.background.paper}, ${alpha(robloxTheme.palette.secondary.main, 0.05)})`,
                  border: `2px solid ${alpha(robloxTheme.palette.secondary.main, 0.2)}`,
                  borderRadius: 3,
                  overflow: 'hidden'
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      mb: 3,
                      color: robloxTheme.palette.secondary.main,
                      textAlign: 'center'
                    }}
                  >
                    Quick Actions
                  </Typography>
                  <Grid container spacing={3}>
                    {[
                      { icon: School, label: 'Start Learning', color: robloxTheme.palette.primary.main },
                      { icon: SportsEsports, label: 'Play Games', color: robloxTheme.palette.secondary.main },
                      { icon: Psychology, label: 'AI Assistant', color: robloxTheme.palette.info.main },
                      { icon: Groups, label: 'Join Class', color: robloxTheme.palette.warning.main }
                    ].map((action, index) => (
                      <Grid item xs={6} md={3} key={index}>
                        <Button
                          fullWidth
                          variant="contained"
                          startIcon={<action.icon />}
                          sx={{
                            py: 2,
                            background: `linear-gradient(135deg, ${action.color}, ${alpha(action.color, 0.7)})`,
                            '&:hover': {
                              background: `linear-gradient(135deg, ${action.color}, ${alpha(action.color, 0.8)})`,
                              transform: 'translateY(-2px)',
                            },
                            transition: 'all 0.3s ease'
                          }}
                        >
                          {action.label}
                        </Button>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Fade>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
};
export default RobloxThemedDashboard;