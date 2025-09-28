/**
 * MetricCard Component
 * Displays metrics with animations, trends, and interactive features
 */

import React, { memo } from 'react';
import {
  Card,
  Text,
  Box,
  Stack,
  Tooltip,
  ActionIcon,
  Skeleton,
  useMantineTheme,
  alpha,
  Group,
} from '@mantine/core';

import {
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconInfoCircle as InfoIcon,
  IconDots as MoreIcon,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  prefix?: string;
  suffix?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  loading?: boolean;
  onClick?: () => void;
  onInfoClick?: () => void;
  description?: string;
  trend?: 'up' | 'down' | 'flat';
  sparklineData?: number[];
}

const MotionCard = motion(Card);

export const MetricCard = memo<MetricCardProps>(({
  title,
  value,
  change,
  changeLabel,
  prefix = '',
  suffix = '',
  icon,
  color = 'primary',
  loading = false,
  onClick,
  onInfoClick,
  description,
  trend,
  sparklineData,
}) => {
  const theme = useMantineTheme();

  const getTrendIcon = () => {
    if (trend === 'up' || (change && change > 0)) {
      return <IconTrendingUp size={16} />;
    }
    if (trend === 'down' || (change && change < 0)) {
      return <IconTrendingDown size={16} />;
    }
    return <IconMinus size={16} />;
  };

  const getTrendColor = () => {
    if (trend === 'up' || (change && change > 0)) {
      return theme.colors.green[6];
    }
    if (trend === 'down' || (change && change < 0)) {
      return theme.colors.red[6];
    }
    return theme.colors.gray[6];
  };

  const formatValue = () => {
    if (typeof value === 'number') {
      // Format large numbers
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      }
      if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    }
    return value;
  };

  const getColorValue = (colorName: string) => {
    const colorMap = {
      primary: theme.colors.blue[6],
      secondary: theme.colors.gray[6],
      success: theme.colors.green[6],
      warning: theme.colors.yellow[6],
      error: theme.colors.red[6],
      info: theme.colors.cyan[6],
    };
    return colorMap[colorName as keyof typeof colorMap] || theme.colors.blue[6];
  };

  const renderSparkline = () => {
    if (!sparklineData || sparklineData.length === 0) return null;

    const max = Math.max(...sparklineData);
    const min = Math.min(...sparklineData);
    const range = max - min || 1;
    const height = 40;
    const width = 100;
    const step = width / (sparklineData.length - 1);

    const points = sparklineData
      .map((val, i) => {
        const x = i * step;
        const y = height - ((val - min) / range) * height;
        return `${x},${y}`;
      })
      .join(' ');

    return (
      <Box style={{ position: 'absolute', right: 16, bottom: 16, opacity: 0.3 }}>
        <svg width={width} height={height}>
          <polyline
            points={points}
            fill="none"
            stroke={getColorValue(color)}
            strokeWidth="2"
          />
        </svg>
      </Box>
    );
  };

  if (loading) {
    return (
      <Card padding="md" withBorder>
        <Stack gap="md">
          <Skeleton height={8} width="60%" />
          <Skeleton height={32} width="40%" />
          <Skeleton height={8} width="30%" />
        </Stack>
      </Card>
    );
  }

  return (
    <MotionCard
      whileHover={{ scale: onClick ? 1.02 : 1 }}
      transition={{ type: 'spring', stiffness: 300 }}
      onClick={onClick}
      padding="md"
      withBorder
      style={{
        cursor: onClick ? 'pointer' : 'default',
        position: 'relative',
        overflow: 'visible',
        background: `linear-gradient(135deg,
          ${alpha(getColorValue(color), 0.05)} 0%,
          ${alpha(getColorValue(color), 0.02)} 100%)`,
        borderLeft: `4px solid ${getColorValue(color)}`,
      }}
    >
      <Stack gap="xs">
        {/* Header */}
        <Group justify="space-between">
          <Group gap="xs">
            {icon && (
              <Box
                style={{
                  color: getColorValue(color),
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {icon}
              </Box>
            )}
            <Text size="sm" c="dimmed" fw={500}>
              {title}
            </Text>
          </Group>
          <Group gap={4}>
            {description && (
              <Tooltip label={description}>
                <ActionIcon size="sm" variant="subtle" onClick={onInfoClick}>
                  <InfoIcon size={16} />
                </ActionIcon>
              </Tooltip>
            )}
            <ActionIcon size="sm" variant="subtle">
              <MoreIcon size={16} />
            </ActionIcon>
          </Group>
        </Group>

        {/* Value */}
        <Group gap="xs" align="baseline">
          {prefix && (
            <Text size="lg" c="dimmed">
              {prefix}
            </Text>
          )}
          <Text size="xl" fw={700}>
            {formatValue()}
          </Text>
          {suffix && (
            <Text size="md" c="dimmed">
              {suffix}
            </Text>
          )}
        </Group>

        {/* Change indicator */}
        {(change !== undefined || changeLabel) && (
          <Group gap="xs">
            <Box
              style={{
                display: 'flex',
                alignItems: 'center',
                color: getTrendColor(),
              }}
            >
              {getTrendIcon()}
            </Box>
            {change !== undefined && (
              <Text
                size="sm"
                fw={600}
                style={{ color: getTrendColor() }}
              >
                {change > 0 ? '+' : ''}{change}%
              </Text>
            )}
            {changeLabel && (
              <Text size="sm" c="dimmed">
                {changeLabel}
              </Text>
            )}
          </Group>
        )}
      </Stack>

      {/* Sparkline */}
      {renderSparkline()}
    </MotionCard>
  );
});

MetricCard.displayName = 'MetricCard';

export default MetricCard;