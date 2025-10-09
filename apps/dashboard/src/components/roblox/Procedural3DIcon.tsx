import React, { useRef, memo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Box as ThreeBox, Sphere, Cone, Cylinder, Torus, Octahedron } from '@react-three/drei';
import { Box } from '@mantine/core';
import type * as THREE from 'three';
import { useWebGLContext } from '../../hooks/useWebGLContext';

// Icon type to 3D shape mapping
const iconShapes: Record<string, React.FunctionComponent<any>> = {
  ROCKET: ({ color, ...props }) => (
    <group {...props}>
      <Cone args={[0.3, 1, 8]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#ff0000'} />
      </Cone>
      <Cylinder args={[0.2, 0.3, 0.4, 8]} position={[0, -0.3, 0]}>
        <meshStandardMaterial color={color || '#ffffff'} />
      </Cylinder>
      <Cone args={[0.2, 0.3, 4]} position={[0.3, -0.4, 0]} rotation={[0, 0, -Math.PI / 4]}>
        <meshStandardMaterial color={color || '#ff4500'} />
      </Cone>
      <Cone args={[0.2, 0.3, 4]} position={[-0.3, -0.4, 0]} rotation={[0, 0, Math.PI / 4]}>
        <meshStandardMaterial color={color || '#ff4500'} />
      </Cone>
    </group>
  ),

  STAR: ({ color, ...props }) => (
    <group {...props}>
      {[...Array(5)].map((_, i) => {
        const angle = (i * 72 * Math.PI) / 180;
        return (
          <Cone
            key={i}
            args={[0.1, 0.6, 3]}
            position={[Math.cos(angle) * 0.3, 0, Math.sin(angle) * 0.3]}
            rotation={[0, 0, angle + Math.PI / 2]}
          >
            <meshStandardMaterial color={color || '#ffff00'} emissive={color || '#ffff00'} emissiveIntensity={0.2} />
          </Cone>
        );
      })}
      <Sphere args={[0.2, 16, 16]}>
        <meshStandardMaterial color={color || '#ffff00'} emissive={color || '#ffff00'} emissiveIntensity={0.3} />
      </Sphere>
    </group>
  ),

  TROPHY: ({ color, ...props }) => (
    <group {...props}>
      <Cylinder args={[0.4, 0.3, 0.8, 8]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#ffd700'} metalness={0.8} roughness={0.2} />
      </Cylinder>
      <Cylinder args={[0.2, 0.3, 0.2, 8]} position={[0, -0.2, 0]}>
        <meshStandardMaterial color={color || '#ffd700'} metalness={0.8} roughness={0.2} />
      </Cylinder>
      <ThreeBox args={[0.5, 0.1, 0.3]} position={[0, -0.4, 0]}>
        <meshStandardMaterial color={color || '#8b4513'} />
      </ThreeBox>
      <Torus args={[0.35, 0.05, 8, 16]} position={[0, 0.2, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color={color || '#ffd700'} metalness={0.9} roughness={0.1} />
      </Torus>
    </group>
  ),

  BOOKS: ({ color, ...props }) => (
    <group {...props}>
      <ThreeBox args={[0.4, 0.6, 0.15]} position={[-0.2, 0, 0]} rotation={[0, 0, 0.1]}>
        <meshStandardMaterial color={color || '#ff0000'} />
      </ThreeBox>
      <ThreeBox args={[0.4, 0.6, 0.15]} position={[0, 0, 0]} rotation={[0, 0, -0.05]}>
        <meshStandardMaterial color={color || '#00ff00'} />
      </ThreeBox>
      <ThreeBox args={[0.4, 0.6, 0.15]} position={[0.2, 0, 0]} rotation={[0, 0, -0.15]}>
        <meshStandardMaterial color={color || '#0000ff'} />
      </ThreeBox>
    </group>
  ),

  SPORTS_ESPORTS: ({ color, ...props }) => (
    <group {...props}>
      <ThreeBox args={[0.8, 0.5, 0.1]} position={[0, 0, 0]}>
        <meshStandardMaterial color={color || '#333333'} />
      </ThreeBox>
      <ThreeBox args={[0.3, 0.2, 0.15]} position={[-0.2, 0, 0.1]}>
        <meshStandardMaterial color={color || '#666666'} />
      </ThreeBox>
      <ThreeBox args={[0.3, 0.2, 0.15]} position={[0.2, 0, 0.1]}>
        <meshStandardMaterial color={color || '#666666'} />
      </ThreeBox>
      <Cylinder args={[0.05, 0.05, 0.3, 8]} position={[0, -0.3, 0]}>
        <meshStandardMaterial color={color || '#444444'} />
      </Cylinder>
    </group>
  ),

  ABC_CUBE: ({ color, ...props }) => (
    <group {...props}>
      <ThreeBox args={[0.6, 0.6, 0.6]}>
        <meshStandardMaterial color={color || '#ff00ff'} />
      </ThreeBox>
    </group>
  ),

  BOARD: ({ color, ...props }) => (
    <group {...props}>
      <ThreeBox args={[0.8, 0.6, 0.05]} position={[0, 0, 0]}>
        <meshStandardMaterial color={color || '#2e7d32'} />
      </ThreeBox>
      <ThreeBox args={[0.7, 0.5, 0.01]} position={[0, 0, 0.03]}>
        <meshStandardMaterial color={color || '#1b5e20'} />
      </ThreeBox>
    </group>
  ),

  SOCCER_BALL: ({ color, ...props }) => (
    <group {...props}>
      <Sphere args={[0.5, 16, 16]}>
        <meshStandardMaterial color={color || '#ffffff'} />
      </Sphere>
      {[...Array(6)].map((_, i) => {
        const phi = Math.acos(-1 + (2 * i) / 5);
        const theta = Math.sqrt(5 * Math.PI) * i;
        return (
          <Sphere
            key={i}
            args={[0.15, 8, 8]}
            position={[
              0.5 * Math.cos(theta) * Math.sin(phi),
              0.5 * Math.sin(theta) * Math.sin(phi),
              0.5 * Math.cos(phi),
            ]}
          >
            <meshStandardMaterial color="#000000" />
          </Sphere>
        );
      })}
    </group>
  ),

  BRUSH_PAINT: ({ color, ...props }) => (
    <group {...props}>
      <Cylinder args={[0.08, 0.08, 0.8, 8]} position={[0, 0, 0]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color={color || '#8b4513'} />
      </Cylinder>
      <Cone args={[0.15, 0.3, 8]} position={[0.2, 0.3, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <meshStandardMaterial color={color || '#ff00ff'} />
      </Cone>
    </group>
  ),

  ASSESSMENT: ({ color, ...props }) => (
    <group {...props}>
      <ThreeBox args={[0.6, 0.8, 0.02]} position={[0, 0, 0]}>
        <meshStandardMaterial color={color || '#ffffff'} />
      </ThreeBox>
      <ThreeBox args={[0.4, 0.05, 0.03]} position={[0, 0.2, 0.02]}>
        <meshStandardMaterial color={color || '#333333'} />
      </ThreeBox>
      <ThreeBox args={[0.4, 0.05, 0.03]} position={[0, 0, 0.02]}>
        <meshStandardMaterial color={color || '#333333'} />
      </ThreeBox>
      <ThreeBox args={[0.4, 0.05, 0.03]} position={[0, -0.2, 0.02]}>
        <meshStandardMaterial color={color || '#333333'} />
      </ThreeBox>
    </group>
  ),

  BADGE: ({ color, ...props }) => (
    <group {...props}>
      <Octahedron args={[0.4, 0]}>
        <meshStandardMaterial color={color || '#ff6b6b'} metalness={0.7} roughness={0.3} />
      </Octahedron>
      <Torus args={[0.35, 0.08, 8, 16]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color={color || '#ffd700'} metalness={0.9} roughness={0.1} />
      </Torus>
    </group>
  ),

  // Default shape for unknown icons
  DEFAULT: ({ color, ...props }) => (
    <ThreeBox args={[0.6, 0.6, 0.6]} {...props}>
      <meshStandardMaterial color={color || '#999999'} />
    </ThreeBox>
  ),
};

// Animated 3D icon component
const AnimatedIcon: React.FunctionComponent<{ iconName: string; color?: string }> = ({ iconName, color }) => {
  const meshRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (meshRef.current) {
      // Use proper Three.js methods to set position and rotation
      meshRef.current.rotation.set(
        meshRef.current.rotation.x,
        state.clock.elapsedTime,
        meshRef.current.rotation.z
      );
      meshRef.current.position.setY(Math.sin(state.clock.elapsedTime * 2) * 0.1);
    }
  });

  // Get the icon shape or use default
  const iconKey = iconName.replace(/_\d+$/, ''); // Remove _1, _2 suffixes
  const IconShape = iconShapes[iconKey] || iconShapes.DEFAULT;

  return (
    <group ref={meshRef}>
      <IconShape color={color} />
    </group>
  );
};

interface Procedural3DIconProps {
  iconName: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  animated?: boolean;
  style?: React.CSSProperties;
}

export const Procedural3DIcon: React.FunctionComponent<Procedural3DIconProps> = memo(({
  iconName,
  size = 'medium',
  color,
  animated = true,
  style,
}) => {
  const { canRender, isQueued } = useWebGLContext();

  const sizeMap = {
    small: 80,
    medium: 120,
    large: 160,
  };

  const iconSize = sizeMap[size];

  // Fallback to 2D representation if WebGL context limit is reached
  if (!canRender) {
    const iconKey = iconName.replace(/_\d+$/, '');
    const iconData = iconShapes[iconKey] ? { emoji: '🎮', color: color || '#666' } : { emoji: '📦', color: '#999' };

    return (
      <Box
        style={{
          width: iconSize,
          height: iconSize,
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: `linear-gradient(135deg, ${iconData.color}20 0%, ${iconData.color}40 100%)`,
          border: `2px solid ${iconData.color}`,
          fontSize: iconSize * 0.5,
          opacity: isQueued ? 0.5 : 1,
          ...style,
        }}
      >
        {iconData.emoji}
      </Box>
    );
  }

  return (
    <Box
      style={{
        width: iconSize,
        height: iconSize,
        borderRadius: '12px',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(0,255,255,0.1) 0%, rgba(255,0,255,0.1) 100%)',
        ...style,
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 3], fov: 50 }}
        style={{ width: '100%', height: '100%' }}
        gl={{
          antialias: false, // Reduce memory usage
          alpha: true,
          powerPreference: 'low-power'
        }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, -5, -5]} intensity={0.5} color="#ff00ff" />

        {animated ? (
          <AnimatedIcon iconName={iconName} color={color} />
        ) : (
          (() => {
            const iconKey = iconName.replace(/_\d+$/, '');
            const IconShape = iconShapes[iconKey] || iconShapes.DEFAULT;
            return <IconShape color={color} />;
          })()
        )}
      </Canvas>
    </Box>
  );
});

export default Procedural3DIcon;