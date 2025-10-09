// Mantine Type Extensions
declare module '@mantine/core' {
  // Ensure all Mantine exports are available
  export * from '@mantine/core';
}

// Legacy type compatibility for migration
declare module '@mantine/theme' {
  interface MantineTheme {
    // Extended theme properties for custom styling
    shadows: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
  }
}
