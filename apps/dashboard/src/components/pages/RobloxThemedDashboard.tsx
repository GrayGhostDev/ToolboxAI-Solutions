import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Chip,
  Fade,
  ThemeProvider,
  alpha,
  useTheme
} from '@mui/material';
import { SimpleGrid } from '@mantine/core';
/**
 * Roblox Themed Dashboard
 * 
 * Main dashboard component that combines all Roblox-themed elements
 * with futuristic design, character integration, and 3D icons
 */
import {
  IconStar,
  IconTrendingUp,
  IconRocket,
  IconUsers,
  IconBrain,
  IconDeviceGamepad2,
  IconSchool
} from '@tabler/icons-react';
import robloxTheme from '../../robloxTheme';
import RobloxDashboardHeader from '../roblox/RobloxDashboardHeader';
import RobloxDashboardGrid from '../roblox/RobloxDashboardGrid';
import RobloxCharacterAvatar from '../roblox/RobloxCharacterAvatar';

interface RobloxThemedDashboardProps {
  onNavigate?: (path: string) => void;
  onItemClick?: (item: any) => void;
}

export const RobloxThemedDashboard: React.FunctionComponent<RobloxThemedDashboardProps> = ({
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
            <IconRocket style={{ fontSize: 40, color: 'white' }} />
          </Box>
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
              radial-gradient(circle at 80% 20%, ${alpha(robloxTheme.palette.secondary.main, 0.1)} 0%, transparent 50%)
            `,
            animation: 'float 20s ease-in-out infinite',
            '@keyframes float': {
              '0%, 100%': { transform: 'translateY(0px)' },
              '50%': { transform: 'translateY(-20px)' }
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
            onNotificationClick={(notification) => console.log('Notification clicked:', notification)}
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
                  borderRadius: 3
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl">
                    <Box>
                      <Box
                        component="h3"
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
                      </Box>
                      <Box sx={{ color: 'text.secondary', mb: 3, lineHeight: 1.6 }}>
                        Explore, learn, and grow with our interactive 3D tools and characters.
                        Your space adventure begins here!
                      </Box>
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        <Chip
                          icon={<IconStar />}
                          label="Level 5 Explorer"
                          sx={{
                            background: `linear-gradient(135deg, ${robloxTheme.palette.warning.main}, ${alpha(robloxTheme.palette.warning.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                        <Chip
                          icon={<IconTrendingUp />}
                          label="85% Progress"
                          sx={{
                            background: `linear-gradient(135deg, ${robloxTheme.palette.success.main}, ${alpha(robloxTheme.palette.success.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                      </Box>
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <RobloxCharacterAvatar
                          character={{
                            name: 'Astro Explorer',
                            type: 'astronaut',
                            level: 5,
                            xp: 1250,
                            achievements: ['Space Walker', 'Quiz Master', 'Art Creator'],
                            isActive: true
                          }}
                          size="large"
                          animated={true}
                          onClick={() => console.log('Character clicked')}
                        />
                      </Box>
                    </Box>
                  </SimpleGrid>
                </CardContent>
              </Card>
            </Fade>

            {/* Dashboard Grid */}
            <RobloxDashboardGrid
              items={[]}
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
                  borderRadius: 3
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Box
                    component="h5"
                    sx={{
                      fontWeight: 700,
                      mb: 3,
                      color: robloxTheme.palette.secondary.main,
                      textAlign: 'center'
                    }}
                  >
                    Quick Actions
                  </Box>
                  <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
                    {[
                      { icon: IconSchool, label: 'Start Learning', color: robloxTheme.palette.primary.main },
                      { icon: IconDeviceGamepad2, label: 'Play Games', color: robloxTheme.palette.secondary.main },
                      { icon: IconBrain, label: 'AI Assistant', color: robloxTheme.palette.info.main },
                      { icon: IconUsers, label: 'Join Class', color: robloxTheme.palette.warning.main }
                    ].map((action, index) => (
                      <Button
                        key={index}
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
                    ))}
                  </SimpleGrid>
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