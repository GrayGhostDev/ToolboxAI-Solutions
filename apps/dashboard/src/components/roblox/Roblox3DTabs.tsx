import React from 'react';
import { Box, Tabs, Text, Badge, useMantineTheme, createStyles, keyframes } from '@mantine/core';

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
const floatAnimation = keyframes({
  '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
  '50%': { transform: 'translateY(-2px) rotate(1deg)' }
});

const pulseAnimation = keyframes({
  '0%': { transform: 'scale(1)' },
  '50%': { transform: 'scale(1.05)' },
  '100%': { transform: 'scale(1)' }
});

const glowAnimation = keyframes({
  '0%': { boxShadow: '0 0 5px currentColor' },
  '50%': { boxShadow: '0 0 15px currentColor, 0 0 25px currentColor' },
  '100%': { boxShadow: '0 0 5px currentColor' }
});

const shimmerAnimation = keyframes({
  '0%': { transform: 'translateX(-100%)' },
  '100%': { transform: 'translateX(100%)' }
});

const useStyles = createStyles((theme, { orientation, animated, size, glowEffect }: any) => {
  const sizeStyles = {
    small: { minHeight: 40, padding: '8px 16px', fontSize: '0.875rem' },
    medium: { minHeight: 48, padding: '12px 20px', fontSize: '1rem' },
    large: { minHeight: 56, padding: '16px 24px', fontSize: '1.125rem' }
  };

  return {
    tabsList: {
      gap: theme.spacing.xs,
      ...(orientation === 'vertical' && {
        flexDirection: 'column',
        alignItems: 'stretch',
      }),
    },

    tab: {
      position: 'relative',
      background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
      border: `2px solid ${theme.colors.blue[2]}`,
      borderRadius: theme.radius.sm,
      margin: theme.spacing.xs / 2,
      textTransform: 'none',
      fontWeight: 600,
      color: theme.colors.gray[7],
      overflow: 'hidden',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      boxShadow: `0 2px 8px ${theme.colors.blue[1]}`,
      ...sizeStyles[size],

      '&:hover': {
        transform: 'translateY(-2px) scale(1.02)',
        background: `linear-gradient(145deg, ${theme.colors.blue[1]}, ${theme.colors.violet[0]})`,
        borderColor: theme.colors.blue[4],
        boxShadow: `0 4px 15px ${theme.colors.blue[3]}`,
        color: theme.colors.blue[6],
      },

      '&[data-active]': {
        background: `linear-gradient(145deg, ${theme.colors.blue[6]}, ${theme.colors.blue[5]})`,
        color: 'white',
        borderColor: theme.colors.blue[6],
        boxShadow: `0 4px 20px ${theme.colors.blue[4]}`,
        transform: 'translateY(-1px)',
      },

      '&[disabled]': {
        background: `linear-gradient(145deg, ${theme.colors.gray[8]}, ${theme.colors.gray[9]})`,
        borderColor: theme.colors.gray[6],
        color: theme.colors.gray[5],
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
          background: `linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent)`,
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
        background: `linear-gradient(135deg, rgba(255,255,255,0.05), transparent, rgba(255,255,255,0.05))`,
        borderRadius: 'inherit',
        opacity: 0,
        transition: 'opacity 0.3s ease',
      },

      '&:hover::after': {
        opacity: 1,
      },
    },

    iconContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.2))',
      transition: 'all 0.3s ease',

      '[data-active] &': {
        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3)) brightness(1.2)',
      }
    }
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

export const Roblox3DTabs: React.FunctionComponent<Roblox3DTabsProps> = ({
  tabs,
  value,
  onChange,
  orientation = 'horizontal',
  variant = 'standard',
  size = 'medium',
  animated = true,
  glowEffect = true,
}) => {
  const theme = useMantineTheme();
  const { classes } = useStyles({ orientation, animated, size, glowEffect });

  const sizeMap = {
    small: { width: 16, height: 16 },
    medium: { width: 20, height: 20 },
    large: { width: 24, height: 24 }
  };

  const iconSize = sizeMap[size];

  return (
    <Tabs
      value={value.toString()}
      onTabChange={(val) => onChange(null as any, parseInt(val || '0'))}
      orientation={orientation}
      variant={variant}
      classNames={{
        list: classes.tabsList,
        tab: classes.tab
      }}
    >
      <Tabs.List>
        {tabs.map((tab, index) => {
          const isSelected = value === index;
          const iconPath = iconImageMap[tab.iconName] || iconImageMap['TROPHY'];

          return (
            <Tabs.Tab
              key={tab.id}
              value={index.toString()}
              disabled={tab.disabled}
              title={tab.tooltip}
            >
              <Box style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.xs }}>
                <Box className={classes.iconContainer} style={iconSize}>
                  <img
                    src={iconPath}
                    alt={tab.iconName}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                    }}
                  />
                </Box>
                <Text
                  weight={600}
                  style={{
                    textShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.3)' : 'none',
                    transition: 'all 0.3s ease',
                  }}
                >
                  {tab.label}
                </Text>
                {tab.badge && tab.badge > 0 && (
                  <Badge
                    color="red"
                    size="sm"
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.red[6]}, ${theme.colors.orange[6]})`,
                      color: 'white',
                      fontWeight: 700,
                      fontSize: '0.7rem',
                      minWidth: 18,
                      height: 18,
                      borderRadius: 9,
                      boxShadow: `0 0 10px ${theme.colors.red[5]}`,
                    }}
                  >
                    {tab.badge}
                  </Badge>
                )}
              </Box>
            </Tabs.Tab>
          );
        })}
      </Tabs.List>
    </Tabs>
  );
};