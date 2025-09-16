/**
 * Inject global animation styles for the wild Roblox theme
 */

import { animationStyles } from './robloxTheme';

export const injectAnimations = () => {
  // Check if animations are already injected
  if (document.getElementById('roblox-animations')) {
    return;
  }

  // Create style element
  const styleElement = document.createElement('style');
  styleElement.id = 'roblox-animations';
  styleElement.innerHTML = animationStyles;

  // Additional global styles for wild effects
  styleElement.innerHTML += `
    /* Global selection color */
    ::selection {
      background: rgba(255, 0, 255, 0.3);
      color: #00ffff;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
      width: 12px;
      height: 12px;
    }

    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.5);
      border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #00ffff, #ff00ff);
      border-radius: 10px;
      border: 2px solid transparent;
      background-clip: padding-box;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: linear-gradient(135deg, #ff00ff, #ffff00);
      background-clip: padding-box;
    }

    /* Cursor trail effect on interactive elements */
    button, a, [role="button"] {
      cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><circle cx="16" cy="16" r="10" fill="%2300ffff" opacity="0.5"/><circle cx="16" cy="16" r="5" fill="%23ff00ff"/></svg>') 16 16, pointer;
    }

    /* Global glow effect for focused elements */
    *:focus-visible {
      outline: 2px solid #00ffff !important;
      outline-offset: 2px;
      box-shadow: 0 0 20px #00ffff !important;
    }

    /* Animated background for body */
    body {
      position: relative;
      overflow-x: hidden;
    }

    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background:
        radial-gradient(circle at 20% 80%, rgba(0, 255, 255, 0.05) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255, 0, 255, 0.05) 0%, transparent 50%),
        radial-gradient(circle at 40% 40%, rgba(255, 255, 0, 0.03) 0%, transparent 50%);
      pointer-events: none;
      z-index: 0;
      animation: background-shift 20s ease-in-out infinite;
    }

    @keyframes background-shift {
      0%, 100% {
        transform: translate(0, 0) scale(1);
      }
      33% {
        transform: translate(-20px, -20px) scale(1.1);
      }
      66% {
        transform: translate(20px, -10px) scale(1.05);
      }
    }

    /* Text glow for headings */
    h1, h2, h3, h4, h5, h6 {
      animation: neon-pulse 3s ease-in-out infinite;
    }

    /* Loading spinner override */
    .MuiCircularProgress-circle {
      stroke: url(#rainbow-gradient) !important;
    }

    /* Add rainbow gradient definition */
    body::after {
      content: '<svg width="0" height="0"><defs><linearGradient id="rainbow-gradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ff0000"/><stop offset="16.66%" stop-color="#ff8800"/><stop offset="33.33%" stop-color="#ffff00"/><stop offset="50%" stop-color="#00ff00"/><stop offset="66.66%" stop-color="#00ffff"/><stop offset="83.33%" stop-color="#0088ff"/><stop offset="100%" stop-color="#ff00ff"/></linearGradient></defs></svg>';
      position: absolute;
      width: 0;
      height: 0;
    }
  `;

  // Inject into head
  document.head.appendChild(styleElement);
};

// Auto-inject on import
if (typeof document !== 'undefined') {
  injectAnimations();
}