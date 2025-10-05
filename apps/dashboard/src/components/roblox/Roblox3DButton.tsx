import React, { useState } from 'react';
import { Button, Box, Text, Tooltip, useMantineTheme, rem } from '@mantine/core';

interface Roblox3DButtonProps {
  iconName: string;
  label?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  tooltip?: string;
  animated?: boolean;
  fullWidth?: boolean;
}

// Keyframe animations defined as CSS strings
const animations = `
  @keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-3px) rotate(2deg); }
  }

  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  }

  @keyframes glow {
    0% { box-shadow: 0 0 5px currentColor; }
    50% { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
    100% { box-shadow: 0 0 5px currentColor; }
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'roblox-3d-button-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = animations;
    document.head.appendChild(style);
  }
}

// Map icon names to their image paths
const iconImageMap: { [key: string]: string } = {
  'ABC_CUBE': '/images/png/3d_icon_ABC_CUBE_1.png',
  'BACKPACK': '/images/png/3d_icon_BACKPACK_1.png',
  'BADGE': '/images/png/3d_icon_BADGE_1.png',
  'BASKETBALL': '/images/png/3d_icon_BASKETBALL_1.png',
  'BOARD': '/images/png/3d_icon_BOARD_1.png',
  'BOOKS': '/images/png/3d_icon_BOOKS_1.png',
  'BRUSH_PAINT': '/images/png/3d_icon_BRUSH_PAINT_1.png',
  'CIRCLE_RULER': '/images/png/3d_icon_CIRCLE_RULER_1.png',
  'CRAYON': '/images/png/3d_icon_CRAYON_1.png',
  'ERASER': '/images/png/3d_icon_ERASER_1.png',
  'GRADUATION_CAP': '/images/png/3d_icon_GRADUATION_CAP_1.png',
  'LAMP': '/images/png/3d_icon_LAMP_1.png',
  'LIGHT_BULB': '/images/png/3d_icon_LIGHT_BULB_1.png',
  'OPEN_BOOK': '/images/png/3d_icon_OPEN_BOOK_1.png',
  'PAPER': '/images/png/3d_icon_PAPER_1.png',
  'PENCIL': '/images/png/3d_icon_PENCIL_1.png',
  'RULER': '/images/png/3d_icon_RULER_1.png',
  'SOCCER_BALL': '/images/png/3d_icon_SOCCER_BALL_1.png',
  'TRIANGLE_RULER': '/images/png/3d_icon_TRIANGLE_RULER_1.png',
  'TROPHY': '/images/png/3d_icon_TROPHY_1.png',
};

export const Roblox3DButton: React.FunctionComponent<Roblox3DButtonProps> = ({
  iconName,
  label,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  tooltip,
  animated = true,
  fullWidth = false,
}) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);

  const variantColors = {
    primary: theme.colors.blue[6],
    secondary: theme.colors.violet[6],
    success: theme.colors.green[6],
    warning: theme.colors.yellow[6],
    error: theme.colors.red[6],
    info: theme.colors.cyan[6]
  };

  const sizeStyles = {
    small: { minHeight: 40, padding: '8px 16px', fontSize: rem(14) },
    medium: { minHeight: 48, padding: '12px 24px', fontSize: rem(16) },
    large: { minHeight: 56, padding: '16px 32px', fontSize: rem(18) }
  };

  const iconSizes = {
    small: { width: 20, height: 20 },
    medium: { width: 24, height: 24 },
    large: { width: 32, height: 32 }
  };

  const mainColor = variantColors[variant];
  const iconPath = iconImageMap[iconName] || iconImageMap['TROPHY'];

  // Button base styles
  const buttonStyle: React.CSSProperties = {
    position: 'relative',
    background: disabled
      ? `linear-gradient(145deg, ${theme.colors.gray[6]}, ${theme.colors.gray[7]})`
      : `linear-gradient(145deg, ${mainColor}, rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.8))`,
    border: `2px solid ${disabled ? theme.colors.gray[6] : mainColor}`,
    borderRadius: rem(12),
    textTransform: 'none' as const,
    fontWeight: 600,
    color: disabled ? theme.colors.gray[4] : 'white',
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: disabled ? 'none' : `0 4px 15px rgba(${parseInt(mainColor.slice(1,3), 16)}, ${parseInt(mainColor.slice(3,5), 16)}, ${parseInt(mainColor.slice(5,7), 16)}, 0.3)`,
    animation: animated && !disabled ? 'float 3s ease-in-out infinite' : 'none',
    width: fullWidth ? '100%' : 'auto',
    transform: isHovered && !disabled ? 'translateY(-2px) scale(1.02)' : disabled ? 'none' : 'translateY(0) scale(1)',
    ...sizeStyles[size],
  };

  const iconContainerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
    transition: 'transform 0.3s ease',
    ...iconSizes[size]
  };

  const loadingSpinnerStyle: React.CSSProperties = {
    width: 20,
    height: 20,
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTop: '2px solid #fff',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  };

  const buttonContent = (
    <Button
      style={buttonStyle}
      disabled={disabled || loading}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      fullWidth={fullWidth}
      variant="filled"
      unstyled
    >
      <Box style={{ display: 'flex', alignItems: 'center', gap: rem(8), position: 'relative', zIndex: 1 }}>
        {loading ? (
          <Box style={loadingSpinnerStyle} />
        ) : (
          <Box style={iconContainerStyle}>
            <Box
              component="img"
              src={iconPath}
              alt={iconName}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
                transition: 'all 0.3s ease'
              }}
            />
          </Box>
        )}

        {label && (
          <Text
            fw={600}
            style={{
              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
              transition: 'all 0.3s ease',
              transform: isHovered ? 'translateX(2px)' : 'translateX(0)',
              color: 'inherit'
            }}
          >
            {label}
          </Text>
        )}
      </Box>

      {/* Shimmer effect on hover */}
      {isHovered && !disabled && (
        <Box
          style={{
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
            animation: 'shimmer 0.6s ease',
            pointerEvents: 'none'
          }}
        />
      )}
    </Button>
  );

  if (tooltip) {
    return (
      <Tooltip label={tooltip} position="top" withArrow>
        {buttonContent}
      </Tooltip>
    );
  }

  return buttonContent;
};
