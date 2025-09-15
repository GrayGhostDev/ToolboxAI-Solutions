import React, { useState } from 'react';
import { Button, useTheme, alpha, keyframes, styled } from '@mui/material';
import { Box, Typography, Tooltip } from '@mui/material';

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

const shimmerAnimation = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
`;

const Styled3DButton = styled(Button)(({ theme, variant, size, animated }: any) => {
  const variantColors = {
    primary: theme.palette.primary.main,
    secondary: theme.palette.secondary.main,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main,
    info: theme.palette.info.main,
  };

  const sizeStyles = {
    small: { minHeight: 40, padding: '8px 16px', fontSize: '0.875rem' },
    medium: { minHeight: 48, padding: '12px 24px', fontSize: '1rem' },
    large: { minHeight: 56, padding: '16px 32px', fontSize: '1.125rem' }
  };

  return {
    position: 'relative',
    background: `linear-gradient(145deg, ${variantColors[variant]}, ${alpha(variantColors[variant], 0.8)})`,
    border: `2px solid ${variantColors[variant]}`,
    borderRadius: 12,
    textTransform: 'none',
    fontWeight: 600,
    color: 'white',
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: `0 4px 15px ${alpha(variantColors[variant], 0.3)}`,
    ...sizeStyles[size],
    
    '&:hover': {
      transform: 'translateY(-2px) scale(1.02)',
      boxShadow: `0 8px 25px ${alpha(variantColors[variant], 0.5)}`,
      background: `linear-gradient(145deg, ${variantColors[variant]}, ${alpha(variantColors[variant], 0.9)})`,
    },
    
    '&:active': {
      transform: 'translateY(0) scale(0.98)',
    },
    
    '&:disabled': {
      background: `linear-gradient(145deg, ${theme.palette.grey[600]}, ${theme.palette.grey[700]})`,
      borderColor: theme.palette.grey[600],
      color: theme.palette.grey[400],
      boxShadow: 'none',
      transform: 'none',
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
      borderRadius: 'inherit',
      opacity: 0,
      transition: 'opacity 0.3s ease',
    },
    
    '&:hover::after': {
      opacity: 1,
    },
  };
});

const IconContainer = styled(Box)(({ theme, size }: any) => {
  const sizeStyles = {
    small: { width: 20, height: 20 },
    medium: { width: 24, height: 24 },
    large: { width: 32, height: 32 }
  };

  return {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...sizeStyles[size],
    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
    transition: 'transform 0.3s ease',
  };
});

const LoadingSpinner = styled(Box)(({ theme }) => ({
  width: 20,
  height: 20,
  border: `2px solid ${alpha('#fff', 0.3)}`,
  borderTop: `2px solid #fff`,
  borderRadius: '50%',
  animation: `${pulseAnimation} 1s linear infinite`,
}));

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

export const Roblox3DButton: React.FC<Roblox3DButtonProps> = ({
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
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  
  const iconPath = iconImageMap[iconName] || iconImageMap['TROPHY'];
  
  const buttonContent = (
    <Styled3DButton
      variant={variant}
      size={size}
      animated={animated}
      disabled={disabled || loading}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      sx={{ width: fullWidth ? '100%' : 'auto' }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <IconContainer size={size}>
            <img
              src={iconPath}
              alt={iconName}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                filter: isHovered ? 'brightness(1.2) contrast(1.1)' : 'none',
                transition: 'all 0.3s ease',
              }}
            />
          </IconContainer>
        )}
        
        {label && (
          <Typography
            variant="button"
            sx={{
              fontWeight: 600,
              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
              transition: 'all 0.3s ease',
              transform: isHovered ? 'translateX(2px)' : 'translateX(0)',
            }}
          >
            {label}
          </Typography>
        )}
      </Box>
    </Styled3DButton>
  );

  if (tooltip) {
    return (
      <Tooltip title={tooltip} arrow placement="top">
        {buttonContent}
      </Tooltip>
    );
  }

  return buttonContent;
};
