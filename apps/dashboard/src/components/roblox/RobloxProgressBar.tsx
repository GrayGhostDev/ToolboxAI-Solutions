import React, { useState, useEffect } from 'react';
import { Box, Progress, Text, useMantineTheme, rem } from '@mantine/core';

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

// Keyframe animations defined as CSS strings
const animations = `
  @keyframes glow {
    0% {
      box-shadow: 0 0 5px currentColor;
    }
    50% {
      box-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
    }
    100% {
      box-shadow: 0 0 5px currentColor;
    }
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }

  @keyframes float {
    0% {
      transform: translateY(0px) rotate(0deg);
      opacity: 1;
    }
    100% {
      transform: translateY(-20px) rotate(360deg);
      opacity: 0;
    }
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'roblox-progress-bar-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = animations;
    document.head.appendChild(style);
  }
}

const FloatingParticle: React.FC<{ delay: string; left: string; color: string }> = ({ delay, left, color }) => {
  const floatingParticleStyle: React.CSSProperties = {
    position: 'absolute',
    width: 4,
    height: 4,
    backgroundColor: color,
    borderRadius: '50%',
    animation: 'float 3s ease-out infinite',
    left,
    animationDelay: delay
  };

  return <Box style={floatingParticleStyle} />;
};

export const RobloxProgressBar: React.FunctionComponent<RobloxProgressBarProps> = ({
  current,
  max,
  label,
  showPercentage = true,
  animated = true,
  color = 'blue',
  size = 'medium',
  variant = 'linear'
}) => {
  const theme = useMantineTheme();
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
    blue: theme.colors.blue[6],
    violet: theme.colors.violet[6],
    green: theme.colors.green[6],
    yellow: theme.colors.yellow[6],
    red: theme.colors.red[6]
  };

  const mainColor = colorStyles[color];

  if (variant === 'circular') {
    const circularSize = size === 'small' ? 60 : size === 'medium' ? 80 : 100;

    const circularContainerStyle: React.CSSProperties = {
      position: 'relative',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column'
    };

    return (
      <Box style={circularContainerStyle}>
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
              color: mainColor,
              textShadow: `0 0 10px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.5)`
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

  const progressContainerStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    animation: isComplete ? 'pulse 0.6s ease-in-out' : 'none'
  };

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
                color: mainColor,
                textShadow: `0 0 5px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.5)`
              }}
            >
              {Math.round(progress)}%
            </Text>
          )}
        </Box>
      )}

      <Box style={progressContainerStyle}>
        <Progress
          value={progress}
          size={sizeStyles[size].height}
          radius="md"
          color={color}
          style={{
            background: `rgba(${parseInt(theme.colors.gray[6].slice(1,3), 16)}, ${parseInt(theme.colors.gray[6].slice(3,5), 16)}, ${parseInt(theme.colors.gray[6].slice(5,7), 16)}, 0.3)`,
            position: 'relative'
          }}
          styles={{
            bar: {
              background: `linear-gradient(90deg, ${mainColor}, rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.8))`,
              boxShadow: `0 0 10px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.5)`,
              borderRadius: rem(6),
              animation: isNearComplete ? 'pulse 1s ease-in-out infinite' : 'none'
            }
          }}
        />

        {/* Shimmer effect overlay */}
        <Box
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
            animation: 'shimmer 2s infinite',
            pointerEvents: 'none',
            borderRadius: rem(6)
          }}
        />

        {animated && isNearComplete && (
          <>
            <FloatingParticle delay="0s" left="10%" color={mainColor} />
            <FloatingParticle delay="0.5s" left="30%" color={mainColor} />
            <FloatingParticle delay="1s" left="50%" color={mainColor} />
            <FloatingParticle delay="1.5s" left="70%" color={mainColor} />
            <FloatingParticle delay="2s" left="90%" color={mainColor} />
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
            animation: 'pulse 0.5s ease-in-out'
          }}
        >
          🎉 Level Complete! 🎉
        </Text>
      )}
    </Box>
  );
};
