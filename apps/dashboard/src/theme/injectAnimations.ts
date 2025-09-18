/**
 * Inject global animation styles for the Roblox-themed dashboard
 */

import { animationStyles } from './robloxTheme';
import { designTokens } from './designTokens';
import { robloxColors } from './robloxTheme';

export const injectAnimations = () => {
  // Check if animations are already injected
  if (document.getElementById('roblox-animations')) {
    return;
  }

  // Create style element
  const styleElement = document.createElement('style');
  styleElement.id = 'roblox-animations';
  styleElement.innerHTML = animationStyles;

  // Additional global styles for Roblox effects
  styleElement.innerHTML += `
    /* CSS Custom Properties for dynamic theming */
    :root {
      --roblox-primary-color: ${robloxColors.brand.red.primary};
      --roblox-secondary-color: ${robloxColors.brand.gray.primary};
      --roblox-success-color: ${robloxColors.semantic.success};
      --roblox-error-color: ${robloxColors.semantic.error};
      --roblox-warning-color: ${robloxColors.semantic.warning};
      --roblox-info-color: ${robloxColors.semantic.info};
      --roblox-border-radius: ${designTokens.borderRadius.xl};
      --roblox-animation-duration: ${designTokens.animation.duration.normal};
      --roblox-animation-easing: ${designTokens.animation.easing.inOut};
    }

    /* Enhanced focus styles for accessibility */
    *:focus-visible {
      outline: 2px solid var(--roblox-primary-color) !important;
      outline-offset: 2px;
      box-shadow: 0 0 0 4px rgba(226, 35, 26, 0.2) !important;
      transition: box-shadow var(--roblox-animation-duration) var(--roblox-animation-easing);
    }

    /* Smooth transitions for interactive elements */
    button, [role="button"], .MuiButton-root, .MuiIconButton-root, .MuiTab-root, .MuiMenuItem-root {
      transition: all var(--roblox-animation-duration) var(--roblox-animation-easing);
    }

    /* Enhanced button hover effects */
    .MuiButton-contained:not(:disabled):hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(226, 35, 26, 0.3);
    }

    .MuiButton-contained:not(:disabled):active {
      transform: translateY(0);
    }

    /* Card hover effects */
    .MuiCard-root {
      transition: all var(--roblox-animation-duration) var(--roblox-animation-easing);
    }

    .MuiCard-root:hover {
      transform: translateY(-2px);
    }

    /* Loading shimmer effect */
    .roblox-shimmer {
      background: linear-gradient(
        90deg,
        transparent,
        rgba(226, 35, 26, 0.1),
        transparent
      );
      background-size: 200% 100%;
      animation: roblox-shimmer 2s infinite;
    }

    @keyframes roblox-shimmer {
      0% {
        background-position: -200% center;
      }
      100% {
        background-position: 200% center;
      }
    }

    /* Pulse animation for notifications */
    .roblox-pulse {
      animation: roblox-pulse 2s ease-in-out infinite;
    }

    @keyframes roblox-pulse {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.9;
        transform: scale(1.02);
      }
    }

    /* Floating animation for gamification elements */
    .roblox-float {
      animation: roblox-float 3s ease-in-out infinite;
    }

    @keyframes roblox-float {
      0%, 100% {
        transform: translateY(0px);
      }
      50% {
        transform: translateY(-8px);
      }
    }

    /* Glow effect for special elements */
    .roblox-glow {
      animation: roblox-glow 2s ease-in-out infinite;
    }

    @keyframes roblox-glow {
      0%, 100% {
        box-shadow: 0 0 5px rgba(226, 35, 26, 0.3);
      }
      50% {
        box-shadow: 0 0 20px rgba(226, 35, 26, 0.6);
      }
    }

    /* Bounce animation for achievements */
    .roblox-bounce {
      animation: roblox-bounce 1s ease-in-out infinite;
    }

    @keyframes roblox-bounce {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-4px);
      }
    }

    /* Spin animation for loading states */
    .roblox-spin {
      animation: roblox-spin 1s linear infinite;
    }

    @keyframes roblox-spin {
      from {
        transform: rotate(0deg);
      }
      to {
        transform: rotate(360deg);
      }
    }

    /* Scale animation for interactive feedback */
    .roblox-scale:hover {
      transform: scale(1.05);
      transition: transform var(--roblox-animation-duration) var(--roblox-animation-easing);
    }

    /* Slide animations for modals and drawers */
    .roblox-slide-in-left {
      animation: roblox-slide-in-left 0.3s ease-out;
    }

    @keyframes roblox-slide-in-left {
      from {
        transform: translateX(-100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .roblox-slide-in-right {
      animation: roblox-slide-in-right 0.3s ease-out;
    }

    @keyframes roblox-slide-in-right {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    /* Fade animations */
    .roblox-fade-in {
      animation: roblox-fade-in 0.3s ease-out;
    }

    @keyframes roblox-fade-in {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    .roblox-fade-out {
      animation: roblox-fade-out 0.3s ease-out;
    }

    @keyframes roblox-fade-out {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    /* Reduce motion for users who prefer it */
    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }
    }

    /* High contrast mode support */
    @media (prefers-contrast: high) {
      :root {
        --roblox-primary-color: #000000;
        --roblox-secondary-color: #666666;
      }

      *:focus-visible {
        outline: 3px solid #000000 !important;
        outline-offset: 2px;
      }
    }

    /* Print styles */
    @media print {
      .roblox-pulse,
      .roblox-float,
      .roblox-glow,
      .roblox-bounce,
      .roblox-spin,
      .roblox-shimmer {
        animation: none !important;
      }

      *:focus-visible {
        outline: 2px solid #000000 !important;
        box-shadow: none !important;
      }
    }
  `;

  // Inject into head
  document.head.appendChild(styleElement);

  // Set up CSS custom properties for dynamic theming
  const updateCSSVariables = () => {
    const root = document.documentElement;
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Update CSS variables based on theme
    if (isDark) {
      root.style.setProperty('--roblox-bg-primary', '#111827');
      root.style.setProperty('--roblox-bg-secondary', '#1F2937');
      root.style.setProperty('--roblox-text-primary', '#FFFFFF');
      root.style.setProperty('--roblox-text-secondary', '#9CA3AF');
    } else {
      root.style.setProperty('--roblox-bg-primary', '#FFFFFF');
      root.style.setProperty('--roblox-bg-secondary', '#F9FAFB');
      root.style.setProperty('--roblox-text-primary', '#111827');
      root.style.setProperty('--roblox-text-secondary', '#6B7280');
    }
  };

  // Initial setup
  updateCSSVariables();

  // Listen for theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', updateCSSVariables);
};

// Auto-inject on import
if (typeof document !== 'undefined') {
  injectAnimations();
}

export default injectAnimations;