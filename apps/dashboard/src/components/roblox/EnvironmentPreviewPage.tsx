/**
 * Environment Preview Page
 * Full-page view for environment previews
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Text, Button, Container, Title } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import EnvironmentPreview from './EnvironmentPreview';

const EnvironmentPreviewPage: React.FunctionComponent<Record<string, any>> = () => {
  const { environmentId } = useParams<{ environmentId: string }>();
  const navigate = useNavigate();

  if (!environmentId) {
    return (
      <Container size="md" mt="xl">
        <Title order={1} c="red">
          Environment ID not found
        </Title>
        <Button
          variant="filled"
          leftSection={<IconArrowLeft size={16} />}
          onClick={() => navigate('/')}
          mt="md"
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  return (
    <Box style={{ minHeight: '100vh' }}>
      {/* Header */}
      <Box p="md" style={{ borderBottom: '1px solid #e0e0e0' }}>
        <Button
          leftSection={<IconArrowLeft size={16} />}
          onClick={() => navigate(-1)}
          mb="md"
          variant="subtle"
        >
          Back
        </Button>
        <Title order={1}>
          Environment Preview
        </Title>
        <Text c="dimmed">
          Preview your Roblox educational environment
        </Text>
      </Box>

      {/* Environment Preview */}
      <Box p="md">
        <EnvironmentPreview
          environmentId={environmentId}
          onClose={() => navigate(-1)}
        />
      </Box>
    </Box>
  );
};

export default EnvironmentPreviewPage;
