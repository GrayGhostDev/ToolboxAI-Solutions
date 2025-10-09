// Global type definitions for ToolBoxAI Dashboard
// Updated for Mantine migration

import type * as React from 'react';

// Mantine component type declarations for global usage
declare global {
  // Common utility types
  type ComponentPropsWithoutRef<T extends React.ElementType> = React.ComponentPropsWithoutRef<T>;
  type ComponentPropsWithRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>;

  // Layout types
  type SpacingValue = number | string;
  type ColorScheme = 'light' | 'dark';
  type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  type Radius = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

  // Common prop patterns
  interface BaseProps {
    className?: string;
    style?: React.CSSProperties;
    children?: React.ReactNode;
  }

  interface SpacingProps {
    m?: SpacingValue;
    mx?: SpacingValue;
    my?: SpacingValue;
    mt?: SpacingValue;
    mb?: SpacingValue;
    ml?: SpacingValue;
    mr?: SpacingValue;
    p?: SpacingValue;
    px?: SpacingValue;
    py?: SpacingValue;
    pt?: SpacingValue;
    pb?: SpacingValue;
    pl?: SpacingValue;
    pr?: SpacingValue;
  }

  // Mantine specific
  interface MantineStyleProp {
    sx?: any; // For backward compatibility with MUI sx prop
  }

  // Legacy MUI component mappings (for compatibility during migration)
  namespace MUI {
    type AlertProps = ComponentPropsWithoutRef<'div'> & {
      severity?: 'error' | 'warning' | 'info' | 'success';
      variant?: 'filled' | 'outlined' | 'standard';
    };

    type ButtonProps = ComponentPropsWithoutRef<'button'> & {
      variant?: 'contained' | 'outlined' | 'text';
      color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
      size?: 'small' | 'medium' | 'large';
      fullWidth?: boolean;
      disabled?: boolean;
      loading?: boolean;
    };

    type ChipProps = ComponentPropsWithoutRef<'div'> & {
      label?: React.ReactNode;
      color?: string;
      variant?: 'filled' | 'outlined';
      size?: 'small' | 'medium';
      onDelete?: () => void;
    };

    type BoxProps = ComponentPropsWithoutRef<'div'> & SpacingProps & MantineStyleProp;

    type TypographyProps = ComponentPropsWithoutRef<'span'> & {
      variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'subtitle1' | 'subtitle2';
      component?: React.ElementType;
      color?: string;
      align?: 'left' | 'center' | 'right';
      gutterBottom?: boolean;
    };

    type CardProps = ComponentPropsWithoutRef<'div'> & {
      elevation?: number;
      variant?: 'elevation' | 'outlined';
    };

    type GridProps = ComponentPropsWithoutRef<'div'> & {
      container?: boolean;
      item?: boolean;
      xs?: number | boolean;
      sm?: number | boolean;
      md?: number | boolean;
      lg?: number | boolean;
      xl?: number | boolean;
      spacing?: number;
    };

    type ContainerProps = ComponentPropsWithoutRef<'div'> & {
      maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
      fixed?: boolean;
    };

    type StackProps = ComponentPropsWithoutRef<'div'> & {
      direction?: 'row' | 'column';
      spacing?: number | string;
      divider?: React.ReactNode;
      alignItems?: string;
      justifyContent?: string;
    };

    type TextFieldProps = ComponentPropsWithoutRef<'input'> & {
      label?: string;
      variant?: 'outlined' | 'filled' | 'standard';
      fullWidth?: boolean;
      multiline?: boolean;
      rows?: number;
      type?: string;
      helperText?: string;
      error?: boolean;
      InputProps?: any;
      inputProps?: any;
    };

    type SelectProps = ComponentPropsWithoutRef<'select'> & {
      value?: any;
      onChange?: (event: any) => void;
      fullWidth?: boolean;
      variant?: 'outlined' | 'filled' | 'standard';
    };

    type DialogProps = ComponentPropsWithoutRef<'div'> & {
      open: boolean;
      onClose?: () => void;
      maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
      fullWidth?: boolean;
      fullScreen?: boolean;
    };

    type TabProps = ComponentPropsWithoutRef<'div'> & {
      label?: React.ReactNode;
      value?: any;
      disabled?: boolean;
    };

    type TabsProps = ComponentPropsWithoutRef<'div'> & {
      value?: any;
      onChange?: (event: any, newValue: any) => void;
      orientation?: 'horizontal' | 'vertical';
      variant?: 'standard' | 'scrollable' | 'fullWidth';
    };

    type ProgressProps = ComponentPropsWithoutRef<'div'> & {
      value?: number;
      variant?: 'determinate' | 'indeterminate';
      color?: string;
      size?: number | string;
    };
  }
}

// Window interface extensions
declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION__?: any;
    __TOOLBOXAI_CONFIG__?: {
      apiUrl: string;
      wsUrl: string;
      version: string;
    };
    // Mantine theme provider support
    __MANTINE_COLOR_SCHEME__?: 'light' | 'dark';
  }
}

// Environment variables
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test';
    VITE_API_BASE_URL?: string;
    VITE_WS_URL?: string;
    VITE_ENABLE_WEBSOCKET?: string;
    VITE_PUSHER_KEY?: string;
    VITE_PUSHER_CLUSTER?: string;
    VITE_PUSHER_AUTH_ENDPOINT?: string;
    VITE_ENABLE_CLERK_AUTH?: string;
    VITE_CLERK_PUBLISHABLE_KEY?: string;
  }
}

// Vite environment variables
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_ENABLE_WEBSOCKET: string;
  readonly VITE_PUSHER_KEY: string;
  readonly VITE_PUSHER_CLUSTER: string;
  readonly VITE_PUSHER_AUTH_ENDPOINT: string;
  readonly VITE_ENABLE_CLERK_AUTH: string;
  readonly VITE_CLERK_PUBLISHABLE_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Roblox theme specific types
declare global {
  namespace Roblox {
    type ColorMode = 'light' | 'dark' | 'system';

    interface ThemeColors {
      primary: string;
      secondary: string;
      background: string;
      surface: string;
      text: string;
      textSecondary: string;
      success: string;
      error: string;
      warning: string;
      info: string;
    }

    interface Theme {
      mode: ColorMode;
      colors: ThemeColors;
      typography: {
        fontFamily: string;
        h1: any;
        h2: any;
        h3: any;
        h4: any;
        h5: any;
        h6: any;
      };
    }
  }
}

export {};