/**
 * Roblox 3D Icon Component
 * 
 * Displays 3D icons from the parsed design assets
 * with interactive hover effects and animations
 */

import React, { useState } from 'react';
import {
  Box,
  Tooltip,
  IconButton,
  Typography,
  Chip,
  Stack,
  useTheme,
  alpha,
  Zoom,
  Fade
} from '@mui/material';
import {
  School,
  SportsEsports,
  Quiz,
  Terrain,
  Psychology,
  Groups,
  Games,
  AutoAwesome
} from '@mui/icons-material';

interface IconData {
  name: string;
  type: 'education' | 'gaming' | 'tool' | 'achievement';
  category: string;
  level: number;
  isUnlocked: boolean;
  imagePath: string;
  description: string;
}

interface Roblox3DIconProps {
  icon: IconData;
  size?: 'small' | 'medium' | 'large';
  showTooltip?: boolean;
  animated?: boolean;
  onClick?: () => void;
}

const ICON_IMAGES = {
  'ABC_CUBE': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/ABC_CUBE_1.png',
  'BACKPACK': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/BACKPACK_1.png',
  'BADGE': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/BADGE_1.png',
  'BASKETBALL': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/BASKETBALL_1.png',
  'BOARD': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/BOARD_1.png',
  'BOOKS': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/BOOKS_1.png',
  'CRAYON': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/CRAYON_1.png',
  'ERASER': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/ERASER_1.png',
  'GRADUATION_CAP': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/GRADUATION_CAP_1.png',
  'LAMP': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/LAMP_1.png',
  'LIGHT_BULB': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/LIGHT_BULB_1.png',
  'OPEN_BOOK': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/OPEN_BOOK_1.png',
  'PAPER': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/PAPER_1.png',
  'PENCIL': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/PENCIL_1.png',
  'RULER': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/RULER_1.png',
  'SOCCER_BALL': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/SOCCER_BALL_1.png',
  'TROPHY': '/images/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/TROPHY_1.png'
};

const ICON_MAPPINGS = {
  'ABC_CUBE': { icon: School, color: '#4caf50' },
  'BACKPACK': { icon: Groups, color: '#2196f3' },
  'BADGE': { icon: AutoAwesome, color: '#ff9800' },
  'BASKETBALL': { icon: SportsEsports, color: '#f44336' },
  'BOARD': { icon: Terrain, color: '#9c27b0' },
  'BOOKS': { icon: School, color: '#4caf50' },
  'CRAYON': { icon: School, color: '#ff5722' },
  'ERASER': { icon: School, color: '#607d8b' },
  'GRADUATION_CAP': { icon: School, color: '#ffc107' },
  'LAMP': { icon: School, color: '#ffeb3b' },
  'LIGHT_BULB': { icon: Psychology, color: '#ffeb3b' },
  'OPEN_BOOK': { icon: School, color: '#4caf50' },
  'PAPER': { icon: School, color: '#e0e0e0' },
  'PENCIL': { icon: School, color: '#ff5722' },
  'RULER': { icon: School, color: '#9e9e9e' },
  'SOCCER_BALL': { icon: SportsEsports, color: '#4caf50' },
  'TROPHY': { icon: AutoAwesome, color: '#ffc107' }
};

export const Roblox3DIcon: React.FC<Roblox3DIconProps> = ({
  icon,
  size = 'medium',
  showTooltip = true,
  animated = true,
  onClick
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const sizeMap = {
    small: 32,
    medium: 48,
    large: 64
  };

  const iconSize = sizeMap[size];
  const iconKey = icon.name.toUpperCase() as keyof typeof ICON_IMAGES;
  const iconMapping = ICON_MAPPINGS[iconKey] || { icon: School, color: '#4caf50' };
  const IconComponent = iconMapping.icon;

  const handleClick = () => {
    if (onClick && icon.isUnlocked) {
      onClick();
    }
  };

  const iconElement = (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-block',
        cursor: icon.isUnlocked && onClick ? 'pointer' : 'default',
        transform: isHovered ? 'scale(1.1) rotate(5deg)' : 'scale(1) rotate(0deg)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        opacity: icon.isUnlocked ? 1 : 0.5,
        filter: icon.isUnlocked ? 'none' : 'grayscale(100%)',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <Box
        sx={{
          width: iconSize,
          height: iconSize,
          borderRadius: 2,
          background: `linear-gradient(145deg, ${alpha(iconMapping.color, 0.1)}, ${alpha(iconMapping.color, 0.05)})`,
          border: `2px solid ${alpha(iconMapping.color, 0.3)}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            border: `2px solid ${iconMapping.color}`,
            boxShadow: `0 8px 25px ${alpha(iconMapping.color, 0.3)}`,
          }
        }}
      >
        {/* Background image if available */}
        {ICON_IMAGES[iconKey] && (
          <Box
            component="img"
            src={ICON_IMAGES[iconKey]}
            alt={icon.name}
            sx={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              position: 'absolute',
              top: 0,
              left: 0,
              zIndex: 1
            }}
          />
        )}
        
        {/* Fallback icon */}
        <IconComponent
          sx={{
            fontSize: iconSize * 0.6,
            color: iconMapping.color,
            zIndex: 2,
            position: 'relative'
          }}
        />

        {/* Level indicator */}
        {icon.level > 0 && (
          <Box
            sx={{
              position: 'absolute',
              top: -4,
              right: -4,
              width: 16,
              height: 16,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.7rem',
              fontWeight: 600,
              color: 'white',
              zIndex: 3
            }}
          >
            {icon.level}
          </Box>
        )}

        {/* Lock overlay for locked icons */}
        {!icon.isUnlocked && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: alpha('#000', 0.5),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 4
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: 'white',
                fontWeight: 600,
                fontSize: '0.6rem'
              }}
            >
              LOCKED
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );

  if (!showTooltip) {
    return iconElement;
  }

  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            {icon.name.replace(/_/g, ' ')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {icon.description}
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip
              label={icon.category}
              size="small"
              sx={{
                fontSize: '0.7rem',
                height: 20,
                background: `linear-gradient(135deg, ${iconMapping.color}, ${alpha(iconMapping.color, 0.7)})`,
                color: 'white'
              }}
            />
            {icon.level > 0 && (
              <Chip
                label={`Level ${icon.level}`}
                size="small"
                sx={{
                  fontSize: '0.7rem',
                  height: 20,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  color: 'white'
                }}
              />
            )}
          </Stack>
        </Box>
      }
      arrow
      placement="top"
    >
      {iconElement}
    </Tooltip>
  );
};

export default Roblox3DIcon;
