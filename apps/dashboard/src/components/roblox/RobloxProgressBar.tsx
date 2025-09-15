import React, { useState, useEffect } from 'react';
import { Box, LinearProgress, Typography, useTheme, alpha } from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';

interface RobloxProgressBarProps {
  current: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  animated?: boolean;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
  variant?: 'linear' | 'circular';
}

// Animated glow effect
const glowAnimation = keyframes`
  0% {
    box-shadow: 0 0 5px currentColor;
  }
  50% {
    box-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
  }
  100% {
    box-shadow: 0 0 5px currentColor;
  }
`;

// Pulse animation for completion
const pulseAnimation = keyframes`
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
`;

// Floating particles animation
const floatAnimation = keyframes`
  0% {
    transform: translateY(0px) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(-20px) rotate(360deg);
    opacity: 0;
  }
`;

const StyledProgressContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main}, ${theme.palette.primary.main})`,
    borderRadius: 'inherit',
    zIndex: -1,
    animation: `${glowAnimation} 2s ease-in-out infinite`,
  }
}));

const StyledLinearProgress = styled(LinearProgress)(({ theme }) => ({
  height: 12,
  borderRadius: 6,
  backgroundColor: alpha(theme.palette.background.paper, 0.3),
  '& .MuiLinearProgress-bar': {
    borderRadius: 6,
    background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    boxShadow: `0 0 10px ${alpha(theme.palette.primary.main, 0.5)}`,
    position: 'relative',
    overflow: 'hidden',
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
      animation: 'shimmer 2s infinite',
    }
  }
}));

const FloatingParticle = styled(Box)(({ theme }) => ({
  position: 'absolute',
  width: 4,
  height: 4,
  backgroundColor: theme.palette.primary.main,
  borderRadius: '50%',
  animation: `${floatAnimation} 3s ease-out infinite`,
  '&:nth-of-type(1)': { left: '10%', animationDelay: '0s' },
  '&:nth-of-type(2)': { left: '30%', animationDelay: '0.5s' },
  '&:nth-of-type(3)': { left: '50%', animationDelay: '1s' },
  '&:nth-of-type(4)': { left: '70%', animationDelay: '1.5s' },
  '&:nth-of-type(5)': { left: '90%', animationDelay: '2s' },
}));

const CircularProgressContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  '& .MuiCircularProgress-root': {
    color: theme.palette.primary.main,
    filter: `drop-shadow(0 0 10px ${alpha(theme.palette.primary.main, 0.5)})`,
  }
}));

export const RobloxProgressBar: React.FC<RobloxProgressBarProps> = ({
  current,
  max,
  label,
  showPercentage = true,
  animated = true,
  color = 'primary',
  size = 'medium',
  variant = 'linear'
}) => {
  const theme = useTheme();
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  
  const percentage = Math.min((current / max) * 100, 100);
  const isNearComplete = percentage >= 90;
  
  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => {
        setProgress(percentage);
        if (percentage >= 100) {
          setIsComplete(true);
        }
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setProgress(percentage);
    }
  }, [percentage, animated]);

  const sizeStyles = {
    small: { height: 8, fontSize: '0.75rem' },
    medium: { height: 12, fontSize: '0.875rem' },
    large: { height: 16, fontSize: '1rem' }
  };

  const colorStyles = {
    primary: theme.palette.primary.main,
    secondary: theme.palette.secondary.main,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main
  };

  if (variant === 'circular') {
    return (
      <CircularProgressContainer>
        <Box
          sx={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: size === 'small' ? 60 : size === 'medium' ? 80 : 100,
            height: size === 'small' ? 60 : size === 'medium' ? 80 : 100,
          }}
        >
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              backgroundColor: 'transparent',
              '& .MuiLinearProgress-bar': {
                borderRadius: '50%',
                background: `conic-gradient(from 0deg, ${colorStyles[color]}, ${alpha(colorStyles[color], 0.3)})`,
              }
            }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: colorStyles[color],
              textShadow: `0 0 10px ${alpha(colorStyles[color], 0.5)}`,
            }}
          >
            {Math.round(progress)}%
          </Typography>
        </Box>
        {label && (
          <Typography
            variant="body2"
            sx={{
              mt: 1,
              textAlign: 'center',
              color: theme.palette.text.secondary,
              fontWeight: 600,
            }}
          >
            {label}
          </Typography>
        )}
      </CircularProgressContainer>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {label && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: theme.palette.text.primary,
            }}
          >
            {label}
          </Typography>
          {showPercentage && (
            <Typography
              variant="body2"
              sx={{
                fontWeight: 700,
                color: colorStyles[color],
                textShadow: `0 0 5px ${alpha(colorStyles[color], 0.5)}`,
              }}
            >
              {Math.round(progress)}%
            </Typography>
          )}
        </Box>
      )}
      
      <StyledProgressContainer
        sx={{
          animation: isComplete ? `${pulseAnimation} 0.6s ease-in-out` : 'none',
        }}
      >
        <StyledLinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: sizeStyles[size].height,
            '& .MuiLinearProgress-bar': {
              background: `linear-gradient(90deg, ${colorStyles[color]}, ${alpha(colorStyles[color], 0.8)})`,
              ...(isNearComplete && {
                animation: `${pulseAnimation} 1s ease-in-out infinite`,
              }),
            }
          }}
        />
        
        {animated && isNearComplete && (
          <>
            <FloatingParticle />
            <FloatingParticle />
            <FloatingParticle />
            <FloatingParticle />
            <FloatingParticle />
          </>
        )}
      </StyledProgressContainer>
      
      {isComplete && (
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            textAlign: 'center',
            mt: 1,
            color: theme.palette.success.main,
            fontWeight: 700,
            animation: `${pulseAnimation} 0.5s ease-in-out`,
          }}
        >
          🎉 Level Complete! 🎉
        </Typography>
      )}
    </Box>
  );
};
