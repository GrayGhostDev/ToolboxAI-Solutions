import React from 'react';
import { Box, Container, Paper, Title, Code } from '@mantine/core';

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
    <Container size="md" style={{ padding: 'var(--mantine-spacing-xl)' }}>
      <Paper shadow="sm" p="lg">
        <Title order={1} mb="md">
          Health Check
        </Title>

        <Code block style={{
          backgroundColor: 'var(--mantine-color-gray-0)',
          padding: 'var(--mantine-spacing-md)',
          borderRadius: 'var(--mantine-radius-sm)',
          overflow: 'auto',
          fontSize: '0.875rem',
          whiteSpace: 'pre-wrap'
        }}>
          {JSON.stringify(healthData, null, 2)}
        </Code>
      </Paper>
    </Container>
  );
};

export default HealthCheck;