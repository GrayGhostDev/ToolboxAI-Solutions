import React from 'react';
import { Box } from '@mantine/core';
import {
  IconRocket,
  IconStar,
  IconTrophy,
  IconBook,
  IconDeviceGamepad2,
  IconCube,
  IconChalkboard,
  IconBallFootball,
  IconBrush,
  IconClipboardCheck,
  IconShieldCheck,
  IconQuestionMark,
} from '@tabler/icons-react';

/**
 * Simple2DIcon - Lightweight 2D icon component using Tabler icons
 *
 * This component provides a fallback for 3D icons without creating WebGL contexts.
 * It maps icon names to Tabler icons for consistent appearance.
 *
 * Features:
 * - Zero WebGL contexts (no Canvas)
 * - Fast rendering
 * - Consistent sizing
 * - Color customization
 */

interface Simple2DIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  style?: React.CSSProperties;
}

// Map 3D icon names to 2D Tabler icons
const iconMap: Record<string, React.ComponentType<any>> = {
  ROCKET: IconRocket,
  ROCKET_1: IconRocket,
  ROCKET_2: IconRocket,
  STAR: IconStar,
  STAR_1: IconStar,
  STAR_2: IconStar,
  TROPHY: IconTrophy,
  TROPHY_1: IconTrophy,
  BOOKS: IconBook,
  BOOKS_1: IconBook,
  SPORTS_ESPORTS: IconDeviceGamepad2,
  SPORTS_ESPORTS_1: IconDeviceGamepad2,
  ABC_CUBE: IconCube,
  BOARD: IconChalkboard,
  BOARD_1: IconChalkboard,
  SOCCER_BALL: IconBallFootball,
  BRUSH_PAINT: IconBrush,
  ASSESSMENT: IconClipboardCheck,
  ASSESSMENT_1: IconClipboardCheck,
  BADGE: IconShieldCheck,
  BADGE_1: IconShieldCheck,
  DEFAULT: IconQuestionMark,
};

export const Simple2DIcon: React.FunctionComponent<Simple2DIconProps> = ({
  iconName,
  size = 'medium',
  color = '#4dabf7',
  style,
}) => {
  const sizeMap = {
    small: 40,
    medium: 60,
    large: 80,
  };

  const iconSize = sizeMap[size];

  // Get the icon, removing any numeric suffix
  const iconKey = iconName.replace(/_\d+$/, '');
  const Icon = iconMap[iconKey] || iconMap.DEFAULT;

  return (
    <Box
      style={{
        width: iconSize,
        height: iconSize,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '8px',
        background: `linear-gradient(135deg, ${color}22 0%, ${color}11 100%)`,
        ...style,
      }}
    >
      <Icon
        size={iconSize * 0.6}
        color={color}
        stroke={1.5}
      />
    </Box>
  );
};

export default Simple2DIcon;
