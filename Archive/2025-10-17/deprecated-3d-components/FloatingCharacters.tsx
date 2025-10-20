/**
 * FloatingCharacters Component
 *
 * Adds floating 3D characters throughout the dashboard
 * for a playful, game-like atmosphere with proper WebGL context handling
 */
import React, { useRef, ErrorBoundary, Component, Suspense } from 'react';
import { Canvas, useFrame, type ThreeElements } from '@react-three/fiber';
import { OrbitControls, Float, Stars, Cloud } from '@react-three/drei';
import { Box, Loader, Alert } from '@mantine/core';
import * as THREE from 'three';
import type { Group } from 'three';

// WebGL Context Check Hook
const useWebGLSupport = () => {
  const [isSupported, setIsSupported] = React.useState(true);

  React.useEffect(() => {
    try {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      setIsSupported(!!context);
    } catch (error) {
      console.warn('WebGL context check failed:', error);
      setIsSupported(false);
    }
  }, []);

  return isSupported;
};

// Error Boundary for 3D Components
class ThreeErrorBoundary extends Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('3D Component Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Alert color="yellow" variant="light">
          3D graphics unavailable - using fallback display
        </Alert>
      );
    }

    return this.props.children;
  }
}

// 2D Fallback Component
const FloatingCharactersFallback: React.FunctionComponent<{ characterCount: number }> = ({ characterCount }) => (
  <Box
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none',
      zIndex: 0,
      background: 'linear-gradient(135deg, rgba(10, 10, 10, 0.1) 0%, rgba(30, 30, 30, 0.1) 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      opacity: 0.3
    }}
  >
    <Box style={{ color: '#666', fontSize: '12px', textAlign: 'center' }}>
      {characterCount} 3D characters (fallback mode)
    </Box>
  </Box>
);
interface FloatingCharacterProps {
  position: [number, number, number] | THREE.Vector3;
  characterType: 'astronaut' | 'robot' | 'wizard' | 'pirate' | 'ninja';
  floatSpeed?: number;
  rotationSpeed?: number;
  scale?: number;
}
// Utility function to convert position to array format
// This prevents "Cannot assign to read only property 'position'" errors
// by ensuring position is always passed as an array [x, y, z] to Three.js
const positionToArray = (pos: [number, number, number] | THREE.Vector3): [number, number, number] => {
  if (pos instanceof THREE.Vector3) {
    return [pos.x, pos.y, pos.z];
  }
  // If it's already an array, ensure it's a proper tuple
  return Array.isArray(pos) ? [pos[0] || 0, pos[1] || 0, pos[2] || 0] as [number, number, number] : [0, 0, 0];
};

