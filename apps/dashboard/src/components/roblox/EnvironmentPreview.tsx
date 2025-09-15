/**
 * Environment Preview Component
 * Displays a 3D-like preview of the generated Roblox environment
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Preview as PreviewIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  Refresh as RefreshIcon,
  School as SchoolIcon,
  Group as GroupIcon,
  Timer as TimerIcon,
  Terrain as TerrainIcon,
  Home as HomeIcon,
  Computer as ComputerIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';

import { robloxEnvironmentService } from '../../services/robloxEnvironment';

interface EnvironmentPreviewProps {
  environmentId: string;
  environmentDetails?: any;
  onClose?: () => void;
}

const EnvironmentPreview: React.FC<EnvironmentPreviewProps> = ({
  environmentId,
  environmentDetails,
  onClose
}) => {
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (environmentId) {
      generatePreview();
    }
  }, [environmentId]);

  const generatePreview = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      // Create a preview request based on environment details
      const previewRequest = {
        name: environmentDetails?.name || environmentId,
        description: environmentDetails?.description || 'Educational environment',
        grade_level: environmentDetails?.grade_level || '',
        subject: environmentDetails?.subject || '',
        max_players: environmentDetails?.max_players || 20,
        settings: environmentDetails?.settings || {}
      };

      const response = await robloxEnvironmentService.previewEnvironment(previewRequest);

      if (response.success && response.preview) {
        setPreview(response.preview);
      } else {
        // Generate fallback preview
        setPreview(generateFallbackPreview(environmentDetails));
      }
    } catch (err) {
      console.error('Preview generation failed:', err);
      setError('Failed to generate preview');
      // Still show fallback preview
      setPreview(generateFallbackPreview(environmentDetails));
    } finally {
      setLoading(false);
      setIsGenerating(false);
    }
  };

  const generateFallbackPreview = (details: any) => {
    return {
      name: details?.name || environmentId,
      description: details?.description || 'Educational environment',
      structure: {
        terrain: [
          { type: 'Grass', position: { x: 0, y: 0, z: 0 }, size: { x: 100, y: 10, z: 100 } },
          { type: 'Hills', position: { x: 50, y: 0, z: 50 }, size: { x: 30, y: 15, z: 30 } }
        ],
        buildings: [
          { type: 'Classroom', position: { x: 20, y: 0, z: 20 }, size: { x: 25, y: 15, z: 25 }, color: '#4CAF50' },
          { type: 'Library', position: { x: 60, y: 0, z: 20 }, size: { x: 20, y: 12, z: 20 }, color: '#2196F3' }
        ],
        objects: [
          { type: 'Desks', position: { x: 25, y: 0, z: 25 }, size: { x: 5, y: 3, z: 5 }, color: '#8D6E63' },
          { type: 'Chairs', position: { x: 30, y: 0, z: 30 }, size: { x: 3, y: 4, z: 3 }, color: '#795548' },
          { type: 'Whiteboard', position: { x: 22, y: 0, z: 22 }, size: { x: 8, y: 6, z: 1 }, color: '#FFFFFF' }
        ]
      },
      lighting: {
        type: 'Bright/Sunny',
        brightness: 0.8,
        color: '#FFE4B5'
      },
      effects: [
        { type: 'Sunshine', intensity: 0.7, active: true }
      ],
      metadata: {
        grade_level: details?.grade_level || 'Any',
        subject: details?.subject || 'General',
        max_players: details?.max_players || 20,
        complexity: 'Medium'
      }
    };
  };

  const handleDeployToRoblox = async () => {
    try {
      // This would trigger deployment to Roblox Studio
      console.log('Deploying to Roblox Studio...');
      // Implementation would call the backend API
    } catch (error) {
      console.error('Deployment failed:', error);
    }
  };

  const handleDownload = async () => {
    try {
      // This would download the .rbxl file
      console.log('Downloading .rbxl file...');
      // Implementation would call the backend API
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Generating environment preview...
        </Typography>
      </Box>
    );
  }

  if (error && !preview) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card sx={{ maxWidth: 800, mx: 'auto', m: 2 }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h5" component="h2">
            {preview?.name || environmentId}
          </Typography>
          <Box>
            <Tooltip title="Refresh Preview">
              <IconButton onClick={generatePreview} disabled={isGenerating}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {onClose && (
              <IconButton onClick={onClose}>
                ×
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Environment Details */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 1, textAlign: 'center' }}>
              <SchoolIcon color="primary" sx={{ mb: 0.5 }} />
              <Typography variant="caption" display="block">
                Grade: {preview?.metadata?.grade_level || 'Any'}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 1, textAlign: 'center' }}>
              <GroupIcon color="primary" sx={{ mb: 0.5 }} />
              <Typography variant="caption" display="block">
                Max Players: {preview?.metadata?.max_players || 20}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 1, textAlign: 'center' }}>
              <TimerIcon color="primary" sx={{ mb: 0.5 }} />
              <Typography variant="caption" display="block">
                Duration: 30-45 min
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 1, textAlign: 'center' }}>
              <Chip
                label={preview?.metadata?.complexity || 'Medium'}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Paper>
          </Grid>
        </Grid>

        {/* 3D Environment Visualization */}
        <Box sx={{
          height: 400,
          backgroundColor: '#f5f5f5',
          borderRadius: 2,
          position: 'relative',
          overflow: 'hidden',
          border: '2px solid #e0e0e0',
          mb: 3
        }}>
          {/* Terrain */}
          {preview?.structure?.terrain?.map((terrain: any, index: number) => (
            <Box
              key={`terrain-${index}`}
              sx={{
                position: 'absolute',
                left: `${terrain.position.x}%`,
                top: `${terrain.position.z}%`,
                width: `${terrain.size.x}px`,
                height: `${terrain.size.z}px`,
                backgroundColor: terrain.type === 'Grass' ? '#4CAF50' : '#8BC34A',
                borderRadius: terrain.type === 'Hills' ? '50%' : '4px',
                opacity: 0.8,
                border: '2px solid #2E7D32',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                fontWeight: 'bold',
                color: 'white',
                textShadow: '1px 1px 1px rgba(0,0,0,0.5)'
              }}
              title={terrain.type}
            >
              {terrain.type}
            </Box>
          ))}

          {/* Buildings */}
          {preview?.structure?.buildings?.map((building: any, index: number) => (
            <Box
              key={`building-${index}`}
              sx={{
                position: 'absolute',
                left: `${building.position.x}%`,
                top: `${building.position.z}%`,
                width: `${building.size.x}px`,
                height: `${building.size.z}px`,
                backgroundColor: building.color,
                border: '2px solid #333',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '9px',
                fontWeight: 'bold',
                color: 'white',
                textShadow: '1px 1px 1px rgba(0,0,0,0.5)',
                borderRadius: '2px'
              }}
              title={building.type}
            >
              {building.type}
            </Box>
          ))}

          {/* Objects */}
          {preview?.structure?.objects?.map((object: any, index: number) => (
            <Box
              key={`object-${index}`}
              sx={{
                position: 'absolute',
                left: `${object.position.x}%`,
                top: `${object.position.z}%`,
                width: `${object.size.x}px`,
                height: `${object.size.z}px`,
                backgroundColor: object.color,
                border: '1px solid #666',
                borderRadius: '2px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '8px',
                color: 'white',
                textShadow: '1px 1px 1px rgba(0,0,0,0.5)'
              }}
              title={object.type}
            >
              {object.type}
            </Box>
          ))}

          {/* Lighting Overlay */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: preview?.lighting?.color || '#FFE4B5',
              opacity: 1 - (preview?.lighting?.brightness || 0.8),
              pointerEvents: 'none'
            }}
          />

          {/* Effects */}
          {preview?.effects?.map((effect: any, index: number) => (
            <Box
              key={`effect-${index}`}
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: effect.type === 'Sunshine' ?
                  'radial-gradient(circle, rgba(255,255,0,0.1) 0%, transparent 70%)' : 'none',
                pointerEvents: 'none',
                opacity: effect.intensity || 0.5
              }}
            />
          ))}

          {/* Legend */}
          <Box sx={{
            position: 'absolute',
            top: 8,
            left: 8,
            backgroundColor: 'rgba(255,255,255,0.9)',
            padding: 1,
            borderRadius: 1,
            fontSize: '10px'
          }}>
            <Typography variant="caption" display="block">
              🟢 Terrain &nbsp; 🏠 Buildings &nbsp; 📦 Objects
            </Typography>
          </Box>
        </Box>

        {/* Environment Components Summary */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <TerrainIcon color="primary" sx={{ mb: 1 }} />
              <Typography variant="subtitle2">Terrain</Typography>
              <Typography variant="body2" color="text.secondary">
                {preview?.structure?.terrain?.length || 0} areas
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <HomeIcon color="primary" sx={{ mb: 1 }} />
              <Typography variant="subtitle2">Buildings</Typography>
              <Typography variant="body2" color="text.secondary">
                {preview?.structure?.buildings?.length || 0} structures
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <ComputerIcon color="primary" sx={{ mb: 1 }} />
              <Typography variant="subtitle2">Objects</Typography>
              <Typography variant="body2" color="text.secondary">
                {preview?.structure?.objects?.length || 0} items
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Action Buttons */}
        <Divider sx={{ mb: 2 }} />
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="contained"
            startIcon={<PreviewIcon />}
            onClick={() => window.open(`/environment-preview/${environmentId}`, '_blank')}
            size="large"
          >
            View Full Preview
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
            size="large"
          >
            Download .rbxl
          </Button>
          <Button
            variant="outlined"
            startIcon={<CodeIcon />}
            onClick={handleDeployToRoblox}
            size="large"
          >
            Deploy to Roblox
          </Button>
        </Box>

        {/* Description */}
        {preview?.description && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              {preview.description}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default EnvironmentPreview;
