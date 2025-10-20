import React from 'react';
import { Box, Tabs, Text, Badge, useMantineTheme } from '@mantine/core';

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

// CSS animations defined in a style tag
const animationStyles = `
  @keyframes float-animation {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-2px) rotate(1deg); }
  }

  @keyframes pulse-animation {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  }

  @keyframes glow-animation {
    0% { box-shadow: 0 0 5px currentColor; }
    50% { box-shadow: 0 0 15px currentColor, 0 0 25px currentColor; }
    100% { box-shadow: 0 0 5px currentColor; }
  }

  @keyframes shimmer-animation {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
`;

// Mantine-compatible styled component approach
const getTabContainerStyles = (theme: any, { orientation, animated, size, glowEffect }: any) => {
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
      backgroundColor: 'transparent',
      borderRadius: theme.radius.lg,
      padding: theme.spacing.xs,
    },
    tab: {
      position: 'relative',
      border: '2px solid transparent',
      borderRadius: theme.radius.md,
      background: `linear-gradient(145deg, ${theme.colors.gray[1]}, ${theme.colors.gray[2]})`,
      cursor: 'pointer',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      overflow: 'hidden',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      ...(animated && {
        animation: 'float-animation 3s ease-in-out infinite',
      }),
      ...(glowEffect && {
        animation: 'glow-animation 2s ease-in-out infinite',
      }),
      ...sizeStyles[size as keyof typeof sizeStyles],
      // Removed pseudo-selectors as they are not supported in inline styles
    },
    shimmer: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)',
      animation: 'shimmer-animation 2s ease-in-out infinite',
      pointerEvents: 'none',
    },
    badge: {
      position: 'absolute',
      top: -8,
      right: -8,
      minWidth: 20,
      height: 20,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.colors.red[6],
      color: theme.colors.white,
      borderRadius: '50%',
      fontSize: '0.75rem',
      fontWeight: 700,
      border: `2px solid ${theme.colors.white}`,
      boxShadow: theme.shadows.sm,
    }
  };
};

export const Roblox3DTabs: React.FunctionComponent<Roblox3DTabsProps> = ({
  tabs,
  value,
  onChange,
  orientation = 'horizontal',
  variant = 'standard',
  size = 'medium',
  animated = true,
  glowEffect = false
}) => {
  const theme = useMantineTheme();

  // Inject animation styles once
  React.useEffect(() => {
    const styleId = 'roblox3d-tabs-animations';
    if (!document.getElementById(styleId)) {
      const styleElement = document.createElement('style');
      styleElement.id = styleId;
      styleElement.innerHTML = animationStyles;
      document.head.appendChild(styleElement);
    }
  }, []);

  const styles = getTabContainerStyles(theme, { orientation, animated, size, glowEffect });

  return (
    <Box>
      <Tabs
        value={value.toString()}
        onTabChange={(value: string | null) => onChange({} as React.SyntheticEvent, parseInt(value || '0', 10))}
        orientation={orientation}
        variant={variant}
        styles={{
          list: styles.tabsList,
          tab: styles.tab,
        }}
      >
        <Tabs.List>
          {tabs.map((tab, index) => (
            <Tabs.Tab
              key={tab.id}
              value={index.toString()}
              disabled={tab.disabled}
              style={{ position: 'relative' }}
            >
              <Box style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.xs }}>
                <Text size={size} weight={600}>
                  {tab.label}
                </Text>

                {/* Badge */}
                {tab.badge && tab.badge > 0 && (
                  <Badge
                    size="sm"
                    color="red"
                    style={styles.badge}
                  >
                    {tab.badge > 99 ? '99+' : tab.badge}
                  </Badge>
                )}

                {/* Shimmer effect for active tabs */}
                {value === index && animated && (
                  <Box style={styles.shimmer} />
                )}
              </Box>
            </Tabs.Tab>
          ))}
        </Tabs.List>
      </Tabs>
    </Box>
  );
};

export default Roblox3DTabs;