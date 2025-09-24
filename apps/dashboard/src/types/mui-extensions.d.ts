/**
 * MUI Theme Extensions
 * Fixes theme.palette property access errors
 */

declare module '@mui/material/styles' {
  interface Palette {
    default: {
      main: string;
      light: string;
      dark: string;
      contrastText: string;
    };
  }

  interface PaletteOptions {
    default?: {
      main: string;
      light?: string;
      dark?: string;
      contrastText?: string;
    };
  }
}

declare module '@mui/material/Button' {
  interface ButtonPropsColorOverrides {
    default: true;
  }
}

declare module '@mui/material/Chip' {
  interface ChipPropsColorOverrides {
    default: true;
  }
}

declare module '@mui/material/Alert' {
  interface AlertPropsColorOverrides {
    default: true;
  }
}

declare module '@mui/material/IconButton' {
  interface IconButtonPropsColorOverrides {
    default: true;
  }
}

// Additional MUI component type fixes
declare module '@mui/material' {
  interface Components {
    MuiDivider?: {
      defaultProps?: Partial<import('@mui/material/Divider').DividerProps>;
      styleOverrides?: any;
    };
  }
}

// Fix for missing Divider export in some contexts
declare global {
  namespace JSX {
    interface IntrinsicElements {
      divider: any;
    }
  }
}