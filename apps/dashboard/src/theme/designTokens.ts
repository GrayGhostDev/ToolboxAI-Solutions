/**
 * Design Tokens System for Roblox-Inspired Dashboard
 * 
 * This file contains all design tokens including:
 * - Color palettes (light/dark modes)
 * - Typography scales
 * - Spacing system
 * - Elevation/shadows
 * - Border radius
 * - Transitions/animations
 */

export const designTokens = {
  // Color System
  colors: {
    // Primary Roblox red with variants
    primary: {
      50: '#FFF0F0',
      100: '#FFE1E1',
      200: '#FFC7C7',
      300: '#FF9D9D',
      400: '#FF6464',
      500: '#E2231A', // Main Roblox red
      600: '#CC1F17',
      700: '#B71C15',
      800: '#9A1812',
      900: '#7D1410',
      950: '#4A0C09'
    },
    
    // Secondary dark gray
    secondary: {
      50: '#F7F7F8',
      100: '#EEEEF0',
      200: '#D9D9DC',
      300: '#B8B8BD',
      400: '#909097',
      500: '#6E6E76',
      600: '#5A5A61',
      700: '#4A4A50',
      800: '#393B3D', // Main Roblox dark gray
      900: '#2A2C2E',
      950: '#1A1C1E'
    },
    
    // Success green
    success: {
      50: '#F0FDF4',
      100: '#DCFCE7',
      200: '#BBF7D0',
      300: '#86EFAC',
      400: '#4ADE80',
      500: '#22C55E',
      600: '#16A34A',
      700: '#15803D',
      800: '#166534',
      900: '#14532D'
    },
    
    // Warning orange
    warning: {
      50: '#FFFBEB',
      100: '#FEF3C7',
      200: '#FDE68A',
      300: '#FCD34D',
      400: '#FBBF24',
      500: '#F59E0B',
      600: '#D97706',
      700: '#B45309',
      800: '#92400E',
      900: '#78350F'
    },
    
    // Error red (different from primary)
    error: {
      50: '#FEF2F2',
      100: '#FEE2E2',
      200: '#FECACA',
      300: '#FCA5A5',
      400: '#F87171',
      500: '#EF4444',
      600: '#DC2626',
      700: '#B91C1C',
      800: '#991B1B',
      900: '#7F1D1D'
    },
    
    // Info blue
    info: {
      50: '#EFF6FF',
      100: '#DBEAFE',
      200: '#BFDBFE',
      300: '#93C5FD',
      400: '#60A5FA',
      500: '#3B82F6',
      600: '#2563EB',
      700: '#1D4ED8',
      800: '#1E40AF',
      900: '#1E3A8A'
    },
    
    // Gamification colors
    gamification: {
      xp: '#8B5CF6',        // Purple for XP
      level: '#F59E0B',     // Gold for levels
      badge: '#10B981',     // Emerald for badges
      achievement: '#F97316', // Orange for achievements
      streak: '#EF4444',    // Red for streaks
      coin: '#FCD34D',      // Yellow for coins
      gem: '#A855F7',       // Violet for gems
      star: '#FBBF24'       // Amber for stars
    },
    
    // Neutral grays
    neutral: {
      0: '#FFFFFF',
      50: '#F9FAFB',
      100: '#F3F4F6',
      200: '#E5E7EB',
      300: '#D1D5DB',
      400: '#9CA3AF',
      500: '#6B7280',
      600: '#4B5563',
      700: '#374151',
      800: '#1F2937',
      900: '#111827',
      950: '#030712'
    }
  },
  
  // Typography Scale
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
      mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      display: ['Fredoka One', 'Inter', 'system-ui', 'sans-serif'] // Fun, game-like font for headings
    },
    
    fontSize: {
      xs: ['0.75rem', { lineHeight: '1rem' }],
      sm: ['0.875rem', { lineHeight: '1.25rem' }],
      base: ['1rem', { lineHeight: '1.5rem' }],
      lg: ['1.125rem', { lineHeight: '1.75rem' }],
      xl: ['1.25rem', { lineHeight: '1.75rem' }],
      '2xl': ['1.5rem', { lineHeight: '2rem' }],
      '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      '5xl': ['3rem', { lineHeight: '1' }],
      '6xl': ['3.75rem', { lineHeight: '1' }],
      '7xl': ['4.5rem', { lineHeight: '1' }],
      '8xl': ['6rem', { lineHeight: '1' }],
      '9xl': ['8rem', { lineHeight: '1' }]
    },
    
    fontWeight: {
      thin: '100',
      extralight: '200',
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
      black: '900'
    }
  },
  
  // Spacing Scale (4px base)
  spacing: {
    0: '0',
    0.5: '0.125rem',   // 2px
    1: '0.25rem',      // 4px
    1.5: '0.375rem',   // 6px
    2: '0.5rem',       // 8px
    2.5: '0.625rem',   // 10px
    3: '0.75rem',      // 12px
    3.5: '0.875rem',   // 14px
    4: '1rem',         // 16px
    5: '1.25rem',      // 20px
    6: '1.5rem',       // 24px
    7: '1.75rem',      // 28px
    8: '2rem',         // 32px
    9: '2.25rem',      // 36px
    10: '2.5rem',      // 40px
    11: '2.75rem',     // 44px
    12: '3rem',        // 48px
    14: '3.5rem',      // 56px
    16: '4rem',        // 64px
    20: '5rem',        // 80px
    24: '6rem',        // 96px
    28: '7rem',        // 112px
    32: '8rem',        // 128px
    36: '9rem',        // 144px
    40: '10rem',       // 160px
    44: '11rem',       // 176px
    48: '12rem',       // 192px
    52: '13rem',       // 208px
    56: '14rem',       // 224px
    60: '15rem',       // 240px
    64: '16rem',       // 256px
    72: '18rem',       // 288px
    80: '20rem',       // 320px
    96: '24rem'        // 384px
  },
  
  // Border Radius
  borderRadius: {
    none: '0',
    sm: '0.125rem',     // 2px
    base: '0.25rem',    // 4px
    md: '0.375rem',     // 6px
    lg: '0.5rem',       // 8px
    xl: '0.75rem',      // 12px
    '2xl': '1rem',      // 16px
    '3xl': '1.5rem',    // 24px
    full: '9999px'
  },
  
  // Elevation/Shadows
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    base: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: '0 0 #0000',
    
    // Roblox-specific elevated shadows
    roblox: {
      card: '0 4px 12px rgba(226, 35, 26, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1)',
      button: '0 2px 8px rgba(226, 35, 26, 0.2)',
      modal: '0 20px 40px rgba(0, 0, 0, 0.15)',
      tooltip: '0 4px 12px rgba(0, 0, 0, 0.15)'
    }
  },
  
  // Animation/Transition Tokens
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
      slower: '750ms'
    },
    
    easing: {
      linear: 'linear',
      in: 'cubic-bezier(0.4, 0, 1, 1)',
      out: 'cubic-bezier(0, 0, 0.2, 1)',
      inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    }
  },
  
  // Z-Index Scale
  zIndex: {
    auto: 'auto',
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
    
    // Semantic z-index values
    hide: '-1',
    base: '0',
    docked: '10',
    dropdown: '1000',
    sticky: '1100',
    banner: '1200',
    overlay: '1300',
    modal: '1400',
    popover: '1500',
    skipLink: '1600',
    toast: '1700',
    tooltip: '1800'
  },
  
  // Breakpoints for responsive design
  breakpoints: {
    xs: '475px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
  }
};

