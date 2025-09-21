import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import { keyframes } from '@mui/material/styles';
import { styled } from '@mui/material/styles';
interface Simple3DIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  onClick?: () => void;
  description?: string;
}
// Animations
const floatAnimation = keyframes`
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-3px) rotate(2deg); }
`;
const pulseAnimation = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;
const glowAnimation = keyframes`
  0% { box-shadow: 0 0 5px currentColor; }
  50% { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
  100% { box-shadow: 0 0 5px currentColor; }
`;
const StyledIconContainer = styled(Box)(({ theme, size }: any) => {
  const sizeStyles = {
    small: { width: 60, height: 60, fontSize: '2rem' },
    medium: { width: 80, height: 80, fontSize: '2.5rem' },
    large: { width: 100, height: 100, fontSize: '3rem' }
  };
  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    background: `linear-gradient(145deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    border: `3px solid ${theme.palette.primary.main}`,
    boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.3)}`,
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    overflow: 'hidden',
    ...sizeStyles[size],
    '&:hover': {
      transform: 'translateY(-5px) scale(1.1)',
      boxShadow: `0 12px 35px ${alpha(theme.palette.primary.main, 0.5)}`,
      borderColor: theme.palette.secondary.main,
    },
    animation: `${floatAnimation} 3s ease-in-out infinite`,
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(45deg, transparent, ${alpha('#fff', 0.2)}, transparent)`,
      transform: 'translateX(-100%)',
      transition: 'transform 0.6s ease',
    },
    '&:hover::before': {
      transform: 'translateX(100%)',
    },
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(135deg, ${alpha('#fff', 0.1)}, transparent, ${alpha('#fff', 0.1)})`,
      borderRadius: '50%',
      opacity: 0,
      transition: 'opacity 0.3s ease',
    },
    '&:hover::after': {
      opacity: 1,
    },
  };
});
// Icon mapping based on the parsed JSON data
const iconMap: { [key: string]: { emoji: string; color: string; description: string } } = {
  'ABC_CUBE': { emoji: '🧩', color: '#4CAF50', description: 'ABC Learning Cube' },
  'BACKPACK': { emoji: '🎒', color: '#FF9800', description: 'Student Backpack' },
  'BADGE': { emoji: '🏅', color: '#E91E63', description: 'Achievement Badge' },
  'BASKETBALL': { emoji: '🏀', color: '#FF5722', description: 'Sports Basketball' },
  'BOARD': { emoji: '📋', color: '#2196F3', description: 'Learning Board' },
  'BOOKS': { emoji: '📚', color: '#9C27B0', description: 'Educational Books' },
  'BRUSH_PAINT': { emoji: '🎨', color: '#FFC107', description: 'Paint Brush' },
  'CIRCLE_RULER': { emoji: '📏', color: '#607D8B', description: 'Circle Ruler' },
  'CRAYON': { emoji: '🖍️', color: '#FF5722', description: 'Coloring Crayon' },
  'ERASER': { emoji: '🧽', color: '#9E9E9E', description: 'Eraser Tool' },
  'GRADUATION_CAP': { emoji: '🎓', color: '#3F51B5', description: 'Graduation Cap' },
  'LAMP': { emoji: '💡', color: '#FFEB3B', description: 'Study Lamp' },
  'LIGHT_BULB': { emoji: '💡', color: '#FFC107', description: 'Light Bulb' },
  'OPEN_BOOK': { emoji: '📖', color: '#4CAF50', description: 'Open Book' },
  'PAPER': { emoji: '📄', color: '#FFFFFF', description: 'Paper Sheet' },
  'PENCIL': { emoji: '✏️', color: '#FF9800', description: 'Pencil Tool' },
  'RULER': { emoji: '📐', color: '#607D8B', description: 'Measuring Ruler' },
  'SOCCER_BALL': { emoji: '⚽', color: '#4CAF50', description: 'Soccer Ball' },
  'TRIANGLE_RULER': { emoji: '📐', color: '#795548', description: 'Triangle Ruler' },
  'TROPHY': { emoji: '🏆', color: '#FFD700', description: 'Trophy Award' },
  'STAR': { emoji: '⭐', color: '#FFC107', description: 'Star Achievement' },
  'ROCKET': { emoji: '🚀', color: '#E91E63', description: 'Rocket Launch' },
  'ASSESSMENT': { emoji: '📝', color: '#2196F3', description: 'Assessment Test' },
  'SETTINGS': { emoji: '⚙️', color: '#607D8B', description: 'Settings Gear' },
  'REFRESH': { emoji: '🔄', color: '#4CAF50', description: 'Refresh Data' },
  'SPORTS_ESPORTS': { emoji: '🎮', color: '#9C27B0', description: 'Gaming Controller' },
};
export const Simple3DIcon: React.FunctionComponent<Simple3DIconProps> = ({
  iconName,
  size = 'medium',
  animated = true,
  onClick,
  description
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const iconData = iconMap[iconName] || iconMap['TROPHY'];
  const displayDescription = description || iconData.description;
  return (
    <StyledIconContainer
      size={size}
      onClick={(e: React.MouseEvent) => onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      sx={{
        background: `linear-gradient(145deg, ${iconData.color}, ${alpha(iconData.color, 0.7)})`,
        borderColor: iconData.color,
        boxShadow: `0 8px 25px ${alpha(iconData.color, 0.3)}`,
        '&:hover': {
          boxShadow: `0 12px 35px ${alpha(iconData.color, 0.5)}`,
          borderColor: iconData.color,
        }
      }}
    >
      <Typography
        sx={{
          fontSize: 'inherit',
          filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
          transition: 'all 0.3s ease',
          textShadow: '0 2px 4px rgba(0,0,0,0.3)',
        }}
      >
        {iconData.emoji}
      </Typography>
      {displayDescription && (
        <Typography
          variant="caption"
          sx={{
            position: 'absolute',
            bottom: -25,
            left: '50%',
            transform: 'translateX(-50%)',
            whiteSpace: 'nowrap',
            fontSize: '0.7rem',
            fontWeight: 600,
            color: theme.palette.text.primary,
            background: alpha(theme.palette.background.paper, 0.9),
            padding: '2px 8px',
            borderRadius: 1,
            border: `1px solid ${alpha(iconData.color, 0.3)}`,
            opacity: isHovered ? 1 : 0,
            transition: 'opacity 0.3s ease',
            pointerEvents: 'none',
          }}
        >
          {displayDescription}
        </Typography>
      )}
    </StyledIconContainer>
  );
};