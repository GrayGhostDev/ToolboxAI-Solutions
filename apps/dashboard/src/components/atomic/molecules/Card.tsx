/**
 * Card Molecule
 *
 * A versatile card component built with atomic design principles,
 * combining Box, Text, and other atoms to create a cohesive display unit.
 */

import React, { forwardRef } from 'react';
import { styled } from '@mui/material';
import { AtomicBox, AtomicText } from '../atoms';
import type { BoxProps } from '../atoms/Box';
import { designTokens } from '../../../theme/designTokens';

export interface CardProps extends Omit<BoxProps, 'variant'> {
  variant?: 'default' | 'outlined' | 'elevated' | 'roblox' | 'game';
  header?: React.ReactNode;
  footer?: React.ReactNode;
  title?: string;
  subtitle?: string;
  avatar?: React.ReactNode;
  actions?: React.ReactNode;
  media?: React.ReactNode;
  interactive?: boolean;
  loading?: boolean;
  robloxTheme?: boolean;
}

const StyledCard = styled(AtomicBox)<CardProps>(({
  theme,
  variant = 'default',
  interactive = false,
  robloxTheme = true
}) => {
  const baseStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    position: 'relative' as const,
    overflow: 'hidden',
    transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,

    ...(interactive && {
      cursor: 'pointer',

      '&:hover': {
        transform: 'translateY(-2px)',
      }
    })
  };

  switch (variant) {
    case 'outlined':
      return {
        ...baseStyles,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: designTokens.borderRadius.lg,
        backgroundColor: theme.palette.background.paper,

        ...(interactive && {
          '&:hover': {
            ...baseStyles['&:hover'],
            borderColor: robloxTheme ? '#E2231A' : theme.palette.primary.main,
            boxShadow: `0 4px 12px ${theme.palette.mode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.1)'}`
          }
        })
      };

    case 'elevated':
      return {
        ...baseStyles,
        borderRadius: designTokens.borderRadius.lg,
        backgroundColor: theme.palette.background.paper,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.06)',

        ...(interactive && {
          '&:hover': {
            ...baseStyles['&:hover'],
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)'
          }
        })
      };

    case 'roblox':
      return {
        ...baseStyles,
        borderRadius: designTokens.borderRadius['2xl'],
        border: `2px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        boxShadow: '0 4px 12px rgba(226, 35, 26, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1)',

        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'linear-gradient(135deg, #E2231A, #B71C15)',
          borderRadius: `${designTokens.borderRadius['2xl']} ${designTokens.borderRadius['2xl']} 0 0`
        },

        ...(interactive && {
          '&:hover': {
            ...baseStyles['&:hover'],
            borderColor: 'rgba(226, 35, 26, 0.5)',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)'
          }
        })
      };

    case 'game':
      return {
        ...baseStyles,
        borderRadius: designTokens.borderRadius['3xl'],
        background: theme.palette.mode === 'dark'
          ? 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)'
          : 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.05) 0%, transparent 50%)',
        border: `1px solid ${theme.palette.divider}`,

        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'conic-gradient(from 0deg, transparent, rgba(226, 35, 26, 0.1), transparent)',
          animation: 'rotate 10s linear infinite',
          pointerEvents: 'none'
        }
      };

    default:
      return {
        ...baseStyles,
        borderRadius: designTokens.borderRadius.lg,
        backgroundColor: theme.palette.background.paper,

        ...(interactive && {
          '&:hover': {
            ...baseStyles['&:hover'],
            backgroundColor: theme.palette.action.hover
          }
        })
      };
  }
});

const CardHeader = styled(AtomicBox)(({ theme }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  padding: designTokens.spacing[4],
  paddingBottom: 0,

  '& .card-header__avatar': {
    marginRight: designTokens.spacing[3]
  },

  '& .card-header__content': {
    flex: 1,
    minWidth: 0
  },

  '& .card-header__actions': {
    marginLeft: designTokens.spacing[2],
    marginTop: designTokens.spacing[-1]
  }
}));

const CardContent = styled(AtomicBox)(() => ({
  flex: 1,
  padding: designTokens.spacing[4]
}));

const CardFooter = styled(AtomicBox)(({ theme }) => ({
  padding: designTokens.spacing[4],
  paddingTop: 0,
  borderTop: `1px solid ${theme.palette.divider}`,
  marginTop: 'auto'
}));

const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      header,
      footer,
      title,
      subtitle,
      avatar,
      actions,
      media,
      interactive = false,
      loading = false,
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
    const hasHeader = header || title || subtitle || avatar || actions;

    if (loading) {
      // TODO: Implement skeleton loading state
      return (
        <StyledCard
          ref={ref}
          variant={variant}
          interactive={false}
          robloxTheme={robloxTheme}
          {...props}
        >
          <CardContent>
            <AtomicText>Loading...</AtomicText>
          </CardContent>
        </StyledCard>
      );
    }

    return (
      <StyledCard
        ref={ref}
        variant={variant}
        interactive={interactive}
        robloxTheme={robloxTheme}
        {...props}
      >
        {/* Media */}
        {media && (
          <AtomicBox>
            {media}
          </AtomicBox>
        )}

        {/* Header */}
        {hasHeader && (
          <CardHeader>
            {avatar && (
              <AtomicBox className="card-header__avatar">
                {avatar}
              </AtomicBox>
            )}

            <AtomicBox className="card-header__content">
              {title && (
                <AtomicText
                  variant="h6"
                  weight="semibold"
                  truncate
                  robloxTheme={robloxTheme}
                >
                  {title}
                </AtomicText>
              )}
              {subtitle && (
                <AtomicText
                  variant="sm"
                  color="secondary"
                  truncate
                >
                  {subtitle}
                </AtomicText>
              )}
            </AtomicBox>

            {actions && (
              <AtomicBox className="card-header__actions">
                {actions}
              </AtomicBox>
            )}
          </CardHeader>
        )}

        {/* Custom header */}
        {header && !hasHeader && header}

        {/* Content */}
        <CardContent>
          {children}
        </CardContent>

        {/* Footer */}
        {footer && (
          <CardFooter>
            {footer}
          </CardFooter>
        )}
      </StyledCard>
    );
  }
);

Card.displayName = 'Card';

export type { CardProps };
export default Card;