/**
 * Atomic Spinner Component
 *
 * A loading spinner with Roblox theming and various animation styles.
 */

import React, { forwardRef } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import CircularProgressProps from '@mui/material/CircularProgressProps';
import { styled } from '@mui/material/styles';
import { keyframes } from '@mui/material/styles';
import { designTokens } from '../../../theme/designTokens';

export interface SpinnerProps extends Omit<CircularProgressProps, 'size'> {
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

// Animations
const robloxPulse = keyframes`
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }
`;

const dotsBounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
`;

const barsScale = keyframes`
  0%, 40%, 100% {
    transform: scaleY(0.4);
  }
  20% {
    transform: scaleY(1);
  }
`;

const StyledSpinner = styled('div')<SpinnerProps>(({
  theme,
  size = 'md',
  variant = 'circular',
  robloxTheme = true
}) => {
  const currentSize = sizeMap[size];
  const robloxColor = '#E2231A';

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  if (variant === 'circular') {
    return {
      ...baseStyles,
      '& .MuiCircularProgress-root': {
        color: robloxTheme ? robloxColor : theme.palette.primary.main
      }
    };
  }

  if (variant === 'dots') {
    return {
      ...baseStyles,
      width: currentSize * 2,
      height: currentSize,

      '& .dot': {
        width: currentSize / 4,
        height: currentSize / 4,
        backgroundColor: robloxTheme ? robloxColor : theme.palette.primary.main,
        borderRadius: '50%',
        display: 'inline-block',
        margin: `0 ${currentSize / 8}px`,
        animation: `${dotsBounce} 1.4s ease-in-out infinite both`,

        '&:nth-child(1)': { animationDelay: '-0.32s' },
        '&:nth-child(2)': { animationDelay: '-0.16s' },
        '&:nth-child(3)': { animationDelay: '0s' }
      }
    };
  }

  if (variant === 'pulse') {
    return {
      ...baseStyles,
      width: currentSize,
      height: currentSize,

      '& .pulse': {
        width: '100%',
        height: '100%',
        backgroundColor: robloxTheme ? robloxColor : theme.palette.primary.main,
        borderRadius: '50%',
        animation: `${robloxPulse} 1s ease-in-out infinite`
      }
    };
  }

  if (variant === 'bars') {
    return {
      ...baseStyles,
      width: currentSize,
      height: currentSize,

      '& .bar': {
        width: currentSize / 5,
        height: '100%',
        backgroundColor: robloxTheme ? robloxColor : theme.palette.primary.main,
        margin: `0 ${currentSize / 20}px`,
        display: 'inline-block',
        animation: `${barsScale} 1.2s infinite ease-in-out`,

        '&:nth-child(1)': { animationDelay: '-1.1s' },
        '&:nth-child(2)': { animationDelay: '-1.0s' },
        '&:nth-child(3)': { animationDelay: '-0.9s' },
        '&:nth-child(4)': { animationDelay: '-0.8s' }
      }
    };
  }

  return baseStyles;
});

const AtomicSpinner = forwardRef<HTMLDivElement, SpinnerProps>(
  (
    {
      size = 'md',
      variant = 'circular',
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
    const currentSize = sizeMap[size];

    const renderSpinner = () => {
      switch (variant) {
        case 'circular':
          return <CircularProgress size={currentSize} {...props} />;

        case 'dots':
          return (
            <>
              <div className="dot" />
              <div className="dot" />
              <div className="dot" />
            </>
          );

        case 'pulse':
          return <div className="pulse" />;

        case 'bars':
          return (
            <>
              <div className="bar" />
              <div className="bar" />
              <div className="bar" />
              <div className="bar" />
            </>
          );

        default:
          return <CircularProgress size={currentSize} {...props} />;
      }
    };

    return (
      <StyledSpinner
        ref={ref}
        size={size}
        variant={variant}
        robloxTheme={robloxTheme}
        role="progressbar"
        aria-label="Loading"
      >
        {renderSpinner()}
      </StyledSpinner>
    );
  }
);

AtomicSpinner.displayName = 'AtomicSpinner';

export type { SpinnerProps };
export default AtomicSpinner;