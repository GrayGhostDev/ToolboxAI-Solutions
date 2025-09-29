/**
 * Atomic Spinner Component
 *
 * A loading spinner with Roblox theming and various animation styles.
 */

import React, { forwardRef } from 'react';
import { Loader, LoaderProps, Box } from '@mantine/core';
import { designTokens } from '../../../theme/designTokens';

export interface SpinnerProps extends Omit<LoaderProps, 'size' | 'variant'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'circular' | 'dots' | 'pulse' | 'bars';
  robloxTheme?: boolean;
}

// Size mapping
const sizeMap = {
  xs: 12,
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48
};

const AtomicSpinner = forwardRef<HTMLDivElement, SpinnerProps>(
  (
    {
      size = 'md',
      variant = 'circular',
      robloxTheme = true,
      color,
      style,
      ...props
    },
    ref
  ) => {
    const currentSize = sizeMap[size];
    const robloxColor = '#E2231A';
    const finalColor = robloxTheme ? robloxColor : color || 'blue';

    // Generate animation CSS for custom variants
    const getAnimationCSS = () => {
      return `
        @keyframes roblox-pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.1);
          }
        }

        @keyframes dots-bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }

        @keyframes bars-scale {
          0%, 40%, 100% {
            transform: scaleY(0.4);
          }
          20% {
            transform: scaleY(1);
          }
        }
      `;
    };

    const baseContainerStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      ...(style as React.CSSProperties)
    };

    const renderSpinner = () => {
      switch (variant) {
        case 'circular':
          return (
            <Loader
              size={currentSize}
              color={finalColor}
              {...props}
            />
          );

        case 'dots':
          return (
            <Box style={{
              ...baseContainerStyle,
              width: currentSize * 2,
              height: currentSize,
            }}>
              {[0, 1, 2].map((i) => (
                <Box
                  key={i}
                  style={{
                    width: currentSize / 4,
                    height: currentSize / 4,
                    backgroundColor: finalColor,
                    borderRadius: '50%',
                    display: 'inline-block',
                    margin: `0 ${currentSize / 8}px`,
                    animation: `dots-bounce 1.4s ease-in-out infinite both`,
                    animationDelay: `${-0.32 + (i * 0.16)}s`
                  }}
                />
              ))}
            </Box>
          );

        case 'pulse':
          return (
            <Box style={{
              ...baseContainerStyle,
              width: currentSize,
              height: currentSize,
            }}>
              <Box
                style={{
                  width: '100%',
                  height: '100%',
                  backgroundColor: finalColor,
                  borderRadius: '50%',
                  animation: 'roblox-pulse 1s ease-in-out infinite'
                }}
              />
            </Box>
          );

        case 'bars':
          return (
            <Box style={{
              ...baseContainerStyle,
              width: currentSize,
              height: currentSize,
            }}>
              {[0, 1, 2, 3].map((i) => (
                <Box
                  key={i}
                  style={{
                    width: currentSize / 5,
                    height: '100%',
                    backgroundColor: finalColor,
                    margin: `0 ${currentSize / 20}px`,
                    display: 'inline-block',
                    animation: 'bars-scale 1.2s infinite ease-in-out',
                    animationDelay: `${-1.1 + (i * 0.1)}s`
                  }}
                />
              ))}
            </Box>
          );

        default:
          return (
            <Loader
              size={currentSize}
              color={finalColor}
              {...props}
            />
          );
      }
    };

    return (
      <>
        {/* Inject animation CSS for custom variants */}
        {variant !== 'circular' && (
          <style dangerouslySetInnerHTML={{ __html: getAnimationCSS() }} />
        )}

        <Box
          ref={ref}
          style={baseContainerStyle}
          role="progressbar"
          aria-label="Loading"
        >
          {renderSpinner()}
        </Box>
      </>
    );
  }
);

AtomicSpinner.displayName = 'AtomicSpinner';

export type { SpinnerProps };
export default AtomicSpinner;