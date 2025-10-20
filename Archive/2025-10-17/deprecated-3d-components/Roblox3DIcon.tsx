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
  ActionIcon,
  Text,
  Badge,
  Group,
  useMantineTheme,
  Transition,
  rem
} from '@mantine/core';
import {
  IconSchool,
  IconDeviceGamepad,
  IconQuestionMark,
  IconMountain,
  IconBrain,
  IconUsers,
  IconDeviceGamepad,
  IconSparkles
} from '@tabler/icons-react';

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
  'ABC_CUBE': { icon: IconSchool, color: '#4caf50' },
  'BACKPACK': { icon: IconUsers, color: '#2196f3' },
  'BADGE': { icon: IconSparkles, color: '#ff9800' },
  'BASKETBALL': { icon: IconDeviceGamepad, color: '#f44336' },
  'BOARD': { icon: IconMountain, color: '#9c27b0' },
  'BOOKS': { icon: IconSchool, color: '#4caf50' },
  'CRAYON': { icon: IconSchool, color: '#ff5722' },
  'ERASER': { icon: IconSchool, color: '#607d8b' },
  'GRADUATION_CAP': { icon: IconSchool, color: '#ffc107' },
  'LAMP': { icon: IconSchool, color: '#ffeb3b' },
  'LIGHT_BULB': { icon: IconBrain, color: '#ffeb3b' },
  'OPEN_BOOK': { icon: IconSchool, color: '#4caf50' },
  'PAPER': { icon: IconSchool, color: '#e0e0e0' },
  'PENCIL': { icon: IconSchool, color: '#ff5722' },
  'RULER': { icon: IconSchool, color: '#9e9e9e' },
  'SOCCER_BALL': { icon: IconDeviceGamepad, color: '#4caf50' },
  'TROPHY': { icon: IconSparkles, color: '#ffc107' }
};

export const Roblox3DIcon: React.FunctionComponent<Roblox3DIconProps> = ({
  icon,
  size = 'medium',
  showTooltip = true,
  animated = true,
  onClick
}) => {
  const theme = useMantineTheme();
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
      style={{
        position: 'relative',
        display: 'inline-block',
        cursor: icon.isUnlocked && onClick ? 'pointer' : 'default',
        transform: isHovered ? 'scale(1.1) rotate(5deg)' : 'scale(1) rotate(0deg)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        opacity: icon.isUnlocked ? 1 : 0.5,
        filter: icon.isUnlocked ? 'none' : 'grayscale(100%)'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <Box
        style={{
          width: iconSize,
          height: iconSize,
          borderRadius: rem(8),
          background: `linear-gradient(145deg, ${theme.fn.rgba(iconMapping.color, 0.1)}, ${theme.fn.rgba(iconMapping.color, 0.05)})`,
          border: `2px solid ${theme.fn.rgba(iconMapping.color, 0.3)}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s ease'
        }}
        styles={{
          root: {
            '&:hover': {
              border: `2px solid ${iconMapping.color}`,
              boxShadow: `0 8px 25px ${theme.fn.rgba(iconMapping.color, 0.3)}`
            }
          }
        }}
      >
        {/* Background image if available */}
        {ICON_IMAGES[iconKey] && (
          <Box
            component="img"
            src={ICON_IMAGES[iconKey]}
            alt={icon.name}
            style={{
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
          size={iconSize * 0.6}
          color={iconMapping.color}
          style={{
            zIndex: 2,
            position: 'relative'
          }}
        />

        {/* Level indicator */}
        {icon.level > 0 && (
          <Badge
            size="xs"
            variant="filled"
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
              zIndex: 3
            }}
          >
            {icon.level}
          </Badge>
        )}

        {/* Lock overlay for locked icons */}
        {!icon.isUnlocked && (
          <Box
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: theme.fn.rgba('#000', 0.5),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 4
            }}
          >
            <Text
              size="xs"
              c="white"
              fw={600}
            >
              LOCKED
            </Text>
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
      label={
        <Box>
          <Text size="sm" fw={600} mb="xs">
            {icon.name.replace(/_/g, ' ')}
          </Text>
          <Text size="xs" c="dimmed" mb="xs">
            {icon.description}
          </Text>
          <Group spacing="xs" align="center">
            <Badge
              size="sm"
              style={{
                background: `linear-gradient(135deg, ${iconMapping.color}, ${theme.fn.rgba(iconMapping.color, 0.7)})`,
                color: 'white'
              }}
            >
              {icon.category}
            </Badge>
            {icon.level > 0 && (
              <Badge
                size="sm"
                style={{
                  background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                  color: 'white'
                }}
              >
                Level {icon.level}
              </Badge>
            )}
          </Group>
        </Box>
      }
      withArrow
      position="top"
    >
      {iconElement}
    </Tooltip>
  );
};

export default Roblox3DIcon;
