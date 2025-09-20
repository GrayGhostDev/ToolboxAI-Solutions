/**
 * MetricCard Component
 * Displays metrics with animations, trends, and interactive features
 */

import React, { memo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Tooltip,
  IconButton,
  Skeleton,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Info as InfoIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
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
  const theme = useTheme();

  const getTrendIcon = () => {
    if (trend === 'up' || (change && change > 0)) {
      return <TrendingUp sx={{ fontSize: 16 }} />;
    }
    if (trend === 'down' || (change && change < 0)) {
      return <TrendingDown sx={{ fontSize: 16 }} />;
    }
    return <TrendingFlat sx={{ fontSize: 16 }} />;
  };

  const getTrendColor = () => {
    if (trend === 'up' || (change && change > 0)) {
      return theme.palette.success.main;
    }
    if (trend === 'down' || (change && change < 0)) {
      return theme.palette.error.main;
    }
    return theme.palette.text.secondary;
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
      <Box sx={{ position: 'absolute', right: 16, bottom: 16, opacity: 0.3 }}>
        <svg width={width} height={height}>
          <polyline
            points={points}
            fill="none"
            stroke={theme.palette[color].main}
            strokeWidth="2"
          />
        </svg>
      </Box>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width="40%" height={32} />
            <Skeleton variant="text" width="30%" />
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <MotionCard
      whileHover={{ scale: onClick ? 1.02 : 1 }}
      transition={{ type: 'spring', stiffness: 300 }}
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        position: 'relative',
        overflow: 'visible',
        background: `linear-gradient(135deg,
          ${alpha(theme.palette[color].main, 0.05)} 0%,
          ${alpha(theme.palette[color].main, 0.02)} 100%)`,
        borderLeft: `4px solid ${theme.palette[color].main}`,
      }}
    >
      <CardContent>
        <Stack spacing={1}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              {icon && (
                <Box
                  sx={{
                    color: theme.palette[color].main,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {icon}
                </Box>
              )}
              <Typography variant="body2" color="text.secondary" fontWeight={500}>
                {title}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={0.5}>
              {description && (
                <Tooltip title={description}>
                  <IconButton size="small" onClick={onInfoClick}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              <IconButton size="small">
                <MoreIcon fontSize="small" />
              </IconButton>
            </Stack>
          </Stack>

          {/* Value */}
          <Typography
            variant="h4"
            fontWeight="bold"
            sx={{
              color: theme.palette.text.primary,
              display: 'flex',
              alignItems: 'baseline',
              gap: 0.5,
            }}
          >
            {prefix && (
              <Typography component="span" variant="h5" color="text.secondary">
                {prefix}
              </Typography>
            )}
            {formatValue()}
            {suffix && (
              <Typography component="span" variant="h6" color="text.secondary">
                {suffix}
              </Typography>
            )}
          </Typography>

          {/* Change indicator */}
          {(change !== undefined || changeLabel) && (
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  color: getTrendColor(),
                }}
              >
                {getTrendIcon()}
              </Box>
              {change !== undefined && (
                <Typography
                  variant="body2"
                  sx={{
                    color: getTrendColor(),
                    fontWeight: 600,
                  }}
                >
                  {change > 0 ? '+' : ''}{change}%
                </Typography>
              )}
              {changeLabel && (
                <Typography variant="body2" color="text.secondary">
                  {changeLabel}
                </Typography>
              )}
            </Stack>
          )}
        </Stack>

        {/* Sparkline */}
        {renderSparkline()}
      </CardContent>
    </MotionCard>
  );
});

MetricCard.displayName = 'MetricCard';

export default MetricCard;