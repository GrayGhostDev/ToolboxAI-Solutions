import React from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Box,
  Typography,
  useTheme
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  SettingsBrightness,
  Check
} from '@mui/icons-material';
import { useThemeContext } from '../contexts/ThemeContext';
import { designTokens } from '../theme/designTokens';

interface ThemeSwitcherProps {
  variant?: 'icon' | 'button' | 'menu';
  showLabel?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({
  variant = 'icon',
  showLabel = false,
  size = 'medium'
}) => {
  const theme = useTheme();
  const { mode, actualMode, toggleTheme, setThemeMode } = useThemeContext();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    if (variant === 'menu') {
      setAnchorEl(event.currentTarget);
    } else {
      toggleTheme();
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleModeSelect = (selectedMode: 'light' | 'dark' | 'system') => {
    setThemeMode(selectedMode);
    handleClose();
  };

  const getIcon = () => {
    if (mode === 'system') {
      return <SettingsBrightness />;
    }
    return actualMode === 'dark' ? <Brightness7 /> : <Brightness4 />;
  };

  const getTooltip = () => {
    if (mode === 'system') {
      return `System theme (${actualMode})`;
    }
    return `Switch to ${actualMode === 'dark' ? 'light' : 'dark'} mode`;
  };

  const getLabel = () => {
    if (mode === 'system') {
      return `System (${actualMode})`;
    }
    return actualMode === 'dark' ? 'Dark' : 'Light';
  };

  const themeOptions = [
    {
      mode: 'light' as const,
      label: 'Light',
      icon: <Brightness7 />,
      description: 'Always use light theme'
    },
    {
      mode: 'dark' as const,
      label: 'Dark',
      icon: <Brightness4 />,
      description: 'Always use dark theme'
    },
    {
      mode: 'system' as const,
      label: 'System',
      icon: <SettingsBrightness />,
      description: 'Use system preference'
    }
  ];

  if (variant === 'button') {
    return (
      <Box
        component="button"
        onClick={handleClick}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          padding: designTokens.spacing[2],
          borderRadius: designTokens.borderRadius.lg,
          border: `1px solid ${theme.palette.divider}`,
          backgroundColor: 'transparent',
          color: theme.palette.text.primary,
          cursor: 'pointer',
          transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
          '&:hover': {
            backgroundColor: theme.palette.action.hover,
            borderColor: theme.palette.primary.main
          },
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: '2px'
          }
        }}
      >
        {getIcon()}
        {showLabel && (
          <Typography variant="body2" component="span">
            {getLabel()}
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <>
      <Tooltip title={getTooltip()} placement="bottom">
        <IconButton
          onClick={handleClick}
          size={size}
          sx={{
            color: theme.palette.text.primary,
            '&:hover': {
              backgroundColor: theme.palette.action.hover,
              color: theme.palette.primary.main
            }
          }}
          aria-label="Toggle theme"
          aria-controls={open ? 'theme-menu' : undefined}
          aria-haspopup={variant === 'menu' ? 'true' : undefined}
          aria-expanded={variant === 'menu' && open ? 'true' : undefined}
        >
          {getIcon()}
        </IconButton>
      </Tooltip>

      {variant === 'menu' && (
        <Menu
          id="theme-menu"
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          MenuListProps={{
            'aria-labelledby': 'theme-button',
            dense: true
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{
            sx: {
              minWidth: 200,
              mt: 1,
              borderRadius: designTokens.borderRadius.xl,
              boxShadow: designTokens.shadows.lg
            }
          }}
        >
          {themeOptions.map((option) => (
            <MenuItem
              key={option.mode}
              onClick={() => handleModeSelect(option.mode)}
              selected={mode === option.mode}
              sx={{
                borderRadius: designTokens.borderRadius.lg,
                mx: 1,
                my: 0.5,
                '&.Mui-selected': {
                  backgroundColor: theme.palette.primary.main + '20',
                  '&:hover': {
                    backgroundColor: theme.palette.primary.main + '30'
                  }
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {option.icon}
              </ListItemIcon>
              <ListItemText
                primary={option.label}
                secondary={option.description}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: mode === option.mode ? 'bold' : 'normal'
                }}
                secondaryTypographyProps={{
                  variant: 'caption'
                }}
              />
              {mode === option.mode && (
                <Check
                  sx={{
                    color: theme.palette.primary.main,
                    ml: 1
                  }}
                />
              )}
            </MenuItem>
          ))}
        </Menu>
      )}
    </>
  );
};

export default ThemeSwitcher;
