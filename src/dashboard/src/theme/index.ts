import { createTheme, alpha } from "@mui/material/styles";

// Color Palette
const colors = {
  primary: {
    main: "#2563EB", // Education Blue
    light: "#60A5FA",
    dark: "#1E40AF",
  },
  secondary: {
    main: "#22C55E", // Success Green
    light: "#86EFAC",
    dark: "#16A34A",
  },
  warning: {
    main: "#FACC15", // Gold/Achievement
    light: "#FDE68A",
    dark: "#CA8A04",
  },
  error: {
    main: "#EF4444",
    light: "#FCA5A5",
    dark: "#DC2626",
  },
  info: {
    main: "#14B8A6", // Teal
    light: "#5EEAD4",
    dark: "#0F766E",
  },
  gamification: {
    xp: "#9333EA", // Purple
    badge: "#14B8A6", // Teal
    level: "#FACC15", // Gold
    achievement: "#F97316", // Orange
  },
  neutral: {
    50: "#F9FAFB",
    100: "#F3F4F6",
    200: "#E5E7EB",
    300: "#D1D5DB",
    400: "#9CA3AF",
    500: "#6B7280",
    600: "#4B5563",
    700: "#374151",
    800: "#1F2937",
    900: "#111827",
  },
};

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: colors.primary,
    secondary: colors.secondary,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    background: {
      default: colors.neutral[50],
      paper: "#FFFFFF",
    },
    text: {
      primary: colors.neutral[900],
      secondary: colors.neutral[600],
    },
  },
  typography: {
    fontFamily: [
      "Inter",
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
    ].join(","),
    h1: {
      fontFamily: '"Playfair Display", Georgia, serif',
      fontWeight: 700,
      fontSize: "3rem",
    },
    h2: {
      fontFamily: '"Playfair Display", Georgia, serif',
      fontWeight: 700,
      fontSize: "2.5rem",
    },
    h3: {
      fontFamily: '"Playfair Display", Georgia, serif',
      fontWeight: 700,
      fontSize: "2rem",
    },
    h4: {
      fontFamily: '"Inter", sans-serif',
      fontWeight: 600,
      fontSize: "1.75rem",
    },
    h5: {
      fontFamily: '"Inter", sans-serif',
      fontWeight: 600,
      fontSize: "1.5rem",
    },
    h6: {
      fontFamily: '"Inter", sans-serif',
      fontWeight: 600,
      fontSize: "1.25rem",
    },
    button: {
      textTransform: "none",
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 16,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
          transition: "all 0.3s ease",
          "&:hover": {
            boxShadow: "0 12px 32px rgba(0,0,0,0.12)",
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: "8px 20px",
          fontSize: "0.95rem",
        },
        contained: {
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          "&:hover": {
            boxShadow: "0 6px 16px rgba(0,0,0,0.15)",
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          height: 8,
          borderRadius: 4,
          backgroundColor: colors.neutral[200],
        },
        bar: {
          borderRadius: 4,
          background: `linear-gradient(90deg, ${colors.gamification.xp} 0%, ${colors.gamification.badge} 100%)`,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backdropFilter: "blur(8px)",
          backgroundColor: alpha("#FFFFFF", 0.8),
          color: colors.neutral[900],
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.neutral[900],
          color: "#FFFFFF",
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: colors.neutral[100],
          "& .MuiTableCell-head": {
            fontWeight: 600,
            color: colors.neutral[700],
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          "&:hover": {
            backgroundColor: alpha(colors.primary.main, 0.04),
          },
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          fontSize: "0.75rem",
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 8,
          backgroundColor: colors.neutral[800],
          fontSize: "0.875rem",
        },
      },
    },
  },
});

// Dark theme variant
export const darkTheme = createTheme({
  ...theme,
  palette: {
    mode: "dark",
    primary: colors.primary,
    secondary: colors.secondary,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    background: {
      default: colors.neutral[900],
      paper: colors.neutral[800],
    },
    text: {
      primary: "#FFFFFF",
      secondary: colors.neutral[400],
    },
  },
  components: {
    ...theme.components,
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          backgroundColor: colors.neutral[800],
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backdropFilter: "blur(8px)",
          backgroundColor: alpha(colors.neutral[900], 0.8),
          color: "#FFFFFF",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.neutral[800],
          color: "#FFFFFF",
        },
      },
    },
  },
});