import { Card, Group, Stack, Text, Badge, ThemeIcon } from '@mantine/core';
import { IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';
import { ReactNode } from 'react';

interface MetricCardProps {
  icon: ReactNode;
  label: string;
  value: string | number;
  trend?: {
    value: number;
    direction: 'up' | 'down';
    label?: string;
  };
  color?: string;
  onClick?: () => void;
  loading?: boolean;
}

/**
 * MetricCard - Displays a key performance indicator with optional trend
 * 
 * @example
 * <MetricCard
 *   icon={<IconUsers size={24} />}
 *   label="Active Students"
 *   value={142}
 *   trend={{ value: 12, direction: 'up', label: 'vs last week' }}
 *   color="blue"
 *   onClick={() => navigate('/students')}
 * />
 */
export function MetricCard({ 
  icon, 
  label, 
  value, 
  trend, 
  color = 'blue',
  onClick,
  loading = false
}: MetricCardProps) {
  return (
    <Card 
      shadow="sm" 
      radius="md" 
      withBorder
      style={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      aria-label={`${label}: ${value}`}
      styles={{
        root: {
          '&:hover': onClick ? {
            transform: 'translateY(-2px)',
            boxShadow: 'var(--mantine-shadow-md)',
          } : {},
        },
      }}
    >
      <Group justify="space-between" mb="xs">
        <ThemeIcon size="xl" radius="md" color={color} variant="light">
          {icon}
        </ThemeIcon>
        {trend && (
          <Badge
            variant="light"
            color={trend.direction === 'up' ? 'green' : 'red'}
            leftSection={
              trend.direction === 'up' ? 
                <IconTrendingUp size={14} /> : 
                <IconTrendingDown size={14} />
            }
          >
            {trend.value > 0 ? '+' : ''}{trend.value}%
          </Badge>
        )}
      </Group>
      
      <Stack gap={4}>
        <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
          {label}
        </Text>
        <Text size="xl" fw={700}>
          {loading ? '...' : value}
        </Text>
        {trend?.label && (
          <Text size="xs" c="dimmed">
            {trend.label}
          </Text>
        )}
      </Stack>
    </Card>
  );
}
