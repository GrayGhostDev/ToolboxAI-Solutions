import type { Meta, StoryObj } from '@storybook/react';
import { DashboardCard } from './DashboardCard';
import { Text, Progress, Group, Button } from '@mantine/core';
import { IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';

const meta = {
  title: 'Dashboard/DashboardCard',
  component: DashboardCard,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Reusable dashboard card component with consistent styling, badges, and action menus.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Card title',
    },
    subtitle: {
      control: 'text',
      description: 'Optional subtitle',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state',
    },
    shadow: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Shadow size',
    },
  },
} satisfies Meta<typeof DashboardCard>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Basic dashboard card with title and content
 */
export const Basic: Story = {
  args: {
    title: 'Active Users',
    children: (
      <Text size="xl" fw={700}>
        1,234
      </Text>
    ),
  },
};

/**
 * Card with subtitle and badge
 */
export const WithBadge: Story = {
  args: {
    title: 'Server Status',
    subtitle: 'Last updated 2 minutes ago',
    badge: {
      label: 'Live',
      color: 'green',
    },
    children: (
      <Text size="xl" fw={700} c="green">
        Operational
      </Text>
    ),
  },
};

/**
 * Card with menu action
 */
export const WithMenu: Story = {
  args: {
    title: 'Revenue',
    subtitle: 'Last 30 days',
    onMenuClick: () => alert('Menu clicked!'),
    children: (
      <div>
        <Text size="xl" fw={700}>
          $12,456
        </Text>
        <Group gap="xs" mt="xs">
          <IconTrendingUp size={16} color="green" />
          <Text size="sm" c="green">
            +12.5%
          </Text>
        </Group>
      </div>
    ),
  },
};

/**
 * Card with progress indicator
 */
export const WithProgress: Story = {
  args: {
    title: 'Storage Usage',
    subtitle: '45 GB of 100 GB used',
    badge: {
      label: '45%',
      color: 'blue',
    },
    children: (
      <div>
        <Progress value={45} size="lg" radius="xl" mb="xs" />
        <Text size="sm" c="dimmed">
          55 GB remaining
        </Text>
      </div>
    ),
  },
};

/**
 * Card with footer actions
 */
export const WithFooter: Story = {
  args: {
    title: 'System Update',
    subtitle: 'New version available',
    badge: {
      label: 'New',
      color: 'blue',
    },
    children: (
      <Text size="sm">
        Version 2.5.0 is now available with bug fixes and performance improvements.
      </Text>
    ),
    footer: (
      <Group justify="space-between">
        <Button variant="subtle" color="gray" size="xs">
          Later
        </Button>
        <Button size="xs">Update Now</Button>
      </Group>
    ),
  },
};

/**
 * Card with negative trend
 */
export const NegativeTrend: Story = {
  args: {
    title: 'Conversion Rate',
    subtitle: 'Last 7 days',
    onMenuClick: () => alert('Menu clicked'),
    children: (
      <div>
        <Text size="xl" fw={700}>
          2.4%
        </Text>
        <Group gap="xs" mt="xs">
          <IconTrendingDown size={16} color="red" />
          <Text size="sm" c="red">
            -0.8%
          </Text>
        </Group>
      </div>
    ),
  },
};

/**
 * Loading state
 */
export const Loading: Story = {
  args: {
    title: 'Loading Data',
    subtitle: 'Please wait...',
    loading: true,
    children: (
      <Text size="xl" fw={700}>
        Loading...
      </Text>
    ),
  },
};

/**
 * Large shadow for emphasis
 */
export const LargeShadow: Story = {
  args: {
    title: 'Important Metric',
    badge: {
      label: 'Critical',
      color: 'red',
    },
    shadow: 'xl',
    children: (
      <Text size="xl" fw={700} c="red">
        Attention Required
      </Text>
    ),
  },
};

/**
 * Dashboard grid example
 */
export const DashboardGrid: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
      <DashboardCard
        title="Active Users"
        subtitle="Real-time count"
        badge={{ label: 'Live', color: 'green' }}
      >
        <Text size="xl" fw={700}>1,234</Text>
      </DashboardCard>

      <DashboardCard
        title="Revenue"
        subtitle="Last 30 days"
        onMenuClick={() => console.log('menu')}
      >
        <div>
          <Text size="xl" fw={700}>$12,456</Text>
          <Group gap="xs" mt="xs">
            <IconTrendingUp size={16} color="green" />
            <Text size="sm" c="green">+12.5%</Text>
          </Group>
        </div>
      </DashboardCard>

      <DashboardCard
        title="Storage"
        subtitle="Current usage"
        badge={{ label: '45%', color: 'blue' }}
      >
        <Progress value={45} size="lg" radius="xl" />
      </DashboardCard>
    </div>
  ),
  parameters: {
    layout: 'padded',
  },
};
