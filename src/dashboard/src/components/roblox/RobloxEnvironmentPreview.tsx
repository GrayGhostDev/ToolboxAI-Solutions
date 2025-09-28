/**
 * RobloxEnvironmentPreview Component
 *
 * 3D preview of Roblox educational environments
 * Displays generated terrain, assets, and interactive elements
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Button,
  ButtonGroup,
  Slider,
  Stack,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  CircularProgress,
  LinearProgress,
  Alert,
  AlertTitle,
  Divider,
  Grid,
  ToggleButton,
  ToggleButtonGroup,
  Collapse,
  Switch,
  FormControlLabel,
  Menu,
  MenuItem,
  useTheme,
  alpha
} from '@mui/material';
import {
  Terrain,
  ThreeDRotation,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Fullscreen,
  FullscreenExit,
  PlayArrow,
  Pause,
  Refresh,
  CameraAlt,
  Visibility,
  VisibilityOff,
  Layers,
  WbSunny,
  NightsStay,
  CloudQueue,
  Grass,
  Water,
  LocalFlorist,
  House,
  DirectionsRun,
  Quiz,
  Flag,
  Settings,
  Download,
  Upload,
  Share,
  Info,
  Timer,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Speed,
  Memory,
  Storage
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketMessageType } from '../../types/websocket';

interface EnvironmentData {
  id: string;
  name: string;
  type: 'classroom' | 'outdoor' | 'laboratory' | 'space_station' | 'underwater' | 'historical';
  status: 'loading' | 'ready' | 'error';
  terrain: TerrainData;
  assets: AssetData[];
  lighting: LightingData;
  metadata: {
    subject: string;
    gradeLevel: number;
    objectives: string[];
    createdAt: Date;
    size: { x: number; y: number; z: number };
    polyCount: number;
    textureMemory: number;
  };
  performance: {
    fps: number;
    renderTime: number;
    memoryUsage: number;
  };
}

interface TerrainData {
  type: string;
  heightMap?: string;
  texture: string;
  props: {
    trees?: number;
    rocks?: number;
    water?: boolean;
    buildings?: number;
  };
}

interface AssetData {
  id: string;
  name: string;
  type: 'model' | 'npc' | 'interactive' | 'decoration';
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  scale: { x: number; y: number; z: number };
  visible: boolean;
  interactive: boolean;
  properties?: Record<string, any>;
}

interface LightingData {
  timeOfDay: 'morning' | 'noon' | 'evening' | 'night';
  ambient: string;
  directional: string;
  fog?: {
    enabled: boolean;
    color: string;
    density: number;
  };
  skybox: string;
}

type ViewMode = 'preview' | 'editor' | 'stats';
type CameraMode = 'orbit' | 'fly' | 'first-person';

const ASSET_ICONS: Record<string, React.ReactNode> = {
  model: <House />,
  npc: <DirectionsRun />,
  interactive: <Quiz />,
  decoration: <LocalFlorist />
};

export const RobloxEnvironmentPreview: React.FC = () => {
  const theme = useTheme();
  const { on, sendMessage, isConnected } = useWebSocketContext();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('preview');
  const [cameraMode, setCameraMode] = useState<CameraMode>('orbit');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoom, setZoom] = useState(100);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [showGrid, setShowGrid] = useState(true);
  const [showStats, setShowStats] = useState(false);
  const [layersVisible, setLayersVisible] = useState({
    terrain: true,
    assets: true,
    lighting: true,
    ui: true
  });
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeEnvironment = on(WebSocketMessageType.ENVIRONMENT_UPDATE, (data: any) => {
      handleEnvironmentUpdate(data);
    });

    const unsubscribeAsset = on(WebSocketMessageType.ASSET_UPDATE, (data: any) => {
      handleAssetUpdate(data);
    });

    const unsubscribePreview = on(WebSocketMessageType.PREVIEW_READY, (data: any) => {
      setPreviewUrl(data.url);
      setLoading(false);
    });

    return () => {
      unsubscribeEnvironment();
      unsubscribeAsset();
      unsubscribePreview();
    };
  }, [isConnected]);

  const handleEnvironmentUpdate = (data: Partial<EnvironmentData>) => {
    setEnvironment(prev => prev ? { ...prev, ...data } : null);
  };

  const handleAssetUpdate = (data: any) => {
    setEnvironment(prev => {
      if (!prev) return null;

      const updatedAssets = prev.assets.map(asset =>
        asset.id === data.assetId ? { ...asset, ...data.updates } : asset
      );

      return { ...prev, assets: updatedAssets };
    });
  };

  const loadEnvironment = (environmentId: string) => {
    setLoading(true);
    sendMessage(WebSocketMessageType.LOAD_ENVIRONMENT, { environmentId });
  };

  const handleZoom = (delta: number) => {
    const newZoom = Math.max(25, Math.min(200, zoom + delta));
    setZoom(newZoom);
    sendPreviewCommand('zoom', { level: newZoom });
  };

  const handleCameraReset = () => {
    setZoom(100);
    sendPreviewCommand('camera.reset');
  };

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      await containerRef.current.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
    sendPreviewCommand(isPlaying ? 'pause' : 'play');
  };

  const sendPreviewCommand = (command: string, params?: any) => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.postMessage({
        type: 'preview-command',
        command,
        params
      }, '*');
    }
  };

  const handleAssetToggle = (assetId: string) => {
    if (!environment) return;

    const asset = environment.assets.find(a => a.id === assetId);
    if (asset) {
      const newVisibility = !asset.visible;
      sendMessage(WebSocketMessageType.TOGGLE_ASSET, {
        assetId,
        visible: newVisibility
      });

      // Optimistic update
      handleAssetUpdate({
        assetId,
        updates: { visible: newVisibility }
      });
    }
  };

  const handleLayerToggle = (layer: keyof typeof layersVisible) => {
    const newState = !layersVisible[layer];
    setLayersVisible(prev => ({ ...prev, [layer]: newState }));
    sendPreviewCommand(`layer.${layer}`, { visible: newState });
  };

  const exportEnvironment = () => {
    if (!environment) return;

    sendMessage(WebSocketMessageType.EXPORT_ENVIRONMENT, {
      environmentId: environment.id,
      format: 'rbxl'
    });
  };

  const shareEnvironment = () => {
    if (!environment) return;

    sendMessage(WebSocketMessageType.SHARE_ENVIRONMENT, {
      environmentId: environment.id
    });
  };

  // Calculate performance color
  const getPerformanceColor = (fps: number) => {
    if (fps >= 55) return 'success';
    if (fps >= 30) return 'warning';
    return 'error';
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        bgcolor: isFullscreen ? 'black' : 'transparent'
      }}
    >
      {/* Header */}
      {!isFullscreen && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Terrain color="primary" fontSize="large" />
                <Box>
                  <Typography variant="h5">Environment Preview</Typography>
                  <Typography variant="body2" color="text.secondary">
                    3D visualization of generated Roblox environment
                  </Typography>
                </Box>
              </Box>

              <Stack direction="row" spacing={1}>
                {environment && (
                  <>
                    <Chip
                      label={environment.status}
                      size="small"
                      color={environment.status === 'ready' ? 'success' :
                             environment.status === 'loading' ? 'warning' : 'error'}
                    />
                    <Chip
                      label={`${environment.performance.fps} FPS`}
                      size="small"
                      color={getPerformanceColor(environment.performance.fps) as any}
                    />
                  </>
                )}
              </Stack>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2 }}>
        {/* Preview Area */}
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Preview Controls */}
          <Box
            sx={{
              p: 1,
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <Stack direction="row" spacing={1}>
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(e, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="preview">
                  <Visibility />
                </ToggleButton>
                <ToggleButton value="editor">
                  <Settings />
                </ToggleButton>
                <ToggleButton value="stats">
                  <Speed />
                </ToggleButton>
              </ToggleButtonGroup>

              <Divider orientation="vertical" flexItem />

              <ButtonGroup size="small">
                <Button onClick={() => handleZoom(-10)}>
                  <ZoomOut />
                </Button>
                <Button disabled>
                  {zoom}%
                </Button>
                <Button onClick={() => handleZoom(10)}>
                  <ZoomIn />
                </Button>
              </ButtonGroup>

              <IconButton size="small" onClick={handleCameraReset}>
                <CenterFocusStrong />
              </IconButton>

              <ToggleButtonGroup
                value={cameraMode}
                exclusive
                onChange={(e, value) => value && setCameraMode(value)}
                size="small"
              >
                <ToggleButton value="orbit">
                  <ThreeDRotation />
                </ToggleButton>
                <ToggleButton value="fly">
                  <CameraAlt />
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>

            <Stack direction="row" spacing={1}>
              <IconButton size="small" onClick={togglePlay}>
                {isPlaying ? <Pause /> : <PlayArrow />}
              </IconButton>

              <IconButton size="small" onClick={() => loadEnvironment('current')}>
                <Refresh />
              </IconButton>

              <IconButton size="small" onClick={exportEnvironment}>
                <Download />
              </IconButton>

              <IconButton size="small" onClick={shareEnvironment}>
                <Share />
              </IconButton>

              <IconButton size="small" onClick={toggleFullscreen}>
                {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
            </Stack>
          </Box>

          {/* Preview Content */}
          <Box sx={{ flex: 1, position: 'relative', bgcolor: '#1a1a1a' }}>
            {loading && (
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  zIndex: 10
                }}
              >
                <CircularProgress size={60} />
                <Typography variant="body2" color="white" sx={{ mt: 2 }}>
                  Loading environment...
                </Typography>
              </Box>
            )}

            {previewUrl && (
              <iframe
                ref={iframeRef}
                src={previewUrl}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  display: loading ? 'none' : 'block'
                }}
                title="Roblox Environment Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            )}

            {!previewUrl && !loading && (
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center'
                }}
              >
                <Terrain sx={{ fontSize: 64, color: 'text.disabled' }} />
                <Typography variant="h6" color="text.secondary" sx={{ mt: 2 }}>
                  No environment loaded
                </Typography>
                <Button
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={() => loadEnvironment('demo')}
                >
                  Load Demo Environment
                </Button>
              </Box>
            )}

            {/* Overlay Stats */}
            {showStats && environment && (
              <Paper
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  p: 1,
                  bgcolor: alpha(theme.palette.background.paper, 0.9)
                }}
              >
                <Stack spacing={0.5}>
                  <Typography variant="caption">
                    FPS: {environment.performance.fps}
                  </Typography>
                  <Typography variant="caption">
                    Render: {environment.performance.renderTime}ms
                  </Typography>
                  <Typography variant="caption">
                    Memory: {environment.performance.memoryUsage}MB
                  </Typography>
                  <Typography variant="caption">
                    Polys: {environment.metadata.polyCount.toLocaleString()}
                  </Typography>
                </Stack>
              </Paper>
            )}

            {/* Grid Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={showGrid}
                  onChange={(e) => {
                    setShowGrid(e.target.checked);
                    sendPreviewCommand('grid', { visible: e.target.checked });
                  }}
                  size="small"
                />
              }
              label="Grid"
              sx={{
                position: 'absolute',
                bottom: 8,
                left: 8,
                bgcolor: alpha(theme.palette.background.paper, 0.9),
                px: 1,
                borderRadius: 1
              }}
            />
          </Box>
        </Card>

        {/* Side Panel */}
        {viewMode !== 'preview' && (
          <Card sx={{ width: 320, overflow: 'auto' }}>
            <CardContent>
              {viewMode === 'editor' && environment && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Environment Settings
                  </Typography>

                  {/* Environment Info */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Information
                    </Typography>
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Type:
                        </Typography>
                        <Typography variant="caption">
                          {environment.type}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Subject:
                        </Typography>
                        <Typography variant="caption">
                          {environment.metadata.subject}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Grade:
                        </Typography>
                        <Typography variant="caption">
                          Level {environment.metadata.gradeLevel}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Size:
                        </Typography>
                        <Typography variant="caption">
                          {environment.metadata.size.x}x{environment.metadata.size.z}
                        </Typography>
                      </Box>
                    </Stack>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Layers */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Layers
                    </Typography>
                    <Stack spacing={1}>
                      {Object.entries(layersVisible).map(([layer, visible]) => (
                        <Box
                          key={layer}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Layers fontSize="small" />
                            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                              {layer}
                            </Typography>
                          </Box>
                          <IconButton
                            size="small"
                            onClick={() => handleLayerToggle(layer as keyof typeof layersVisible)}
                          >
                            {visible ? <Visibility /> : <VisibilityOff />}
                          </IconButton>
                        </Box>
                      ))}
                    </Stack>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Lighting */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Lighting
                    </Typography>
                    <ToggleButtonGroup
                      value={environment.lighting.timeOfDay}
                      exclusive
                      onChange={(e, value) => {
                        if (value) {
                          sendPreviewCommand('lighting.time', { time: value });
                        }
                      }}
                      size="small"
                      fullWidth
                    >
                      <ToggleButton value="morning">
                        <Tooltip title="Morning">
                          <WbSunny fontSize="small" />
                        </Tooltip>
                      </ToggleButton>
                      <ToggleButton value="noon">
                        <Tooltip title="Noon">
                          <WbSunny fontSize="small" />
                        </Tooltip>
                      </ToggleButton>
                      <ToggleButton value="evening">
                        <Tooltip title="Evening">
                          <CloudQueue fontSize="small" />
                        </Tooltip>
                      </ToggleButton>
                      <ToggleButton value="night">
                        <Tooltip title="Night">
                          <NightsStay fontSize="small" />
                        </Tooltip>
                      </ToggleButton>
                    </ToggleButtonGroup>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Assets */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Assets ({environment.assets.length})
                    </Typography>
                    <List dense>
                      {environment.assets.map((asset) => (
                        <ListItem
                          key={asset.id}
                          button
                          selected={selectedAsset === asset.id}
                          onClick={() => setSelectedAsset(asset.id)}
                        >
                          <ListItemIcon>
                            {ASSET_ICONS[asset.type] || <House />}
                          </ListItemIcon>
                          <ListItemText
                            primary={asset.name}
                            secondary={`${asset.type} - ${asset.interactive ? 'Interactive' : 'Static'}`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton
                              edge="end"
                              size="small"
                              onClick={() => handleAssetToggle(asset.id)}
                            >
                              {asset.visible ? <Visibility /> : <VisibilityOff />}
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </>
              )}

              {viewMode === 'stats' && environment && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Performance Stats
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Speed color="primary" />
                        <Typography variant="h4">
                          {environment.performance.fps}
                        </Typography>
                        <Typography variant="caption">FPS</Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Memory color="warning" />
                        <Typography variant="h4">
                          {environment.performance.memoryUsage}
                        </Typography>
                        <Typography variant="caption">MB Used</Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Timer color="info" />
                        <Typography variant="h4">
                          {environment.performance.renderTime}
                        </Typography>
                        <Typography variant="caption">ms Render</Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Storage color="success" />
                        <Typography variant="h4">
                          {(environment.metadata.textureMemory / 1024).toFixed(1)}
                        </Typography>
                        <Typography variant="caption">MB Textures</Typography>
                      </Paper>
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Resource Usage
                    </Typography>

                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption">Polygon Count</Typography>
                        <Typography variant="caption">
                          {environment.metadata.polyCount.toLocaleString()} / 100,000
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(environment.metadata.polyCount / 100000) * 100}
                        color={environment.metadata.polyCount > 80000 ? 'error' :
                               environment.metadata.polyCount > 60000 ? 'warning' : 'success'}
                      />
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption">Texture Memory</Typography>
                        <Typography variant="caption">
                          {(environment.metadata.textureMemory / 1024).toFixed(1)} / 256 MB
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(environment.metadata.textureMemory / (256 * 1024)) * 100}
                        color={environment.metadata.textureMemory > 200 * 1024 ? 'error' :
                               environment.metadata.textureMemory > 150 * 1024 ? 'warning' : 'success'}
                      />
                    </Box>
                  </Box>

                  <Alert severity={
                    environment.performance.fps < 30 ? 'error' :
                    environment.performance.fps < 55 ? 'warning' : 'success'
                  } sx={{ mt: 2 }}>
                    <AlertTitle>Performance Rating</AlertTitle>
                    {environment.performance.fps >= 55 && 'Excellent - Smooth gameplay experience'}
                    {environment.performance.fps >= 30 && environment.performance.fps < 55 && 'Good - Acceptable for most devices'}
                    {environment.performance.fps < 30 && 'Poor - May cause lag on some devices'}
                  </Alert>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
};
