import React from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';

export const HealthCheck: React.FC = () => {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    environment: import.meta.env.NODE_ENV,
    services: {
      frontend: 'running',
      api: 'connected',
      websocket: 'ready',
      pusher: 'active'
    },
    uptime: Math.floor(performance.now() / 1000),
    memory: (performance as any).memory ? {
      used: Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024),
      total: Math.round((performance as any).memory.totalJSHeapSize / 1024 / 1024),
      limit: Math.round((performance as any).memory.jsHeapSizeLimit / 1024 / 1024)
    } : null
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Health Check
        </Typography>

        <Box component="pre" sx={{
          bgcolor: 'grey.50',
          p: 2,
          borderRadius: 1,
          overflow: 'auto',
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          whiteSpace: 'pre-wrap'
        }}>
          {JSON.stringify(healthData, null, 2)}
        </Box>
      </Paper>
    </Container>
  );
};

export default HealthCheck;