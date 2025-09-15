import React, { useState } from 'react';
import { 
  Box, 
  Tabs, 
  Tab, 
  useTheme, 
  alpha, 
  keyframes, 
  styled,
  Typography,
  Badge
} from '@mui/material';

interface TabItem {
  id: string;
  label: string;
  iconName: string;
  badge?: number;
  disabled?: boolean;
  tooltip?: string;
}

interface Roblox3DTabsProps {
  tabs: TabItem[];
  value: number;
  onChange: (event: React.SyntheticEvent, newValue: number) => void;
  orientation?: 'horizontal' | 'vertical';
  variant?: 'standard' | 'scrollable' | 'fullWidth';
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  glowEffect?: boolean;
}

// Animations
const floatAnimation = keyframes`
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-2px) rotate(1deg); }
`;

const pulseAnimation = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const glowAnimation = keyframes`
  0% { box-shadow: 0 0 5px currentColor; }
  50% { box-shadow: 0 0 15px currentColor, 0 0 25px currentColor; }
  100% { box-shadow: 0 0 5px currentColor; }
`;

const shimmerAnimation = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
`;

const StyledTabs = styled(Tabs)(({ theme, orientation, animated }: any) => ({
  '& .MuiTabs-indicator': {
    background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    height: 4,
    borderRadius: 2,
    boxShadow: `0 0 10px ${alpha(theme.palette.primary.main, 0.5)}`,
    ...(orientation === 'vertical' && {
      width: 4,
      height: 'auto',
      left: 0,
      right: 'auto',
    }),
  },
  
  '& .MuiTabs-flexContainer': {
    gap: 8,
    ...(orientation === 'vertical' && {
      flexDirection: 'column',
      alignItems: 'stretch',
    }),
  },
}));

const StyledTab = styled(Tab)(({ theme, size, animated, glowEffect }: any) => {
  const sizeStyles = {
    small: { minHeight: 40, padding: '8px 16px', fontSize: '0.875rem' },
    medium: { minHeight: 48, padding: '12px 20px', fontSize: '1rem' },
    large: { minHeight: 56, padding: '16px 24px', fontSize: '1.125rem' }
  };

  return {
    position: 'relative',
    background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
    border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
    borderRadius: 12,
    margin: '4px',
    textTransform: 'none',
    fontWeight: 600,
    color: theme.palette.text.primary,
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.1)}`,
    ...sizeStyles[size],
    
    '&:hover': {
      transform: 'translateY(-2px) scale(1.02)',
      background: `linear-gradient(145deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.05)})`,
      borderColor: theme.palette.primary.main,
      boxShadow: `0 4px 15px ${alpha(theme.palette.primary.main, 0.3)}`,
      color: theme.palette.primary.main,
    },
    
    '&.Mui-selected': {
      background: `linear-gradient(145deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.main, 0.8)})`,
      color: 'white',
      borderColor: theme.palette.primary.main,
      boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.4)}`,
      transform: 'translateY(-1px)',
    },
    
    '&.Mui-disabled': {
      background: `linear-gradient(145deg, ${theme.palette.grey[800]}, ${theme.palette.grey[900]})`,
      borderColor: theme.palette.grey[600],
      color: theme.palette.grey[500],
      boxShadow: 'none',
      transform: 'none',
    },
    
    ...(animated && {
      animation: `${floatAnimation} 4s ease-in-out infinite`,
    }),
    
    ...(glowEffect && {
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(45deg, transparent, ${alpha('#fff', 0.1)}, transparent)`,
        transform: 'translateX(-100%)',
        transition: 'transform 0.6s ease',
      },
      '&:hover::before': {
        transform: 'translateX(100%)',
      },
    }),
    
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `linear-gradient(135deg, ${alpha('#fff', 0.05)}, transparent, ${alpha('#fff', 0.05)})`,
      borderRadius: 'inherit',
      opacity: 0,
      transition: 'opacity 0.3s ease',
    },
    
    '&:hover::after': {
      opacity: 1,
    },
  };
});

const IconContainer = styled(Box)(({ theme, size, isSelected }: any) => {
  const sizeStyles = {
    small: { width: 16, height: 16 },
    medium: { width: 20, height: 20 },
    large: { width: 24, height: 24 }
  };

  return {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...sizeStyles[size],
    filter: isSelected 
      ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.3)) brightness(1.2)' 
      : 'drop-shadow(0 1px 2px rgba(0,0,0,0.2))',
    transition: 'all 0.3s ease',
  };
});

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

export const Roblox3DTabs: React.FC<Roblox3DTabsProps> = ({
  tabs,
  value,
  onChange,
  orientation = 'horizontal',
  variant = 'standard',
  size = 'medium',
  animated = true,
  glowEffect = true,
}) => {
  const theme = useTheme();

  return (
    <StyledTabs
      value={value}
      onChange={onChange}
      orientation={orientation}
      variant={variant}
      animated={animated}
      sx={{
        '& .MuiTabs-scrollButtons': {
          color: theme.palette.primary.main,
          '&.Mui-disabled': {
            color: theme.palette.grey[500],
          },
        },
      }}
    >
      {tabs.map((tab, index) => {
        const isSelected = value === index;
        const iconPath = iconImageMap[tab.iconName] || iconImageMap['TROPHY'];
        
        return (
          <StyledTab
            key={tab.id}
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IconContainer size={size} isSelected={isSelected}>
                  <img
                    src={iconPath}
                    alt={tab.iconName}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                    }}
                  />
                </IconContainer>
                
                <Typography
                  variant="button"
                  sx={{
                    fontWeight: 600,
                    textShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.3)' : 'none',
                    transition: 'all 0.3s ease',
                  }}
                >
                  {tab.label}
                </Typography>
                
                {tab.badge && tab.badge > 0 && (
                  <Badge
                    badgeContent={tab.badge}
                    color="error"
                    sx={{
                      '& .MuiBadge-badge': {
                        background: `linear-gradient(135deg, ${theme.palette.error.main}, ${theme.palette.warning.main})`,
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '0.7rem',
                        minWidth: 18,
                        height: 18,
                        borderRadius: 9,
                        boxShadow: `0 0 10px ${alpha(theme.palette.error.main, 0.5)}`,
                      },
                    }}
                  />
                )}
              </Box>
            }
            disabled={tab.disabled}
            size={size}
            animated={animated}
            glowEffect={glowEffect}
            title={tab.tooltip}
          />
        );
      })}
    </StyledTabs>
  );
};
