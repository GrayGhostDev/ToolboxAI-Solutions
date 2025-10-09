import React, { Suspense } from 'react';
import { Card, Text, Group, Button, Badge, useMantineTheme } from '@mantine/core';

// Lazy load 3D icons
const Real3DIcon = React.lazy(() => import('../../roblox/Real3DIcon').then(m => ({ default: m.Real3DIcon })));

interface NavigationItem {
  name: string;
  icon: string;
  iconColor: string;
  path: string;
  badge?: number;
}

// Simple emoji fallback for icons
const SimpleNavIcon = ({ icon, color }: { icon: string; color: string }) => {
  const iconEmojis: Record<string, string> = {
    'BOARD': '📋',
    'BOOKS': '📚',
    'ASSESSMENT': '📝',
    'TROPHY': '🏆',
    'BADGE': '🏅'
  };

  return (
    <span style={{ fontSize: '1.5rem', color }}>{iconEmojis[icon] || '🎮'}</span>
  );
};

interface RobloxNavigationHubProps {
  navigate: (path: string) => void;
}

const RobloxNavigationHub: React.FC<RobloxNavigationHubProps> = ({ navigate }) => {
  const theme = useMantineTheme();
  const [use3D, setUse3D] = React.useState(false);

  // Enable 3D icons after initial render
  React.useEffect(() => {
    const timer = setTimeout(() => setUse3D(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  const navigationItems: NavigationItem[] = [
    { name: 'Dashboard', icon: 'BOARD', iconColor: '#00bcd4', path: '/dashboard' },
    { name: 'Lessons', icon: 'BOOKS', iconColor: '#4caf50', path: '/lessons', badge: 3 },
    { name: 'Assessments', icon: 'ASSESSMENT', iconColor: '#e91e63', path: '/assessments' },
    { name: 'Rewards', icon: 'TROPHY', iconColor: '#ffc107', path: '/rewards', badge: 5 },
    { name: 'Profile', icon: 'BADGE', iconColor: '#9c27b0', path: '/profile' },
  ];

  return (
    <Card
      style={{
        background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
        border: `2px solid ${theme.colors.blue[2]}`,
        borderRadius: theme.radius.md,
        padding: 16,
      }}
    >
      <Text size="lg" ta="center" mb="md" fw={700}>
        📋 Navigation Hub
      </Text>

      <Group justify="center" gap="md" wrap="wrap">
        {navigationItems.map((item, index) => (
          <Button
            key={index}
            variant="filled"
            leftSection={
              use3D ? (
                <Suspense fallback={<SimpleNavIcon icon={item.icon} color={item.iconColor} />}>
                  <Real3DIcon
                    iconName={item.icon}
                    size="small"
                    animated={false}
                  />
                </Suspense>
              ) : (
                <SimpleNavIcon icon={item.icon} color={item.iconColor} />
              )
            }
            onClick={() => navigate(item.path)}
            style={{
              background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
              borderRadius: theme.radius.sm,
              padding: '8px 24px',
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            {item.name}
            {item.badge && (
              <Badge
                size="sm"
                style={{
                  marginLeft: 8,
                  backgroundColor: theme.colors.red[6],
                  color: 'white',
                  fontSize: '0.7rem',
                }}
              >
                {item.badge}
              </Badge>
            )}
          </Button>
        ))}
      </Group>
    </Card>
  );
};

export default RobloxNavigationHub;