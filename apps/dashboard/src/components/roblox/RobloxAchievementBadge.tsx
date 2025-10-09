import React, { useState } from 'react';
import {
  Box,
  Text,
  Tooltip,
  useMantineTheme,
  rem,
  Progress
} from '@mantine/core';
import { IconTrophy, IconStar, IconFlame, IconSchool, IconDeviceGamepad } from '@tabler/icons-react';

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

  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-5px);
    }
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
    100% {
      transform: scale(1);
    }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'roblox-achievement-badge-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = animations;
    document.head.appendChild(style);
  }
}

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

const getIconComponent = (iconName: string) => {
  const iconMap: { [key: string]: React.ComponentType<any> } = {
    'trophy': IconTrophy,
    'star': IconStar,
    'fire': IconFlame,
    'school': IconSchool,
    'game': IconDeviceGamepad,
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

  const IconComponent = getIconComponent(achievement.icon);
  const progress = achievement.progress && achievement.maxProgress
    ? (achievement.progress / achievement.maxProgress) * 100
    : 0;

  const sizeStyles = {
    small: { width: 60, height: 60, fontSize: rem(24) },
    medium: { width: 80, height: 80, fontSize: rem(32) },
    large: { width: 100, height: 100, fontSize: rem(40) }
  };

  const rarityColor = rarityColors[achievement.rarity];
  const rarityGradient = rarityGradients[achievement.rarity];

  const badgeStyle: React.CSSProperties = {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    background: achievement.unlocked ? rarityGradient : `linear-gradient(135deg, ${theme.colors.gray[8]}, ${theme.colors.gray[9]})`,
    border: `3px solid ${achievement.unlocked ? rarityColor : theme.colors.gray[6]}`,
    boxShadow: achievement.unlocked
      ? `0 0 20px rgba(${parseInt(rarityColor.slice(1,3), 16)}, ${parseInt(rarityColor.slice(3,5), 16)}, ${parseInt(rarityColor.slice(5,7), 16)}, 0.5), inset 0 0 20px rgba(255, 255, 255, 0.1)`
      : `0 0 10px rgba(${parseInt(theme.colors.gray[6].slice(1,3), 16)}, ${parseInt(theme.colors.gray[6].slice(3,5), 16)}, ${parseInt(theme.colors.gray[6].slice(5,7), 16)}, 0.3)`,
    filter: achievement.unlocked ? 'none' : 'grayscale(100%)',
    animation: animated && achievement.unlocked ? 'float 3s ease-in-out infinite' : 'none',
    transform: isHovered ? 'scale(1.1) translateY(-5px)' : 'none',
    ...sizeStyles[size]
  };

  const progressRingStyle: React.CSSProperties = {
    position: 'absolute',
    top: -3,
    left: -3,
    right: -3,
    bottom: -3,
    borderRadius: '50%',
    zIndex: -2,
    background: `conic-gradient(from 0deg, ${theme.colors.blue[6]} ${progress * 3.6}deg, transparent ${progress * 3.6}deg)`
  };

  const rarityIndicatorStyle: React.CSSProperties = {
    position: 'absolute',
    top: -8,
    right: -8,
    width: 16,
    height: 16,
    borderRadius: '50%',
    background: rarityGradient,
    border: '2px solid white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: rem(10),
    fontWeight: 'bold',
    color: 'white',
    textShadow: '0 1px 2px rgba(0,0,0,0.5)'
  };

  const glowOverlayStyle: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    background: `radial-gradient(circle, transparent 30%, rgba(${parseInt(rarityColor.slice(1,3), 16)}, ${parseInt(rarityColor.slice(3,5), 16)}, ${parseInt(rarityColor.slice(5,7), 16)}, 0.3) 100%)`,
    animation: 'glow 2s ease-in-out infinite'
  };

  const spinningRingStyle: React.CSSProperties = {
    content: '""',
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: '50%',
    background: `conic-gradient(from 0deg, ${rarityColor}, transparent, ${rarityColor})`,
    zIndex: -1,
    animation: 'spin 3s linear infinite'
  };

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
        style={badgeStyle}
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {showProgress && !achievement.unlocked && progress > 0 && (
          <Box style={progressRingStyle} />
        )}

        {achievement.unlocked && (
          <Box style={spinningRingStyle} />
        )}

        <IconComponent
          size={size === 'small' ? 24 : size === 'medium' ? 32 : 40}
          color={achievement.unlocked ? 'white' : theme.colors.gray[5]}
          style={{
            filter: achievement.unlocked ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' : 'none',
            animation: isHovered && achievement.unlocked ? 'pulse 0.6s ease-in-out' : 'none'
          }}
        />

        <Box style={rarityIndicatorStyle}>
          {achievement.rarity.charAt(0).toUpperCase()}
        </Box>

        {achievement.unlocked && (
          <Box style={glowOverlayStyle} />
        )}
      </Box>
    </Tooltip>
  );
};