const FloatingCharacter: React.FunctionComponent<FloatingCharacterProps> = ({
  position,
  characterType,
  floatSpeed = 1,
  rotationSpeed = 0.5,
  scale = 1
}) => {
  const meshRef = useRef<Group>(null);
  const positionArray = positionToArray(position);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += rotationSpeed * 0.01;
      meshRef.current.position.y = positionArray[1] + Math.sin(state.clock.elapsedTime * floatSpeed) * 0.2;
    }
  });
  const characterColors = {
    astronaut: { primary: '#ffffff', secondary: '#00ffff', accent: '#ff00ff' },
    robot: { primary: '#c0c0c0', secondary: '#00ff00', accent: '#ffff00' },
    wizard: { primary: '#6b46c1', secondary: '#ffd700', accent: '#ff1493' },
    pirate: { primary: '#8b4513', secondary: '#ffd700', accent: '#ff0000' },
    ninja: { primary: '#1a1a1a', secondary: '#ff0000', accent: '#ffffff' }
  };
  const colors = characterColors[characterType];
  return (
    <Float speed={floatSpeed} rotationIntensity={0.5} floatIntensity={0.5}>
      <group ref={meshRef} position={positionArray} scale={scale}>
        {characterType === 'astronaut' && (
          <>
            {/* Helmet */}
            <mesh position={[0, 0.8, 0]}>
              <sphereGeometry args={[0.35, 16, 16]} />
              <meshStandardMaterial
                color={colors.primary}
                metalness={0.8}
                roughness={0.2}
                transparent
                opacity={0.7}
              />
            </mesh>
            {/* Visor */}
            <mesh position={[0, 0.8, 0.2]}>
              <sphereGeometry args={[0.25, 16, 16, 0, Math.PI]} />
              <meshStandardMaterial
                color={colors.secondary}
                metalness={1}
                roughness={0.1}
                emissive={colors.secondary}
                emissiveIntensity={0.3}
              />
            </mesh>
            {/* Body */}
            <mesh position={[0, 0, 0]}>
              <cylinderGeometry args={[0.3, 0.35, 1, 8]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Jetpack */}
            <mesh position={[-0.3, 0, 0]}>
              <boxGeometry args={[0.15, 0.4, 0.2]} />
              <meshStandardMaterial
                color={colors.accent}
                emissive={colors.accent}
                emissiveIntensity={0.5}
              />
            </mesh>
          </>
        )}
        {characterType === 'robot' && (
          <>
            {/* Head */}
            <mesh position={[0, 0.8, 0]}>
              <boxGeometry args={[0.4, 0.4, 0.4]} />
              <meshStandardMaterial
                color={colors.primary}
                metalness={0.9}
                roughness={0.1}
              />
            </mesh>
            {/* Eyes */}
            <mesh position={[0.1, 0.85, 0.2]}>
              <sphereGeometry args={[0.05, 8, 8]} />
              <meshStandardMaterial
                color={colors.secondary}
                emissive={colors.secondary}
                emissiveIntensity={1}
              />
            </mesh>
            <mesh position={[-0.1, 0.85, 0.2]}>
              <sphereGeometry args={[0.05, 8, 8]} />
              <meshStandardMaterial
                color={colors.secondary}
                emissive={colors.secondary}
                emissiveIntensity={1}
              />
            </mesh>
            {/* Body */}
            <mesh position={[0, 0, 0]}>
              <boxGeometry args={[0.5, 0.8, 0.3]} />
              <meshStandardMaterial
                color={colors.primary}
                metalness={0.8}
                roughness={0.2}
              />
            </mesh>
            {/* Antenna */}
            <mesh position={[0, 1.1, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.3, 8]} />
              <meshStandardMaterial color={colors.accent} />
            </mesh>
            <mesh position={[0, 1.25, 0]}>
              <sphereGeometry args={[0.05, 8, 8]} />
              <meshStandardMaterial
                color={colors.accent}
                emissive={colors.accent}
                emissiveIntensity={0.8}
              />
            </mesh>
          </>
        )}
        {characterType === 'wizard' && (
          <>
            {/* Hat */}
            <mesh position={[0, 1, 0]}>
              <coneGeometry args={[0.3, 0.6, 8]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Stars on hat */}
            {[0, 72, 144, 216, 288].map((angle, i) => (
              <mesh
                key={i}
                position={[
                  Math.cos((angle * Math.PI) / 180) * 0.25,
                  0.9,
                  Math.sin((angle * Math.PI) / 180) * 0.25
                ]}
              >
                <octahedronGeometry args={[0.03, 0]} />
                <meshStandardMaterial
                  color={colors.secondary}
                  emissive={colors.secondary}
                  emissiveIntensity={0.5}
                />
              </mesh>
            ))}
            {/* Head */}
            <mesh position={[0, 0.5, 0]}>
              <sphereGeometry args={[0.25, 16, 16]} />
              <meshStandardMaterial color="#fdbcb4" />
            </mesh>
            {/* Beard */}
            <mesh position={[0, 0.3, 0.15]}>
              <coneGeometry args={[0.15, 0.3, 8]} />
              <meshStandardMaterial color="#ffffff" />
            </mesh>
            {/* Body/Robe */}
            <mesh position={[0, -0.2, 0]}>
              <coneGeometry args={[0.4, 1, 8]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Staff */}
            <mesh position={[0.4, 0, 0]}>
              <cylinderGeometry args={[0.03, 0.03, 1.5, 8]} />
              <meshStandardMaterial color="#8b4513" />
            </mesh>
            {/* Crystal on staff */}
            <mesh position={[0.4, 0.8, 0]}>
              <octahedronGeometry args={[0.1, 0]} />
              <meshStandardMaterial
                color={colors.accent}
                emissive={colors.accent}
                emissiveIntensity={1}
                transparent
                opacity={0.8}
              />
            </mesh>
          </>
        )}
        {characterType === 'pirate' && (
          <>
            {/* Hat */}
            <mesh position={[0, 0.9, 0]}>
              <cylinderGeometry args={[0.3, 0.25, 0.15, 8]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Skull on hat */}
            <mesh position={[0, 0.9, 0.25]}>
              <sphereGeometry args={[0.08, 8, 8]} />
              <meshStandardMaterial color="#ffffff" />
            </mesh>
            {/* Head */}
            <mesh position={[0, 0.5, 0]}>
              <sphereGeometry args={[0.25, 16, 16]} />
              <meshStandardMaterial color="#fdbcb4" />
            </mesh>
            {/* Eye patch */}
            <mesh position={[-0.1, 0.55, 0.24]}>
              <planeGeometry args={[0.12, 0.08]} />
              <meshStandardMaterial color="#000000" />
            </mesh>
            {/* Body */}
            <mesh position={[0, -0.1, 0]}>
              <cylinderGeometry args={[0.3, 0.35, 0.8, 8]} />
              <meshStandardMaterial color={colors.accent} />
            </mesh>
            {/* Sword */}
            <mesh position={[0.4, 0, 0]} rotation={[0, 0, Math.PI / 6]}>
              <boxGeometry args={[0.05, 0.8, 0.02]} />
              <meshStandardMaterial
                color="#c0c0c0"
                metalness={0.9}
                roughness={0.1}
              />
            </mesh>
            {/* Sword handle */}
            <mesh position={[0.4, -0.45, 0]} rotation={[0, 0, Math.PI / 6]}>
              <cylinderGeometry args={[0.03, 0.03, 0.2, 8]} />
              <meshStandardMaterial color={colors.secondary} />
            </mesh>
          </>
        )}
        {characterType === 'ninja' && (
          <>
            {/* Head/Mask */}
            <mesh position={[0, 0.7, 0]}>
              <sphereGeometry args={[0.25, 16, 16]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Eye slit */}
            <mesh position={[0, 0.75, 0.24]}>
              <planeGeometry args={[0.3, 0.05]} />
              <meshStandardMaterial color="#333333" />
            </mesh>
            {/* Body */}
            <mesh position={[0, 0, 0]}>
              <cylinderGeometry args={[0.25, 0.3, 1, 8]} />
              <meshStandardMaterial color={colors.primary} />
            </mesh>
            {/* Belt */}
            <mesh position={[0, 0, 0]}>
              <torusGeometry args={[0.28, 0.03, 8, 16]} />
              <meshStandardMaterial color={colors.accent} />
            </mesh>
            {/* Throwing star */}
            <mesh position={[0.35, 0.2, 0]} rotation={[0, 0, Math.PI / 4]}>
              <cylinderGeometry args={[0.08, 0.08, 0.01, 4]} />
              <meshStandardMaterial
                color="#c0c0c0"
                metalness={0.9}
                roughness={0.1}
              />
            </mesh>
          </>
        )}
        {/* Shadow */}
        <mesh position={[0, -0.8, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[1, 1]} />
          <meshStandardMaterial
            color="#000000"
            transparent
            opacity={0.2}
          />
        </mesh>
      </group>
    </Float>
  );
};
interface FloatingCharactersProps {
  characters?: Array<{
    type: 'astronaut' | 'robot' | 'wizard' | 'pirate' | 'ninja';
    position: [number, number, number] | THREE.Vector3;
  }>;
  showStars?: boolean;
  showClouds?: boolean;
}
export const FloatingCharacters: React.FunctionComponent<FloatingCharactersProps> = ({
  characters = [
    { type: 'astronaut', position: [-3, 1, -2] },
    { type: 'robot', position: [3, 0, -2] },
    { type: 'wizard', position: [0, 1.5, -3] },
    { type: 'pirate', position: [-2, -0.5, -1] },
    { type: 'ninja', position: [2, 0.5, -1] }
  ],
  showStars = true,
  showClouds = true
}) => {
  const isWebGLSupported = useWebGLSupport();

  // Test environment detection
  const isTestEnvironment = process.env.NODE_ENV === 'test' || typeof window === 'undefined';

  // Fallback for non-WebGL environments or test environments
  if (!isWebGLSupported || isTestEnvironment) {
    return <FloatingCharactersFallback characterCount={characters.length} />;
  }

  return (
    <ThreeErrorBoundary fallback={<FloatingCharactersFallback characterCount={characters.length} />}>
      <Box
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 0
        }}
      >
        <Canvas
          camera={{ position: [0, 0, 5], fov: 60 }}
          style={{ background: 'transparent' }}
          dpr={[1, 2]}
          performance={{ min: 0.5 }}
          frameloop="demand"
          gl={{
            powerPreference: 'high-performance',
            antialias: false,
            alpha: true,
            depth: false,
            stencil: false,
          }}
          onCreated={(state) => {
            // Ensure canvas is properly initialized
            state.gl.setClearColor('#000000', 0);
            state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 2));
          }}
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={0.8} />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff00ff" />
            {showStars && <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade />}
            {showClouds && (
              <>
                <Cloud position={[-4, 2, -5]} speed={0.2} opacity={0.3} />
                <Cloud position={[4, -2, -5]} speed={0.3} opacity={0.2} />
              </>
            )}
            {characters.map((char, index) => (
              <FloatingCharacter
                key={`${char.type}-${index}`}
                characterType={char.type}
                position={char.position}
                floatSpeed={1 + index * 0.2}
                rotationSpeed={0.5 + index * 0.1}
                scale={0.8 + (index % 2) * 0.2}
              />
            ))}
            <OrbitControls
              enableZoom={false}
              enablePan={false}
              enableRotate={false}
              makeDefault
            />
          </Suspense>
        </Canvas>
      </Box>
    </ThreeErrorBoundary>
  );
};
export default FloatingCharacters;