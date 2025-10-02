import { Card, Text, Group, ActionIcon, Badge, Stack } from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import type { ReactNode } from 'react';

/**
 * DashboardCard - Reusable card component for dashboard widgets
 *
 * Features:
 * - Consistent styling across dashboard
 * - Optional badge for status/notifications
 * - Action menu support
 * - Responsive padding and shadows
 *
 * @example
 * ```tsx
 * <DashboardCard
 *   title="Active Users"
 *   badge={{ label: "Live", color: "green" }}
 *   onMenuClick={() => console.log('menu')}
 * >
 *   <Text size="xl" fw={700}>1,234</Text>
 * </DashboardCard>
 * ```
 */

interface DashboardCardProps {
  /** Card title */
  title: string;

  /** Card subtitle (optional) */
  subtitle?: string;

  /** Badge configuration (optional) */
  badge?: {
    label: string;
    color?: string;
  };

  /** Card content */
  children: ReactNode;

  /** Action menu click handler (optional) */
  onMenuClick?: () => void;

  /** Custom footer content (optional) */
  footer?: ReactNode;

  /** Loading state */
  loading?: boolean;

  /** Shadow size */
  shadow?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';

  /** Custom className */
  className?: string;

  /** Custom styles */
  style?: React.CSSProperties;
}

export function DashboardCard({
  title,
  subtitle,
  badge,
  children,
  onMenuClick,
  footer,
  loading = false,
  shadow = 'sm',
  className,
  style,
}: DashboardCardProps) {
  return (
    <Card
      shadow={shadow}
      padding="lg"
      radius="md"
      withBorder
      className={className}
      style={style}
    >
      {/* Header */}
      <Group justify="space-between" mb="md">
        <Stack gap={4}>
          <Group gap="sm">
            <Text fw={500} size="lg">
              {title}
            </Text>
            {badge && (
              <Badge color={badge.color} variant="light" size="sm">
                {badge.label}
              </Badge>
            )}
          </Group>
          {subtitle && (
            <Text size="sm" c="dimmed">
              {subtitle}
            </Text>
          )}
        </Stack>

        {onMenuClick && (
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={onMenuClick}
            aria-label="Card menu"
          >
            <IconDots size={18} />
          </ActionIcon>
        )}
      </Group>

      {/* Content */}
      <div style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <Card.Section withBorder inheritPadding py="xs" mt="md">
          {footer}
        </Card.Section>
      )}
    </Card>
  );
}

DashboardCard.displayName = 'DashboardCard';
