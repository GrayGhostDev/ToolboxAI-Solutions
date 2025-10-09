import React from 'react';
import {
  Card,
  Text,
  Button,
  Badge,
  Progress,
  Box,
  ActionIcon,
  Menu,
  Group,
  Stack,
  Flex,
} from '@mantine/core';
import {
  IconPlayerPlay as PlayIcon,
  IconDownload as DownloadIcon,
  IconTrash as DeleteIcon,
  IconDots as MoreIcon,
  IconCloudUpload as DeployIcon,
} from '@tabler/icons-react';
import { RobloxEnvironment } from '../services/robloxSync';
import { GenerationStatus } from '../store/slices/robloxSlice';

interface RobloxEnvironmentCardProps {
  environment: RobloxEnvironment;
  generationStatus?: GenerationStatus;
  onGenerate: (id: string) => void;
  onDeploy: (id: string) => void;
  onDownload: (id: string) => void;
  onDelete: (id: string) => void;
  onPreview: (id: string) => void;
}

export const RobloxEnvironmentCard: React.FC<RobloxEnvironmentCardProps> = ({
  environment,
  generationStatus,
  onGenerate,
  onDeploy,
  onDownload,
  onDelete,
  onPreview,
}) => {
  const [menuAnchor, setMenuAnchor] = React.useState<null | HTMLElement>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'green';
      case 'generating': return 'orange';
      case 'deployed': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'draft': return 'Draft';
      case 'generating': return 'Generating';
      case 'ready': return 'Ready';
      case 'deployed': return 'Deployed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const isGenerating = generationStatus?.status === 'generating';
  const canGenerate = environment.status === 'draft';
  const canDeploy = environment.status === 'ready' && environment.downloadUrl;
  const canDownload = environment.status === 'ready' && environment.downloadUrl;

  return (
    <Card h="100%" style={{ display: 'flex', flexDirection: 'column' }}>
      <Card.Section p="lg" style={{ flexGrow: 1 }}>
        <Flex justify="space-between" align="flex-start" mb="xs">
          <Text size="lg" fw={600} truncate>
            {environment.name}
          </Text>
          <Menu shadow="md" width={200} opened={Boolean(menuAnchor)} onChange={setMenuAnchor}>
            <Menu.Target>
              <ActionIcon
                size="sm"
                variant="subtle"
                onClick={(e) => setMenuAnchor(e.currentTarget)}
              >
                <MoreIcon size={16} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item
                leftSection={<DeleteIcon size={16} />}
                color="red"
                onClick={() => {
                  onDelete(environment.id);
                  setMenuAnchor(null);
                }}
              >
                Delete
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Flex>

        <Text c="dimmed" mb="sm">
          {environment.theme} • {environment.mapType.replace('_', ' ')}
        </Text>

        <Box mb="md">
          <Badge
            color={getStatusColor(environment.status)}
            size="sm"
            variant="light"
          >
            {getStatusText(environment.status)}
          </Badge>
        </Box>

        {environment.spec.learning_objectives && (
          <Box mb="md">
            <Text size="sm" c="dimmed" mb="xs">
              Learning Objectives:
            </Text>
            <Text size="sm">
              {environment.spec.learning_objectives.join(', ')}
            </Text>
          </Box>
        )}

        {isGenerating && generationStatus && (
          <Stack gap="xs" mb="md">
            <Text size="sm" c="dimmed">
              {generationStatus.message}
            </Text>
            <Progress
              value={generationStatus.progress || 0}
              color="blue"
              size="sm"
            />
            <Text size="xs" c="dimmed">
              {generationStatus.progress}% • {generationStatus.stage}
            </Text>
          </Stack>
        )}

        {environment.status === 'error' && generationStatus?.error && (
          <Text size="sm" c="red">
            Error: {generationStatus.error}
          </Text>
        )}
      </Card.Section>

      <CardActions>
        {canGenerate && (
          <Button
            startIcon={<PlayIcon />}
            onClick={() => onGenerate(environment.id)}
            variant="contained"
            color="primary"
          >
            Generate
          </Button>
        )}

        {canDownload && (
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => onDownload(environment.id)}
            size="small"
          >
            Download
          </Button>
        )}

        {canDeploy && (
          <Button
            startIcon={<DeployIcon />}
            onClick={() => onDeploy(environment.id)}
            size="small"
            variant="outlined"
          >
            Deploy
          </Button>
        )}

        {environment.previewUrl && (
          <Button
            onClick={() => onPreview(environment.id)}
            size="small"
          >
            Preview
          </Button>
        )}
      </CardActions>

      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => {
          onDelete(environment.id);
          setMenuAnchor(null);
        }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default RobloxEnvironmentCard;
