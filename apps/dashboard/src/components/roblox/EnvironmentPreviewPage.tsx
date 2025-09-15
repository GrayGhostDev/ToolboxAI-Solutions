/**
 * Environment Preview Page
 * Full-page view for environment previews
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Button, Container } from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import EnvironmentPreview from './EnvironmentPreview';

const EnvironmentPreviewPage: React.FC = () => {
  const { environmentId } = useParams<{ environmentId: string }>();
  const navigate = useNavigate();

  if (!environmentId) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography variant="h4" color="error">
          Environment ID not found
        </Typography>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          sx={{ mb: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Environment Preview
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Preview your Roblox educational environment
        </Typography>
      </Box>

      {/* Environment Preview */}
      <Box sx={{ p: 2 }}>
        <EnvironmentPreview
          environmentId={environmentId}
          onClose={() => navigate(-1)}
        />
      </Box>
    </Box>
  );
};

export default EnvironmentPreviewPage;
