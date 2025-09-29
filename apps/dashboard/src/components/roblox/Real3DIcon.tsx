import React, { useState } from 'react';
import { Box, Text, useMantineTheme } from '@mantine/core';
import { keyframes } from '@mantine/core';
import { Procedural3DIcon } from './Procedural3DIcon';

interface Real3DIconProps {
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

// Mantine-compatible styled component approach
const getIconContainerStyles = (theme: any, size: string) => {
  const sizeStyles = {
    small: { width: 60, height: 60 },
    medium: { width: 80, height: 80 },
    large: { width: 100, height: 100 }
  };

  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    background: `linear-gradient(145deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
    border: `3px solid ${theme.colors.blue[6]}`,
    boxShadow: `0 8px 25px ${theme.colors.blue[2]}`,
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    overflow: 'hidden',
    animation: `${floatAnimation} 3s ease-in-out infinite`,
    ...sizeStyles[size as keyof typeof sizeStyles]
  };
};

// Particle effect generator
function createParticleEffect(x: number, y: number, type: string) {
  const colors = ['#00ffff', '#ff00ff', '#ffff00', '#00ff00'];
  const particleCount = type === 'burst' ? 20 : 10;

  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.left = `${x}px`;
    particle.style.top = `${y}px`;
    particle.style.width = type === 'confetti' ? '10px' : '6px';
    particle.style.height = type === 'confetti' ? '10px' : '6px';
    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
    particle.style.borderRadius = type === 'confetti' ? '2px' : '50%';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '9999';
    particle.style.boxShadow = `0 0 10px currentColor`;

    const angle = (i / particleCount) * Math.PI * 2;
    const velocity = 5 + Math.random() * 5;
    const vx = Math.cos(angle) * velocity;
    const vy = Math.sin(angle) * velocity - 5;

    document.body.appendChild(particle);

    let posX = 0;
    let posY = 0;
    let opacity = 1;
    let rotation = 0;

    const animate = () => {
      posX += vx;
      posY += vy + 0.5; // gravity
      opacity -= 0.02;
      rotation += 10;

      particle.style.transform = `translate(${posX}px, ${posY}px) rotate(${rotation}deg)`;
      particle.style.opacity = opacity.toString();

      if (opacity > 0) {
        requestAnimationFrame(animate);
      } else {
        particle.remove();
      }
    };

    requestAnimationFrame(animate);
  }
}

// Icon mapping with actual 3D image data
const iconMap: { [key: string]: { 
  emoji: string; 
  color: string; 
  description: string;
  imagePath: string;
  fallbackColor: string;
} } = {
  'ABC_CUBE': { 
    emoji: '🧩', 
    color: '#4CAF50', 
    description: 'ABC Learning Cube',
    imagePath: '/images/png/3d_icon_ABC_CUBE_1.json',
    fallbackColor: '#4CAF50'
  },
  'BACKPACK': { 
    emoji: '🎒', 
    color: '#FF9800', 
    description: 'Student Backpack',
    imagePath: '/images/png/3d_icon_BACKPACK_1.json',
    fallbackColor: '#FF9800'
  },
  'BADGE': { 
    emoji: '🏅', 
    color: '#E91E63', 
    description: 'Achievement Badge',
    imagePath: '/images/png/3d_icon_BADGE_1.json',
    fallbackColor: '#E91E63'
  },
  'BASKETBALL': { 
    emoji: '🏀', 
    color: '#FF5722', 
    description: 'Sports Basketball',
    imagePath: '/images/png/3d_icon_BASKETBALL_1.json',
    fallbackColor: '#FF5722'
  },
  'BOARD': { 
    emoji: '📋', 
    color: '#2196F3', 
    description: 'Learning Board',
    imagePath: '/images/png/3d_icon_BOARD_1.json',
    fallbackColor: '#2196F3'
  },
  'BOOKS': { 
    emoji: '📚', 
    color: '#9C27B0', 
    description: 'Educational Books',
    imagePath: '/images/png/3d_icon_BOOKS_1.json',
    fallbackColor: '#9C27B0'
  },
  'BRUSH_PAINT': { 
    emoji: '🎨', 
    color: '#FFC107', 
    description: 'Paint Brush',
    imagePath: '/images/png/3d_icon_BRUSH_PAINT_1.json',
    fallbackColor: '#FFC107'
  },
  'CIRCLE_RULER': { 
    emoji: '📏', 
    color: '#607D8B', 
    description: 'Circle Ruler',
    imagePath: '/images/png/3d_icon_CIRCLE_RULER_1.json',
    fallbackColor: '#607D8B'
  },
  'CRAYON': { 
    emoji: '🖍️', 
    color: '#FF5722', 
    description: 'Coloring Crayon',
    imagePath: '/images/png/3d_icon_CRAYON_1.json',
    fallbackColor: '#FF5722'
  },
  'ERASER': { 
    emoji: '🧽', 
    color: '#9E9E9E', 
    description: 'Eraser Tool',
    imagePath: '/images/png/3d_icon_ERASER_1.json',
    fallbackColor: '#9E9E9E'
  },
  'GRADUATION_CAP': { 
    emoji: '🎓', 
    color: '#3F51B5', 
    description: 'Graduation Cap',
    imagePath: '/images/png/3d_icon_GRADUATION_CAP_1.json',
    fallbackColor: '#3F51B5'
  },
  'LAMP': { 
    emoji: '💡', 
    color: '#FFEB3B', 
    description: 'Study Lamp',
    imagePath: '/images/png/3d_icon_LAMP_1.json',
    fallbackColor: '#FFEB3B'
  },
  'LIGHT_BULB': { 
    emoji: '💡', 
    color: '#FFC107', 
    description: 'Light Bulb',
    imagePath: '/images/png/3d_icon_LIGHT_BULB_1.json',
    fallbackColor: '#FFC107'
  },
  'OPEN_BOOK': { 
    emoji: '📖', 
    color: '#4CAF50', 
    description: 'Open Book',
    imagePath: '/images/png/3d_icon_OPEN_BOOK_1.json',
    fallbackColor: '#4CAF50'
  },
  'PAPER': { 
    emoji: '📄', 
    color: '#FFFFFF', 
    description: 'Paper Sheet',
    imagePath: '/images/png/3d_icon_PAPER_1.json',
    fallbackColor: '#FFFFFF'
  },
  'PENCIL': { 
    emoji: '✏️', 
    color: '#FF9800', 
    description: 'Pencil Tool',
    imagePath: '/images/png/3d_icon_PENCIL_1.json',
    fallbackColor: '#FF9800'
  },
  'RULER': { 
    emoji: '📐', 
    color: '#607D8B', 
    description: 'Measuring Ruler',
    imagePath: '/images/png/3d_icon_RULER_1.json',
    fallbackColor: '#607D8B'
  },
  'SOCCER_BALL': { 
    emoji: '⚽', 
    color: '#4CAF50', 
    description: 'Soccer Ball',
    imagePath: '/images/png/3d_icon_SOCCER_BALL_1.json',
    fallbackColor: '#4CAF50'
  },
  'TRIANGLE_RULER': { 
    emoji: '📐', 
    color: '#795548', 
    description: 'Triangle Ruler',
    imagePath: '/images/png/3d_icon_TRIANGLE_RULER_1.json',
    fallbackColor: '#795548'
  },
  'TROPHY': { 
    emoji: '🏆', 
    color: '#FFD700', 
    description: 'Trophy Award',
    imagePath: '/images/png/3d_icon_TROPHY_1.json',
    fallbackColor: '#FFD700'
  },
  'STAR': { 
    emoji: '⭐', 
    color: '#FFC107', 
    description: 'Star Achievement',
    imagePath: '/images/png/3d_icon_STAR_1.json',
    fallbackColor: '#FFC107'
  },
  'ROCKET': { 
    emoji: '🚀', 
    color: '#E91E63', 
    description: 'Rocket Launch',
    imagePath: '/images/png/3d_icon_ROCKET_1.json',
    fallbackColor: '#E91E63'
  },
  'ASSESSMENT': { 
    emoji: '📝', 
    color: '#2196F3', 
    description: 'Assessment Test',
    imagePath: '/images/png/3d_icon_ASSESSMENT_1.json',
    fallbackColor: '#2196F3'
  },
  'SETTINGS': { 
    emoji: '⚙️', 
    color: '#607D8B', 
    description: 'Settings Gear',
    imagePath: '/images/png/3d_icon_SETTINGS_1.json',
    fallbackColor: '#607D8B'
  },
  'REFRESH': { 
    emoji: '🔄', 
    color: '#4CAF50', 
    description: 'Refresh Data',
    imagePath: '/images/png/3d_icon_REFRESH_1.json',
    fallbackColor: '#4CAF50'
  },
  'SPORTS_ESPORTS': { 
    emoji: '🎮', 
    color: '#9C27B0', 
    description: 'Gaming Controller',
    imagePath: '/images/png/3d_icon_SPORTS_ESPORTS_1.json',
    fallbackColor: '#9C27B0'
  },
};

export const Real3DIcon: React.FunctionComponent<Real3DIconProps> = ({
  iconName,
  size = 'medium',
  animated = true,
  onClick,
  description
}) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);

  // Map icon names like ROCKET_1 to ROCKET
  const cleanIconName = iconName.replace(/_\d+$/, '');
  const iconData = iconMap[cleanIconName] || iconMap['TROPHY'];
  const displayDescription = description || iconData.description;

  // Handle click with particle effect
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      onClick();
    }
    // Create particle effect at click position
    createParticleEffect(e.clientX, e.clientY, 'burst');
  };

  return (
    <Box
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: theme.spacing.xs,
        position: 'relative',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      {/* Use Procedural 3D Icon */}
      <Procedural3DIcon
        iconName={cleanIconName}
        size={size}
        color={iconData.fallbackColor}
        animated={animated}
        style={{
          cursor: 'pointer',
          transition: 'transform 0.3s ease',
          transform: isHovered ? 'scale(1.1)' : 'scale(1)',
        }}
      />

      {/* Tooltip */}
      {displayDescription && isHovered && (
        <Text
          size="xs"
          style={{
            position: 'absolute',
            bottom: -25,
            left: '50%',
            transform: 'translateX(-50%)',
            whiteSpace: 'nowrap',
            fontWeight: 600,
            color: theme.colors.dark[9],
            backgroundColor: theme.colors.gray[0],
            padding: '4px 12px',
            borderRadius: 8,
            border: `2px solid ${iconData.fallbackColor}40`,
            boxShadow: `0 4px 12px ${theme.colors.dark[2]}`,
            zIndex: 1000,
            pointerEvents: 'none',
          }}
        >
          {displayDescription}
        </Text>
      )}
    </Box>
  );
};
