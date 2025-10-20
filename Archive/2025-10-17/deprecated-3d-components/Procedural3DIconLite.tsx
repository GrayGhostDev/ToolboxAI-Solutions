import React, { useRef, useMemo } from 'react';
import { Box } from '@mantine/core';

// Lightweight 3D-looking CSS component without Three.js Canvas
interface Procedural3DIconLiteProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  animated?: boolean;
  style?: React.CSSProperties;
}

// Simple emoji mapping for fallback
const iconEmojis: Record<string, string> = {
  ROCKET: '🚀',
  STAR: '⭐',
  TROPHY: '🏆',
  BOOKS: '📚',
  SPORTS_ESPORTS: '🎮',
  ABC_CUBE: '🧩',
  BOARD: '📋',
  SOCCER_BALL: '⚽',
  BRUSH_PAINT: '🎨',
  ASSESSMENT: '📝',
  BADGE: '🏅',
  LIGHT_BULB: '💡',
  OPEN_BOOK: '📖',
  PENCIL: '✏️',
  DEFAULT: '📱'
};

// CSS-based 3D effect styles
const get3DStyles = (color: string, size: number, animated: boolean) => ({
  width: size,
  height: size,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '12px',
  background: `linear-gradient(135deg,
    ${color}20 0%,
    ${color}40 25%,
    ${color}60 50%,
    ${color}40 75%,
    ${color}20 100%)`,
  boxShadow: `
    0 ${size * 0.1}px ${size * 0.2}px rgba(0,0,0,0.2),
    inset 0 1px 0 rgba(255,255,255,0.3),
    inset 0 -1px 0 rgba(0,0,0,0.1)
  `,
  border: `2px solid ${color}60`,
  fontSize: `${size * 0.4}px`,
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  transform: 'translateZ(0)', // Enable hardware acceleration
  position: 'relative' as const,
  overflow: 'hidden',
  ...(animated && {
    animation: 'lite3d-float 3s ease-in-out infinite'
  })
});

// CSS keyframes for animation
const animationCSS = `
  @keyframes lite3d-float {
    0%, 100% {
      transform: translateY(0px) rotateX(0deg) rotateY(0deg);
      box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    25% {
      transform: translateY(-2px) rotateX(5deg) rotateY(2deg);
      box-shadow: 0 12px 24px rgba(0,0,0,0.25);
    }
    50% {
      transform: translateY(-4px) rotateX(0deg) rotateY(5deg);
      box-shadow: 0 16px 32px rgba(0,0,0,0.3);
    }
    75% {
      transform: translateY(-2px) rotateX(-5deg) rotateY(2deg);
      box-shadow: 0 12px 24px rgba(0,0,0,0.25);
    }
  }

  @keyframes lite3d-hover {
    0% {
      transform: scale(1) rotateX(0deg);
    }
    100% {
      transform: scale(1.05) rotateX(10deg);
      box-shadow: 0 16px 32px rgba(0,0,0,0.4);
    }
  }

  .lite3d-icon:hover {
    animation: lite3d-hover 0.3s ease-out forwards;
  }

  .lite3d-icon:active {
    transform: scale(0.95) translateY(2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  }
`;

export const Procedural3DIconLite: React.FunctionComponent<Procedural3DIconLiteProps> = ({
  iconName,
  size = 'medium',
  color = '#4CAF50',
  animated = true,
  style,
}) => {
  const hasInjectedCSS = useRef(false);

  // Inject CSS animation styles once
  React.useEffect(() => {
    if (!hasInjectedCSS.current) {
      const styleElement = document.createElement('style');
      styleElement.id = 'lite3d-animations';
      styleElement.innerHTML = animationCSS;
      if (!document.getElementById('lite3d-animations')) {
        document.head.appendChild(styleElement);
      }
      hasInjectedCSS.current = true;
    }
  }, []);

  const sizeMap = {
    small: 80,
    medium: 120,
    large: 160,
  };

  const iconSize = sizeMap[size];
  const cleanIconName = iconName.replace(/_\d+$/, '');
  const emoji = iconEmojis[cleanIconName] || iconEmojis.DEFAULT;

  const containerStyle = useMemo(() => ({
    ...get3DStyles(color, iconSize, animated),
    ...style,
  }), [color, iconSize, animated, style]);

  return (
    <Box
      className="lite3d-icon"
      style={containerStyle}
    >
      {/* Emoji content */}
      <span
        style={{
          fontSize: `${iconSize * 0.4}px`,
          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
          userSelect: 'none'
        }}
      >
        {emoji}
      </span>

      {/* CSS-based shine effect */}
      <div
        style={{
          position: 'absolute',
          top: '10%',
          left: '20%',
          right: '20%',
          height: '30%',
          background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.3) 50%, transparent 70%)',
          borderRadius: '50%',
          transform: 'rotate(45deg)',
          pointerEvents: 'none'
        }}
      />

      {/* Bottom shadow for depth */}
      <div
        style={{
          position: 'absolute',
          bottom: '15%',
          left: '25%',
          right: '25%',
          height: '20%',
          background: 'linear-gradient(ellipse, rgba(0,0,0,0.2) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none'
        }}
      />
    </Box>
  );
};

export default Procedural3DIconLite;