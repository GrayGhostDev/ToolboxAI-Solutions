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
import { type RobloxEnvironment } from '../services/robloxSync';
import { type GenerationStatus } from '../store/slices/robloxSlice';

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

      <Card.Section p="md" pt={0}>
        <Group gap="sm" wrap="wrap">
          {canGenerate && (
            <Button
              leftSection={<PlayIcon size={16} />}
              onClick={() => onGenerate(environment.id)}
              variant="filled"
              color="blue"
              size="sm"
            >
              Generate
            </Button>
          )}

          {canDownload && (
            <Button
              leftSection={<DownloadIcon size={16} />}
              onClick={() => onDownload(environment.id)}
              variant="light"
              size="sm"
            >
              Download
            </Button>
          )}

          {canDeploy && (
            <Button
              leftSection={<DeployIcon size={16} />}
              onClick={() => onDeploy(environment.id)}
              variant="outline"
              size="sm"
            >
              Deploy
            </Button>
          )}

          {environment.previewUrl && (
            <Button
              onClick={() => onPreview(environment.id)}
              variant="subtle"
              size="sm"
            >
              Preview
            </Button>
          )}
        </Group>
      </Card.Section>
    </Card>
  );
};

export default RobloxEnvironmentCard;
