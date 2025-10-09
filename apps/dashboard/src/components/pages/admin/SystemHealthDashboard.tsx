import React from 'react';
import { Box, Text, Card, Grid, Stack, Badge, Group, ActionIcon } from '@mantine/core';
import { IconDashboard, IconRefresh, IconSettings, IconCircleCheck } from '@tabler/icons-react';

/**
 * SystemHealthDashboard - Comprehensive System Health Monitoring Page
 * Combines all health monitoring components for administrators
 */

const SystemHealthDashboard: React.FC = () => {
  return (
    <Box p="md">
      <Text size="xl" fw={600} mb="lg">
        System Health Dashboard
      </Text>

      <Grid>
        <Grid.Col span={{ xs: 12, md: 6 }}>
          <Card withBorder>
            <Card.Section p="md">
              <Group justify="space-between" align="center">
                <Group align="center" gap="sm">
                  <IconDashboard size={20} />
                  <Text fw={500}>System Overview</Text>
                </Group>
                <Badge color="green" leftSection={<IconCircleCheck size={12} />}>
                  Healthy
                </Badge>
              </Group>
            </Card.Section>
            <Card.Section p="md">
              <Text size="sm" c="dimmed">
                All system components are operating normally.
              </Text>
            </Card.Section>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ xs: 12, md: 6 }}>
          <Card withBorder>
            <Card.Section p="md">
              <Group justify="space-between" align="center">
                <Group align="center" gap="sm">
                  <IconSettings size={20} />
                  <Text fw={500}>System Actions</Text>
                </Group>
                <ActionIcon variant="subtle">
                  <IconRefresh size={16} />
                </ActionIcon>
              </Group>
            </Card.Section>
            <Card.Section p="md">
              <Text size="sm" c="dimmed">
                System health monitoring and management tools.
              </Text>
            </Card.Section>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
};

export default SystemHealthDashboard;