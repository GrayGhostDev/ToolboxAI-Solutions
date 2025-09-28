/**
 * Safe3DIcon Component
 * 
 * A safe wrapper for displaying 3D icons with fallback mechanisms
 * and error handling for Roblox content in the ToolboxAI Dashboard.
 * 
 * @version 2025
 */

import React, { useState, useCallback, useEffect, memo } from 'react';

interface Safe3DIconProps {
  src: string;
  fallbackSrc?: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  style?: React.CSSProperties;
}

const Safe3DIcon: React.FC<Safe3DIconProps> = memo(({
  src,
  fallbackSrc,
  alt,
  width = 64,
  height = 64,
  className,
  onLoad,
  onError,
  style
}) => {
  const [useProceduralIcon, setUseProceduralIcon] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentSrc, setCurrentSrc] = useState(src);

  // Dynamic condition based on state instead of constant
  const shouldUseFallback = hasError || !currentSrc || currentSrc.trim() === '';

  const handleImageError = useCallback((error: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('Image failed to load:', currentSrc);
    
    // Try fallback first if available
    if (fallbackSrc && currentSrc !== fallbackSrc) {
      setCurrentSrc(fallbackSrc);
      setIsLoading(true);
      return;
    }
    
    // No fallback available or fallback also failed
    setHasError(true);
    setIsLoading(false);
    setUseProceduralIcon(true);
    
    const errorEvent = new Error(`Failed to load 3D icon: ${currentSrc}`);
    onError?.(errorEvent);
  }, [currentSrc, fallbackSrc, onError]);

  const handleImageLoad = useCallback(() => {
    setHasError(false);
    setIsLoading(false);
    setUseProceduralIcon(false);
    onLoad?.();
  }, [onLoad]);

  const generateProceduralIcon = useCallback(() => {
    // Generate a simple geometric pattern as fallback
    return (
      <svg
        width={width}
        height={height}
        viewBox="0 0 64 64"
        className={`procedural-icon ${className || ''}`}
        style={style}
        role="img"
        aria-label={alt}
      >
        <defs>
          <linearGradient id={`iconGradient-${Math.random()}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#4299e1" />
            <stop offset="100%" stopColor="#3182ce" />
          </linearGradient>
        </defs>
        <rect
          x="8"
          y="8"
          width="48"
          height="48"
          rx="8"
          fill={`url(#iconGradient-${Math.random()})`}
          stroke="#2d3748"
          strokeWidth="2"
        />
        <circle
          cx="32"
          cy="32"
          r="16"
          fill="rgba(255, 255, 255, 0.2)"
          stroke="rgba(255, 255, 255, 0.4)"
          strokeWidth="1"
        />
        <path
          d="M24 32 L32 24 L40 32 L32 40 Z"
          fill="rgba(255, 255, 255, 0.8)"
          stroke="#2d3748"
          strokeWidth="1"
        />
      </svg>
    );
  }, [width, height, className, style, alt]);

  // Reset error state when src changes
  useEffect(() => {
    if (src && src.trim() !== '') {
      setHasError(false);
      setIsLoading(true);
      setUseProceduralIcon(false);
      setCurrentSrc(src);
    }
  }, [src]);

  // Loading state
  if (isLoading && !shouldUseFallback) {
    return (
      <div
        className={`loading-icon ${className || ''}`}
        style={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f7fafc',
          borderRadius: '8px',
          ...style
        }}
        role="img"
        aria-label={`Loading ${alt}`}
      >
        <div
          style={{
            width: '24px',
            height: '24px',
            border: '3px solid #e2e8f0',
            borderTop: '3px solid #4299e1',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}
        />
      </div>
    );
  }

  // Show procedural icon if we should use fallback
  if (shouldUseFallback || useProceduralIcon) {
    return generateProceduralIcon();
  }

  // Show the actual image
  return (
    <img
      src={currentSrc}
      alt={alt}
      width={width}
      height={height}
      className={className}
      style={style}
      onLoad={handleImageLoad}
      onError={handleImageError}
      loading="lazy"
      decoding="async"
    />
  );
});

Safe3DIcon.displayName = 'Safe3DIcon';

export default Safe3DIcon;