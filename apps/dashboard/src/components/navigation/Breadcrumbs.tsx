import { Breadcrumbs as MantineBreadcrumbs, Anchor, Text } from '@mantine/core';
import { useLocation, Link } from 'react-router-dom';
import { IconHome } from '@tabler/icons-react';

const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  'lessons': 'Lessons',
  'assessments': 'Assessments',
  'classes': 'Classes',
  'students': 'Students',
  'analytics': 'Analytics',
  'settings': 'Settings',
  'roblox': 'Roblox Studio',
  'roblox-studio': 'Roblox Studio',
  'agents': 'Agent System',
  'users': 'Users',
  'schools': 'Schools',
  'compliance': 'Compliance',
  'integrations': 'Integrations',
  'missions': 'Missions',
  'rewards': 'Rewards',
  'progress': 'Progress',
  'leaderboard': 'Leaderboard',
  'avatar': 'Avatar',
  'play': 'Play',
  'messages': 'Messages',
  'reports': 'Reports',
  'gameplay-replay': 'Gameplay Replay',
};

/**
 * Breadcrumbs - Dynamic breadcrumb navigation based on current route
 * Automatically generates breadcrumb trail from URL path
 */
export function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Don't show breadcrumbs on home page
  if (pathnames.length === 0) {
    return null;
  }

  return (
    <MantineBreadcrumbs
      mb="md"
      styles={{
        separator: { color: 'var(--mantine-color-dimmed)' },
        breadcrumb: { fontSize: '0.875rem' },
      }}
    >
      <Anchor component={Link} to="/" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <IconHome size={16} />
        Home
      </Anchor>
      
      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const label = routeLabels[name] || name.charAt(0).toUpperCase() + name.slice(1).replace(/-/g, ' ');

        return isLast ? (
          <Text key={name} c="dimmed">
            {label}
          </Text>
        ) : (
          <Anchor key={name} component={Link} to={routeTo}>
            {label}
          </Anchor>
        );
      })}
    </MantineBreadcrumbs>
  );
}
