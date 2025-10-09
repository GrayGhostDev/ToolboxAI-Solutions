import { Box, Button, Text, Paper, Stack, Container, Card, Tabs } from '@mantine/core';
import React from 'react';
import { ButtonMigrationExample } from '../migration/examples/ButtonMigration';
import { CardMigrationExample } from '../migration/examples/CardMigration';
import { MantineMigrationGuide } from '../migration/MantineMigrationGuide';
import { useMigrationPlanner } from '../../hooks/useMigration';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`migration-tabpanel-${index}`}
      aria-labelledby={`migration-tab-${index}`}
      {...other}
    >
      {value === index && <Box p="md">{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `migration-tab-${index}`,
    'aria-controls': `migration-tabpanel-${index}`,
  };
}

export default function MigrationDemo() {
  const [value, setValue] = React.useState(0);
  const { getMigrationProgress, getNextComponents, getMigrationPlan } = useMigrationPlanner();

  const progress = getMigrationProgress();
  const nextComponents = getNextComponents();
  const plan = getMigrationPlan();

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container size="lg" py="xl">
      <Text size="xl" fw={700} mb="md">
        Mantine Migration Demo
      </Text>

      <Text size="md" c="dimmed" mb="xl">
        Interactive demonstration of the MUI to Mantine migration process
      </Text>

      {/* Migration Progress Summary */}
      <Paper withBorder p="md" mb="xl">
        <Text size="lg" fw={600} mb="md">
          Migration Progress
        </Text>
        <Box style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Box>
            <Text size="sm" c="dimmed">
              Total Components
            </Text>
            <Text size="xl" fw={700} c="blue">
              {progress.total}
            </Text>
          </Box>
          <Box>
            <Text size="sm" c="dimmed">
              Completed
            </Text>
            <Text size="xl" fw={700} c="green">
              {progress.completed}
            </Text>
          </Box>
          <Box>
            <Text size="sm" c="dimmed">
              In Progress
            </Text>
            <Text size="xl" fw={700} c="orange">
              {progress.inProgress}
            </Text>
          </Box>
          <Box>
            <Text size="sm" c="dimmed">
              Progress
            </Text>
            <Text size="xl" fw={700} c="cyan">
              {progress.completionPercentage.toFixed(1)}%
            </Text>
          </Box>
        </Box>
      </Paper>

      <Tabs value={value.toString()} onChange={(val) => handleChange({} as React.SyntheticEvent, parseInt(val || '0'))}>
        <Tabs.List>
          <Tabs.Tab value="0">Component Examples</Tabs.Tab>
          <Tabs.Tab value="1">Migration Guide</Tabs.Tab>
          <Tabs.Tab value="2">Migration Plan</Tabs.Tab>
          <Tabs.Tab value="3">Next Steps</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="0">
          <Text size="lg" fw={600} mb="md">
            Interactive Component Examples
          </Text>
          <Text size="md" c="dimmed" mb="xl">
            See side-by-side comparisons of MUI and Mantine components. Use the Migration Control Panel
            (bottom right) to switch between versions or enable comparison mode.
          </Text>

          <Box mt="xl">
            <Text size="md" fw={600} mb="md">
              Button Migration
            </Text>
            <ButtonMigrationExample />
          </Box>

          <Box mt="xl">
            <Text size="md" fw={600} mb="md">
              Card Migration
            </Text>
            <CardMigrationExample />
          </Box>
        </Tabs.Panel>

        <Tabs.Panel value="1">
          <MantineMigrationGuide />
        </Tabs.Panel>

        <Tabs.Panel value="2">
          <Text size="lg" fw={600} mb="md">
            Migration Plan Overview
          </Text>
          <Text size="md" c="dimmed" mb="xl">
            Comprehensive plan for migrating all components from MUI to Mantine.
          </Text>

          <Box mt="md">
            <Text size="md" fw={600} mb="md">
              Component Status
            </Text>
            <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
              {plan.map((component: any) => (
                <Paper
                  key={component.id}
                  p="md"
                  withBorder
                  bg={component.phase === 'complete' ? 'green.1' :
                      component.phase === 'development' ? 'orange.1' :
                      'gray.0'}
                >
                  <Text size="md" fw={700}>
                    {component.name}
                  </Text>
                  <Text size="sm" c="dimmed">
                    Phase: {component.phase} | Priority: {component.priority}
                  </Text>
                  {component.notes && (
                    <Text size="xs" c="dimmed" mt="xs">
                      {component.notes}
                    </Text>
                  )}
                </Paper>
              ))}
            </Box>
          </Box>
        </Tabs.Panel>

        <Tabs.Panel value="3">
          <Text size="lg" fw={600} mb="md">
            Next Components to Migrate
          </Text>
          <Text size="md" c="dimmed" mb="xl">
            These are the highest priority components ready for migration.
          </Text>

          <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
            {nextComponents.map((component: any) => (
              <Paper
                key={component.id}
                p="lg"
                withBorder
                style={{ borderWidth: 2, borderColor: 'var(--mantine-color-blue-4)' }}
                bg="blue.1"
              >
                <Text size="md" fw={600} mb="xs">
                  {component.name}
                </Text>
                <Text size="sm" style={{ opacity: 0.9 }}>
                  Priority: {component.priority}
                </Text>
                {component.notes && (
                  <Text size="sm" mt="xs" style={{ opacity: 0.8 }}>
                    {component.notes}
                  </Text>
                )}
              </Paper>
            ))}
          </Box>

          {nextComponents.length === 0 && (
            <Paper
              p="xl"
              withBorder
              ta="center"
              bg="green.1"
            >
              <Text size="md" fw={600} mb="xs">
                🎉 All Components Migrated!
              </Text>
              <Text size="md">
                Congratulations! You've successfully migrated all planned components to Mantine.
              </Text>
            </Paper>
          )}

          <Paper p="md" mt="xl" bg="cyan.1" withBorder>
            <Text size="md" fw={600} mb="xs">
              Development Tools
            </Text>
            <Text size="sm" c="dimmed">
              • Use the Migration Control Panel (bottom right) to test different versions
              • Set localStorage flag 'enableMantineMigration' to 'true' for global migration
              • Individual components can be controlled with 'migration-[component-id]' flags
            </Text>
          </Paper>
        </Tabs.Panel>
      </Tabs>
    </Container>
  );
}