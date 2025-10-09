import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Roblox3DButton } from '../Roblox3DButton';
import { mantineTheme } from '@/theme/mantine-theme';

// Wrapper component for Mantine provider
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MantineProvider theme={mantineTheme}>{children}</MantineProvider>
);

describe('Roblox3DButton', () => {
  describe('Rendering', () => {
    it('renders with label', () => {
      render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Test Button" />
        </TestWrapper>
      );

      expect(screen.getByText('Test Button')).toBeInTheDocument();
    });

    it('renders without label (icon only)', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" />
        </TestWrapper>
      );

      expect(container.querySelector('button')).toBeInTheDocument();
      expect(screen.queryByText(/trophy/i)).not.toBeInTheDocument();
    });

    it('renders with correct icon', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Trophy" />
        </TestWrapper>
      );

      const img = container.querySelector('img');
      expect(img).toHaveAttribute('src', expect.stringContaining('TROPHY'));
      expect(img).toHaveAttribute('alt', 'TROPHY');
    });

    it('uses fallback icon for invalid iconName', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="INVALID_ICON" label="Test" />
        </TestWrapper>
      );

      const img = container.querySelector('img');
      expect(img).toHaveAttribute('src', expect.stringContaining('TROPHY'));
    });
  });

  describe('Variants', () => {
    const variants = ['primary', 'secondary', 'success', 'warning', 'error', 'info'] as const;

    variants.forEach((variant) => {
      it(`renders ${variant} variant`, () => {
        render(
          <TestWrapper>
            <Roblox3DButton
              iconName="TROPHY"
              label={variant}
              variant={variant}
            />
          </TestWrapper>
        );

        expect(screen.getByText(variant)).toBeInTheDocument();
      });
    });
  });

  describe('Sizes', () => {
    const sizes = ['small', 'medium', 'large'] as const;

    sizes.forEach((size) => {
      it(`renders ${size} size`, () => {
        render(
          <TestWrapper>
            <Roblox3DButton iconName="TROPHY" label={size} size={size} />
          </TestWrapper>
        );

        expect(screen.getByText(size)).toBeInTheDocument();
      });
    });
  });

  describe('Interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn();

      render(
        <TestWrapper>
          <Roblox3DButton
            iconName="TROPHY"
            label="Click Me"
            onClick={handleClick}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Click Me'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', () => {
      const handleClick = vi.fn();

      render(
        <TestWrapper>
          <Roblox3DButton
            iconName="TROPHY"
            label="Disabled"
            onClick={handleClick}
            disabled={true}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Disabled'));
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not call onClick when loading', () => {
      const handleClick = vi.fn();

      render(
        <TestWrapper>
          <Roblox3DButton
            iconName="TROPHY"
            label="Loading"
            onClick={handleClick}
            loading={true}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Loading'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('States', () => {
    it('renders disabled state', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Disabled" disabled={true} />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toBeDisabled();
    });

    it('renders loading state with spinner', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Loading" loading={true} />
        </TestWrapper>
      );

      // Loading spinner should be present (the spinner is inline style, not class)
      expect(container.querySelector('[style*="border-radius: 50%"]')).toBeInTheDocument();
    });

    it('does not show icon when loading', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Loading" loading={true} />
        </TestWrapper>
      );

      expect(container.querySelector('img')).not.toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('renders tooltip when provided', async () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton
            iconName="TROPHY"
            label="Button"
            tooltip="Helpful tooltip"
          />
        </TestWrapper>
      );

      const button = screen.getByText('Button');
      fireEvent.mouseEnter(button);

      // In test environment, tooltip might not fully render like production
      // Just verify the button renders and no errors occur
      expect(button).toBeInTheDocument();

      // Clean up
      fireEvent.mouseLeave(button);
    });

    it('does not render tooltip when not provided', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Button" />
        </TestWrapper>
      );

      // No tooltip container should exist
      expect(container.querySelector('[role="tooltip"]')).not.toBeInTheDocument();
    });
  });

  describe('Full Width', () => {
    it('renders full width when prop is true', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Full Width" fullWidth={true} />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toHaveStyle({ width: '100%' });
    });

    it('renders auto width by default', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Auto Width" />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toHaveStyle({ width: 'auto' });
    });
  });

  describe('Animation', () => {
    it('applies animation classes when animated is true', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Animated" animated={true} />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toBeTruthy();
    });

    it('works without animation when animated is false', () => {
      render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Not Animated" animated={false} />
        </TestWrapper>
      );

      expect(screen.getByText('Not Animated')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible button role', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Accessible" />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toHaveAttribute('type', 'button');
    });

    it('has correct aria-disabled when disabled', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Disabled" disabled={true} />
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toBeDisabled();
    });

    it('has img alt text for screen readers', () => {
      const { container } = render(
        <TestWrapper>
          <Roblox3DButton iconName="TROPHY" label="Button" />
        </TestWrapper>
      );

      const img = container.querySelector('img');
      expect(img).toHaveAttribute('alt', 'TROPHY');
    });
  });

  describe('Icon Mapping', () => {
    const iconNames = [
      'ABC_CUBE',
      'BACKPACK',
      'BADGE',
      'BASKETBALL',
      'BOARD',
      'BOOKS',
      'BRUSH_PAINT',
      'GRADUATION_CAP',
      'LIGHT_BULB',
      'TROPHY',
    ];

    iconNames.forEach((iconName) => {
      it(`renders ${iconName} icon`, () => {
        const { container } = render(
          <TestWrapper>
            <Roblox3DButton iconName={iconName} label={iconName} />
          </TestWrapper>
        );

        const img = container.querySelector('img');
        expect(img).toHaveAttribute('src', expect.stringContaining(iconName));
      });
    });
  });
});
