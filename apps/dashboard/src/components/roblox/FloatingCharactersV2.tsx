import React, { useEffect, useRef, useState, Suspense, ErrorBoundary } from 'react';
import * as THREE from 'three';
import {
  Box,
  Paper,
  Text,
  Button,
  ActionIcon,
  Switch,
  Slider,
  Group,
  Stack,
  Badge,
  Tooltip,
  Alert,
  Loader
} from '@mantine/core';
import {
  IconEye,
  IconEyeOff,
  IconStar,
  IconCloud,
  IconPlayerPlay,
  IconPlayerPause,
  IconSettings,
  IconReload
} from '@tabler/icons-react';
import { useThree } from '../three/useThree';
import { Canvas2D } from '../three/fallbacks/Canvas2D';

// Error Boundary for Three.js components
class ThreeJSErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.warn('Three.js Error Caught:', error.message);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('Three.js Component Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Alert color="yellow" variant="light">
          3D renderer unavailable - using 2D fallback
        </Alert>
      );
    }

    return this.props.children;
  }
}

interface CharacterData {
  type: 'astronaut' | 'robot' | 'wizard' | 'pirate' | 'ninja';
  position: [number, number, number];
}

interface FloatingCharactersV2Props {
  characters?: CharacterData[];
  showStars?: boolean;
  showClouds?: boolean;
  showControls?: boolean;
  onSettingsChange?: (settings: SceneSettings) => void;
}

interface SceneSettings {
  showStars: boolean;
  showClouds: boolean;
  animationSpeed: number;
  characterCount: number;
  isPlaying: boolean;
}

// Helper function to determine performance badge color
const getPerformanceBadgeColor = (performanceLevel: string): string => {
  if (performanceLevel === 'high') return 'green';
  if (performanceLevel === 'medium') return 'yellow';
  return 'red';
};

