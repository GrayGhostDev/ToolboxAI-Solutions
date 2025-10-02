import React, { useState, useEffect } from 'react';
import { Box, Progress, Text, useMantineTheme, rem, keyframes } from '@mantine/core';
// import { createStyles } from '@mantine/emotion'; // Removed - using inline styles instead

interface RobloxProgressBarProps {
  current: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  animated?: boolean;
  color?: 'blue' | 'violet' | 'green' | 'yellow' | 'red';
  size?: 'small' | 'medium' | 'large';
  variant?: 'linear' | 'circular';
}

// Animated glow effect
const glowAnimation = keyframes({
  '0%': {
    boxShadow: '0 0 5px currentColor'
  },
  '50%': {
    boxShadow: '0 0 20px currentColor, 0 0 30px currentColor'
  },
  '100%': {
    boxShadow: '0 0 5px currentColor'
  }
});

// Pulse animation for completion
const pulseAnimation = keyframes({
  '0%': {
    transform: 'scale(1)'
  },
  '50%': {
    transform: 'scale(1.05)'
  },
  '100%': {
    transform: 'scale(1)'
  }
});

// Floating particles animation
const floatAnimation = keyframes({
  '0%': {
    transform: 'translateY(0px) rotate(0deg)',
    opacity: 1
  },
  '100%': {
    transform: 'translateY(-20px) rotate(360deg)',
    opacity: 0
  }
});

const useStyles = createStyles((theme) => ({
  progressContainer: {
    position: 'relative',
    width: '100%',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: -2,
      left: -2,
      right: -2,
      bottom: -2,
      background: `linear-gradient(45deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]}, ${theme.colors.blue[6]})`,
      borderRadius: 'inherit',
      zIndex: -1,
      animation: `${glowAnimation} 2s ease-in-out infinite`
    }
  },
  floatingParticle: {
    position: 'absolute',
    width: 4,
    height: 4,
    backgroundColor: theme.colors.blue[6],
    borderRadius: '50%',
    animation: `${floatAnimation} 3s ease-out infinite`
  },
  circularContainer: {
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
}));

const FloatingParticle: React.FC<{ delay: string; left: string }> = ({ delay, left }) => {
  const { classes } = useStyles();
  return (
    <Box
      className={classes.floatingParticle}
      style={{
        left,
        animationDelay: delay
      }}
    />
  );
};

export const RobloxProgressBar: React.FunctionComponent<RobloxProgressBarProps> = ({
  current,
  max,
  label,
  showPercentage = true,
  animated = true,
  color = 'primary',
  size = 'medium',
  variant = 'linear'
}) => {
  const theme = useMantineTheme();
  const { classes } = useStyles();
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
    primary: theme.colors.blue[6],
    secondary: theme.colors.violet[6],
    success: theme.colors.green[6],
    warning: theme.colors.yellow[6],
    error: theme.colors.red[6]
  };

  if (variant === 'circular') {
    const circularSize = size === 'small' ? 60 : size === 'medium' ? 80 : 100;

    return (
      <Box className={classes.circularContainer}>
        <Box
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: circularSize,
            height: circularSize
          }}
        >
          <Progress
            value={progress}
            size={circularSize}
            radius="xl"
            color={color}
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%'
            }}
          />
          <Text
            size="lg"
            fw={700}
            style={{
              color: colorStyles[color],
              textShadow: `0 0 10px ${theme.fn.rgba(colorStyles[color], 0.5)}`
            }}
          >
            {Math.round(progress)}%
          </Text>
        </Box>
        {label && (
          <Text
            size="sm"
            ta="center"
            c="dimmed"
            fw={600}
            mt="xs"
          >
            {label}
          </Text>
        )}
      </Box>
    );
  }

  return (
    <Box w="100%">
      {label && (
        <Box style={{ display: 'flex', justifyContent: 'space-between', marginBottom: rem(8) }}>
          <Text
            size="sm"
            fw={600}
          >
            {label}
          </Text>
          {showPercentage && (
            <Text
              size="sm"
              fw={700}
              style={{
                color: colorStyles[color],
                textShadow: `0 0 5px ${theme.fn.rgba(colorStyles[color], 0.5)}`
              }}
            >
              {Math.round(progress)}%
            </Text>
          )}
        </Box>
      )}

      <Box
        className={classes.progressContainer}
        style={{
          animation: isComplete ? `${pulseAnimation} 0.6s ease-in-out` : 'none'
        }}
      >
        <Progress
          value={progress}
          size={sizeStyles[size].height}
          radius="md"
          color={color}
          style={{
            background: theme.fn.rgba(theme.colors.gray[6], 0.3)
          }}
          styles={{
            bar: {
              background: `linear-gradient(90deg, ${colorStyles[color]}, ${theme.fn.rgba(colorStyles[color], 0.8)})`,
              boxShadow: `0 0 10px ${theme.fn.rgba(colorStyles[color], 0.5)}`,
              borderRadius: rem(6),
              animation: isNearComplete ? `${pulseAnimation} 1s ease-in-out infinite` : 'none',
              '&::after': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                animation: 'shimmer 2s infinite'
              }
            }
          }}
        />

        {animated && isNearComplete && (
          <>
            <FloatingParticle delay="0s" left="10%" />
            <FloatingParticle delay="0.5s" left="30%" />
            <FloatingParticle delay="1s" left="50%" />
            <FloatingParticle delay="1.5s" left="70%" />
            <FloatingParticle delay="2s" left="90%" />
          </>
        )}
      </Box>

      {isComplete && (
        <Text
          size="xs"
          ta="center"
          mt="xs"
          fw={700}
          style={{
            color: theme.colors.green[6],
            animation: `${pulseAnimation} 0.5s ease-in-out`
          }}
        >
          🎉 Level Complete! 🎉
        </Text>
      )}
    </Box>
  );
};
