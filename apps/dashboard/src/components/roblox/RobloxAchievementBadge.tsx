import React, { useState } from 'react';
import {
  Box,
  Text,
  Tooltip,
  useMantineTheme,
  keyframes,
  rem,
  Progress
} from '@mantine/core';
import { createStyles } from '@mantine/emotion';
import { IconTrophy, IconStar, IconFlame, IconSchool, IconDeviceGamepad2 } from '@tabler/icons-react';

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlocked: boolean;
  unlockedAt?: Date;
  progress?: number;
  maxProgress?: number;
}

interface RobloxAchievementBadgeProps {
  achievement: Achievement;
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  showProgress?: boolean;
  onClick?: (achievement: Achievement) => void;
}

// Rarity-based animations
const glowAnimation = keyframes({
  '0%': { boxShadow: '0 0 5px currentColor' },
  '50%': { boxShadow: '0 0 20px currentColor, 0 0 30px currentColor' },
  '100%': { boxShadow: '0 0 5px currentColor' }
});

const floatAnimation = keyframes({
  '0%, 100%': { transform: 'translateY(0px)' },
  '50%': { transform: 'translateY(-5px)' }
});

const spinAnimation = keyframes({
  '0%': { transform: 'rotate(0deg)' },
  '100%': { transform: 'rotate(360deg)' }
});

const pulseAnimation = keyframes({
  '0%': { transform: 'scale(1)' },
  '50%': { transform: 'scale(1.1)' },
  '100%': { transform: 'scale(1)' }
});

const rarityColors = {
  common: '#9E9E9E',
  rare: '#2196F3',
  epic: '#9C27B0',
  legendary: '#FF9800'
};

const rarityGradients = {
  common: 'linear-gradient(135deg, #9E9E9E, #757575)',
  rare: 'linear-gradient(135deg, #2196F3, #1976D2)',
  epic: 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
  legendary: 'linear-gradient(135deg, #FF9800, #F57C00)'
};

const useStyles = createStyles((theme, { rarity, unlocked, animated, size }: { rarity: string; unlocked: boolean; animated: boolean; size: string }) => {
  const sizeStyles = {
    small: { width: 60, height: 60, fontSize: rem(24) },
    medium: { width: 80, height: 80, fontSize: rem(32) },
    large: { width: 100, height: 100, fontSize: rem(40) }
  };

  return {
    badge: {
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '50%',
      cursor: 'pointer',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      background: unlocked ? rarityGradients[rarity as keyof typeof rarityGradients] : `linear-gradient(135deg, ${theme.colors.gray[8]}, ${theme.colors.gray[9]})`,
      border: `3px solid ${unlocked ? rarityColors[rarity as keyof typeof rarityColors] : theme.colors.gray[6]}`,
      boxShadow: unlocked
        ? `0 0 20px ${theme.fn.rgba(rarityColors[rarity as keyof typeof rarityColors], 0.5)}, inset 0 0 20px ${theme.fn.rgba('#fff', 0.1)}`
        : `0 0 10px ${theme.fn.rgba(theme.colors.gray[6], 0.3)}`,
      filter: unlocked ? 'none' : 'grayscale(100%)',
      animation: animated && unlocked ? `${floatAnimation} 3s ease-in-out infinite` : 'none',
      ...sizeStyles[size as keyof typeof sizeStyles],

      '&:hover': {
        transform: 'scale(1.1) translateY(-5px)',
        boxShadow: unlocked
          ? `0 0 30px ${theme.fn.rgba(rarityColors[rarity as keyof typeof rarityColors], 0.8)}, 0 10px 30px ${theme.fn.rgba(rarityColors[rarity as keyof typeof rarityColors], 0.3)}`
          : `0 0 15px ${theme.fn.rgba(theme.colors.gray[6], 0.5)}`,
        animation: unlocked ? `${pulseAnimation} 0.6s ease-in-out` : 'none'
      },

      '&::before': unlocked ? {
        content: '""',
        position: 'absolute',
        top: -2,
        left: -2,
        right: -2,
        bottom: -2,
        borderRadius: '50%',
        background: `conic-gradient(from 0deg, ${rarityColors[rarity as keyof typeof rarityColors]}, transparent, ${rarityColors[rarity as keyof typeof rarityColors]})`,
        zIndex: -1,
        animation: `${spinAnimation} 3s linear infinite`
      } : {}
    },
    progressRing: {
      position: 'absolute',
      top: -3,
      left: -3,
      right: -3,
      bottom: -3,
      borderRadius: '50%',
      zIndex: -2
    },
    rarityIndicator: {
      position: 'absolute',
      top: -8,
      right: -8,
      width: 16,
      height: 16,
      borderRadius: '50%',
      background: rarityGradients[rarity as keyof typeof rarityGradients],
      border: '2px solid white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: rem(10),
      fontWeight: 'bold',
      color: 'white',
      textShadow: '0 1px 2px rgba(0,0,0,0.5)'
    },
    glowOverlay: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: '100%',
      height: '100%',
      borderRadius: '50%',
      background: `radial-gradient(circle, transparent 30%, ${theme.fn.rgba(rarityColors[rarity as keyof typeof rarityColors], 0.3)} 100%)`,
      animation: `${glowAnimation} 2s ease-in-out infinite`
    }
  };
});

