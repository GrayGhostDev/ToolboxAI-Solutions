import React, { useState } from 'react';
import { Box } from '@mantine/core';
import { Procedural3DIcon } from './Procedural3DIcon';
interface Safe3DIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  animated?: boolean;
  fallbackSrc?: string;
  style?: React.CSSProperties;
}
export const Safe3DIcon: React.FunctionComponent<Safe3DIconProps> = ({
  iconName,
  size = 'medium',
  color,
  animated = true,
  fallbackSrc,
  style,
}) => {
  const [useProceduralIcon, setUseProceduralIcon] = useState(false);
  const [imageError, setImageError] = useState(false);
  const sizeMap = {
    small: 40,
    medium: 60,
    large: 80,
  };
  const iconSize = sizeMap[size];
  // Always use procedural icons for now since we don't have image assets
  if (true || useProceduralIcon || imageError) {
    return (
      <Procedural3DIcon
        iconName={iconName}
        size={size}
        color={color}
        animated={animated}
        style={style}
      />
    );
  }
  // This code path won't be reached but keeping for future when we have real assets
  return (
    <Box
      style={{
        width: iconSize,
        height: iconSize,
        position: 'relative',
        ...style,
      }}
    >
      <img
        src={`/assets/3d-icons/${iconName}.png`}
        alt={iconName}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
        onError={() => {
          console.log(`3D icon ${iconName} not found, using procedural icon`);
          setImageError(true);
        }}
      />
    </Box>
  );
};
// Export a function to replace Real3DIcon globally
export const Real3DIcon = Safe3DIcon;
export default Safe3DIcon;