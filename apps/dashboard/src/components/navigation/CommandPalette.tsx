import { Spotlight, spotlight } from '@mantine/spotlight';
import { 
  IconSearch, 
  IconSchool, 
  IconTrophy, 
  IconSettings, 
  IconRocket,
  IconUsers,
  IconChartBar,
  IconShield,
  IconClipboardCheck,
  IconDeviceGamepad,
  IconAward,
  IconMessage,
  IconFlag,
  IconPlus,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useHotkeys } from '@mantine/hooks';
import { useAppSelector } from '../../store';
import type { SpotlightActionData } from '@mantine/spotlight';

/**
 * CommandPalette - Quick navigation and action launcher (Cmd/Ctrl + K)
 * Provides role-based actions and navigation shortcuts
 */
export function CommandPalette() {
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);

  // Register Cmd/Ctrl + K shortcut
  useHotkeys([['mod+K', () => spotlight.open()]]);

  // Common actions available to all roles
  const commonActions: SpotlightActionData[] = [
    {
      id: 'home',
      label: 'Home Dashboard',
      description: 'Go to home page',
      onClick: () => navigate('/'),
      leftSection: <IconSchool size={18} />,
      group: 'Navigation',
    },
    {
      id: 'settings',
      label: 'Settings',
      description: 'Configure your preferences',
      onClick: () => navigate('/settings'),
      leftSection: <IconSettings size={18} />,
      group: 'Navigation',
    },
  ];

  // Role-specific actions
  const roleActions: Record<string, SpotlightActionData[]> = {
    admin: [
      {
        id: 'users',
        label: 'Manage Users',
        description: 'View and manage all users',
        onClick: () => navigate('/users'),
        leftSection: <IconUsers size={18} />,
        group: 'Admin',
      },
      {
        id: 'schools',
        label: 'Manage Schools',
        description: 'View and manage schools',
        onClick: () => navigate('/schools'),
        leftSection: <IconSchool size={18} />,
        group: 'Admin',
      },
      {
        id: 'analytics',
        label: 'Analytics Dashboard',
        description: 'View system analytics',
        onClick: () => navigate('/analytics'),
        leftSection: <IconChartBar size={18} />,
        group: 'Admin',
      },
      {
        id: 'compliance',
        label: 'Compliance',
        description: 'View compliance status',
        onClick: () => navigate('/compliance'),
        leftSection: <IconShield size={18} />,
        group: 'Admin',
      },
      {
        id: 'agents',
        label: 'Agent System',
        description: 'Manage AI agents',
        onClick: () => navigate('/agents'),
        leftSection: <IconRocket size={18} />,
        group: 'Admin',
      },
    ],
    teacher: [
      {
        id: 'lessons',
        label: 'View Lessons',
        description: 'Browse all lessons',
        onClick: () => navigate('/lessons'),
        leftSection: <IconSchool size={18} />,
        group: 'Teaching',
      },
      {
        id: 'create-lesson',
        label: 'Create New Lesson',
        description: 'Start creating a new lesson',
        onClick: () => navigate('/lessons/new'),
        leftSection: <IconPlus size={18} />,
        group: 'Teaching',
      },
      {
        id: 'classes',
        label: 'My Classes',
        description: 'View and manage classes',
        onClick: () => navigate('/classes'),
        leftSection: <IconUsers size={18} />,
        group: 'Teaching',
      },
      {
        id: 'assessments',
        label: 'Assessments',
        description: 'View and grade assessments',
        onClick: () => navigate('/assessments'),
        leftSection: <IconClipboardCheck size={18} />,
        group: 'Teaching',
      },
      {
        id: 'roblox',
        label: 'Roblox Studio',
        description: 'Open Roblox Studio integration',
        onClick: () => navigate('/roblox-studio'),
        leftSection: <IconRocket size={18} />,
        group: 'Teaching',
      },
      {
        id: 'reports',
        label: 'Student Reports',
        description: 'View student progress reports',
        onClick: () => navigate('/reports'),
        leftSection: <IconChartBar size={18} />,
        group: 'Teaching',
      },
    ],
    student: [
      {
        id: 'missions',
        label: 'My Missions',
        description: 'View available missions',
        onClick: () => navigate('/missions'),
        leftSection: <IconFlag size={18} />,
        group: 'Learning',
      },
      {
        id: 'play',
        label: 'Play',
        description: 'Enter the learning world',
        onClick: () => navigate('/play'),
        leftSection: <IconDeviceGamepad size={18} />,
        group: 'Learning',
      },
      {
        id: 'progress',
        label: 'My Progress',
        description: 'View your learning progress',
        onClick: () => navigate('/progress'),
        leftSection: <IconChartBar size={18} />,
        group: 'Learning',
      },
      {
        id: 'rewards',
        label: 'Rewards',
        description: 'View your achievements and rewards',
        onClick: () => navigate('/rewards'),
        leftSection: <IconAward size={18} />,
        group: 'Learning',
      },
      {
        id: 'leaderboard',
        label: 'Leaderboard',
        description: 'See where you rank',
        onClick: () => navigate('/leaderboard'),
        leftSection: <IconTrophy size={18} />,
        group: 'Learning',
      },
    ],
    parent: [
      {
        id: 'progress',
        label: "Child's Progress",
        description: "View your child's learning progress",
        onClick: () => navigate('/progress'),
        leftSection: <IconChartBar size={18} />,
        group: 'Parent',
      },
      {
        id: 'reports',
        label: 'Reports',
        description: 'View detailed progress reports',
        onClick: () => navigate('/reports'),
        leftSection: <IconClipboardCheck size={18} />,
        group: 'Parent',
      },
      {
        id: 'messages',
        label: 'Messages',
        description: 'Communicate with teachers',
        onClick: () => navigate('/messages'),
        leftSection: <IconMessage size={18} />,
        group: 'Parent',
      },
    ],
  };

  // Combine common actions with role-specific actions
  const actions = [
    ...commonActions,
    ...(roleActions[role as string] || []),
  ];

  return (
    <Spotlight
      actions={actions}
      searchProps={{
        leftSection: <IconSearch size={18} />,
        placeholder: 'Search actions... (Cmd/Ctrl + K)',
      }}
      nothingFound="Nothing found..."
      highlightQuery
      shortcut="mod + K"
      limit={10}
    />
  );
}
