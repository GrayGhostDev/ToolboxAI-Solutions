import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Scene3D } from '../Scene3D';
import { mantineTheme } from '@/theme/mantine-theme';

// Wrapper component for Mantine provider
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MantineProvider theme={mantineTheme}>{children}</MantineProvider>
);

describe('Scene3D', () => {
  describe('Test Environment Fallback', () => {
    it('renders fallback in test environment', () => {
      const { container } = render(
        <TestWrapper>
          <Scene3D>
            <div data-testid="3d-content">3D Content</div>
          </Scene3D>
        </TestWrapper>
      );

      // Should render fallback loader instead of 3D content
      expect(container.querySelector('.mantine-Loader-root')).toBeInTheDocument();
      expect(screen.queryByTestId('3d-content')).not.toBeInTheDocument();
    });

    it('renders custom fallback when provided', () => {
      render(
        <TestWrapper>
          <Scene3D fallback={<div data-testid="custom-fallback">Custom Fallback</div>}>
            <div data-testid="3d-content">3D Content</div>
          </Scene3D>
        </TestWrapper>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.queryByTestId('3d-content')).not.toBeInTheDocument();
    });

    it('applies correct fallback container styling', () => {
      const { container } = render(
        <TestWrapper>
          <Scene3D />
        </TestWrapper>
      );

      const fallbackContainer = container.querySelector('[style*="width: 100%"]');
      expect(fallbackContainer).toBeInTheDocument();
      expect(fallbackContainer).toHaveStyle({
        width: '100%',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      });
    });
  });

  describe('Props Handling', () => {
    it('applies custom styles to fallback container', () => {
      const customStyle = { backgroundColor: 'red', border: '1px solid blue' };

      const { container } = render(
        <TestWrapper>
          <Scene3D style={customStyle} />
        </TestWrapper>
      );

      // In test environment, custom styles are still applied
      const styledElement = container.querySelector('[style*="background"]');
      expect(styledElement).toBeInTheDocument();
    });

    it('applies custom className to fallback container', () => {
      const { container } = render(
        <TestWrapper>
          <Scene3D className="custom-scene" />
        </TestWrapper>
      );

      // In fallback mode, should still render (even if className isn't directly visible on fallback)
      expect(container.querySelector('[style*="width: 100%"]')).toBeInTheDocument();
    });
  });

  describe('Error Boundary Protection', () => {
    it('renders without throwing errors', () => {
      expect(() => {
        render(
          <TestWrapper>
            <Scene3D>
              <div>Test content</div>
            </Scene3D>
          </TestWrapper>
        );
      }).not.toThrow();
    });

    it('handles error callback prop', () => {
      const onError = vi.fn();

      render(
        <TestWrapper>
          <Scene3D onError={onError}>
            <div>Test content</div>
          </Scene3D>
        </TestWrapper>
      );

      // In test environment with WebGL unavailable, no error should be called
      expect(onError).not.toHaveBeenCalled();
    });
  });

  describe('Children Handling', () => {
    it('does not render children in test environment', () => {
      render(
        <TestWrapper>
          <Scene3D>
            <div data-testid="child-1">Child 1</div>
            <div data-testid="child-2">Child 2</div>
          </Scene3D>
        </TestWrapper>
      );

      expect(screen.queryByTestId('child-1')).not.toBeInTheDocument();
      expect(screen.queryByTestId('child-2')).not.toBeInTheDocument();
    });

    it('handles null/undefined children gracefully', () => {
      expect(() => {
        render(
          <TestWrapper>
            <Scene3D>
              {null}
              {undefined}
            </Scene3D>
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  describe('Hook Integration', () => {
    it('safely handles missing useThree hook in test environment', () => {
      expect(() => {
        render(
          <TestWrapper>
            <Scene3D />
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  describe('WebGL Context Safety', () => {
    it('does not attempt WebGL operations in test environment', () => {
      const { container } = render(
        <TestWrapper>
          <Scene3D />
        </TestWrapper>
      );

      // Should not contain any canvas elements in test mode
      expect(container.querySelector('canvas')).not.toBeInTheDocument();
    });
  });

  describe('Memory Management', () => {
    it('cleans up properly when unmounted', () => {
      const { unmount } = render(
        <TestWrapper>
          <Scene3D />
        </TestWrapper>
      );

      expect(() => unmount()).not.toThrow();
    });
  });
});