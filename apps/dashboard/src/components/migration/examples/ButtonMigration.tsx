import React from 'react';
import { Button as MuiButton } from '@mui/material';
import { Button as MantineButton } from '@mantine/core';
import { MigrationWrapper } from '../MigrationWrapper';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'contained' | 'outlined' | 'text';
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  onClick?: () => void;
  fullWidth?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  loading?: boolean;
}

// MUI version of the button
const MuiButtonVersion: React.FC<ButtonProps> = ({
  children,
  variant = 'contained',
  color = 'primary',
  size = 'medium',
  disabled = false,
  onClick,
  fullWidth = false,
  startIcon,
  endIcon,
  loading = false,
}) => (
  <MuiButton
    variant={variant}
    color={color}
    size={size}
    disabled={disabled || loading}
    onClick={onClick}
    fullWidth={fullWidth}
    startIcon={loading ? undefined : startIcon}
    endIcon={loading ? undefined : endIcon}
    sx={{
      textTransform: 'none',
      fontWeight: 600,
    }}
  >
    {loading ? 'Loading...' : children}
  </MuiButton>
);

// Mantine version of the button
const MantineButtonVersion: React.FC<ButtonProps> = ({
  children,
  variant = 'contained',
  color = 'primary',
  size = 'medium',
  disabled = false,
  onClick,
  fullWidth = false,
  startIcon,
  endIcon,
  loading = false,
}) => {
  // Map MUI props to Mantine props
  const mantineVariant = variant === 'contained' ? 'filled' : variant === 'outlined' ? 'outline' : 'subtle';
  const mantineColor = color === 'primary' ? 'roblox-cyan' :
                      color === 'secondary' ? 'roblox-purple' :
                      color === 'error' ? 'roblox-red' :
                      color === 'warning' ? 'roblox-orange' :
                      color === 'info' ? 'roblox-blue' :
                      color === 'success' ? 'roblox-green' : 'roblox-cyan';

  const mantineSize = size === 'small' ? 'sm' : size === 'large' ? 'lg' : 'md';

  return (
    <MantineButton
      variant={mantineVariant}
      color={mantineColor}
      size={mantineSize}
      disabled={disabled}
      onClick={onClick}
      fullWidth={fullWidth}
      leftSection={loading ? undefined : startIcon}
      rightSection={loading ? undefined : endIcon}
      loading={loading}
    >
      {children}
    </MantineButton>
  );
};

// Migrated button component
export const MigratedButton: React.FC<ButtonProps> = (props) => {
  return (
    <MigrationWrapper
      componentId="button"
      muiComponent={<MuiButtonVersion {...props} />}
      mantineComponent={<MantineButtonVersion {...props} />}
    />
  );
};

// Example usage component
export const ButtonMigrationExample: React.FC = () => {
  const [loading, setLoading] = React.useState(false);

  const handleClick = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h3>Button Migration Example</h3>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <MigratedButton variant="contained" color="primary">
          Primary Button
        </MigratedButton>

        <MigratedButton variant="outlined" color="secondary">
          Secondary Button
        </MigratedButton>

        <MigratedButton variant="text" color="info">
          Text Button
        </MigratedButton>

        <MigratedButton
          variant="contained"
          color="success"
          loading={loading}
          onClick={handleClick}
        >
          Loading Button
        </MigratedButton>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <MigratedButton variant="contained" size="small">
          Small
        </MigratedButton>

        <MigratedButton variant="contained" size="medium">
          Medium
        </MigratedButton>

        <MigratedButton variant="contained" size="large">
          Large
        </MigratedButton>
      </div>

      <div>
        <MigratedButton variant="contained" fullWidth>
          Full Width Button
        </MigratedButton>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <MigratedButton variant="contained" color="error">
          Error
        </MigratedButton>

        <MigratedButton variant="contained" color="warning">
          Warning
        </MigratedButton>

        <MigratedButton variant="contained" disabled>
          Disabled
        </MigratedButton>
      </div>
    </div>
  );
};