// Theme mode specific tokens
export const lightModeTokens = {
  colors: {
    background: {
      primary: designTokens.colors.neutral[0],
      secondary: designTokens.colors.neutral[50],
      tertiary: designTokens.colors.neutral[100]
    },
    surface: {
      primary: designTokens.colors.neutral[0],
      secondary: designTokens.colors.neutral[50],
      raised: designTokens.colors.neutral[0]
    },
    text: {
      primary: designTokens.colors.neutral[900],
      secondary: designTokens.colors.neutral[600],
      tertiary: designTokens.colors.neutral[500],
      inverse: designTokens.colors.neutral[0]
    },
    border: {
      primary: designTokens.colors.neutral[200],
      secondary: designTokens.colors.neutral[300],
      focus: designTokens.colors.primary[500]
    }
  }
};

export const darkModeTokens = {
  colors: {
    background: {
      primary: designTokens.colors.neutral[950],
      secondary: designTokens.colors.neutral[900],
      tertiary: designTokens.colors.neutral[800]
    },
    surface: {
      primary: designTokens.colors.neutral[900],
      secondary: designTokens.colors.neutral[800],
      raised: designTokens.colors.neutral[700]
    },
    text: {
      primary: designTokens.colors.neutral[0],
      secondary: designTokens.colors.neutral[300],
      tertiary: designTokens.colors.neutral[400],
      inverse: designTokens.colors.neutral[900]
    },
    border: {
      primary: designTokens.colors.neutral[700],
      secondary: designTokens.colors.neutral[600],
      focus: designTokens.colors.primary[400]
    }
  }
};

export type DesignTokens = typeof designTokens;
export type LightModeTokens = typeof lightModeTokens;
export type DarkModeTokens = typeof darkModeTokens;

/**
 * Check color contrast ratio for WCAG compliance
 * @param foreground - Foreground color in hex format
 * @param background - Background color in hex format
 * @returns Object with contrast ratio and WCAG AA compliance status
 */
export function checkContrast(foreground: string, background: string): {
  ratio: number;
  passes: boolean;
  level: 'AAA' | 'AA' | 'Fail';
} {
  const getLuminance = (hex: string): number => {
    // Remove # if present
    const cleanHex = hex.replace('#', '');
    const rgb = parseInt(cleanHex, 16);
    const r = ((rgb >> 16) & 0xff) / 255;
    const g = ((rgb >> 8) & 0xff) / 255;
    const b = (rgb & 0xff) / 255;
    
    const [rs, gs, bs] = [r, g, b].map(val =>
      val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4)
    );
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  
  return {
    ratio: Math.round(ratio * 100) / 100,
    passes: ratio >= 4.5, // WCAG AA standard for normal text
    level: ratio >= 7 ? 'AAA' : ratio >= 4.5 ? 'AA' : 'Fail',
  };
}
