import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import { styled, keyframes } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { robloxColors } from '../..//robloxTheme';
import { motion } from 'framer-motion';
const float = keyframes`
  0%, 100% { transform: translateY(0px) rotateX(0deg); }
  50% { transform: translateY(-10px) rotateX(5deg); }
`;
const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 ${alpha(robloxColors.primary, 0.7)}; }
  70% { box-shadow: 0 0 0 10px ${alpha(robloxColors.primary, 0)}; }
  100% { box-shadow: 0 0 0 0 ${alpha(robloxColors.primary, 0)}; }
`;
const shine = keyframes`
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
`;
const StyledCard = styled(Card)<{ glowcolor?: string; isHovered?: boolean }>(({ theme, glowcolor, isHovered }) => ({
  background: `linear-gradient(135deg, ${robloxColors.dark} 0%, ${robloxColors.darkGray} 100%)`,
  border: `2px solid ${glowcolor || robloxColors.primary}`,
  borderRadius: '16px',
  position: 'relative',
  overflow: 'visible',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  transform: isHovered ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
  animation: isHovered ? `${float} 2s ease-in-out infinite` : 'none',
  cursor: 'pointer',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `linear-gradient(105deg, transparent 40%, ${alpha(glowcolor || robloxColors.primary, 0.1)} 50%, transparent 60%)`,
    backgroundSize: '200% 100%',
    animation: isHovered ? `${shine} 2s linear infinite` : 'none',
    borderRadius: '16px',
    pointerEvents: 'none',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '-4px',
    left: '-4px',
    right: '-4px',
    bottom: '-4px',
    background: `linear-gradient(45deg, ${glowcolor || robloxColors.primary}, ${robloxColors.secondary})`,
    borderRadius: '20px',
    opacity: isHovered ? 0.8 : 0,
    filter: 'blur(12px)',
    transition: 'opacity 0.3s ease',
    zIndex: -1,
  },
  boxShadow: isHovered
    ? `0 20px 40px ${alpha(glowcolor || robloxColors.primary, 0.4)}, inset 0 1px 0 ${alpha('#fff', 0.1)}`
    : `0 4px 12px ${alpha('#000', 0.2)}, inset 0 1px 0 ${alpha('#fff', 0.05)}`,
}));
const IconContainer = styled(Box)<{ bgcolor?: string }>(({ bgcolor }) => ({
  width: 64,
  height: 64,
  borderRadius: '12px',
  background: `linear-gradient(135deg, ${bgcolor || robloxColors.primary} 0%, ${alpha(bgcolor || robloxColors.primary, 0.8)} 100%)`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  boxShadow: `0 4px 12px ${alpha(bgcolor || robloxColors.primary, 0.3)}`,
  '& svg': {
    fontSize: 32,
    color: '#fff',
    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '100%',
    height: '100%',
    borderRadius: '12px',
    border: `2px solid ${alpha('#fff', 0.2)}`,
    animation: `${pulse} 2s infinite`,
  },
}));
const ValueDisplay = styled(Typography)(({ theme }) => ({
  fontSize: '2.5rem',
  fontWeight: 800,
  background: `linear-gradient(135deg, #fff 0%, ${robloxColors.accent} 100%)`,
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  textShadow: '0 2px 8px rgba(0,0,0,0.1)',
  letterSpacing: '-0.02em',
  lineHeight: 1,
}));
const TrendIndicator = styled(Box)<{ trend: 'up' | 'down' | 'neutral' }>(({ trend }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '4px 8px',
  borderRadius: '8px',
  background: trend === 'up'
    ? alpha(robloxColors.success, 0.1)
    : trend === 'down'
    ? alpha(robloxColors.error, 0.1)
    : alpha(robloxColors.gray, 0.1),
  '& svg': {
    fontSize: 18,
    color: trend === 'up'
      ? robloxColors.success
      : trend === 'down'
      ? robloxColors.error
      : robloxColors.gray,
  },
}));
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
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <StyledCard
        glowcolor={color}
        isHovered={isHovered}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={(e: React.MouseEvent) => onClick}
      >
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <Typography
                  variant="h6"
                  sx={{
                    color: robloxColors.lightGray,
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {title}
                </Typography>
                {tooltip && (
                  <Tooltip title={tooltip} arrow placement="top">
                    <IconButton size="small" sx={{ p: 0.5, color: robloxColors.gray }}>
                      <InfoOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
              <ValueDisplay>{displayValue}</ValueDisplay>
              {subtitle && (
                <Typography
                  variant="body2"
                  sx={{
                    color: alpha(robloxColors.lightGray, 0.7),
                    mt: 0.5,
                    fontSize: '0.75rem',
                  }}
                >
                  {subtitle}
                </Typography>
              )}
            </Box>
            <IconContainer bgcolor={color}>
              {icon}
            </IconContainer>
          </Box>
          {trend && (
            <TrendIndicator trend={trend.direction}>
              {trend.direction === 'up' ? (
                <TrendingUpIcon />
              ) : trend.direction === 'down' ? (
                <TrendingDownIcon />
              ) : null}
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: trend.direction === 'up'
                    ? robloxColors.success
                    : trend.direction === 'down'
                    ? robloxColors.error
                    : robloxColors.gray,
                }}
              >
                {trend.value > 0 ? '+' : ''}{trend.value}%
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: alpha(robloxColors.lightGray, 0.7),
                  ml: 0.5,
                }}
              >
                vs last week
              </Typography>
            </TrendIndicator>
          )}
        </CardContent>
      </StyledCard>
    </motion.div>
  );
};
export default Roblox3DMetricCard;