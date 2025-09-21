import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import Tooltip from '@mui/material/Tooltip';
import Zoom from '@mui/material/Zoom';
import { keyframes } from '@mui/material/styles';
import { styled } from '@mui/material/styles';
import { EmojiEvents, Star, LocalFireDepartment, School, SportsEsports } from '@mui/icons-material';

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
const glowAnimation = keyframes`
  0% { box-shadow: 0 0 5px currentColor; }
  50% { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
  100% { box-shadow: 0 0 5px currentColor; }
`;

const floatAnimation = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
`;

const spinAnimation = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const pulseAnimation = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
`;

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

const StyledBadge = styled(Box)(({ theme, rarity, unlocked, animated }: any) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '50%',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  background: unlocked ? rarityGradients[rarity] : `linear-gradient(135deg, ${theme.palette.grey[800]}, ${theme.palette.grey[900]})`,
  border: `3px solid ${unlocked ? rarityColors[rarity] : theme.palette.grey[600]}`,
  boxShadow: unlocked 
    ? `0 0 20px ${alpha(rarityColors[rarity], 0.5)}, inset 0 0 20px ${alpha('#fff', 0.1)}`
    : `0 0 10px ${alpha(theme.palette.grey[600], 0.3)}`,
  filter: unlocked ? 'none' : 'grayscale(100%)',
  animation: animated && unlocked ? `${floatAnimation} 3s ease-in-out infinite` : 'none',
  
  '&:hover': {
    transform: 'scale(1.1) translateY(-5px)',
    boxShadow: unlocked 
      ? `0 0 30px ${alpha(rarityColors[rarity], 0.8)}, 0 10px 30px ${alpha(rarityColors[rarity], 0.3)}`
      : `0 0 15px ${alpha(theme.palette.grey[600], 0.5)}`,
    animation: unlocked ? `${pulseAnimation} 0.6s ease-in-out` : 'none',
  },
  
  '&::before': unlocked ? {
    content: '""',
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: '50%',
    background: `conic-gradient(from 0deg, ${rarityColors[rarity]}, transparent, ${rarityColors[rarity]})`,
    zIndex: -1,
    animation: `${spinAnimation} 3s linear infinite`,
  } : {},
}));

const ProgressRing = styled(Box)(({ theme, progress }: any) => ({
  position: 'absolute',
  top: -3,
  left: -3,
  right: -3,
  bottom: -3,
  borderRadius: '50%',
  background: `conic-gradient(from 0deg, ${theme.palette.primary.main} ${progress * 3.6}deg, transparent ${progress * 3.6}deg)`,
  zIndex: -2,
}));

const RarityIndicator = styled(Box)(({ rarity }: any) => ({
  position: 'absolute',
  top: -8,
  right: -8,
  width: 16,
  height: 16,
  borderRadius: '50%',
  background: rarityGradients[rarity],
  border: '2px solid white',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '10px',
  fontWeight: 'bold',
  color: 'white',
  textShadow: '0 1px 2px rgba(0,0,0,0.5)',
}));

const getIconComponent = (iconName: string) => {
  const iconMap: { [key: string]: React.ComponentType<any> } = {
    'trophy': EmojiEvents,
    'star': Star,
    'fire': LocalFireDepartment,
    'school': School,
    'game': SportsEsports,
  };
  return iconMap[iconName] || EmojiEvents;
};

export const RobloxAchievementBadge: React.FunctionComponent<RobloxAchievementBadgeProps> = ({
  achievement,
  size = 'medium',
  animated = true,
  showProgress = true,
  onClick
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  
  const sizeStyles = {
    small: { width: 60, height: 60, fontSize: '1.5rem' },
    medium: { width: 80, height: 80, fontSize: '2rem' },
    large: { width: 100, height: 100, fontSize: '2.5rem' }
  };

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
      title={
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'white' }}>
            {achievement.name}
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
            {achievement.description}
          </Typography>
          {achievement.unlockedAt && (
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
              Unlocked: {achievement.unlockedAt.toLocaleDateString()}
            </Typography>
          )}
          {showProgress && achievement.progress && achievement.maxProgress && !achievement.unlocked && (
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
              Progress: {achievement.progress}/{achievement.maxProgress}
            </Typography>
          )}
        </Box>
      }
      arrow
      placement="top"
      TransitionComponent={Zoom}
    >
      <StyledBadge
        rarity={achievement.rarity}
        unlocked={achievement.unlocked}
        animated={animated}
        sx={sizeStyles[size]}
        onClick={(e: React.MouseEvent) => handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {showProgress && !achievement.unlocked && progress > 0 && (
          <ProgressRing progress={progress} />
        )}
        
        <IconComponent
          sx={{
            fontSize: 'inherit',
            color: achievement.unlocked ? 'white' : theme.palette.grey[500],
            filter: achievement.unlocked ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' : 'none',
            animation: isHovered && achievement.unlocked ? `${pulseAnimation} 0.6s ease-in-out` : 'none',
          }}
        />
        
        <RarityIndicator rarity={achievement.rarity}>
          {achievement.rarity.charAt(0).toUpperCase()}
        </RarityIndicator>
        
        {achievement.unlocked && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: `radial-gradient(circle, transparent 30%, ${alpha(rarityColors[achievement.rarity], 0.3)} 100%)`,
              animation: `${glowAnimation} 2s ease-in-out infinite`,
            }}
          />
        )}
      </StyledBadge>
    </Tooltip>
  );
};
