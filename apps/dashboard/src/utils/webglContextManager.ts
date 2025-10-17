/**
 * WebGL Context Manager
 *
 * Manages WebGL contexts to prevent "too many active WebGL contexts" errors.
 * Browsers typically limit to 8-16 concurrent WebGL contexts.
 *
 * This manager:
 * - Tracks active Canvas instances
 * - Enforces a maximum limit (default: 6 to be safe)
 * - Properly disposes of old contexts when limit is reached
 * - Provides hooks for React components
 */

interface CanvasRegistration {
  id: string;
  canvas: HTMLCanvasElement | null;
  gl: WebGLRenderingContext | WebGL2RenderingContext | null;
  timestamp: number;
  priority: number; // Higher priority = less likely to be disposed
}

class WebGLContextManager {
  private static instance: WebGLContextManager;
  private registrations: Map<string, CanvasRegistration> = new Map();
  private readonly MAX_CONTEXTS = 6; // Safe limit for most browsers
  private disposeCallbacks: Map<string, () => void> = new Map();

  private constructor() {}

  public static getInstance(): WebGLContextManager {
    if (!WebGLContextManager.instance) {
      WebGLContextManager.instance = new WebGLContextManager();
    }
    return WebGLContextManager.instance;
  }

  /**
   * Register a new Canvas component
   * @param id Unique identifier for the canvas
   * @param canvas HTML canvas element (can be null initially)
   * @param priority Priority level (0-10, higher = more important)
   * @param onDispose Callback to clean up resources when context is forcibly disposed
   */
  public register(
    id: string,
    canvas: HTMLCanvasElement | null,
    priority: number = 5,
    onDispose?: () => void
  ): boolean {
    // Check if we need to free up space
    if (this.registrations.size >= this.MAX_CONTEXTS && !this.registrations.has(id)) {
      this.evictLowestPriority(priority);
    }

    // Get WebGL context if canvas is available
    let gl: WebGLRenderingContext | WebGL2RenderingContext | null = null;
    if (canvas) {
      gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    }

    const registration: CanvasRegistration = {
      id,
      canvas,
      gl,
      timestamp: Date.now(),
      priority
    };

    this.registrations.set(id, registration);

    if (onDispose) {
      this.disposeCallbacks.set(id, onDispose);
    }

    console.log(`[WebGLContextManager] Registered context ${id} (${this.registrations.size}/${this.MAX_CONTEXTS})`);

    return true;
  }

  /**
   * Update canvas reference for an existing registration
   */
  public updateCanvas(id: string, canvas: HTMLCanvasElement): void {
    const registration = this.registrations.get(id);
    if (!registration) {
      console.warn(`[WebGLContextManager] Attempted to update non-existent registration: ${id}`);
      return;
    }

    registration.canvas = canvas;
    registration.gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    registration.timestamp = Date.now();
  }

  /**
   * Unregister a Canvas component
   */
  public unregister(id: string): void {
    const registration = this.registrations.get(id);
    if (registration) {
      this.disposeContext(registration);
      this.registrations.delete(id);
      this.disposeCallbacks.delete(id);
      console.log(`[WebGLContextManager] Unregistered context ${id} (${this.registrations.size}/${this.MAX_CONTEXTS})`);
    }
  }

  /**
   * Update priority for an existing registration
   */
  public updatePriority(id: string, priority: number): void {
    const registration = this.registrations.get(id);
    if (registration) {
      registration.priority = priority;
      registration.timestamp = Date.now();
    }
  }

  /**
   * Evict the lowest priority context to make room for a new one
   */
  private evictLowestPriority(requiredPriority: number): void {
    let lowestPriority = Infinity;
    let oldestTimestamp = Infinity;
    let victimId: string | null = null;

    // Find the lowest priority context, or oldest if priorities are equal
    for (const [id, reg] of this.registrations.entries()) {
      if (reg.priority < lowestPriority ||
          (reg.priority === lowestPriority && reg.timestamp < oldestTimestamp)) {
        lowestPriority = reg.priority;
        oldestTimestamp = reg.timestamp;
        victimId = id;
      }
    }

    // Only evict if victim has lower priority than required
    if (victimId && lowestPriority < requiredPriority) {
      console.warn(`[WebGLContextManager] Evicting context ${victimId} (priority ${lowestPriority}) to make room for priority ${requiredPriority}`);
      this.unregister(victimId);
    } else {
      console.warn(`[WebGLContextManager] Cannot evict - all contexts have equal or higher priority`);
    }
  }

  /**
   * Properly dispose of a WebGL context and associated resources
   */
  private disposeContext(registration: CanvasRegistration): void {
    // Call custom dispose callback if provided
    const disposeCallback = this.disposeCallbacks.get(registration.id);
    if (disposeCallback) {
      try {
        disposeCallback();
      } catch (error) {
        console.error(`[WebGLContextManager] Error in dispose callback for ${registration.id}:`, error);
      }
    }

    // Lose WebGL context
    if (registration.gl && registration.canvas) {
      const loseContext = registration.gl.getExtension('WEBGL_lose_context');
      if (loseContext) {
        loseContext.loseContext();
      }
    }
  }

  /**
   * Get current statistics
   */
  public getStats(): { active: number; max: number; registrations: string[] } {
    return {
      active: this.registrations.size,
      max: this.MAX_CONTEXTS,
      registrations: Array.from(this.registrations.keys())
    };
  }

  /**
   * Check if we're at capacity
   */
  public isAtCapacity(): boolean {
    return this.registrations.size >= this.MAX_CONTEXTS;
  }

  /**
   * Force cleanup of all contexts (use with caution)
   */
  public cleanup(): void {
    console.log(`[WebGLContextManager] Cleaning up all ${this.registrations.size} contexts`);
    for (const id of Array.from(this.registrations.keys())) {
      this.unregister(id);
    }
  }
}

export const webglContextManager = WebGLContextManager.getInstance();

/**
 * React hook for managing WebGL contexts
 */
export function useWebGLContext(
  id: string,
  priority: number = 5,
  onDispose?: () => void
) {
  const [isRegistered, setIsRegistered] = React.useState(false);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

  React.useEffect(() => {
    // Register on mount
    const registered = webglContextManager.register(id, canvasRef.current, priority, onDispose);
    setIsRegistered(registered);

    // Unregister on unmount
    return () => {
      webglContextManager.unregister(id);
    };
  }, [id, priority]);

  // Update canvas ref when it changes
  const setCanvasRef = React.useCallback((canvas: HTMLCanvasElement | null) => {
    canvasRef.current = canvas;
    if (canvas && isRegistered) {
      webglContextManager.updateCanvas(id, canvas);
    }
  }, [id, isRegistered]);

  return {
    canvasRef: setCanvasRef,
    isRegistered,
    stats: webglContextManager.getStats()
  };
}

// Add React import for the hook
import * as React from 'react';
