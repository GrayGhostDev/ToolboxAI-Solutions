/**
 * Roblox Environment Preview Component (Mantine v8)
 * Displays 3D environment preview with controls and real-time updates
 * Completely converted from MUI to Mantine v8
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  Text,
  Title,
  Button,
  ActionIcon,
  Group,
  Stack,
  Badge,
  Progress,
  Alert,
  Modal,
  SegmentedControl,
  Slider,
  Switch,
  Tooltip,
  Divider,
  ScrollArea,
  Paper,
  Grid,
  Loader
} from '@mantine/core';
import { useLocation } from 'react-router-dom';
import {
  IconMountain,
  IconRotate,
  IconZoomIn,
  IconZoomOut,
  IconFocus2,
  IconMaximize,
  IconMinimize,
  IconPlayerPlay,
  IconPlayerPause,
  IconRefresh,
  IconCamera,
  IconEye,
  IconEyeOff,
  IconStack,
  IconSun,
  IconMoon,
  IconCloud,
  IconLeaf,
  IconDroplet,
  IconFlower,
  IconHome,
  IconRun,
  IconQuestionMark,
  IconFlag,
  IconSettings,
  IconDownload,
  IconUpload,
  IconShare,
  IconInfoCircle,
  IconCheck,
  IconAlertTriangle,
  IconX,
  IconGauge,
  IconCpu,
  IconDatabase
} from '@tabler/icons-react';
import { usePusherContext } from '../../contexts/PusherContext';
import { WebSocketMessageType } from '../../types/websocket';

interface EnvironmentData {
  id: string;
  name: string;
  description: string;
  type: 'classroom' | 'playground' | 'assessment' | 'custom';
  status: 'active' | 'inactive' | 'maintenance';
  thumbnail: string;
  previewUrl: string;
  assets: Array<{
    id: string;
    name: string;
    type: 'model' | 'texture' | 'script' | 'sound';
    size: number;
    url: string;
  }>;
  lighting: {
    ambient: number;
    brightness: number;
    contrast: number;
    shadows: boolean;
  };
  performance: {
    fps: number;
    memory: number;
    polygons: number;
  };
  metadata: {
    created: string;
    modified: string;
    author: string;
    version: string;
    polygonCount: number;
    textureMemory: number;
  };
}

interface SessionData {
  id: string;
  name: string;
  objectives: string[];
  duration: number;
  studentsConnected: number;
}

const RobloxEnvironmentPreview: React.FunctionComponent<{ environmentId?: string }> = ({ environmentId }) => {
  // State management
  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'preview' | 'editor' | 'stats'>('preview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Layer visibility controls
  const [layersVisible, setLayersVisible] = useState({
    terrain: true,
    buildings: true,
    characters: true,
    effects: true,
    ui: true
  });

  // Lighting controls
  const [lightingSettings, setLightingSettings] = useState({
    ambient: 0.5,
    brightness: 1.0,
    contrast: 1.0,
    shadows: true
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const { send } = usePusherContext();

  // Mock environment data
  useEffect(() => {
    const mockEnvironment: EnvironmentData = {
      id: environmentId || 'env_001',
      name: 'Math Adventure Classroom',
      description: 'Interactive 3D classroom for mathematics learning',
      type: 'classroom',
      status: 'active',
      thumbnail: '/api/environments/env_001/thumbnail.jpg',
      previewUrl: '/api/environments/env_001/preview',
      assets: [
        { id: 'asset_1', name: 'Classroom Model', type: 'model', size: 2048, url: '/assets/classroom.fbx' },
        { id: 'asset_2', name: 'Whiteboard Texture', type: 'texture', size: 512, url: '/assets/whiteboard.png' },
        { id: 'asset_3', name: 'Interaction Script', type: 'script', size: 64, url: '/scripts/interaction.lua' }
      ],
      lighting: {
        ambient: 0.5,
        brightness: 1.0,
        contrast: 1.0,
        shadows: true
      },
      performance: {
        fps: 60,
        memory: 128,
        polygons: 15000
      },
      metadata: {
        created: '2025-09-20',
        modified: '2025-09-27',
        author: 'ToolboxAI',
        version: '1.2.0',
        polygonCount: 15000,
        textureMemory: 64 * 1024
      }
    };

    const mockSession: SessionData = {
      id: 'session_001',
      name: 'Algebra Basics Session',
      objectives: [
        'Understand linear equations',
        'Solve for x in basic equations',
        'Apply algebra to real-world problems'
      ],
      duration: 45,
      studentsConnected: 12
    };

    setEnvironment(mockEnvironment);
    setSessionData(mockSession);
    setPreviewUrl('/api/environments/env_001/preview');
    setLoading(false);
  }, [environmentId]);

  // Control functions
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  const togglePlay = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleViewModeChange = useCallback((mode: string) => {
    setViewMode(mode as 'preview' | 'editor' | 'stats');
  }, []);

  const toggleLayer = useCallback((layer: string) => {
    setLayersVisible(prev => ({
      ...prev,
      [layer]: !prev[layer as keyof typeof prev]
    }));
  }, []);

  const handleLightingChange = useCallback((setting: string, value: number) => {
    setLightingSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  }, []);

  if (loading) {
    return (
      <Box p="xl">
        <Stack align="center" gap="md">
          <Loader size="xl" />
          <Text>Loading environment preview...</Text>
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p="xl">
        <Alert color="red" icon={<IconAlertTriangle size={16} />} title="Error Loading Environment">
          <Text size="sm">{error}</Text>
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      ref={containerRef}
      style={{
        height: isFullscreen ? '100vh' : '600px',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#1a1a1a',
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 9999 : 'auto'
      }}
    >
      {/* Header */}
      {!isFullscreen && (
        <Card withBorder>
          <Card.Section p="md">
            <Group justify="space-between">
              <Group>
                <IconMountain color="var(--mantine-color-blue-6)" size={32} />
                <Box>
                  <Text size="xl" fw={600}>
                    {sessionData ? sessionData.name : 'Environment Preview'}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {environment?.description}
                  </Text>
                </Box>
              </Group>
              <Group>
                {environment && (
                  <>
                    <Badge color={environment.status === 'active' ? 'green' : 'red'}>
                      {environment.status}
                    </Badge>
                    <ActionIcon variant="outline" onClick={toggleFullscreen}>
                      <IconMaximize size={16} />
                    </ActionIcon>
                  </>
                )}
              </Group>
            </Group>
          </Card.Section>
        </Card>
      )}

      {/* Main Content */}
      <Group align="stretch" style={{ flex: 1 }}>
        {/* Preview Area */}
        <Card style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Preview Controls */}
          <Card.Section
            p="sm"
            style={{
              borderBottom: '1px solid var(--mantine-color-gray-3)',
              backgroundColor: 'var(--mantine-color-gray-0)'
            }}
          >
            <Group>
              <SegmentedControl
                value={viewMode}
                onChange={handleViewModeChange}
                data={[
                  { label: 'Preview', value: 'preview' },
                  { label: 'Editor', value: 'editor' },
                  { label: 'Stats', value: 'stats' }
                ]}
              />

              <Group gap="xs">
                <Tooltip label="Zoom In">
                  <ActionIcon variant="outline" size="sm">
                    <IconZoomIn size={16} />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Zoom Out">
                  <ActionIcon variant="outline" size="sm">
                    <IconZoomOut size={16} />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Center View">
                  <ActionIcon variant="outline" size="sm">
                    <IconFocus2 size={16} />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Reset View">
                  <ActionIcon variant="outline" size="sm">
                    <IconRefresh size={16} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            </Group>

            <Group>
              <ActionIcon size="sm" onClick={togglePlay}>
                {isPlaying ? <IconPlayerPause size={16} /> : <IconPlayerPlay size={16} />}
              </ActionIcon>
              <Text size="sm" c="dimmed">
                {isPlaying ? 'Playing' : 'Paused'}
              </Text>

              {isFullscreen && (
                <ActionIcon
                  variant="outline"
                  onClick={toggleFullscreen}
                  style={{ marginLeft: 'auto' }}
                >
                  <IconMinimize size={16} />
                </ActionIcon>
              )}
            </Group>
          </Card.Section>

          {/* Preview Content */}
          <Box style={{ flex: 1, position: 'relative', backgroundColor: '#1a1a1a' }}>
            {loading && (
              <Box
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  zIndex: 10
                }}
              >
                <Stack align="center" gap="md">
                  <Loader size="xl" color="blue" />
                  <Text c="white">Loading 3D environment...</Text>
                </Stack>
              </Box>
            )}

            {previewUrl && !loading && (
              <iframe
                src={previewUrl}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  borderRadius: '8px'
                }}
                title="Environment Preview"
              />
            )}

            {!previewUrl && !loading && (
              <Box
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center'
                }}
              >
                <Stack align="center" gap="md">
                  <IconMountain size={64} color="var(--mantine-color-gray-5)" />
                  <Text c="white" size="lg">No preview available</Text>
                  <Text c="gray" size="sm">
                    Environment preview is not configured for this session
                  </Text>
                </Stack>
              </Box>
            )}

            {/* Session Objectives Overlay */}
            {sessionData && sessionData.objectives && (
              <Paper
                p="md"
                style={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                  width: 300,
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(8px)'
                }}
              >
                <Stack gap="sm">
                  <Text fw={600}>Session Objectives</Text>
                  <Text size="sm" c="dimmed">
                    Duration: {sessionData.duration} minutes
                  </Text>
                  <Text size="sm" c="dimmed">
                    Students: {sessionData.studentsConnected} connected
                  </Text>

                  {sessionData.objectives.length > 0 && (
                    <Stack gap="xs">
                      <Text fw={500} size="sm">Objectives:</Text>
                      <Stack gap={4}>
                        {sessionData.objectives.map((obj: string, idx: number) => (
                          <Group key={idx} gap="xs">
                            <IconCheck size={14} color="var(--mantine-color-green-6)" />
                            <Text size="xs">{obj}</Text>
                          </Group>
                        ))}
                      </Stack>
                    </Stack>
                  )}
                </Stack>
              </Paper>
            )}
          </Box>
        </Card>

        {/* Side Panel */}
        {viewMode !== 'preview' && (
          <Card style={{ width: 320, overflow: 'auto' }}>
            <Card.Section p="md" withBorder>
              <Title order={5}>Environment Settings</Title>
            </Card.Section>

            <Stack gap="md" p="md">
              {viewMode === 'editor' && environment && (
                <>
                  <Text fw={500}>Environment Information</Text>

                  {/* Environment Info */}
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Type:</Text>
                      <Badge variant="outline">{environment.type}</Badge>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Subject:</Text>
                      <Text size="sm" fw={500}>Mathematics</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Grade:</Text>
                      <Text size="sm" fw={500}>8th Grade</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm" c="dimmed">Size:</Text>
                      <Text size="sm" fw={500}>
                        {(environment.assets.reduce((acc, asset) => acc + asset.size, 0) / 1024).toFixed(1)} KB
                      </Text>
                    </Group>
                  </Stack>

                  <Divider />

                  {/* Layers */}
                  <Stack gap="sm">
                    <Text fw={500}>Layers</Text>
                    {Object.entries(layersVisible).map(([layer, visible]) => (
                      <Group key={layer} justify="space-between">
                        <Group gap="xs">
                          <IconStack size={16} />
                          <Text size="sm" style={{ textTransform: 'capitalize' }}>
                            {layer}
                          </Text>
                        </Group>
                        <Switch
                          checked={visible}
                          onChange={() => toggleLayer(layer)}
                          size="sm"
                        />
                      </Group>
                    ))}
                  </Stack>

                  <Divider />

                  {/* Lighting */}
                  <Stack gap="sm">
                    <Text fw={500}>Lighting</Text>

                    <Stack gap="xs">
                      <Text size="sm">Ambient Light</Text>
                      <Slider
                        value={lightingSettings.ambient}
                        onChange={(value) => handleLightingChange('ambient', value)}
                        min={0}
                        max={1}
                        step={0.1}
                        size="sm"
                      />
                    </Stack>

                    <Stack gap="xs">
                      <Text size="sm">Brightness</Text>
                      <Slider
                        value={lightingSettings.brightness}
                        onChange={(value) => handleLightingChange('brightness', value)}
                        min={0}
                        max={2}
                        step={0.1}
                        size="sm"
                      />
                    </Stack>

                    <Stack gap="xs">
                      <Text size="sm">Contrast</Text>
                      <Slider
                        value={lightingSettings.contrast}
                        onChange={(value) => handleLightingChange('contrast', value)}
                        min={0}
                        max={2}
                        step={0.1}
                        size="sm"
                      />
                    </Stack>

                    <Group justify="space-between">
                      <Text size="sm">Shadows</Text>
                      <Switch
                        checked={lightingSettings.shadows}
                        onChange={(event) => handleLightingChange('shadows', event.currentTarget.checked ? 1 : 0)}
                        size="sm"
                      />
                    </Group>
                  </Stack>

                  <Divider />

                  {/* Assets */}
                  <Stack gap="sm">
                    <Text fw={500}>Assets ({environment.assets.length})</Text>
                    <ScrollArea h={200}>
                      <Stack gap="xs">
                        {environment.assets.map((asset) => (
                          <Paper key={asset.id} p="xs" withBorder>
                            <Group justify="space-between">
                              <Group gap="xs">
                                {asset.type === 'model' && <IconDatabase size={14} />}
                                {asset.type === 'texture' && <IconCamera size={14} />}
                                {asset.type === 'script' && <IconSettings size={14} />}
                                {asset.type === 'sound' && <IconShare size={14} />}
                                <Text size="xs">{asset.name}</Text>
                              </Group>
                              <Text size="xs" c="dimmed">
                                {(asset.size / 1024).toFixed(1)} KB
                              </Text>
                            </Group>
                          </Paper>
                        ))}
                      </Stack>
                    </ScrollArea>
                  </Stack>
                </>
              )}

              {viewMode === 'stats' && environment && (
                <>
                  <Text fw={500}>Performance Statistics</Text>

                  <Stack gap="md">
                    <Group justify="space-between">
                      <Text size="sm">Frame Rate</Text>
                      <Badge color={environment.performance.fps >= 55 ? 'green' : environment.performance.fps >= 30 ? 'yellow' : 'red'}>
                        {environment.performance.fps} FPS
                      </Badge>
                    </Group>

                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="sm">Polygon Count</Text>
                        <Text size="sm" fw={500}>
                          {environment.metadata.polygonCount.toLocaleString()}
                        </Text>
                      </Group>
                      <Progress
                        value={(environment.metadata.polygonCount / 50000) * 100}
                        size="sm"
                        color={environment.metadata.polygonCount > 30000 ? 'red' :
                               environment.metadata.polygonCount > 20000 ? 'yellow' : 'green'}
                      />
                    </Stack>

                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="sm">Texture Memory</Text>
                        <Text size="sm" fw={500}>
                          {(environment.metadata.textureMemory / 1024).toFixed(1)} MB
                        </Text>
                      </Group>
                      <Progress
                        value={(environment.metadata.textureMemory / (256 * 1024)) * 100}
                        size="sm"
                        color={environment.metadata.textureMemory > 200 * 1024 ? 'red' :
                               environment.metadata.textureMemory > 150 * 1024 ? 'yellow' : 'green'}
                      />
                    </Stack>

                    <Alert color="blue" icon={<IconInfoCircle size={16} />}>
                      <Text size="sm">
                        <strong>Performance Rating:</strong>{' '}
                        {environment.performance.fps >= 55 && 'Excellent - Smooth gameplay experience'}
                        {environment.performance.fps >= 30 && environment.performance.fps < 55 && 'Good - Acceptable for most devices'}
                        {environment.performance.fps < 30 && 'Poor - May cause lag on some devices'}
                      </Text>
                    </Alert>
                  </Stack>
                </>
              )}
            </Stack>
          </Card>
        )}
      </Group>
    </Box>
  );
};

export default RobloxEnvironmentPreview;
