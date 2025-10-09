/**
 * Card Molecule
 *
 * A versatile card component built with atomic design principles,
 * combining Box, Text, and other atoms to create a cohesive display unit.
 */

import React, { forwardRef } from 'react';
import { Card as MantineCard, type CardProps as MantineCardProps, Box } from '@mantine/core';
import { AtomicText } from '../atoms';
import { designTokens } from '../../../theme/designTokens';

export interface CardProps extends Omit<MantineCardProps, 'variant'> {
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
      style,
      ...props
    },
    ref
  ) => {
    const hasHeader = header || title || subtitle || avatar || actions;

    // Get styles based on variant
    const getCardStyles = () => {
      const baseStyles: React.CSSProperties = {
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
        ...(style as React.CSSProperties)
      };

      if (interactive) {
        baseStyles.cursor = 'pointer';
      }

      switch (variant) {
        case 'outlined':
          return {
            ...baseStyles,
            border: '1px solid var(--mantine-color-gray-4)',
            borderRadius: designTokens.borderRadius.lg,
            backgroundColor: 'var(--mantine-color-body)',
          };

        case 'elevated':
          return {
            ...baseStyles,
            borderRadius: designTokens.borderRadius.lg,
            backgroundColor: 'var(--mantine-color-body)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.06)',
          };

        case 'roblox':
          return {
            ...baseStyles,
            borderRadius: designTokens.borderRadius['2xl'],
            border: '2px solid var(--mantine-color-gray-4)',
            backgroundColor: 'var(--mantine-color-body)',
            boxShadow: '0 4px 12px rgba(226, 35, 26, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1)',
          };

        case 'game':
          return {
            ...baseStyles,
            borderRadius: designTokens.borderRadius['3xl'],
            background: 'radial-gradient(circle at 20% 80%, rgba(226, 35, 26, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
            border: '1px solid var(--mantine-color-gray-4)',
          };

        default:
          return {
            ...baseStyles,
            borderRadius: designTokens.borderRadius.lg,
            backgroundColor: 'var(--mantine-color-body)',
          };
      }
    };

    // Get hover styles for interactive cards
    const getHoverStyles = () => {
      if (!interactive) return {};

      return {
        '&:hover': {
          transform: 'translateY(-2px)',
          ...(variant === 'outlined' && {
            borderColor: robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
          }),
          ...(variant === 'elevated' && {
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)'
          }),
          ...(variant === 'roblox' && {
            borderColor: 'rgba(226, 35, 26, 0.5)',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)'
          }),
          ...(variant === 'default' && {
            backgroundColor: 'var(--mantine-color-gray-1)'
          })
        }
      };
    };

    // Generate CSS for special variants
    const getSpecialCSS = () => {
      let css = '';

      if (variant === 'roblox') {
        css += `
          .roblox-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #E2231A, #B71C15);
            border-radius: ${designTokens.borderRadius['2xl']} ${designTokens.borderRadius['2xl']} 0 0;
          }
        `;
      }

      if (variant === 'game') {
        css += `
          @keyframes card-rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          .game-card::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: conic-gradient(from 0deg, transparent, rgba(226, 35, 26, 0.1), transparent);
            animation: card-rotate 10s linear infinite;
            pointer-events: none;
          }
        `;
      }

      return css;
    };

    if (loading) {
      return (
        <MantineCard
          ref={ref}
          style={getCardStyles()}
          styles={{
            root: getHoverStyles()
          }}
          {...props}
        >
          <MantineCard.Section>
            <Box p={designTokens.spacing[4]}>
              <AtomicText>Loading...</AtomicText>
            </Box>
          </MantineCard.Section>
        </MantineCard>
      );
    }

    return (
      <>
        {/* Inject special CSS */}
        {(variant === 'roblox' || variant === 'game') && (
          <style dangerouslySetInnerHTML={{ __html: getSpecialCSS() }} />
        )}

        <MantineCard
          ref={ref}
          style={getCardStyles()}
          styles={{
            root: getHoverStyles()
          }}
          className={
            variant === 'roblox' ? 'roblox-card' :
            variant === 'game' ? 'game-card' : undefined
          }
          {...props}
        >
          {/* Media */}
          {media && (
            <MantineCard.Section>
              {media}
            </MantineCard.Section>
          )}

          {/* Header */}
          {hasHeader && (
            <MantineCard.Section>
              <Box
                p={designTokens.spacing[4]}
                pb={0}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start'
                }}
              >
                {avatar && (
                  <Box mr={designTokens.spacing[3]}>
                    {avatar}
                  </Box>
                )}

                <Box style={{ flex: 1, minWidth: 0 }}>
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
                </Box>

                {actions && (
                  <Box ml={designTokens.spacing[2]} mt={-4}>
                    {actions}
                  </Box>
                )}
              </Box>
            </MantineCard.Section>
          )}

          {/* Custom header */}
          {header && !hasHeader && (
            <MantineCard.Section>
              {header}
            </MantineCard.Section>
          )}

          {/* Content */}
          <MantineCard.Section>
            <Box p={designTokens.spacing[4]} style={{ flex: 1 }}>
              {children}
            </Box>
          </MantineCard.Section>

          {/* Footer */}
          {footer && (
            <MantineCard.Section>
              <Box
                p={designTokens.spacing[4]}
                pt={0}
                style={{
                  borderTop: '1px solid var(--mantine-color-gray-4)',
                  marginTop: 'auto'
                }}
              >
                {footer}
              </Box>
            </MantineCard.Section>
          )}
        </MantineCard>
      </>
    );
  }
);

Card.displayName = 'Card';

export type { CardProps };
export default Card;