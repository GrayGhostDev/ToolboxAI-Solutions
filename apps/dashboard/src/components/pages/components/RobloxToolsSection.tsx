import React, { Suspense } from 'react';
import { Grid, Card, Text, Box, useMantineTheme } from '@mantine/core';
import { PerformanceSkeleton } from '../../atomic/atoms/PerformanceSkeleton';

// Lazy load the heavy 3D icon component
const Real3DIcon = React.lazy(() => import('../../roblox/Real3DIcon').then(m => ({ default: m.Real3DIcon })));

// Fallback component for 3D icons
const SimpleIcon = ({ name, description }: { name: string; description: string }) => {
  const iconEmojis: Record<string, string> = {
    'ABC_CUBE': '🧩',
    'BOARD': '📋',
    'ROCKET': '🚀',
    'SOCCER_BALL': '⚽',
    'BRUSH_PAINT': '🎨',
    'TROPHY': '🏆'
  };

  return (
    <Box
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: 16,
        fontSize: '2rem',
        cursor: 'pointer',
        transition: 'transform 0.3s ease',
      }}
      onClick={() => console.log(`Clicked ${name}`)}
    >
      <div style={{ fontSize: '3rem', marginBottom: 8 }}>{iconEmojis[name] || '🎮'}</div>
      <Text size="sm" ta="center" fw={600}>
        {description}
      </Text>
    </Box>
  );
};

const RobloxToolsSection: React.FC = () => {
  const theme = useMantineTheme();
  const [use3D, setUse3D] = React.useState(false);

  // Enable 3D components after component mount to improve initial load
  React.useEffect(() => {
    const timer = setTimeout(() => setUse3D(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  const tools = [
    { name: 'ABC_CUBE', description: 'ABC Learning Cube' },
    { name: 'BOARD', description: 'Math Learning Board' },
    { name: 'ROCKET', description: 'Space Quiz Mission' },
    { name: 'SOCCER_BALL', description: 'Sports Challenge' },
    { name: 'BRUSH_PAINT', description: 'Art Studio' },
    { name: 'TROPHY', description: 'Achievements Hall' },
  ];

  return (
    <Card
      style={{
        background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
        border: `2px solid ${theme.colors.blue[2]}`,
        borderRadius: theme.radius.md,
        overflow: 'hidden'
      }}
    >
      <Card.Section p="xl">
        <Text
          size="xl"
          fw={700}
          style={{
            marginBottom: 24,
            textAlign: 'center',
            background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          🎮 Your Learning Tools
        </Text>

        <Grid gutter="md" justify="center">
          {tools.map((tool, index) => (
            <Grid.Col span={{ base: 6, sm: 4, md: 2 }} key={index}>
              <Box
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: 16,
                  borderRadius: theme.radius.md,
                  background: `linear-gradient(145deg, ${theme.colors.blue[1]}, ${theme.colors.violet[0]})`,
                  border: `2px solid ${theme.colors.blue[3]}`,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  minHeight: 120,
                }}
                onClick={() => console.log(`Clicked ${tool.name}`)}
              >
                {use3D ? (
                  <Suspense fallback={<SimpleIcon name={tool.name} description={tool.description} />}>
                    <Real3DIcon
                      iconName={tool.name}
                      size="large"
                      animated={true}
                      description={tool.description}
                    />
                  </Suspense>
                ) : (
                  <SimpleIcon name={tool.name} description={tool.description} />
                )}
              </Box>
            </Grid.Col>
          ))}
        </Grid>
      </Card.Section>
    </Card>
  );
};

export default RobloxToolsSection;