import React, { useState, useEffect } from 'react';
import { Box, Card, Text, Group, ActionIcon, Tooltip, useMantineTheme } from '@mantine/core';
import { IconTrendingUp, IconTrendingDown, IconInfoCircle } from '@tabler/icons-react';
import { motion } from 'framer-motion';
import { robloxColors } from '../../theme/robloxTheme';
// Helper function to add transparency to colors
const alphaColor = (color: string, alpha: number) => {
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
interface Roblox3DMetricCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  color?: string;
  subtitle?: string;
  onClick?: () => void;
  tooltip?: string;
  format?: 'number' | 'percentage' | 'currency' | 'time';
}
export const Roblox3DMetricCard: React.FunctionComponent<Roblox3DMetricCardProps> = ({
  title,
  value,
  icon,
  trend,
  color = robloxColors.primary,
  subtitle,
  onClick,
  tooltip,
  format = 'number',
}) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [displayValue, setDisplayValue] = useState<string>('0');
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    // Animate number counting
    if (typeof value === 'number') {
      const duration = 1000;
      const steps = 60;
      const stepDuration = duration / steps;
      const increment = value / steps;
      let current = 0;
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          current = value;
          clearInterval(timer);
        }
        setAnimatedValue(current);
      }, stepDuration);
      return () => clearInterval(timer);
    } else {
      setDisplayValue(value);
    }
  }, [value]);

  useEffect(() => {
    // Format the animated value
    let formatted = '';
    switch (format) {
      case 'percentage':
        formatted = `${Math.round(animatedValue)}%`;
        break;
      case 'currency':
        formatted = `$${animatedValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        break;
      case 'time':
        formatted = `${Math.round(animatedValue)}h`;
        break;
      default:
        formatted = animatedValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }
    setDisplayValue(formatted);
  }, [animatedValue, format]);

  const cardStyles = {
    background: `linear-gradient(135deg, ${robloxColors.darkBase} 0%, ${robloxColors.darkGray} 100%)`,
    border: `2px solid ${color}`,
    borderRadius: '16px',
    cursor: onClick ? 'pointer' : 'default',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    transform: isHovered ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
    boxShadow: isHovered
      ? `0 20px 40px ${alphaColor(color, 0.4)}`
      : `0 4px 12px ${alphaColor('#000000', 0.2)}`,
  };

  const iconContainerStyles = {
    width: 64,
    height: 64,
    borderRadius: '12px',
    background: `linear-gradient(135deg, ${color} 0%, ${alphaColor(color, 0.8)} 100%)`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: `0 4px 12px ${alphaColor(color, 0.3)}`,
  };

  const valueDisplayStyles = {
    fontSize: '2.5rem',
    fontWeight: 800,
    background: `linear-gradient(135deg, #fff 0%, ${robloxColors.accent} 100%)`,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: '-0.02em',
    lineHeight: 1,
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return robloxColors.success;
      case 'down':
        return robloxColors.error;
      default:
        return robloxColors.gray;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <Card
        style={cardStyles}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
        p="lg"
      >
        <Group justify="space-between" align="flex-start" mb="md">
          <Box style={{ flex: 1 }}>
            <Group gap="xs" mb="xs">
              <Text
                size="sm"
                fw={600}
                tt="uppercase"
                style={{
                  color: robloxColors.lightGray,
                  letterSpacing: '0.05em',
                }}
              >
                {title}
              </Text>
              {tooltip && (
                <Tooltip label={tooltip}>
                  <ActionIcon size="sm" variant="subtle" color="gray">
                    <IconInfoCircle size={14} />
                  </ActionIcon>
                </Tooltip>
              )}
            </Group>
            <Text style={valueDisplayStyles}>
              {displayValue}
            </Text>
            {subtitle && (
              <Text
                size="xs"
                style={{
                  color: alphaColor(robloxColors.lightGray, 0.7),
                  marginTop: 4,
                }}
              >
                {subtitle}
              </Text>
            )}
          </Box>
          <Box style={iconContainerStyles}>
            <Box style={{ color: '#fff', fontSize: 32 }}>
              {icon}
            </Box>
          </Box>
        </Group>
        {trend && (
          <Group
            gap="xs"
            p="xs"
            style={{
              borderRadius: '8px',
              backgroundColor: alphaColor(getTrendColor(trend.direction), 0.1),
            }}
          >
            {trend.direction === 'up' ? (
              <IconTrendingUp size={18} color={getTrendColor(trend.direction)} />
            ) : trend.direction === 'down' ? (
              <IconTrendingDown size={18} color={getTrendColor(trend.direction)} />
            ) : null}
            <Text
              size="sm"
              fw={600}
              style={{ color: getTrendColor(trend.direction) }}
            >
              {trend.value > 0 ? '+' : ''}{trend.value}%
            </Text>
            <Text
              size="xs"
              style={{ color: alphaColor(robloxColors.lightGray, 0.7) }}
            >
              vs last week
            </Text>
          </Group>
        )}
      </Card>
    </motion.div>
  );
};
export default Roblox3DMetricCard;