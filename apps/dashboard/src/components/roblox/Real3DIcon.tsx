import React, { useState, useEffect } from 'react';
import { Box, Typography, useTheme, alpha, keyframes, styled, CircularProgress } from '@mui/material';

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

const StyledIconContainer = styled(Box)(({ theme, size, animated }: any) => {
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
    
    ...(animated && {
      animation: `${floatAnimation} 3s ease-in-out infinite`,
    }),
    
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

export const Real3DIcon: React.FC<Real3DIconProps> = ({
  iconName,
  size = 'medium',
  animated = true,
  onClick,
  description
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [imageData, setImageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  const iconData = iconMap[iconName] || iconMap['TROPHY'];
  const displayDescription = description || iconData.description;

  // Load the 3D image data from JSON
  useEffect(() => {
    const loadImageData = async () => {
      try {
        setLoading(true);
        const response = await fetch(iconData.imagePath);
        if (response.ok) {
          const data = await response.json();
          setImageData(data);
        } else {
          setError(true);
        }
      } catch (err) {
        console.warn(`Failed to load 3D image data for ${iconName}:`, err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    loadImageData();
  }, [iconName, iconData.imagePath]);

  // Create a data URL from the parsed image data
  const createImageFromData = () => {
    if (!imageData?.parsed_data) return null;
    
    // For now, we'll use the emoji as fallback since we don't have the actual PNG files
    // In a real implementation, you would reconstruct the image from the parsed data
    return null;
  };

  const imageUrl = createImageFromData();

  return (
    <StyledIconContainer
      size={size}
      animated={animated}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      sx={{
        background: `linear-gradient(145deg, ${iconData.fallbackColor}, ${alpha(iconData.fallbackColor, 0.7)})`,
        borderColor: iconData.fallbackColor,
        boxShadow: `0 8px 25px ${alpha(iconData.fallbackColor, 0.3)}`,
        '&:hover': {
          boxShadow: `0 12px 35px ${alpha(iconData.fallbackColor, 0.5)}`,
          borderColor: iconData.fallbackColor,
        }
      }}
    >
      {loading ? (
        <CircularProgress size={size === 'small' ? 20 : size === 'medium' ? 30 : 40} />
      ) : error || !imageUrl ? (
        <Typography
          sx={{
            fontSize: size === 'small' ? '1.5rem' : size === 'medium' ? '2rem' : '2.5rem',
            filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
            transition: 'all 0.3s ease',
            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
          }}
        >
          {iconData.emoji}
        </Typography>
      ) : (
        <Box
          component="img"
          src={imageUrl}
          alt={displayDescription}
          sx={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
            transition: 'all 0.3s ease',
          }}
        />
      )}
      
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
            border: `1px solid ${alpha(iconData.fallbackColor, 0.3)}`,
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