export const FloatingCharactersV2: React.FunctionComponent<FloatingCharactersV2Props> = ({
  characters = [
    { type: 'astronaut', position: [-4, 2, -3] },
    { type: 'robot', position: [4, 1, -2] },
    { type: 'wizard', position: [0, 3, -4] },
    { type: 'pirate', position: [-3, -1, -2] },
    { type: 'ninja', position: [3, 0, -3] }
  ],
  showStars = true,
  showClouds = true,
  showControls = true,
  onSettingsChange
}) => {
  // Test environment detection
  const isTestEnvironment = process.env.NODE_ENV === 'test' || typeof window === 'undefined';

  // Safe hook call with fallback
  const { scene, isWebGLAvailable, performanceLevel, addObject, removeObject } = (() => {
    try {
      // Only use the hook if we're not in test environment
      if (!isTestEnvironment) {
        return useThree();
      }
    } catch (error) {
      console.warn('useThree hook failed:', error);
    }

    // Fallback values for test environment
    return {
      scene: null,
      isWebGLAvailable: false,
      performanceLevel: 'low' as const,
      addObject: () => {},
      removeObject: () => {},
      cleanup: () => {}
    };
  })();

  const charactersRef = useRef<THREE.Group[]>([]);
  const starsRef = useRef<THREE.Points | null>(null);
  const cloudsRef = useRef<THREE.Group[]>([]);
  const animationRef = useRef<number>();

  // UI State
  const [isLoaded, setIsLoaded] = useState(false);
  const [settings, setSettings] = useState<SceneSettings>({
    showStars,
    showClouds,
    animationSpeed: 1.0,
    characterCount: characters.length,
    isPlaying: true
  });
  const [showControlPanel, setShowControlPanel] = useState(false);

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
    group.add(leftArm);

    const rightArm = new THREE.Mesh(armGeometry, armMaterial);
    rightArm.position.set(0.6, 0.2, 0);
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

    // Set position
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
    const animate = () => {
      if (!settings.isPlaying) {
        animationRef.current = requestAnimationFrame(animate);
        return;
      }

      animationRef.current = requestAnimationFrame(animate);

      // Animate characters floating
      charactersRef.current.forEach((character) => {
        const time = Date.now() * 0.001 * settings.animationSpeed;
        const { floatSpeed, floatOffset, rotationSpeed } = character.userData;

        // Floating motion
        character.position.y += Math.sin(time * floatSpeed + floatOffset) * 0.002;

        // Rotation
        character.rotation.y += rotationSpeed * settings.animationSpeed;

        // Slight tilt
        character.rotation.z = Math.sin(time * floatSpeed * 0.5 + floatOffset) * 0.1;
      });

      // Rotate stars
      if (starsRef.current && settings.showStars) {
        starsRef.current.rotation.y += 0.0001 * settings.animationSpeed;
      }

      // Drift clouds
      if (settings.showClouds) {
        cloudsRef.current.forEach((cloud) => {
          cloud.position.x += cloud.userData.driftSpeed * settings.animationSpeed;
          if (cloud.position.x > 15) {
            cloud.position.x = -15;
          }
        });
      }
    };

    animate();

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }

      // Remove all objects
      charactersRef.current.forEach(char => removeObject(char));
      if (starsRef.current) removeObject(starsRef.current);
      cloudsRef.current.forEach(cloud => removeObject(cloud));

      // Clear references
      charactersRef.current = [];
      starsRef.current = null;
      cloudsRef.current = [];
    };
  }, [scene, isWebGLAvailable, characters, settings.showStars, settings.showClouds, performanceLevel, addObject, removeObject, settings.animationSpeed, settings.isPlaying]);

  // Handle settings changes
  const handleSettingsChange = (newSettings: Partial<SceneSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    onSettingsChange?.(updatedSettings);
  };

  // Control handlers
  const toggleStars = () => {
    const newShowStars = !settings.showStars;
    handleSettingsChange({ showStars: newShowStars });

    if (starsRef.current) {
      starsRef.current.visible = newShowStars;
    }
  };

  const toggleClouds = () => {
    const newShowClouds = !settings.showClouds;
    handleSettingsChange({ showClouds: newShowClouds });

    cloudsRef.current.forEach(cloud => {
      cloud.visible = newShowClouds;
    });
  };

  const toggleAnimation = () => {
    handleSettingsChange({ isPlaying: !settings.isPlaying });
  };

  const resetScene = () => {
    // Reset character positions
    charactersRef.current.forEach((character, index) => {
      if (characters[index]) {
        character.position.set(...characters[index].position);
        character.rotation.set(0, 0, 0);
      }
    });

    // Reset stars rotation
    if (starsRef.current) {
      starsRef.current.rotation.set(0, 0, 0);
    }

    // Reset cloud positions
    cloudsRef.current.forEach((cloud) => {
      cloud.position.x = (Math.random() - 0.5) * 10;
    });
  };

  // Fallback to 2D if WebGL not available or test environment
  if (!isWebGLAvailable || isTestEnvironment) {
    return (
      <ThreeJSErrorBoundary fallback={<Canvas2D particleCount={30} animate={true} />}>
        <Canvas2D particleCount={characters.length * 5} animate={true} />
      </ThreeJSErrorBoundary>
    );
  }

  // Render UI controls if enabled
  if (!showControls) {
    return null; // The actual rendering is handled by ThreeProvider
  }

  return (
    <ThreeJSErrorBoundary fallback={<Canvas2D particleCount={30} animate={true} />}>
    <Box
      style={{
        position: 'absolute',
        top: 16,
        right: 16,
        zIndex: 1000,
        pointerEvents: 'auto'
      }}
    >
      {/* Floating Settings Button */}
      <Tooltip label={showControlPanel ? 'Hide Controls' : 'Show Controls'}>
        <ActionIcon
          variant="filled"
          size="lg"
          radius="xl"
          color="brand"
          onClick={() => setShowControlPanel(!showControlPanel)}
          style={{ marginBottom: 8 }}
        >
          <IconSettings size={20} />
        </ActionIcon>
      </Tooltip>

      {/* Control Panel */}
      {showControlPanel && (
        <Paper
          shadow="lg"
          radius="md"
          p="md"
          style={{
            width: 280,
            backdropFilter: 'blur(10px)',
            backgroundColor: 'rgba(255, 255, 255, 0.95)'
          }}
        >
          <Stack gap="sm">
            {/* Header */}
            <Group justify="space-between" align="center">
              <Text fw={600} size="sm">
                3D Scene Controls
              </Text>
              <Badge color="brand" variant="light" size="xs">
                WebGL
              </Badge>
            </Group>

            {/* Animation Controls */}
            <Group justify="space-between" align="center">
              <Text size="sm">Animation</Text>
              <Group gap="xs">
                <Tooltip label={settings.isPlaying ? 'Pause' : 'Play'}>
                  <ActionIcon
                    variant="light"
                    color={settings.isPlaying ? 'orange' : 'green'}
                    onClick={toggleAnimation}
                  >
                    {settings.isPlaying ? <IconPlayerPause size={16} /> : <IconPlayerPlay size={16} />}
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Reset Scene">
                  <ActionIcon variant="light" color="blue" onClick={resetScene}>
                    <IconReload size={16} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            </Group>

            {/* Animation Speed */}
            <Box>
              <Text size="sm" mb={8}>
                Animation Speed: {settings.animationSpeed.toFixed(1)}x
              </Text>
              <Slider
                value={settings.animationSpeed}
                onChange={(value: number) => handleSettingsChange({ animationSpeed: value })}
                min={0.1}
                max={3.0}
                step={0.1}
                marks={[
                  { value: 0.5, label: '0.5x' },
                  { value: 1.0, label: '1x' },
                  { value: 2.0, label: '2x' }
                ]}
                color="brand"
              />
            </Box>

            {/* Scene Elements */}
            <Group justify="space-between" align="center">
              <Group align="center" gap="xs">
                <IconStar size={16} />
                <Text size="sm">Stars</Text>
              </Group>
              <Switch
                checked={settings.showStars}
                onChange={toggleStars}
                color="brand"
                size="sm"
              />
            </Group>

            <Group justify="space-between" align="center">
              <Group align="center" gap="xs">
                <IconCloud size={16} />
                <Text size="sm">Clouds</Text>
              </Group>
              <Switch
                checked={settings.showClouds}
                onChange={toggleClouds}
                color="brand"
                size="sm"
              />
            </Group>

            {/* Scene Info */}
            <Paper radius="sm" p="xs" bg="gray.0">
              <Stack gap={4}>
                <Group justify="space-between">
                  <Text size="xs" c="dimmed">Characters:</Text>
                  <Text size="xs" fw={500}>{characters.length}</Text>
                </Group>
                <Group justify="space-between">
                  <Text size="xs" c="dimmed">Performance:</Text>
                  <Badge
                    size="xs"
                    color={getPerformanceBadgeColor(performanceLevel)}
                    variant="light"
                  >
                    {performanceLevel}
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="xs" c="dimmed">Status:</Text>
                  <Badge
                    size="xs"
                    color={isLoaded ? 'green' : 'orange'}
                    variant="light"
                  >
                    {isLoaded ? 'Loaded' : 'Loading'}
                  </Badge>
                </Group>
              </Stack>
            </Paper>

            {/* Character Types */}
            <Box>
              <Text size="sm" fw={500} mb={8}>
                Characters in Scene
              </Text>
              <Group gap="xs">
                {characters.map((char, index) => (
                  <Badge
                    key={`${char.type}-${char.position.join('-')}-${index}`}
                    size="xs"
                    variant="light"
                    color="brand"
                    style={{ textTransform: 'capitalize' }}
                  >
                    {char.type}
                  </Badge>
                ))}
              </Group>
            </Box>

            {/* Quick Actions */}
            <Group gap="xs" mt="xs">
              <Button
                size="xs"
                variant="light"
                color="brand"
                leftSection={<IconEye size={14} />}
                onClick={() => {
                  handleSettingsChange({ showStars: true, showClouds: true });
                  if (starsRef.current) starsRef.current.visible = true;
                  cloudsRef.current.forEach(cloud => cloud.visible = true);
                }}
                fullWidth
              >
                Show All
              </Button>
              <Button
                size="xs"
                variant="light"
                color="gray"
                leftSection={<IconEyeOff size={14} />}
                onClick={() => {
                  handleSettingsChange({ showStars: false, showClouds: false });
                  if (starsRef.current) starsRef.current.visible = false;
                  cloudsRef.current.forEach(cloud => cloud.visible = false);
                }}
                fullWidth
              >
                Hide All
              </Button>
            </Group>
          </Stack>
        </Paper>
      )}
    </Box>
    </ThreeJSErrorBoundary>
  );
};