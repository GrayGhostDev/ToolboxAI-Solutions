import React from 'react';
import { Simple2DIcon } from './Simple2DIcon';
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
  // Use Simple2DIcon by default to avoid WebGL context limits and HTML nesting errors
  // This eliminates "Too many active WebGL contexts" warnings
  // and fixes "div cannot be descendant of p" HTML nesting errors
  return (
    <Simple2DIcon
      iconName={iconName}
      size={size}
      color={color}
      style={style}
    />
  );
};
// Export a function to replace Real3DIcon globally
export const Real3DIcon = Safe3DIcon;
export default Safe3DIcon;