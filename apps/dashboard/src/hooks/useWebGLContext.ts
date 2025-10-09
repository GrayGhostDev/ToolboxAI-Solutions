import { useEffect, useRef, useState } from 'react';

// Maximum number of WebGL contexts allowed (browser limit is typically 8-16)
const MAX_WEBGL_CONTEXTS = 8;

// Global registry of active WebGL contexts
const activeContexts = new Set<WebGLRenderingContext | WebGL2RenderingContext>();

// Queue of pending context requests
const contextQueue: Array<{
  resolve: (value: boolean) => void;
  reject: (reason?: any) => void;
}> = [];

// Check if we can create a new context
const canCreateContext = () => activeContexts.size < MAX_WEBGL_CONTEXTS;

// Process the queue when a context becomes available
const processQueue = () => {
  if (contextQueue.length > 0 && canCreateContext()) {
    const request = contextQueue.shift();
    request?.resolve(true);
  }
};

// Register a context
export const registerContext = (context: WebGLRenderingContext | WebGL2RenderingContext) => {
  activeContexts.add(context);
};

// Unregister a context
export const unregisterContext = (context: WebGLRenderingContext | WebGL2RenderingContext) => {
  activeContexts.delete(context);
  processQueue();
};

// Hook to manage WebGL context availability
export const useWebGLContext = () => {
  const [canRender, setCanRender] = useState(false);
  const [isQueued, setIsQueued] = useState(false);
  const requestRef = useRef<{ resolve: (value: boolean) => void; reject: (reason?: any) => void }>();

  useEffect(() => {
    // Check if we can render immediately
    if (canCreateContext()) {
      setCanRender(true);
    } else {
      // Queue the request
      setIsQueued(true);
      const request = new Promise<boolean>((resolve, reject) => {
        requestRef.current = { resolve, reject };
        contextQueue.push({ resolve, reject });
      });

      request.then((allowed) => {
        setCanRender(allowed);
        setIsQueued(false);
      });
    }

    return () => {
      // Remove from queue if component unmounts while queued
      if (requestRef.current) {
        const index = contextQueue.findIndex(
          (item) => item.resolve === requestRef.current?.resolve
        );
        if (index !== -1) {
          contextQueue.splice(index, 1);
        }
      }
    };
  }, []);

  return {
    canRender,
    isQueued,
    activeContextCount: activeContexts.size,
    maxContexts: MAX_WEBGL_CONTEXTS,
  };
};

// Hook to manage a specific WebGL canvas
export const useWebGLCanvas = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const contextRef = useRef<WebGLRenderingContext | WebGL2RenderingContext | null>(null);
  const [hasContext, setHasContext] = useState(false);

  useEffect(() => {
    if (canvasRef.current && !contextRef.current && canCreateContext()) {
      try {
        // Try WebGL2 first, fallback to WebGL
        const context =
          canvasRef.current.getContext('webgl2') ||
          canvasRef.current.getContext('webgl') ||
          canvasRef.current.getContext('experimental-webgl');

        if (context) {
          contextRef.current = context as WebGLRenderingContext | WebGL2RenderingContext;
          registerContext(contextRef.current);
          setHasContext(true);
        }
      } catch (error) {
        console.warn('Failed to create WebGL context:', error);
        setHasContext(false);
      }
    }

    return () => {
      // Cleanup context on unmount
      if (contextRef.current) {
        unregisterContext(contextRef.current);
        // Lose the context to free resources
        const loseContext = (contextRef.current as any).getExtension('WEBGL_lose_context');
        if (loseContext) {
          loseContext.loseContext();
        }
        contextRef.current = null;
        setHasContext(false);
      }
    };
  }, []);

  return {
    canvasRef,
    context: contextRef.current,
    hasContext,
    activeContextCount: activeContexts.size,
  };
};

// Utility to check WebGL support
export const isWebGLSupported = (): boolean => {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
};

// Utility to check WebGL2 support
export const isWebGL2Supported = (): boolean => {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGL2RenderingContext && canvas.getContext('webgl2'));
  } catch (e) {
    return false;
  }
};