import React, { useState } from 'react';
import { Box, Text } from '@mantine/core';

interface Simple3DIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  onClick?: () => void;
  description?: string;
}

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
  const [isHovered, setIsHovered] = useState(false);
  const iconData = iconMap[iconName] || iconMap['TROPHY'];
  const displayDescription = description || iconData.description;

  const getSizeStyles = () => {
    const sizes = {
      small: { width: 60, height: 60, fontSize: '2rem' },
      medium: { width: 80, height: 80, fontSize: '2.5rem' },
      large: { width: 100, height: 100, fontSize: '3rem' }
    };
    return sizes[size];
  };

  const sizeStyles = getSizeStyles();

  return (
    <Box
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '50%',
        background: `linear-gradient(145deg, ${iconData.color}, ${iconData.color}CC)`,
        border: `3px solid ${iconData.color}`,
        boxShadow: `0 8px 25px ${iconData.color}4D`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        ...sizeStyles,
        transform: isHovered ? 'translateY(-5px) scale(1.1)' : 'translateY(0) scale(1)',
        animation: animated ? 'float 3s ease-in-out infinite' : 'none',
      }}
    >
      <Text
        style={{
          fontSize: 'inherit',
          filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
          transition: 'all 0.3s ease',
          textShadow: '0 2px 4px rgba(0,0,0,0.3)',
        }}
      >
        {iconData.emoji}
      </Text>

      {displayDescription && isHovered && (
        <Text
          size="xs"
          style={{
            position: 'absolute',
            bottom: -25,
            left: '50%',
            transform: 'translateX(-50%)',
            whiteSpace: 'nowrap',
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'var(--mantine-color-text)',
            background: 'var(--mantine-color-white)',
            padding: '2px 8px',
            borderRadius: 4,
            border: `1px solid ${iconData.color}4D`,
            opacity: isHovered ? 1 : 0,
            transition: 'opacity 0.3s ease',
            pointerEvents: 'none',
          }}
        >
          {displayDescription}
        </Text>
      )}

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-3px) rotate(2deg); }
        }
      `}</style>
    </Box>
  );
};
