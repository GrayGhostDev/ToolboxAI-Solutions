import React from 'react';
import { ActionIcon, Menu, Text, Box, Tooltip } from '@mantine/core';
import { IconSun, IconMoon, IconDeviceDesktop, IconCheck } from '@tabler/icons-react';
import { useThemeContext } from '../contexts/ThemeContext';
import { designTokens } from '../theme/designTokens';

interface ThemeSwitcherProps {
  variant?: 'icon' | 'button' | 'menu';
  showLabel?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

const ThemeSwitcher: React.FunctionComponent<ThemeSwitcherProps> = ({
  variant = 'icon',
  showLabel = false,
  size = 'md'
}) => {
  const { mode, actualMode, toggleTheme, setThemeMode } = useThemeContext();
  const [opened, setOpened] = React.useState(false);

  const handleClick = () => {
    if (variant === 'menu') {
      setOpened((o) => !o);
    } else {
      toggleTheme();
    }
  };

  const handleModeSelect = (selectedMode: 'light' | 'dark' | 'system') => {
    setThemeMode(selectedMode);
    setOpened(false);
  };

  const getIcon = () => {
    if (mode === 'system') {
      return <IconDeviceDesktop size={16} />;
    }
    return actualMode === 'dark' ? <IconSun size={16} /> : <IconMoon size={16} />;
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
      icon: <IconSun size={16} />,
      description: 'Always use light theme'
    },
    {
      mode: 'dark' as const,
      label: 'Dark',
      icon: <IconMoon size={16} />,
      description: 'Always use dark theme'
    },
    {
      mode: 'system' as const,
      label: 'System',
      icon: <IconDeviceDesktop size={16} />,
      description: 'Use system preference'
    }
  ];

  if (variant === 'button') {
    return (
      <Box
        component="button"
        onClick={handleClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: designTokens.spacing[2],
          borderRadius: designTokens.borderRadius.lg,
          border: '1px solid var(--mantine-color-gray-4)',
          backgroundColor: 'transparent',
          color: 'var(--mantine-color-text)',
          cursor: 'pointer',
          transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--mantine-color-gray-1)';
          e.currentTarget.style.borderColor = 'var(--mantine-color-blue-6)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
          e.currentTarget.style.borderColor = 'var(--mantine-color-gray-4)';
        }}
        onFocus={(e) => {
          e.currentTarget.style.outline = '2px solid var(--mantine-color-blue-6)';
          e.currentTarget.style.outlineOffset = '2px';
        }}
        onBlur={(e) => {
          e.currentTarget.style.outline = 'none';
        }}
      >
        {getIcon()}
        {showLabel && (
          <Text size="sm">
            {getLabel()}
          </Text>
        )}
      </Box>
    );
  }

  const iconButton = (
    <ActionIcon
      onClick={handleClick}
      size={size}
      variant="subtle"
      aria-label="Toggle theme"
    >
      {getIcon()}
    </ActionIcon>
  );

  if (variant === 'menu') {
    return (
      <Menu
        opened={opened}
        onChange={setOpened}
        position="bottom-end"
        withArrow
        shadow="md"
        width={200}
      >
        <Menu.Target>
          <Tooltip label={getTooltip()} position="bottom">
            {iconButton}
          </Tooltip>
        </Menu.Target>

        <Menu.Dropdown>
          {themeOptions.map((option) => (
            <Menu.Item
              key={option.mode}
              onClick={() => handleModeSelect(option.mode)}
              leftSection={option.icon}
              rightSection={mode === option.mode ? <IconCheck size={16} /> : null}
              style={{
                borderRadius: designTokens.borderRadius.lg,
                ...(mode === option.mode && {
                  backgroundColor: 'var(--mantine-color-blue-1)',
                })
              }}
            >
              <Box>
                <Text size="sm" fw={mode === option.mode ? 600 : 400}>
                  {option.label}
                </Text>
                <Text size="xs" c="dimmed">
                  {option.description}
                </Text>
              </Box>
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    );
  }

  return (
    <Tooltip label={getTooltip()} position="bottom">
      {iconButton}
    </Tooltip>
  );
};

export default ThemeSwitcher;