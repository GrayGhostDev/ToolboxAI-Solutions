/**
 * ParticleEffects Component
 *
 * Animated particle effects for enhanced visual experience
 */

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import { Box } from '@mui/material';
import * as THREE from 'three';
import { robloxColors } from '../../theme/robloxTheme';

interface ParticlesProps {
  count?: number;
  color?: string;
  size?: number;
  spread?: number;
  speed?: number;
}

const Particles: React.FC<ParticlesProps> = ({
  count = 500,
  color = robloxColors.neon.electricBlue,
  size = 0.05,
  spread = 10,
  speed = 0.5
}) => {
  const pointsRef = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const velocities = new Float32Array(count * 3);

    const color3 = new THREE.Color(color);

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;

      // Random position
      positions[i3] = (Math.random() - 0.5) * spread;
      positions[i3 + 1] = (Math.random() - 0.5) * spread;
      positions[i3 + 2] = (Math.random() - 0.5) * spread;

      // Random velocity
      velocities[i3] = (Math.random() - 0.5) * speed;
      velocities[i3 + 1] = (Math.random() - 0.5) * speed;
      velocities[i3 + 2] = (Math.random() - 0.5) * speed;

      // Color with slight variation
      const colorVariation = 0.2;
      colors[i3] = color3.r + (Math.random() - 0.5) * colorVariation;
      colors[i3 + 1] = color3.g + (Math.random() - 0.5) * colorVariation;
      colors[i3 + 2] = color3.b + (Math.random() - 0.5) * colorVariation;
    }

    return { positions, colors, velocities };
  }, [count, color, spread, speed]);

  useFrame((state) => {
    if (pointsRef.current) {
      const positions = pointsRef.current.geometry.attributes.position.array as Float32Array;
      const velocities = particles.velocities;
      const time = state.clock.elapsedTime;

      for (let i = 0; i < count; i++) {
        const i3 = i * 3;

        // Update positions
        positions[i3] += velocities[i3] * 0.01;
        positions[i3 + 1] += velocities[i3 + 1] * 0.01 + Math.sin(time + i) * 0.001;
        positions[i3 + 2] += velocities[i3 + 2] * 0.01;

        // Wrap around edges
        if (Math.abs(positions[i3]) > spread / 2) {
          positions[i3] = -positions[i3];
        }
        if (Math.abs(positions[i3 + 1]) > spread / 2) {
          positions[i3 + 1] = -positions[i3 + 1];
        }
        if (Math.abs(positions[i3 + 2]) > spread / 2) {
          positions[i3 + 2] = -positions[i3 + 2];
        }
      }

      pointsRef.current.geometry.attributes.position.needsUpdate = true;

      // Rotate the entire particle system
      pointsRef.current.rotation.y += 0.001;
      pointsRef.current.rotation.x += 0.0005;
    }
  });

  return (
    <Points ref={pointsRef} positions={particles.positions} colors={particles.colors}>
      <PointMaterial
        size={size}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </Points>
  );
};

interface MagicOrbsProps {
  count?: number;
  colors?: string[];
}

const MagicOrbs: React.FC<MagicOrbsProps> = ({
  count = 10,
  colors = [
    robloxColors.neon.electricBlue,
    robloxColors.neon.hotPink,
    robloxColors.neon.plasmaYellow,
    robloxColors.neon.toxicGreen,
    robloxColors.neon.deepPurple
  ]
}) => {
  const orbsRef = useRef<THREE.Group>(null);
  const orbData = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      position: new THREE.Vector3(
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8
      ),
      velocity: new THREE.Vector3(
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02
      ),
      color: colors[Math.floor(Math.random() * colors.length)],
      scale: 0.1 + Math.random() * 0.2,
      phase: Math.random() * Math.PI * 2
    }));
  }, [count, colors]);

  useFrame((state) => {
    if (orbsRef.current) {
      const time = state.clock.elapsedTime;

      orbsRef.current.children.forEach((orb, i) => {
        const data = orbData[i];

        // Update position with velocity
        orb.position.x += data.velocity.x;
        orb.position.y += data.velocity.y + Math.sin(time * 2 + data.phase) * 0.01;
        orb.position.z += data.velocity.z;

        // Wrap around edges
        if (Math.abs(orb.position.x) > 4) orb.position.x = -orb.position.x;
        if (Math.abs(orb.position.y) > 4) orb.position.y = -orb.position.y;
        if (Math.abs(orb.position.z) > 4) orb.position.z = -orb.position.z;

        // Pulse effect
        const scale = data.scale * (1 + Math.sin(time * 3 + data.phase) * 0.2);
        orb.scale.set(scale, scale, scale);

        // Rotate
        orb.rotation.x += 0.01;
        orb.rotation.y += 0.02;
      });
    }
  });

  return (
    <group ref={orbsRef}>
      {orbData.map((data, i) => (
        <mesh key={i} position={data.position}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshStandardMaterial
            color={data.color}
            emissive={data.color}
            emissiveIntensity={0.8}
            transparent
            opacity={0.6}
            roughness={0}
            metalness={0.5}
          />
        </mesh>
      ))}
    </group>
  );
};

interface ParticleEffectsProps {
  variant?: 'particles' | 'orbs' | 'mixed';
  intensity?: 'low' | 'medium' | 'high';
  position?: 'fixed' | 'absolute';
  zIndex?: number;
}

export const ParticleEffects: React.FC<ParticleEffectsProps> = ({
  variant = 'mixed',
  intensity = 'medium',
  position = 'fixed',
  zIndex = -1
}) => {
  const particleCount = {
    low: 200,
    medium: 500,
    high: 1000
  }[intensity];

  const orbCount = {
    low: 5,
    medium: 10,
    high: 20
  }[intensity];

  return (
    <Box
      sx={{
        position,
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex,
        opacity: 0.7
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 75 }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />

        {(variant === 'particles' || variant === 'mixed') && (
          <>
            <Particles
              count={particleCount}
              color={robloxColors.neon.electricBlue}
              size={0.03}
              spread={10}
              speed={0.3}
            />
            <Particles
              count={particleCount / 2}
              color={robloxColors.neon.hotPink}
              size={0.02}
              spread={8}
              speed={0.5}
            />
          </>
        )}

        {(variant === 'orbs' || variant === 'mixed') && (
          <MagicOrbs count={orbCount} />
        )}
      </Canvas>
    </Box>
  );
};

export default ParticleEffects;