import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { FloatingCharacters } from '../FloatingCharacters';
import { mantineTheme } from '@/theme/mantine-theme';
import * as THREE from 'three';

// Wrapper component for Mantine provider
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MantineProvider theme={mantineTheme}>{children}</MantineProvider>
);

describe('FloatingCharacters', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
  });

  describe('Test Environment Fallback', () => {
    it('renders fallback component in test environment', () => {
      const { container } = render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      // Should render fallback instead of 3D canvas
      expect(container.querySelector('[data-testid="three-canvas"]')).not.toBeInTheDocument();

      // Should show fallback text
      const fallbackText = screen.getByText(/3D characters \(fallback mode\)/);
      expect(fallbackText).toBeInTheDocument();
    });

    it('displays correct character count in fallback', () => {
      const customCharacters = [
        { type: 'astronaut' as const, position: [0, 0, 0] as [number, number, number] },
        { type: 'robot' as const, position: [1, 1, 1] as [number, number, number] },
      ];

      render(
        <TestWrapper>
          <FloatingCharacters characters={customCharacters} />
        </TestWrapper>
      );

      expect(screen.getByText('2 3D characters (fallback mode)')).toBeInTheDocument();
    });
  });

  describe('Props Handling', () => {
    it('handles default characters prop', () => {
      render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      // Default has 5 characters
      expect(screen.getByText('5 3D characters (fallback mode)')).toBeInTheDocument();
    });

    it('handles custom characters prop', () => {
      const characters = [
        { type: 'wizard' as const, position: [-1, 0, 1] as [number, number, number] }
      ];

      render(
        <TestWrapper>
          <FloatingCharacters characters={characters} />
        </TestWrapper>
      );

      expect(screen.getByText('1 3D characters (fallback mode)')).toBeInTheDocument();
    });

    it('handles Vector3 position objects without errors', () => {
      // Test for the fix: "Cannot assign to read only property 'position'" errors
      const charactersWithVector3 = [
        { type: 'astronaut' as const, position: new THREE.Vector3(1, 2, 3) },
        { type: 'robot' as const, position: new THREE.Vector3(-1, 0, 1) }
      ];

      expect(() => {
        render(
          <TestWrapper>
            <FloatingCharacters characters={charactersWithVector3} />
          </TestWrapper>
        );
      }).not.toThrow();

      // Should show correct character count
      expect(screen.getByText('2 3D characters (fallback mode)')).toBeInTheDocument();
    });

    it('handles mixed position formats (arrays and Vector3)', () => {
      const mixedPositions = [
        { type: 'wizard' as const, position: [0, 1, 2] as [number, number, number] },
        { type: 'ninja' as const, position: new THREE.Vector3(3, 4, 5) },
        { type: 'pirate' as const, position: [-1, -2, -3] as [number, number, number] }
      ];

      expect(() => {
        render(
          <TestWrapper>
            <FloatingCharacters characters={mixedPositions} />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(screen.getByText('3 3D characters (fallback mode)')).toBeInTheDocument();
    });

    it('handles stars and clouds props', () => {
      render(
        <TestWrapper>
          <FloatingCharacters showStars={false} showClouds={false} />
        </TestWrapper>
      );

      // Component should still render fallback regardless of 3D props
      expect(screen.getByText(/3D characters \(fallback mode\)/)).toBeInTheDocument();
    });
  });

  describe('Error Boundary Protection', () => {
    it('renders without throwing errors', () => {
      expect(() => {
        render(
          <TestWrapper>
            <FloatingCharacters />
          </TestWrapper>
        );
      }).not.toThrow();
    });

    it('handles invalid character types gracefully', () => {
      const invalidCharacters = [
        { type: 'invalid' as any, position: [0, 0, 0] as [number, number, number] }
      ];

      expect(() => {
        render(
          <TestWrapper>
            <FloatingCharacters characters={invalidCharacters} />
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  describe('Fallback Component Styling', () => {
    it('applies correct styling to fallback container', () => {
      const { container } = render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      // Look for the Box with the specific styling instead of firstChild
      const fallbackContainer = container.querySelector('[style*="position"]');
      expect(fallbackContainer).toBeInTheDocument();
      expect(fallbackContainer).toHaveStyle('position: fixed');
    });

    it('has correct opacity and background styling', () => {
      const { container } = render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      const innerBox = container.querySelector('[style*="opacity: 0.3"]');
      expect(innerBox).toBeInTheDocument();
    });
  });

  describe('WebGL Detection', () => {
    it('falls back correctly when WebGL is not available', () => {
      // Mock WebGL as unavailable
      const originalCreateElement = document.createElement;
      document.createElement = vi.fn((tagName) => {
        if (tagName === 'canvas') {
          return {
            getContext: vi.fn(() => null) // Return null to simulate no WebGL
          } as any;
        }
        return originalCreateElement.call(document, tagName);
      });

      render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      expect(screen.getByText(/3D characters \(fallback mode\)/)).toBeInTheDocument();

      // Restore original function
      document.createElement = originalCreateElement;
    });
  });

  describe('Performance Considerations', () => {
    it('renders fallback instead of initializing WebGL', () => {
      const { container } = render(
        <TestWrapper>
          <FloatingCharacters />
        </TestWrapper>
      );

      // Should render fallback text, which means WebGL was not attempted
      expect(screen.getByText(/3D characters \(fallback mode\)/)).toBeInTheDocument();

      // Should not contain any Three.js canvas elements
      expect(container.querySelector('[data-testid="three-canvas"]')).not.toBeInTheDocument();
    });
  });
});