const getIconComponent = (iconName: string) => {
  const iconMap: { [key: string]: React.ComponentType<any> } = {
    'trophy': IconTrophy,
    'star': IconStar,
    'fire': IconFlame,
    'school': IconSchool,
    'game': IconDeviceGamepad2,
  };
  return iconMap[iconName] || IconTrophy;
};

export const RobloxAchievementBadge: React.FunctionComponent<RobloxAchievementBadgeProps> = ({
  achievement,
  size = 'medium',
  animated = true,
  showProgress = true,
  onClick
}) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);
  const { classes } = useStyles({ rarity: achievement.rarity, unlocked: achievement.unlocked, animated, size });

  const IconComponent = getIconComponent(achievement.icon);
  const progress = achievement.progress && achievement.maxProgress
    ? (achievement.progress / achievement.maxProgress) * 100
    : 0;

  const handleClick = () => {
    if (onClick) {
      onClick(achievement);
    }
  };

  return (
    <Tooltip
      label={
        <Box>
          <Text size="sm" fw={700} c="white">
            {achievement.name}
          </Text>
          <Text size="sm" style={{ color: 'rgba(255,255,255,0.8)' }}>
            {achievement.description}
          </Text>
          {achievement.unlockedAt && (
            <Text size="xs" style={{ color: 'rgba(255,255,255,0.6)' }}>
              Unlocked: {achievement.unlockedAt.toLocaleDateString()}
            </Text>
          )}
          {showProgress && achievement.progress && achievement.maxProgress && !achievement.unlocked && (
            <Text size="xs" style={{ color: 'rgba(255,255,255,0.6)' }}>
              Progress: {achievement.progress}/{achievement.maxProgress}
            </Text>
          )}
        </Box>
      }
      withArrow
      position="top"
    >
      <Box
        className={classes.badge}
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {showProgress && !achievement.unlocked && progress > 0 && (
          <Progress
            value={progress}
            size="xl"
            radius="xl"
            className={classes.progressRing}
            style={{
              background: `conic-gradient(from 0deg, ${theme.colors.blue[6]} ${progress * 3.6}deg, transparent ${progress * 3.6}deg)`
            }}
          />
        )}

        <IconComponent
          size={size === 'small' ? 24 : size === 'medium' ? 32 : 40}
          color={achievement.unlocked ? 'white' : theme.colors.gray[5]}
          style={{
            filter: achievement.unlocked ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' : 'none',
            animation: isHovered && achievement.unlocked ? `${pulseAnimation} 0.6s ease-in-out` : 'none'
          }}
        />

        <Box className={classes.rarityIndicator}>
          {achievement.rarity.charAt(0).toUpperCase()}
        </Box>

        {achievement.unlocked && (
          <Box className={classes.glowOverlay} />
        )}
      </Box>
    </Tooltip>
  );
};