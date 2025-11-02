/**
 * Shared Canvas Wrapper for @react-three/fiber
 *
 * Prevents multiple WebGL context creation by providing a shared
 * Canvas component that all 3D components must use.
 *
 * This solves the "Too many active WebGL contexts" warning.
 */

import React, { useRef, useEffect } from 'react';
import { Canvas as R3FCanvas } from '@react-three/fiber';
import type { Props as CanvasProps } from '@react-three/fiber';

// Global registry to track active Canvas instances
let activeCanvasCount = 0;
const MAX_CANVAS_INSTANCES = 2; // Limit to 2 concurrent Canvas instances

interface SharedCanvasProps extends CanvasProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * SharedCanvas - A wrapper around @react-three/fiber Canvas
 * that enforces a maximum number of concurrent WebGL contexts
 */
export const SharedCanvas: React.FC<SharedCanvasProps> = ({
  children,
  fallback,
  ...canvasProps
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [canMount, setCanMount] = React.useState(false);

  useEffect(() => {
    // Check if we can create another Canvas instance
    if (activeCanvasCount < MAX_CANVAS_INSTANCES) {
      activeCanvasCount++;
      setCanMount(true);

      return () => {
        // Clean up: decrement counter when component unmounts
        activeCanvasCount--;
      };
    } else {
      console.warn(
        `[SharedCanvas] Maximum Canvas instances (${MAX_CANVAS_INSTANCES}) reached. ` +
        'Showing fallback instead.'
      );
      setCanMount(false);
    }
  }, []);

  if (!canMount) {
    return fallback ? <>{fallback}</> : null;
  }

  return (
    <div ref={canvasRef} style={{ width: '100%', height: '100%' }}>
      <R3FCanvas {...canvasProps}>
        {children}
      </R3FCanvas>
    </div>
  );
};

/**
 * Hook to check if Canvas can be mounted
 * Useful for conditional rendering before attempting to mount Canvas
 */
export const useCanMountCanvas = (): boolean => {
  const [canMount, setCanMount] = React.useState(false);

  useEffect(() => {
    setCanMount(activeCanvasCount < MAX_CANVAS_INSTANCES);
  }, []);

  return canMount;
};

/**
 * Get current active Canvas count (for debugging)
 */
export const getActiveCanvasCount = (): number => {
  return activeCanvasCount;
};

export default SharedCanvas;

