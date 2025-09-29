// MUI Type Shims
declare module '@/utils/mui-imports' {
  export * from '@mantine/core';
  export * from '@mantine/core';
}

declare module '@mantine/core' {
  export * from '@mantine/core';
}

declare module '@mantine/core' {
  export const createStyles: any;
  export const MantineProvider: any;
  export const useMantineTheme: any;
}
