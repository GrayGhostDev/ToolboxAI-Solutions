/**
 * Environment Preview Component
 * Displays a 3D-like preview of the generated Roblox environment
 */

import React, { useState, useEffect } from 'react';
import { Box, Card, Text, Button, Loader, Alert, Badge, Grid, Paper, ActionIcon, Tooltip, Divider, Group, useMantineTheme } from '@mantine/core';
import {
  IconEye,
  IconDownload,
  IconCode,
  IconRefresh,
  IconSchool,
  IconUsers,
  IconClock,
  IconMountain,
  IconHome,
  IconDeviceDesktop,
  IconX
} from '@tabler/icons-react';

import { robloxEnvironmentService } from '../../services/robloxEnvironment';

interface EnvironmentPreviewProps {
  environmentId: string;
  environmentDetails?: any;
  onClose?: () => void;
}

const EnvironmentPreview: React.FunctionComponent<EnvironmentPreviewProps> = ({
  environmentId,
  environmentDetails,
  onClose
}) => {
  const theme = useMantineTheme();
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
      <Box style={{ padding: theme.spacing.lg, textAlign: 'center' }}>
        <Loader size={40} />
        <Text mt="md">
          Generating environment preview...
        </Text>
      </Box>
    );
  }

  if (error && !preview) {
    return (
      <Alert color="red" style={{ margin: theme.spacing.md }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card withBorder style={{ maxWidth: 800, margin: '0 auto' }} mt="md">
      {/* Header */}
      <Group position="apart" align="center" mb="md">
        <Text size="xl" weight={700}>
          {preview?.name || environmentId}
        </Text>
        <Group spacing={theme.spacing.xs}>
          <Tooltip label="Refresh Preview">
            <ActionIcon onClick={generatePreview} disabled={isGenerating}>
              <IconRefresh />
            </ActionIcon>
          </Tooltip>
          {onClose && (
            <ActionIcon onClick={onClose}>
              <IconX />
            </ActionIcon>
          )}
        </Group>
      </Group>

      {/* Environment Details */}
      <Grid mb="lg">
        <Grid.Col span={6} sm={3}>
          <Paper style={{ padding: theme.spacing.xs, textAlign: 'center' }}>
            <IconSchool color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs / 2 }} />
            <Text size="xs">
              Grade: {preview?.metadata?.grade_level || 'Any'}
            </Text>
          </Paper>
        </Grid.Col>
        <Grid.Col span={6} sm={3}>
          <Paper style={{ padding: theme.spacing.xs, textAlign: 'center' }}>
            <IconUsers color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs / 2 }} />
            <Text size="xs">
              Max Players: {preview?.metadata?.max_players || 20}
            </Text>
          </Paper>
        </Grid.Col>
        <Grid.Col span={6} sm={3}>
          <Paper style={{ padding: theme.spacing.xs, textAlign: 'center' }}>
            <IconClock color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs / 2 }} />
            <Text size="xs">
              Duration: 30-45 min
            </Text>
          </Paper>
        </Grid.Col>
        <Grid.Col span={6} sm={3}>
          <Paper style={{ padding: theme.spacing.xs, textAlign: 'center' }}>
            <Badge
              size="sm"
              color="blue"
              variant="outline"
            >
              {preview?.metadata?.complexity || 'Medium'}
            </Badge>
          </Paper>
        </Grid.Col>
      </Grid>

      {/* 3D Environment Visualization */}
      <Box style={{
        height: 400,
        backgroundColor: theme.colors.gray[1],
        borderRadius: theme.radius.md,
        position: 'relative',
        overflow: 'hidden',
        border: `2px solid ${theme.colors.gray[3]}`,
        marginBottom: theme.spacing.lg
      }}>
        {/* Terrain */}
        {preview?.structure?.terrain?.map((terrain: any, index: number) => (
          <Box
            key={`terrain-${index}`}
            style={{
              position: 'absolute',
              left: `${terrain.position.x}%`,
              top: `${terrain.position.z}%`,
              width: `${terrain.size.x}px`,
              height: `${terrain.size.z}px`,
              backgroundColor: terrain.type === 'Grass' ? theme.colors.green[5] : theme.colors.green[4],
              borderRadius: terrain.type === 'Hills' ? '50%' : theme.radius.xs,
              opacity: 0.8,
              border: `2px solid ${theme.colors.green[7]}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '10px',
              fontWeight: 700,
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
            style={{
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
              fontWeight: 700,
              color: 'white',
              textShadow: '1px 1px 1px rgba(0,0,0,0.5)',
              borderRadius: theme.radius.xs
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
            style={{
              position: 'absolute',
              left: `${object.position.x}%`,
              top: `${object.position.z}%`,
              width: `${object.size.x}px`,
              height: `${object.size.z}px`,
              backgroundColor: object.color,
              border: '1px solid #666',
              borderRadius: theme.radius.xs,
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
          style={{
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
            style={{
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
        <Box style={{
          position: 'absolute',
          top: 8,
          left: 8,
          backgroundColor: 'rgba(255,255,255,0.9)',
          padding: theme.spacing.xs,
          borderRadius: theme.radius.sm,
          fontSize: '10px'
        }}>
          <Text size="xs">
            🟢 Terrain   🏠 Buildings   📦 Objects
          </Text>
        </Box>
      </Box>

      {/* Environment Components Summary */}
      <Grid mb="lg">
        <Grid.Col span={12} sm={4}>
          <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
            <IconMountain color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
            <Text weight={600} size="sm">Terrain</Text>
            <Text size="sm" color="dimmed">
              {preview?.structure?.terrain?.length || 0} areas
            </Text>
          </Paper>
        </Grid.Col>
        <Grid.Col span={12} sm={4}>
          <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
            <IconHome color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
            <Text weight={600} size="sm">Buildings</Text>
            <Text size="sm" color="dimmed">
              {preview?.structure?.buildings?.length || 0} structures
            </Text>
          </Paper>
        </Grid.Col>
        <Grid.Col span={12} sm={4}>
          <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
            <IconDeviceDesktop color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
            <Text weight={600} size="sm">Objects</Text>
            <Text size="sm" color="dimmed">
              {preview?.structure?.objects?.length || 0} items
            </Text>
          </Paper>
        </Grid.Col>
      </Grid>

      {/* Action Buttons */}
      <Divider mb="md" />
      <Group position="center" spacing={theme.spacing.md}>
        <Button
          leftIcon={<IconEye />}
          onClick={() => window.open(`/environment-preview/${environmentId}`, '_blank')}
          size="md"
        >
          View Full Preview
        </Button>
        <Button
          variant="outline"
          leftIcon={<IconDownload />}
          onClick={handleDownload}
          size="md"
        >
          Download .rbxl
        </Button>
        <Button
          variant="outline"
          leftIcon={<IconCode />}
          onClick={handleDeployToRoblox}
          size="md"
        >
          Deploy to Roblox
        </Button>
      </Group>

      {/* Description */}
      {preview?.description && (
        <Box mt="lg">
          <Text size="sm" color="dimmed">
            {preview.description}
          </Text>
        </Box>
      )}
    </Card>
  );
};

export default EnvironmentPreview;