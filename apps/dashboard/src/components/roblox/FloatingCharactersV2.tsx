import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { useThree } from '../three/useThree';
import { Canvas2D } from '../three/fallbacks/Canvas2D';

interface CharacterData {
  type: 'astronaut' | 'robot' | 'wizard' | 'pirate' | 'ninja';
  position: [number, number, number];
}

interface FloatingCharactersV2Props {
  characters?: CharacterData[];
  showStars?: boolean;
  showClouds?: boolean;
}

export const FloatingCharactersV2: React.FunctionComponent<FloatingCharactersV2Props> = ({
  characters = [
    { type: 'astronaut', position: [-4, 2, -3] },
    { type: 'robot', position: [4, 1, -2] },
    { type: 'wizard', position: [0, 3, -4] },
    { type: 'pirate', position: [-3, -1, -2] },
    { type: 'ninja', position: [3, 0, -3] }
  ],
  showStars = true,
  showClouds = true
}) => {
  const { scene, isWebGLAvailable, performanceLevel, addObject, removeObject } = useThree();
  const charactersRef = useRef<THREE.Group[]>([]);
  const starsRef = useRef<THREE.Points | null>(null);
  const cloudsRef = useRef<THREE.Group[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Create simple procedural character
  const createCharacter = (type: string, position: [number, number, number]) => {
    const group = new THREE.Group();

    // Character colors based on type
    const colors: Record<string, number> = {
      astronaut: 0xffffff,
      robot: 0x888888,
      wizard: 0x6b5b95,
      pirate: 0x8b4513,
      ninja: 0x000000
    };

    // Body
    const bodyGeometry = new THREE.BoxGeometry(0.8, 1.2, 0.6);
    const bodyMaterial = new THREE.MeshPhongMaterial({
      color: colors[type] || 0xffffff,
      emissive: colors[type] || 0xffffff,
      emissiveIntensity: 0.1
    });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    group.add(body);

    // Head
    const headGeometry = new THREE.SphereGeometry(0.4, 8, 6);
    const headMaterial = new THREE.MeshPhongMaterial({
      color: 0xffdbac,
      emissive: 0xffdbac,
      emissiveIntensity: 0.05
    });
    const head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.y = 1;
    group.add(head);

    // Arms
    const armGeometry = new THREE.BoxGeometry(0.2, 0.8, 0.2);
    const armMaterial = new THREE.MeshPhongMaterial({ color: colors[type] || 0xffffff });

    const leftArm = new THREE.Mesh(armGeometry, armMaterial);
    leftArm.position.set(-0.6, 0.2, 0);
    leftArm.castShadow = performanceLevel !== 'low';
    leftArm.receiveShadow = performanceLevel !== 'low';
    group.add(leftArm);

    const rightArm = new THREE.Mesh(armGeometry, armMaterial);
    rightArm.position.set(0.6, 0.2, 0);
    rightArm.castShadow = performanceLevel !== 'low';
    rightArm.receiveShadow = performanceLevel !== 'low';
    group.add(rightArm);

    // Legs
    const legGeometry = new THREE.BoxGeometry(0.3, 0.8, 0.3);
    const legMaterial = new THREE.MeshPhongMaterial({ color: 0x333333 });

    const leftLeg = new THREE.Mesh(legGeometry, legMaterial);
    leftLeg.position.set(-0.25, -0.8, 0);
    group.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeometry, legMaterial);
    rightLeg.position.set(0.25, -0.8, 0);
    group.add(rightLeg);

    // Set position using setter to avoid read-only property errors
    group.position.set(...position);

    // Add floating animation data
    group.userData = {
      floatSpeed: Math.random() * 0.5 + 0.5,
      floatOffset: Math.random() * Math.PI * 2,
      rotationSpeed: Math.random() * 0.02 + 0.01,
      autoRotate: true
    };

    // Enable shadows if performance allows
    if (performanceLevel !== 'low') {
      group.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.castShadow = true;
          child.receiveShadow = true;
        }
      });
    }

    return group;
  };

  // Create stars
  const createStars = () => {
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.02,
      transparent: true,
      opacity: 0.8
    });

    const starsVertices = [];
    for (let i = 0; i < 1000; i++) {
      const x = (Math.random() - 0.5) * 100;
      const y = (Math.random() - 0.5) * 100;
      const z = (Math.random() - 0.5) * 100;
      starsVertices.push(x, y, z);
    }

    starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
    return new THREE.Points(starsGeometry, starsMaterial);
  };

  // Create clouds
  const createCloud = (x: number, y: number, z: number) => {
    const cloud = new THREE.Group();

    const cloudMaterial = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.6,
      depthWrite: false
    });

    // Create cloud from multiple spheres
    for (let i = 0; i < 5; i++) {
      const radius = Math.random() * 0.5 + 0.3;
      const cloudPart = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 6, 4),
        cloudMaterial
      );

      cloudPart.position.set(
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 0.5,
        (Math.random() - 0.5) * 1
      );

      cloud.add(cloudPart);
    }

    cloud.position.set(x, y, z);
    cloud.userData = {
      driftSpeed: Math.random() * 0.001 + 0.001
    };

    return cloud;
  };

  // Initialize scene objects
  useEffect(() => {
    if (!scene || !isWebGLAvailable) return;

    // Create and add characters
    characters.forEach((char) => {
      const character = createCharacter(char.type, char.position);
      charactersRef.current.push(character);
      addObject(character);
    });

    // Add stars
    if (showStars) {
      const stars = createStars();
      starsRef.current = stars;
      addObject(stars);
    }

    // Add clouds
    if (showClouds && performanceLevel !== 'low') {
      for (let i = 0; i < 3; i++) {
        const cloud = createCloud(
          (Math.random() - 0.5) * 10,
          Math.random() * 5 + 5,
          (Math.random() - 0.5) * 10
        );
        cloudsRef.current.push(cloud);
        addObject(cloud);
      }
    }

    setIsLoaded(true);

    // Animation loop
    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);

      // Animate characters floating
      charactersRef.current.forEach((character) => {
        const time = Date.now() * 0.001;
        const { floatSpeed, floatOffset, rotationSpeed } = character.userData;

        // Floating motion
        character.position.y += Math.sin(time * floatSpeed + floatOffset) * 0.002;

        // Rotation
        character.rotation.y += rotationSpeed;

        // Slight tilt
        character.rotation.z = Math.sin(time * floatSpeed * 0.5 + floatOffset) * 0.1;
      });

      // Rotate stars
      if (starsRef.current) {
        starsRef.current.rotation.y += 0.0001;
      }

      // Drift clouds
      cloudsRef.current.forEach((cloud) => {
        cloud.position.x += cloud.userData.driftSpeed;
        if (cloud.position.x > 15) {
          cloud.position.x = -15;
        }
      });
    };

    animate();

    // Track disposed state to prevent double-dispose in React StrictMode
    let isDisposed = false;

    // Cleanup
    return () => {
      if (isDisposed) return; // Prevent double disposal
      isDisposed = true;

      cancelAnimationFrame(animationId);

      // Remove all objects safely
      charactersRef.current.forEach(char => {
        if (char && char.parent) {
          removeObject(char);
        }
      });
      if (starsRef.current && starsRef.current.parent) {
        removeObject(starsRef.current);
      }
      cloudsRef.current.forEach(cloud => {
        if (cloud && cloud.parent) {
          removeObject(cloud);
        }
      });

      // Clear references
      charactersRef.current = [];
      starsRef.current = null;
      cloudsRef.current = [];
    };
  }, [scene, isWebGLAvailable, characters, showStars, showClouds, performanceLevel, addObject, removeObject]);

  // Fallback to 2D if WebGL not available
  if (!isWebGLAvailable) {
    return <Canvas2D particleCount={30} animate={true} />;
  }

  return null; // The actual rendering is handled by ThreeProvider
};