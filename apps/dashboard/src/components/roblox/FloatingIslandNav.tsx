import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Box, Card, Text, useMantineTheme } from '@mantine/core';
import { OrbitControls, Text as ThreeText, Float, Cloud, Stars, Sparkles } from '@react-three/drei';
import * as THREE from 'three';
import { useNavigate } from 'react-router-dom';
import ThreeJSErrorBoundary from '../common/ThreeJSErrorBoundary';

// Floating animation keyframes
const floatAnimationKeyframes = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
  }
`;

// 3D Island Component
function Island({ position, color, label, onClick, isHovered, scale = 1 }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      // Use proper Three.js methods instead of direct assignment
      meshRef.current.rotation.y += 0.002;
      meshRef.current.position.setY(Math.sin(state.clock.elapsedTime + position[0]) * 0.1);
    }
  });

  return (
    <Float
      speed={2}
      rotationIntensity={0.2}
      floatIntensity={0.5}
      floatingRange={[-0.1, 0.1]}
    >
      <group
        position={position}
        scale={hovered ? scale * 1.2 : scale}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        {/* Island base */}
        <mesh ref={meshRef} castShadow receiveShadow>
          <cylinderGeometry args={[1.5, 2, 0.5, 8]} />
          <meshStandardMaterial color={color} roughness={0.8} />
        </mesh>

        {/* Grass on top */}
        <mesh position={[0, 0.3, 0]} castShadow>
          <cylinderGeometry args={[1.4, 1.4, 0.2, 8]} />
          <meshStandardMaterial color="#32CD32" roughness={0.9} />
        </mesh>

        {/* Trees */}
        <mesh position={[0.5, 0.8, 0.3]} castShadow>
          <coneGeometry args={[0.3, 0.8, 6]} />
          <meshStandardMaterial color="#228B22" />
        </mesh>
        <mesh position={[0.5, 0.4, 0.3]}>
          <cylinderGeometry args={[0.1, 0.1, 0.3]} />
          <meshStandardMaterial color="#8B4513" />
        </mesh>

        {/* House/Building */}
        <mesh position={[-0.3, 0.6, -0.2]} castShadow>
          <boxGeometry args={[0.5, 0.5, 0.5]} />
          <meshStandardMaterial color={hovered ? '#FFD700' : '#FF6B6B'} />
        </mesh>
        <mesh position={[-0.3, 0.95, -0.2]} castShadow>
          <coneGeometry args={[0.4, 0.3, 4]} />
          <meshStandardMaterial color="#8B4513" />
        </mesh>

        {/* Label */}
        <ThreeText
          position={[0, -1, 0]}
          fontSize={0.3}
          color={hovered ? '#FFD700' : '#FFFFFF'}
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.02}
          outlineColor="#000000"
        >
          {label}
        </ThreeText>

        {/* Sparkles when hovered */}
        {hovered && (
          <Sparkles
            count={30}
            scale={3}
            size={2}
            speed={0.4}
            color="#FFD700"
          />
        )}
      </group>
    </Float>
  );
}

// Bridge Component
function Bridge({ start, end, visible }) {
  const bridgeRef = useRef();

  // Calculate bridge position and rotation
  const startVec = new THREE.Vector3(...start);
  const endVec = new THREE.Vector3(...end);
  const midpoint = startVec.clone().add(endVec).multiplyScalar(0.5);
  const distance = startVec.distanceTo(endVec);

  useFrame((state) => {
    if (bridgeRef.current) {
      bridgeRef.current.material.opacity = visible ? 1 : 0;
    }
  });

  return (
    <mesh
      ref={bridgeRef}
      position={[midpoint.x, midpoint.y - 0.5, midpoint.z]}
      rotation={[0, Math.atan2(end[2] - start[2], end[0] - start[0]), 0]}
    >
      <boxGeometry args={[distance, 0.1, 0.5]} />
      <meshStandardMaterial
        color="#8B4513"
        transparent
        opacity={visible ? 1 : 0}
      />
    </mesh>
  );
}

// Character that moves between islands
function FlyingCharacter({ targetPosition }) {
  const meshRef = useRef();
  const [currentPos, setCurrentPos] = useState([0, 2, 0]);

  useFrame((state) => {
    if (meshRef.current && targetPosition) {
      // Smooth movement to target - use proper Three.js methods
      meshRef.current.position.setX(
        meshRef.current.position.x + (targetPosition[0] - meshRef.current.position.x) * 0.05
      );
      meshRef.current.position.setY(
        2 + Math.sin(state.clock.elapsedTime * 2) * 0.3
      );
      meshRef.current.position.setZ(
        meshRef.current.position.z + (targetPosition[2] - meshRef.current.position.z) * 0.05
      );

      // Rotation
      meshRef.current.rotation.setY(state.clock.elapsedTime);
    }
  });

  return (
    <group ref={meshRef} position={currentPos}>
      {/* Body */}
      <mesh castShadow>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#FFD700" emissive="#FFD700" emissiveIntensity={0.2} />
      </mesh>

      {/* Wings */}
      <mesh position={[0.3, 0, 0]} rotation={[0, 0, Math.PI / 6]}>
        <planeGeometry args={[0.3, 0.2]} />
        <meshStandardMaterial color="#FFFFFF" side={THREE.DoubleSide} transparent opacity={0.8} />
      </mesh>
      <mesh position={[-0.3, 0, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <planeGeometry args={[0.3, 0.2]} />
        <meshStandardMaterial color="#FFFFFF" side={THREE.DoubleSide} transparent opacity={0.8} />
      </mesh>

      <Sparkles
        count={20}
        scale={1}
        size={1}
        speed={0.2}
        color="#FFD700"
      />
    </group>
  );
}

interface FloatingIslandNavProps {
  onNavigate?: (route: string) => void;
}

export const FloatingIslandNav: React.FunctionComponent<FloatingIslandNavProps> = ({ onNavigate }) => {
  const theme = useMantineTheme();
  const navigate = useNavigate();
  const [hoveredIsland, setHoveredIsland] = useState<number | null>(null);
  const [selectedIsland, setSelectedIsland] = useState<number>(0);

  const islands = [
    { position: [-3, 0, 0], color: '#FF6B6B', label: 'Dashboard', route: '/dashboard' },
    { position: [0, 0.5, -2], color: '#4ECDC4', label: 'Classes', route: '/classes' },
    { position: [3, -0.5, 0], color: '#95E77E', label: 'Lessons', route: '/lessons' },
    { position: [0, 0, 2], color: '#FFD93D', label: 'Games', route: '/games' },
    { position: [-2, -0.3, 2], color: '#A8E6CF', label: 'Progress', route: '/progress' },
    { position: [2, 0.3, 2], color: '#FFB6C1', label: 'Rewards', route: '/rewards' },
  ];

  const handleIslandClick = (index: number, route: string) => {
    setSelectedIsland(index);
    setTimeout(() => {
      if (onNavigate) {
        onNavigate(route);
      } else {
        navigate(route);
      }
    }, 500);
  };

  // Container styles using modern Mantine v8 patterns
  const containerStyles = {
    background: 'linear-gradient(180deg, #87CEEB 0%, #FFB6C1 50%, #FFD700 100%)',
    borderRadius: theme.radius.xl,
    padding: theme.spacing.md,
    position: 'relative' as const,
    overflow: 'hidden' as const,
    height: '400px',
  };

  return (
    <>
      <style>{floatAnimationKeyframes}</style>
      <Card style={containerStyles} shadow="none">
        {/* Radial gradient overlay using Box */}
        <Box
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.3) 0%, transparent 50%)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />

        <Box style={{ position: 'absolute', top: 16, left: 16, zIndex: 1 }}>
          <Text
            size="xl"
            fw={800}
            style={{
              color: '#FFFFFF',
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
              animation: 'float 3s ease-in-out infinite',
            }}
          >
            Choose Your Adventure! 🏝️
          </Text>
        </Box>

        {/* 3D Scene with Error Boundary */}
        <ThreeJSErrorBoundary>
          <Canvas
            camera={{ position: [0, 5, 10], fov: 60 }}
            shadows
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
          >
            <ambientLight intensity={0.6} />
            <directionalLight
              position={[10, 10, 5]}
              intensity={1}
              castShadow
              shadow-mapSize-width={1024}
              shadow-mapSize-height={1024}
            />
            <fog attach="fog" args={['#FFB6C1', 5, 30]} />

            {/* Sky gradient using Stars component */}
            <Stars
              radius={100}
              depth={50}
              count={5000}
              factor={4}
              saturation={0}
              fade
            />

            {/* Floating islands */}
            {islands.map((island, index) => (
              <Island
                key={index}
                position={island.position}
                color={island.color}
                label={island.label}
                onClick={() => handleIslandClick(index, island.route)}
                isHovered={hoveredIsland === index}
                scale={selectedIsland === index ? 1.3 : 1}
              />
            ))}

            {/* Bridges between islands */}
            {islands.map((island, index) => {
              if (index === 0) return null;
              return (
                <Bridge
                  key={`bridge-${index}`}
                  start={islands[index - 1].position}
                  end={island.position}
                  visible={index <= selectedIsland}
                />
              );
            })}

            {/* Flying character */}
            <FlyingCharacter targetPosition={islands[selectedIsland]?.position} />

            {/* Clouds */}
            <Cloud
              opacity={0.3}
              speed={0.2}
              width={10}
              depth={1.5}
              segments={20}
              position={[5, 6, -10]}
            />
            <Cloud
              opacity={0.3}
              speed={0.2}
              width={10}
              depth={1.5}
              segments={20}
              position={[-5, 8, -15]}
            />

            {/* Camera controls */}
            <OrbitControls
              enablePan={false}
              enableZoom={true}
              minDistance={5}
              maxDistance={20}
              maxPolarAngle={Math.PI / 2}
            />
          </Canvas>
        </ThreeJSErrorBoundary>

        {/* Particle effects overlay */}
        <Box
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            pointerEvents: 'none',
            background: 'radial-gradient(circle at 50% 50%, transparent 0%, rgba(255,255,255,0.1) 100%)',
          }}
        />
      </Card>
    </>
  );
};

export default FloatingIslandNav;