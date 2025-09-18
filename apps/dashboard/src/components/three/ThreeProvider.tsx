import React, { createContext, useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';

// Singleton instance storage for WebGL renderer to prevent context limit
let globalRenderer: THREE.WebGLRenderer | null = null;
let globalRendererRefCount = 0;

interface ThreeContextType {
  scene: THREE.Scene | null;
  camera: THREE.PerspectiveCamera | null;
  renderer: THREE.WebGLRenderer | null;
  isWebGLAvailable: boolean;
  performanceLevel: 'high' | 'medium' | 'low';
  addObject: (object: THREE.Object3D) => void;
  removeObject: (object: THREE.Object3D) => void;
  cleanup: () => void;
}

export const ThreeContext = createContext<ThreeContextType>({
  scene: null,
  camera: null,
  renderer: null,
  isWebGLAvailable: false,
  performanceLevel: 'high',
  addObject: () => {},
  removeObject: () => {},
  cleanup: () => {}
});

interface ThreeProviderProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const ThreeProvider: React.FC<ThreeProviderProps> = ({ children, fallback }) => {
  const [isWebGLAvailable, setIsWebGLAvailable] = useState(false);
  const [performanceLevel, setPerformanceLevel] = useState<'high' | 'medium' | 'low'>('high');
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const frameIdRef = useRef<number>();
  const objectsRef = useRef<Set<THREE.Object3D>>(new Set());

  // Check WebGL availability
  useEffect(() => {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    setIsWebGLAvailable(!!gl);

    // Detect performance level
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        // Simple performance detection based on renderer
        if (renderer.includes('Intel') || renderer.includes('Mesa')) {
          setPerformanceLevel('low');
        } else if (renderer.includes('AMD') || renderer.includes('NVIDIA')) {
          setPerformanceLevel('high');
        } else {
          setPerformanceLevel('medium');
        }
      }
    }
  }, []);

  // Initialize Three.js scene
  useEffect(() => {
    if (!isWebGLAvailable) return;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    scene.fog = new THREE.Fog(0x0a0a0a, 10, 50);
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 5;
    cameraRef.current = camera;

    // Create or reuse renderer (singleton pattern to avoid WebGL context limit)
    let renderer: THREE.WebGLRenderer;
    if (globalRenderer && globalRenderer.domElement.isConnected === false) {
      // Reuse existing renderer if available
      renderer = globalRenderer;
      globalRendererRefCount++;
    } else if (!globalRenderer) {
      // Create new renderer only if none exists
      renderer = new THREE.WebGLRenderer({
        antialias: performanceLevel === 'high',
        powerPreference: performanceLevel === 'high' ? 'high-performance' : 'low-power',
        alpha: true
      });
      globalRenderer = renderer;
      globalRendererRefCount = 1;
    } else {
      // Use existing renderer
      renderer = globalRenderer;
      globalRendererRefCount++;
    }

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, performanceLevel === 'high' ? 2 : 1));
    renderer.shadowMap.enabled = performanceLevel !== 'low';
    renderer.shadowMap.type = performanceLevel === 'high' ? THREE.PCFSoftShadowMap : THREE.BasicShadowMap;
    rendererRef.current = renderer;

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 10);
    if (performanceLevel !== 'low') {
      directionalLight.castShadow = true;
      directionalLight.shadow.mapSize.width = 2048;
      directionalLight.shadow.mapSize.height = 2048;
    }
    scene.add(directionalLight);

    // Animation loop
    const animate = () => {
      frameIdRef.current = requestAnimationFrame(animate);

      // Auto-rotate objects
      objectsRef.current.forEach(obj => {
        if (obj.userData.autoRotate) {
          obj.rotation.y += 0.01;
        }
      });

      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (frameIdRef.current) {
        cancelAnimationFrame(frameIdRef.current);
      }

      // Cleanup
      globalRendererRefCount--;

      // Only dispose renderer if no other components are using it
      if (globalRendererRefCount <= 0 && globalRenderer) {
        globalRenderer.dispose();
        globalRenderer = null;
        globalRendererRefCount = 0;
      }

      scene.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach(material => material.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    };
  }, [isWebGLAvailable, performanceLevel]);

  const addObject = useCallback((object: THREE.Object3D) => {
    if (sceneRef.current) {
      sceneRef.current.add(object);
      objectsRef.current.add(object);
    }
  }, []);

  const removeObject = useCallback((object: THREE.Object3D) => {
    if (sceneRef.current) {
      sceneRef.current.remove(object);
      objectsRef.current.delete(object);

      // Cleanup geometry and materials
      object.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach(material => material.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    }
  }, []);

  const cleanup = useCallback(() => {
    objectsRef.current.forEach(obj => removeObject(obj));
    objectsRef.current.clear();
  }, [removeObject]);

  const contextValue: ThreeContextType = {
    scene: sceneRef.current,
    camera: cameraRef.current,
    renderer: rendererRef.current,
    isWebGLAvailable,
    performanceLevel,
    addObject,
    removeObject,
    cleanup
  };

  if (!isWebGLAvailable && fallback) {
    return <>{fallback}</>;
  }

  return (
    <ThreeContext.Provider value={contextValue}>
      {children}
    </ThreeContext.Provider>
  );
};