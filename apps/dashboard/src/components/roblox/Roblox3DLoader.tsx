/**
 * Roblox3DLoader Component
 *
 * A fun, animated 3D loading spinner for the dashboard
 */

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Text, RoundedBox, Float } from '@react-three/drei';
import { Box, Text as MantineText } from '@mantine/core';
import * as THREE from 'three';
import { robloxColors } from '../../theme/robloxTheme';

interface SpinningCubeProps {
  position: [number, number, number];
  color: string;
  delay: number;
}

const SpinningCube: React.FunctionComponent<SpinningCubeProps> = ({ position, color, delay }) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      const time = state.clock.elapsedTime;
      meshRef.current.rotation.x = time * 2 + delay;
      meshRef.current.rotation.y = time * 1.5 + delay;
      meshRef.current.position.y = position[1] + Math.sin(time * 3 + delay) * 0.3;

      // Pulse effect
      const scale = 1 + Math.sin(time * 4 + delay) * 0.1;
      meshRef.current.scale.set(scale, scale, scale);
    }
  });

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
      <mesh ref={meshRef} position={position}>
        <RoundedBox args={[0.4, 0.4, 0.4]} radius={0.05} smoothness={4}>
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.5}
            metalness={0.8}
            roughness={0.2}
          />
        </RoundedBox>
      </mesh>
    </Float>
  );
};

interface LoadingRocketProps {
  scale?: number;
}

const LoadingRocket: React.FunctionComponent<LoadingRocketProps> = ({ scale = 1 }) => {
  const rocketRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (rocketRef.current) {
      const time = state.clock.elapsedTime;
      // Orbit motion
      rocketRef.current.position.x = Math.cos(time * 2) * 1.5;
      rocketRef.current.position.z = Math.sin(time * 2) * 1.5;
      rocketRef.current.position.y = Math.sin(time * 3) * 0.5;

      // Point rocket in direction of motion
      rocketRef.current.rotation.y = -time * 2 + Math.PI / 2;
      rocketRef.current.rotation.z = Math.sin(time * 4) * 0.1;
    }
  });

  return (
    <group ref={rocketRef} scale={scale}>
      {/* Rocket Body */}
      <mesh>
        <coneGeometry args={[0.2, 0.6, 8]} />
        <meshStandardMaterial
          color={robloxColors.neon.electricBlue}
          emissive={robloxColors.neon.electricBlue}
          emissiveIntensity={0.3}
          metalness={0.9}
          roughness={0.1}
        />
      </mesh>

      {/* Rocket Fins */}
      {[0, 120, 240].map((angle) => (
        <mesh
          key={angle}
          position={[
            Math.cos((angle * Math.PI) / 180) * 0.15,
            -0.2,
            Math.sin((angle * Math.PI) / 180) * 0.15
          ]}
          rotation={[0, (angle * Math.PI) / 180, Math.PI / 6]}
        >
          <planeGeometry args={[0.1, 0.2]} />
          <meshStandardMaterial
            color={robloxColors.neon.hotPink}
            emissive={robloxColors.neon.hotPink}
            emissiveIntensity={0.5}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}

      {/* Exhaust Fire */}
      <mesh position={[0, -0.35, 0]}>
        <coneGeometry args={[0.15, 0.3, 8]} />
        <meshStandardMaterial
          color={robloxColors.neon.plasmaYellow}
          emissive={robloxColors.neon.plasmaYellow}
          emissiveIntensity={1}
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  );
};

interface Roblox3DLoaderProps {
  message?: string;
  variant?: 'cubes' | 'rocket' | 'both';
  size?: 'small' | 'medium' | 'large';
  showBackground?: boolean;
}

export const Roblox3DLoader: React.FunctionComponent<Roblox3DLoaderProps> = ({
  message = 'Loading...',
  variant = 'both',
  size = 'medium',
  showBackground = true
}) => {
  const sizeMap = {
    small: { width: 150, height: 150 },
    medium: { width: 250, height: 250 },
    large: { width: 350, height: 350 }
  };

  const dimensions = sizeMap[size];

  const cubeColors = [
    robloxColors.neon.electricBlue,
    robloxColors.neon.toxicGreen,
    robloxColors.neon.hotPink,
    robloxColors.neon.plasmaYellow,
    robloxColors.neon.deepPurple
  ];

  return (
    <Box
      style={{
        width: dimensions.width,
        height: dimensions.height,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 12,
        background: showBackground
          ? `linear-gradient(135deg, rgba(15, 15, 46, 0.9), rgba(46, 11, 46, 0.9))`
          : 'transparent',
        backdropFilter: showBackground ? 'blur(10px)' : 'none',
        border: showBackground ? `2px solid ${robloxColors.neon.electricBlue}20` : 'none',
        boxShadow: showBackground
          ? `0 0 30px ${robloxColors.neon.electricBlue}40`
          : 'none'
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color={robloxColors.neon.hotPink} />

        {(variant === 'cubes' || variant === 'both') && (
          <>
            {cubeColors.map((color, index) => {
              const angle = (index / cubeColors.length) * Math.PI * 2;
              const radius = 1.2;
              return (
                <SpinningCube
                  key={index}
                  position={[
                    Math.cos(angle) * radius,
                    0,
                    Math.sin(angle) * radius
                  ]}
                  color={color}
                  delay={index * 0.2}
                />
              );
            })}
          </>
        )}

        {(variant === 'rocket' || variant === 'both') && (
          <LoadingRocket scale={variant === 'both' ? 0.8 : 1.2} />
        )}

        {message && (
          <Text
            position={[0, -2, 0]}
            fontSize={0.3}
            color={robloxColors.neon.electricBlue}
            anchorX="center"
            anchorY="middle"
            font="/fonts/bold.woff"
          >
            {message}
          </Text>
        )}
      </Canvas>

      {message && (
        <MantineText
          size="sm"
          style={{
            position: 'absolute',
            bottom: 20,
            color: robloxColors.neon.electricBlue,
            fontWeight: 600,
            textShadow: `0 0 10px ${robloxColors.neon.electricBlue}80`,
            animation: 'pulse 1.5s ease-in-out infinite',
          }}
        >
          {message}
        </MantineText>
      )}

      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
          }
        `}
      </style>
    </Box>
  );
};

export default Roblox3DLoader;