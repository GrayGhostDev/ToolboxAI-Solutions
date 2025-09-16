import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Box as ThreeBox, Sphere, Cylinder, Cone } from '@react-three/drei';
import { Box } from '@mui/material';
import * as THREE from 'three';

// Character type definitions
const characterTypes: Record<string, React.FC<any>> = {
  astronaut: ({ color, ...props }) => (
    <group {...props}>
      {/* Helmet */}
      <Sphere args={[0.35, 16, 16]} position={[0, 0.8, 0]}>
        <meshStandardMaterial
          color="#ffffff"
          transparent
          opacity={0.8}
          roughness={0.1}
          metalness={0.5}
        />
      </Sphere>
      {/* Visor */}
      <Sphere args={[0.32, 16, 16]} position={[0, 0.8, 0.05]}>
        <meshStandardMaterial
          color="#4444ff"
          transparent
          opacity={0.6}
          roughness={0}
          metalness={0.8}
        />
      </Sphere>
      {/* Body */}
      <Cylinder args={[0.25, 0.3, 0.6, 8]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#ff6b35'} />
      </Cylinder>
      {/* Arms */}
      <Cylinder args={[0.08, 0.08, 0.4, 6]} position={[0.3, 0.2, 0]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color={color || '#ff6b35'} />
      </Cylinder>
      <Cylinder args={[0.08, 0.08, 0.4, 6]} position={[-0.3, 0.2, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <meshStandardMaterial color={color || '#ff6b35'} />
      </Cylinder>
      {/* Legs */}
      <Cylinder args={[0.1, 0.08, 0.4, 6]} position={[0.15, -0.3, 0]}>
        <meshStandardMaterial color={color || '#ff6b35'} />
      </Cylinder>
      <Cylinder args={[0.1, 0.08, 0.4, 6]} position={[-0.15, -0.3, 0]}>
        <meshStandardMaterial color={color || '#ff6b35'} />
      </Cylinder>
      {/* Backpack */}
      <ThreeBox args={[0.15, 0.3, 0.1]} position={[0, 0.2, -0.2]}>
        <meshStandardMaterial color="#666666" />
      </ThreeBox>
    </group>
  ),

  robot: ({ color, ...props }) => (
    <group {...props}>
      {/* Head */}
      <ThreeBox args={[0.4, 0.3, 0.3]} position={[0, 0.8, 0]}>
        <meshStandardMaterial color={color || '#888888'} metalness={0.8} roughness={0.2} />
      </ThreeBox>
      {/* Eyes */}
      <Sphere args={[0.08, 8, 8]} position={[0.1, 0.85, 0.16]}>
        <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={0.5} />
      </Sphere>
      <Sphere args={[0.08, 8, 8]} position={[-0.1, 0.85, 0.16]}>
        <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={0.5} />
      </Sphere>
      {/* Antenna */}
      <Cylinder args={[0.02, 0.02, 0.2, 6]} position={[0, 1.05, 0]}>
        <meshStandardMaterial color="#ff0000" />
      </Cylinder>
      <Sphere args={[0.05, 8, 8]} position={[0, 1.15, 0]}>
        <meshStandardMaterial color="#ff0000" emissive="#ff0000" emissiveIntensity={0.5} />
      </Sphere>
      {/* Body */}
      <ThreeBox args={[0.35, 0.5, 0.25]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#666666'} metalness={0.7} roughness={0.3} />
      </ThreeBox>
      {/* Arms */}
      <ThreeBox args={[0.1, 0.35, 0.1]} position={[0.25, 0.2, 0]}>
        <meshStandardMaterial color={color || '#555555'} metalness={0.7} roughness={0.3} />
      </ThreeBox>
      <ThreeBox args={[0.1, 0.35, 0.1]} position={[-0.25, 0.2, 0]}>
        <meshStandardMaterial color={color || '#555555'} metalness={0.7} roughness={0.3} />
      </ThreeBox>
      {/* Legs */}
      <ThreeBox args={[0.12, 0.35, 0.12]} position={[0.12, -0.3, 0]}>
        <meshStandardMaterial color={color || '#555555'} metalness={0.7} roughness={0.3} />
      </ThreeBox>
      <ThreeBox args={[0.12, 0.35, 0.12]} position={[-0.12, -0.3, 0]}>
        <meshStandardMaterial color={color || '#555555'} metalness={0.7} roughness={0.3} />
      </ThreeBox>
    </group>
  ),

  wizard: ({ color, ...props }) => (
    <group {...props}>
      {/* Hat */}
      <Cone args={[0.25, 0.5, 6]} position={[0, 1.0, 0]}>
        <meshStandardMaterial color={color || '#4b0082'} />
      </Cone>
      {/* Head */}
      <Sphere args={[0.25, 12, 12]} position={[0, 0.6, 0]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Sphere>
      {/* Beard */}
      <Cone args={[0.15, 0.3, 6]} position={[0, 0.35, 0.1]} rotation={[Math.PI, 0, 0]}>
        <meshStandardMaterial color="#ffffff" />
      </Cone>
      {/* Body/Robe */}
      <Cone args={[0.35, 0.8, 8]} position={[0, 0, 0]}>
        <meshStandardMaterial color={color || '#4b0082'} />
      </Cone>
      {/* Staff */}
      <Cylinder args={[0.03, 0.03, 1.2, 6]} position={[0.4, 0.2, 0]} rotation={[0, 0, 0.1]}>
        <meshStandardMaterial color="#8b4513" />
      </Cylinder>
      {/* Crystal on staff */}
      <Sphere args={[0.08, 8, 8]} position={[0.42, 0.8, 0]}>
        <meshStandardMaterial
          color="#00ffff"
          emissive="#00ffff"
          emissiveIntensity={0.8}
          transparent
          opacity={0.8}
        />
      </Sphere>
    </group>
  ),

  pirate: ({ color, ...props }) => (
    <group {...props}>
      {/* Hat */}
      <ThreeBox args={[0.35, 0.1, 0.3]} position={[0, 0.9, 0]}>
        <meshStandardMaterial color="#000000" />
      </ThreeBox>
      {/* Skull on hat */}
      <Sphere args={[0.08, 8, 8]} position={[0, 0.95, 0.15]}>
        <meshStandardMaterial color="#ffffff" />
      </Sphere>
      {/* Head */}
      <Sphere args={[0.25, 12, 12]} position={[0, 0.6, 0]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Sphere>
      {/* Eye patch */}
      <ThreeBox args={[0.15, 0.08, 0.02]} position={[0.1, 0.65, 0.25]}>
        <meshStandardMaterial color="#000000" />
      </ThreeBox>
      {/* Body */}
      <Cylinder args={[0.25, 0.3, 0.5, 8]} position={[0, 0.1, 0]}>
        <meshStandardMaterial color={color || '#8b0000'} />
      </Cylinder>
      {/* Arms */}
      <Cylinder args={[0.08, 0.08, 0.35, 6]} position={[0.3, 0.15, 0]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Cylinder>
      <Cylinder args={[0.08, 0.08, 0.35, 6]} position={[-0.3, 0.15, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Cylinder>
      {/* Hook hand */}
      <Cone args={[0.05, 0.15, 4]} position={[-0.4, -0.05, 0]} rotation={[0, 0, Math.PI / 2]}>
        <meshStandardMaterial color="#c0c0c0" metalness={0.8} roughness={0.2} />
      </Cone>
      {/* Legs */}
      <Cylinder args={[0.1, 0.08, 0.4, 6]} position={[0.15, -0.35, 0]}>
        <meshStandardMaterial color="#000000" />
      </Cylinder>
      <Cylinder args={[0.08, 0.06, 0.3, 6]} position={[-0.15, -0.35, 0]}>
        <meshStandardMaterial color="#8b4513" />
      </Cylinder>
    </group>
  ),

  ninja: ({ color, ...props }) => (
    <group {...props}>
      {/* Head with mask */}
      <Sphere args={[0.25, 12, 12]} position={[0, 0.7, 0]}>
        <meshStandardMaterial color="#000000" />
      </Sphere>
      {/* Eyes */}
      <ThreeBox args={[0.3, 0.05, 0.02]} position={[0, 0.75, 0.25]}>
        <meshStandardMaterial color="#333333" />
      </ThreeBox>
      {/* Body */}
      <Cylinder args={[0.2, 0.25, 0.5, 8]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#000000'} />
      </Cylinder>
      {/* Arms */}
      <Cylinder args={[0.07, 0.07, 0.35, 6]} position={[0.25, 0.2, 0]} rotation={[0, 0, Math.PI / 8]}>
        <meshStandardMaterial color={color || '#000000'} />
      </Cylinder>
      <Cylinder args={[0.07, 0.07, 0.35, 6]} position={[-0.25, 0.2, 0]} rotation={[0, 0, -Math.PI / 8]}>
        <meshStandardMaterial color={color || '#000000'} />
      </Cylinder>
      {/* Sword on back */}
      <ThreeBox args={[0.05, 0.6, 0.02]} position={[0, 0.3, -0.15]} rotation={[0, 0, 0.3]}>
        <meshStandardMaterial color="#c0c0c0" metalness={0.9} roughness={0.1} />
      </ThreeBox>
      {/* Legs */}
      <Cylinder args={[0.09, 0.07, 0.4, 6]} position={[0.12, -0.3, 0]}>
        <meshStandardMaterial color={color || '#000000'} />
      </Cylinder>
      <Cylinder args={[0.09, 0.07, 0.4, 6]} position={[-0.12, -0.3, 0]}>
        <meshStandardMaterial color={color || '#000000'} />
      </Cylinder>
    </group>
  ),

  // Default character
  default: ({ color, ...props }) => (
    <group {...props}>
      {/* Head */}
      <Sphere args={[0.25, 12, 12]} position={[0, 0.7, 0]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Sphere>
      {/* Eyes */}
      <Sphere args={[0.04, 6, 6]} position={[0.08, 0.75, 0.22]}>
        <meshStandardMaterial color="#000000" />
      </Sphere>
      <Sphere args={[0.04, 6, 6]} position={[-0.08, 0.75, 0.22]}>
        <meshStandardMaterial color="#000000" />
      </Sphere>
      {/* Body */}
      <Cylinder args={[0.2, 0.25, 0.5, 8]} position={[0, 0.2, 0]}>
        <meshStandardMaterial color={color || '#4169e1'} />
      </Cylinder>
      {/* Arms */}
      <Cylinder args={[0.07, 0.07, 0.35, 6]} position={[0.25, 0.2, 0]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Cylinder>
      <Cylinder args={[0.07, 0.07, 0.35, 6]} position={[-0.25, 0.2, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <meshStandardMaterial color="#fdbcb4" />
      </Cylinder>
      {/* Legs */}
      <Cylinder args={[0.09, 0.07, 0.4, 6]} position={[0.12, -0.3, 0]}>
        <meshStandardMaterial color="#333333" />
      </Cylinder>
      <Cylinder args={[0.09, 0.07, 0.4, 6]} position={[-0.12, -0.3, 0]}>
        <meshStandardMaterial color="#333333" />
      </Cylinder>
    </group>
  ),
};

// Animated character component
const AnimatedCharacter: React.FC<{ type: string; color?: string }> = ({ type, color }) => {
  const meshRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (meshRef.current) {
      // Idle animation - gentle bobbing
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 2) * 0.05;
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime) * 0.1;
    }
  });

  const CharacterModel = characterTypes[type] || characterTypes.default;

  return (
    <group ref={meshRef}>
      <CharacterModel color={color} />
    </group>
  );
};

interface Procedural3DCharacterProps {
  characterType?: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  animated?: boolean;
  style?: React.CSSProperties;
}

export const Procedural3DCharacter: React.FC<Procedural3DCharacterProps> = ({
  characterType = 'default',
  size = 'medium',
  color,
  animated = true,
  style,
}) => {
  const sizeMap = {
    small: 100,
    medium: 150,
    large: 200,
  };

  const characterSize = sizeMap[size];

  // Clean up character type (remove _1, _2 suffixes)
  const cleanType = characterType.replace(/_\d+$/, '').toLowerCase();

  return (
    <Box
      sx={{
        width: characterSize,
        height: characterSize,
        borderRadius: '50%',
        overflow: 'hidden',
        background: 'radial-gradient(circle, rgba(0,255,255,0.1) 0%, rgba(255,0,255,0.1) 100%)',
        border: '3px solid rgba(255,255,255,0.2)',
        ...style,
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 2.5], fov: 50 }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, 5, -5]} intensity={0.5} color="#00ffff" />
        <pointLight position={[5, -5, 5]} intensity={0.3} color="#ff00ff" />

        {animated ? (
          <AnimatedCharacter type={cleanType} color={color} />
        ) : (
          (() => {
            const CharacterModel = characterTypes[cleanType] || characterTypes.default;
            return <CharacterModel color={color} />;
          })()
        )}
      </Canvas>
    </Box>
  );
};

export default Procedural3DCharacter;