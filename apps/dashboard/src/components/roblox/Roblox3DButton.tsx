import React, { useState } from 'react';
import { Button, Box, Text, Tooltip, useMantineTheme, rem } from '@mantine/core';
// import { createStyles } from '@mantine/emotion'; // Removed - using inline styles instead

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

// CSS Animations - using CSS keyframes instead of Mantine keyframes
const floatAnimation = 'floatAnimation 3s ease-in-out infinite';
const pulseAnimation = 'pulseAnimation 1s linear infinite';
const glowAnimation = 'glowAnimation 2s ease-in-out infinite';
const shimmerAnimation = 'shimmerAnimation 0.6s ease';

// Add CSS styles to document head
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes floatAnimation {
      0%, 100% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-3px) rotate(2deg); }
    }
    @keyframes pulseAnimation {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }
    @keyframes glowAnimation {
      0% { box-shadow: 0 0 5px currentColor; }
      50% { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
      100% { box-shadow: 0 0 5px currentColor; }
    }
    @keyframes shimmerAnimation {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(100%); }
    }
  `;
  if (!document.head.querySelector('style[data-roblox-animations]')) {
    style.setAttribute('data-roblox-animations', 'true');
    document.head.appendChild(style);
  }
}

// const useStyles = createStyles((theme, { variant, size }: { variant: string; size: string }) => {
// Temporarily disabled - using inline styles instead
const getButtonStyles = (theme: any, variant: string, size: string) => {
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

  return {
    button: {
      position: 'relative',
      background: `linear-gradient(145deg, ${variantColors[variant as keyof typeof variantColors]}, rgba(37, 99, 235, 0.8))`,
      border: `2px solid ${variantColors[variant as keyof typeof variantColors]}`,
      borderRadius: rem(12),
      textTransform: 'none',
      fontWeight: 600,
      color: 'white',
      overflow: 'hidden',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      boxShadow: `0 4px 15px rgba(37, 99, 235, 0.3)`,
      animation: `${floatAnimation} 3s ease-in-out infinite`,
      ...sizeStyles[size as keyof typeof sizeStyles],

      '&:hover': {
        transform: 'translateY(-2px) scale(1.02)',
        boxShadow: `0 8px 25px rgba(37, 99, 235, 0.5)`,
        background: `linear-gradient(145deg, ${variantColors[variant as keyof typeof variantColors]}, rgba(37, 99, 235, 0.9))`
      },

      '&:active': {
        transform: 'translateY(0) scale(0.98)'
      },

      '&:disabled': {
        background: `linear-gradient(145deg, ${theme.colors.gray[6]}, ${theme.colors.gray[7]})`,
        borderColor: theme.colors.gray[6],
        color: theme.colors.gray[4],
        boxShadow: 'none',
        transform: 'none'
      },

      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent)`,
        transform: 'translateX(-100%)',
        transition: 'transform 0.6s ease'
      },
      '&:hover::before': {
        transform: 'translateX(100%)'
      },

      '&::after': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent, rgba(255, 255, 255, 0.1))`,
        borderRadius: 'inherit',
        opacity: 0,
        transition: 'opacity 0.3s ease'
      },

      '&:hover::after': {
        opacity: 1
      }
    },
    iconContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
      transition: 'transform 0.3s ease',
      ...iconSizes[size as keyof typeof iconSizes]
    },
    loadingSpinner: {
      width: 20,
      height: 20,
      border: `2px solid rgba(255, 255, 255, 0.3)`,
      borderTop: '2px solid #fff',
      borderRadius: '50%',
      animation: `${pulseAnimation} 1s linear infinite`
    }
  };
};

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
  const classes = getButtonStyles(theme, variant, size);
  const [isHovered, setIsHovered] = useState(false);

  const iconPath = iconImageMap[iconName] || iconImageMap['TROPHY'];

  const buttonContent = (
    <Button
      className={classes.button}
      disabled={disabled || loading}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      fullWidth={fullWidth}
      style={{
        width: fullWidth ? '100%' : 'auto'
      }}
    >
      <Box style={{ display: 'flex', alignItems: 'center', gap: rem(8) }}>
        {loading ? (
          <Box className={classes.loadingSpinner} />
        ) : (
          <Box className={classes.iconContainer}>
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
              transform: isHovered ? 'translateX(2px)' : 'translateX(0)'
            }}
          >
            {label}
          </Text>
        )}
      </Box>
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
