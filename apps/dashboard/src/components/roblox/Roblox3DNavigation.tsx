import React, { useState } from 'react';
import { Box, Text, Paper, Stack, useMantineTheme } from '@mantine/core';
import { Roblox3DButton } from './Roblox3DButton';
import { Roblox3DTabs } from './Roblox3DTabs';

interface NavigationItem {
  id: string;
  label: string;
  iconName: string;
  path?: string;
  badge?: number;
  disabled?: boolean;
  tooltip?: string;
  children?: NavigationItem[];
}

interface Roblox3DNavigationProps {
  items: NavigationItem[];
  onItemClick: (item: NavigationItem) => void;
  orientation?: 'horizontal' | 'vertical';
  variant?: 'buttons' | 'tabs' | 'mixed';
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  glowEffect?: boolean;
  showLabels?: boolean;
  compact?: boolean;
}

// Removed animations for Mantine v8 compatibility

const useStyles = (params: { orientation: string; variant: string }) => {
  const theme = useMantineTheme();
  const { orientation, variant } = params;

  return {
    classes: {
  styledNavigation: {
    background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
    border: `1px solid ${theme.colors.blue[2]}`,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    boxShadow: `0 8px 32px ${theme.colors.blue[1]}`,
    backdropFilter: 'blur(10px)',
    
    ...(orientation === 'vertical' && {
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing.xs,
    }),

    ...(orientation === 'horizontal' && {
      display: 'flex',
      flexDirection: 'row',
      gap: theme.spacing.sm,
      alignItems: 'center',
      flexWrap: 'wrap',
    }),

    ...(variant === 'tabs' && {
      padding: theme.spacing.xs,
      background: `linear-gradient(135deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
    }),
  },

  navigationHeader: {
    marginBottom: theme.spacing.md,
    paddingBottom: theme.spacing.sm,
    borderBottom: `2px solid ${theme.colors.blue[2]}`,

    '& .mantine-Text-root': {
      background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      fontWeight: 800,
      textShadow: '0 2px 4px rgba(0,0,0,0.1)',
    },
  },

  subNavigation: {
    marginLeft: theme.spacing.lg,
    marginTop: theme.spacing.xs,
    padding: theme.spacing.sm,
    background: `linear-gradient(145deg, ${theme.colors.blue[0]}, ${theme.colors.violet[0]})`,
    borderRadius: theme.radius.sm,
    border: `1px solid ${theme.colors.blue[1]}`,
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.xs,
        }
    }
  };
};

export const Roblox3DNavigation: React.FunctionComponent<Roblox3DNavigationProps> = ({
  items,
  onItemClick,
  orientation = 'horizontal',
  variant = 'buttons',
  size = 'medium',
  animated = true,
  glowEffect = true,
  showLabels = true,
  compact = false,
}) => {
  const theme = useMantineTheme();
  const { classes } = useStyles({ orientation, variant });
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [activeItem, setActiveItem] = useState<string | null>(null);

  const handleItemClick = (item: NavigationItem) => {
    setActiveItem(item.id);
    onItemClick(item);

    if (item.children && item.children.length > 0) {
      const newExpanded = new Set(expandedItems);
      if (newExpanded.has(item.id)) {
        newExpanded.delete(item.id);
      } else {
        newExpanded.add(item.id);
      }
      setExpandedItems(newExpanded);
    }
  };

  const renderNavigationItem = (item: NavigationItem, index: number) => {
    const isActive = activeItem === item.id;
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;

    if (variant === 'buttons') {
      return (
        <Box key={item.id} style={{ position: 'relative' }}>
          <Roblox3DButton
            iconName={item.iconName}
            label={showLabels ? item.label : undefined}
            onClick={() => handleItemClick(item)}
            variant={isActive ? 'primary' : 'secondary'}
            size={size}
            disabled={item.disabled}
            tooltip={item.tooltip}
            animated={animated}
            glowEffect={glowEffect}
            fullWidth={orientation === 'vertical'}
          />

          {hasChildren && isExpanded && (
            <Box className={classes.subNavigation}>
              {item.children!.map((child, childIndex) => (
                <Box key={child.id} style={{ position: 'relative' }}>
                  <Roblox3DButton
                    iconName={child.iconName}
                    label={showLabels ? child.label : undefined}
                    onClick={() => handleItemClick(child)}
                    variant={isActive ? 'primary' : 'info'}
                    size="small"
                    disabled={child.disabled}
                    tooltip={child.tooltip}
                    animated={animated}
                    glowEffect={glowEffect}
                    fullWidth
                  />
                </Box>
              ))}
            </Box>
          )}
        </Box>
      );
    }

    if (variant === 'tabs') {
      const tabItems = items.map(item => ({
        id: item.id,
        label: showLabels ? item.label : '',
        iconName: item.iconName,
        badge: item.badge,
        disabled: item.disabled,
        tooltip: item.tooltip,
      }));

      return (
        <Roblox3DTabs
          key={`tabs-${index}`}
          tabs={tabItems}
          value={items.findIndex(i => i.id === activeItem) || 0}
          onChange={(event, newValue) => {
            const selectedItem = items[newValue];
            if (selectedItem) {
              handleItemClick(selectedItem);
            }
          }}
          orientation={orientation}
          variant="standard"
          size={size}
          animated={animated}
          glowEffect={glowEffect}
        />
      );
    }

    // Mixed variant - buttons for main items, tabs for sub-items
    return (
      <Box key={item.id} style={{ position: 'relative' }}>
        <Roblox3DButton
          iconName={item.iconName}
          label={showLabels ? item.label : undefined}
          onClick={() => handleItemClick(item)}
          variant={isActive ? 'primary' : 'secondary'}
          size={size}
          disabled={item.disabled}
          tooltip={item.tooltip}
          animated={animated}
          glowEffect={glowEffect}
          fullWidth={orientation === 'vertical'}
        />

        {hasChildren && isExpanded && (
          <Box className={classes.subNavigation}>
            <Text size="xs" color="dimmed" mb="xs">
              {item.label} Options:
            </Text>
            {item.children!.map((child, childIndex) => (
              <Box key={child.id} style={{ position: 'relative' }}>
                <Roblox3DButton
                  iconName={child.iconName}
                  label={showLabels ? child.label : undefined}
                  onClick={() => handleItemClick(child)}
                  variant={isActive ? 'primary' : 'info'}
                  size="small"
                  disabled={child.disabled}
                  tooltip={child.tooltip}
                  animated={animated}
                  glowEffect={glowEffect}
                  fullWidth
                />
              </Box>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Paper
      className={classes.styledNavigation}
      shadow="none"
    >
      {!compact && (
        <Box className={classes.navigationHeader}>
          <Text size="lg" weight={700}>
            🚀 Navigation Hub
          </Text>
        </Box>
      )}

      <Stack
        spacing={orientation === 'vertical' ? theme.spacing.xs : theme.spacing.sm}
        style={{
          ...(orientation === 'horizontal' && {
            flexDirection: 'row',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }),
        }}
      >
        {items.map((item, index) => renderNavigationItem(item, index))}
      </Stack>
    </Paper>
  );
};