import React, { useState } from 'react';
import { 
  Box, 
  useTheme, 
  alpha, 
  keyframes, 
  styled,
  Typography,
  Paper,
  Stack
} from '@mui/material';
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

// Animations
const slideInAnimation = keyframes`
  0% { transform: translateX(-100%); opacity: 0; }
  100% { transform: translateX(0); opacity: 1; }
`;

const fadeInAnimation = keyframes`
  0% { opacity: 0; transform: scale(0.9); }
  100% { opacity: 1; transform: scale(1); }
`;

const StyledNavigation = styled(Paper)(({ theme, orientation, variant }: any) => ({
  background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
  borderRadius: 16,
  padding: 16,
  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.1)}`,
  backdropFilter: 'blur(10px)',
  animation: `${slideInAnimation} 0.5s ease-out`,
  
  ...(orientation === 'vertical' && {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  }),
  
  ...(orientation === 'horizontal' && {
    display: 'flex',
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
    flexWrap: 'wrap',
  }),
  
  ...(variant === 'tabs' && {
    padding: 8,
    background: `linear-gradient(135deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.02)})`,
  }),
}));

const NavigationHeader = styled(Box)(({ theme }) => ({
  marginBottom: 16,
  paddingBottom: 12,
  borderBottom: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
  
  '& .MuiTypography-root': {
    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    fontWeight: 800,
    textShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
}));

const SubNavigation = styled(Box)(({ theme, isOpen }: any) => ({
  marginLeft: 24,
  marginTop: 8,
  padding: 12,
  background: `linear-gradient(145deg, ${alpha(theme.palette.primary.main, 0.05)}, ${alpha(theme.palette.secondary.main, 0.02)})`,
  borderRadius: 12,
  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
  display: isOpen ? 'flex' : 'none',
  flexDirection: 'column',
  gap: 8,
  animation: isOpen ? `${fadeInAnimation} 0.3s ease-out` : 'none',
}));

export const Roblox3DNavigation: React.FC<Roblox3DNavigationProps> = ({
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
  const theme = useTheme();
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
        <Box key={item.id} sx={{ position: 'relative' }}>
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
          
          {hasChildren && (
            <SubNavigation isOpen={isExpanded}>
              {item.children!.map((child, childIndex) => (
                <Box key={child.id} sx={{ position: 'relative' }}>
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
            </SubNavigation>
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
      <Box key={item.id} sx={{ position: 'relative' }}>
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
        
        {hasChildren && (
          <SubNavigation isOpen={isExpanded}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
              {item.label} Options:
            </Typography>
            {item.children!.map((child, childIndex) => (
              <Box key={child.id} sx={{ position: 'relative' }}>
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
          </SubNavigation>
        )}
      </Box>
    );
  };

  return (
    <StyledNavigation
      orientation={orientation}
      variant={variant}
      elevation={0}
    >
      {!compact && (
        <NavigationHeader>
          <Typography variant="h6">
            🚀 Navigation Hub
          </Typography>
        </NavigationHeader>
      )}
      
      <Stack
        direction={orientation === 'vertical' ? 'column' : 'row'}
        spacing={orientation === 'vertical' ? 1 : 2}
        sx={{
          ...(orientation === 'horizontal' && {
            flexWrap: 'wrap',
            justifyContent: 'center',
          }),
        }}
      >
        {items.map((item, index) => renderNavigationItem(item, index))}
      </Stack>
    </StyledNavigation>
  );
};
