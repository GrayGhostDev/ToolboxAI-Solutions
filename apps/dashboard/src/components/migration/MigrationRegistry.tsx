import React from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Badge,
  Progress,
  Group,
  Stack,
  Button,
  Table,
  ActionIcon,
  Code,
  Alert,
  Tabs,
  Card,
  Switch,
  Tooltip,
  rem
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconCheck,
  IconX,
  IconClock,
  IconEye,
  IconFlask,
  IconInfoCircle,
  IconTrendingUp,
  IconBrandReact,
  IconSettings
} from '@tabler/icons-react';
import { useMigration } from './MigrationWrapper';

export interface MigrationComponent {
  id: string;
  name: string;
  description: string;
  status: 'not-started' | 'in-progress' | 'completed' | 'testing';
  priority: 'low' | 'medium' | 'high' | 'critical';
  complexity: 'simple' | 'moderate' | 'complex';
  estimatedHours: number;
  actualHours?: number;
  mantineFeatures: string[];
  muiDependencies: string[];
  testCoverage: number;
  performanceGain?: string;
  notes?: string;
}

const MIGRATION_COMPONENTS: MigrationComponent[] = [
  {
    id: 'login-page',
    name: 'Login Component',
    description: 'Main authentication login form with validation and demo credentials',
    status: 'completed',
    priority: 'critical',
    complexity: 'moderate',
    estimatedHours: 8,
    actualHours: 6,
    mantineFeatures: [
      'TextInput with leftSection',
      'PasswordInput with built-in toggle',
      'Button with gradient variant',
      'Notifications for feedback',
      'Clickable demo credentials',
      'Enhanced accessibility'
    ],
    muiDependencies: [
      'TextField',
      'Button',
      'Alert',
      'Paper',
      'Typography',
      'InputAdornment',
      'IconButton'
    ],
    testCoverage: 95,
    performanceGain: '~15KB bundle reduction',
    notes: 'Successfully migrated with enhanced UX. Mantine version includes clickable demo credentials and better notifications.'
  },
  // Future components can be added here
  {
    id: 'dashboard-nav',
    name: 'Navigation Component',
    description: 'Main navigation sidebar with role-based menu items',
    status: 'not-started',
    priority: 'high',
    complexity: 'complex',
    estimatedHours: 12,
    mantineFeatures: [],
    muiDependencies: ['Drawer', 'List', 'ListItem', 'Collapse', 'Divider'],
    testCoverage: 0,
  },
  {
    id: 'data-table',
    name: 'Data Table Component',
    description: 'Reusable data table with sorting, filtering, and pagination',
    status: 'not-started',
    priority: 'medium',
    complexity: 'complex',
    estimatedHours: 16,
    mantineFeatures: [],
    muiDependencies: ['Table', 'TableContainer', 'TablePagination', 'Checkbox'],
    testCoverage: 0,
  },
  {
    id: 'form-builder',
    name: 'Dynamic Form Builder',
    description: 'Form builder for educational content creation',
    status: 'not-started',
    priority: 'medium',
    complexity: 'complex',
    estimatedHours: 20,
    mantineFeatures: [],
    muiDependencies: ['FormControl', 'FormLabel', 'Select', 'Autocomplete'],
    testCoverage: 0,
  },
];

export function MigrationRegistry() {
  const {
    migrationFlags,
    setComponentMigration,
    toggleGlobalMigration,
    getMigrationStats,
    isGlobalMigrationEnabled,
  } = useMigration();

  const stats = getMigrationStats();
  const registryStats = React.useMemo(() => {
    const completed = MIGRATION_COMPONENTS.filter(c => c.status === 'completed').length;
    const inProgress = MIGRATION_COMPONENTS.filter(c => c.status === 'in-progress').length;
    const testing = MIGRATION_COMPONENTS.filter(c => c.status === 'testing').length;
    const total = MIGRATION_COMPONENTS.length;
    const totalEstimatedHours = MIGRATION_COMPONENTS.reduce((sum, c) => sum + c.estimatedHours, 0);
    const completedHours = MIGRATION_COMPONENTS
      .filter(c => c.actualHours)
      .reduce((sum, c) => sum + (c.actualHours || 0), 0);

    return {
      completed,
      inProgress,
      testing,
      total,
      percentage: total > 0 ? (completed / total) * 100 : 0,
      totalEstimatedHours,
      completedHours,
    };
  }, []);

  const getStatusIcon = (status: MigrationComponent['status']) => {
    switch (status) {
      case 'completed':
        return <IconCheck size={16} color="green" />;
      case 'in-progress':
        return <IconClock size={16} color="orange" />;
      case 'testing':
        return <IconFlask size={16} color="blue" />;
      default:
        return <IconX size={16} color="gray" />;
    }
  };

  const getStatusColor = (status: MigrationComponent['status']) => {
    switch (status) {
      case 'completed': return 'green';
      case 'in-progress': return 'orange';
      case 'testing': return 'blue';
      default: return 'gray';
    }
  };

  const getPriorityColor = (priority: MigrationComponent['priority']) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      default: return 'gray';
    }
  };

  const handleToggleComponent = (componentId: string) => {
    const currentStatus = migrationFlags[componentId] || 'mui';
    const newStatus = currentStatus === 'mui' ? 'mantine' : 'mui';
    setComponentMigration(componentId, newStatus);

    notifications.show({
      title: 'Migration Updated',
      message: `${componentId} switched to ${newStatus.toUpperCase()}`,
      color: newStatus === 'mantine' ? 'green' : 'blue',
      icon: newStatus === 'mantine' ? <IconCheck size={rem(18)} /> : <IconBrandReact size={rem(18)} />,
    });
  };

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <div>
          <Group justify="space-between" align="flex-end" mb="md">
            <div>
              <Title order={1}>Migration Registry</Title>
              <Text size="lg" c="dimmed">
                Track progress of MUI to Mantine component migration
              </Text>
            </div>
            <Group>
              <Switch
                label="Global Mantine Migration"
                checked={isGlobalMigrationEnabled}
                onChange={(e) => toggleGlobalMigration(e.currentTarget.checked)}
                color="green"
              />
            </Group>
          </Group>

          <Alert icon={<IconInfoCircle />} color="blue" mb="xl">
            <Text fw={500}>Migration Strategy</Text>
            <Text size="sm" mt="xs">
              We're gradually migrating from Material-UI to Mantine to improve performance,
              reduce bundle size, and enhance developer experience. Each component is migrated
              individually with comprehensive testing.
            </Text>
          </Alert>
        </div>

        {/* Stats Dashboard */}
        <Paper withBorder p="xl" radius="md">
          <Group justify="space-between" align="flex-start">
            <div>
              <Text size="sm" c="dimmed" fw={500}>OVERALL PROGRESS</Text>
              <Title order={2} mt={rem(4)}>{registryStats.percentage.toFixed(1)}%</Title>
              <Progress
                value={registryStats.percentage}
                size="lg"
                radius="md"
                mt="md"
                color="green"
                style={{ width: rem(200) }}
              />
              <Text size="xs" c="dimmed" mt="xs">
                {registryStats.completed} of {registryStats.total} components completed
              </Text>
            </div>

            <Group gap="xl">
              <div style={{ textAlign: 'center' }}>
                <Text size="xl" fw={700} c="green">{registryStats.completed}</Text>
                <Text size="sm" c="dimmed">Completed</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <Text size="xl" fw={700} c="orange">{registryStats.inProgress}</Text>
                <Text size="sm" c="dimmed">In Progress</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <Text size="xl" fw={700} c="blue">{registryStats.testing}</Text>
                <Text size="sm" c="dimmed">Testing</Text>
              </div>
              <div style={{ textAlign: 'center' }}>
                <Text size="xl" fw={700} c="gray">{registryStats.total - registryStats.completed - registryStats.inProgress - registryStats.testing}</Text>
                <Text size="sm" c="dimmed">Not Started</Text>
              </div>
            </Group>

            <div style={{ textAlign: 'right' }}>
              <Text size="sm" c="dimmed" fw={500}>EFFORT TRACKING</Text>
              <Text size="lg" fw={600}>{registryStats.completedHours}h / {registryStats.totalEstimatedHours}h</Text>
              <Text size="xs" c="dimmed">Time invested / Estimated</Text>
            </div>
          </Group>
        </Paper>

        {/* Component Details */}
        <Tabs defaultValue="overview">
          <Tabs.List>
            <Tabs.Tab value="overview" leftSection={<IconTrendingUp size={16} />}>
              Overview
            </Tabs.Tab>
            <Tabs.Tab value="active" leftSection={<IconSettings size={16} />}>
              Active Testing
            </Tabs.Tab>
            <Tabs.Tab value="detailed" leftSection={<IconEye size={16} />}>
              Detailed View
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="md">
            <Stack gap="md">
              {MIGRATION_COMPONENTS.map((component) => (
                <Card key={component.id} withBorder p="md" radius="md">
                  <Group justify="space-between" wrap="nowrap">
                    <Group>
                      {getStatusIcon(component.status)}
                      <div>
                        <Group gap="xs" align="center">
                          <Text fw={600}>{component.name}</Text>
                          <Badge size="xs" color={getPriorityColor(component.priority)} variant="light">
                            {component.priority}
                          </Badge>
                          <Badge size="xs" variant="outline">
                            {component.complexity}
                          </Badge>
                        </Group>
                        <Text size="sm" c="dimmed" mt={rem(2)}>
                          {component.description}
                        </Text>
                        {component.notes && (
                          <Text size="xs" c="dimmed" mt={rem(4)} style={{ fontStyle: 'italic' }}>
                            {component.notes}
                          </Text>
                        )}
                      </div>
                    </Group>

                    <Group gap="md">
                      <div style={{ textAlign: 'center' }}>
                        <Text size="xs" c="dimmed">Estimated</Text>
                        <Text size="sm" fw={500}>{component.estimatedHours}h</Text>
                      </div>
                      {component.actualHours && (
                        <div style={{ textAlign: 'center' }}>
                          <Text size="xs" c="dimmed">Actual</Text>
                          <Text size="sm" fw={500} c="green">{component.actualHours}h</Text>
                        </div>
                      )}
                      {component.testCoverage > 0 && (
                        <div style={{ textAlign: 'center' }}>
                          <Text size="xs" c="dimmed">Coverage</Text>
                          <Text size="sm" fw={500} c="blue">{component.testCoverage}%</Text>
                        </div>
                      )}
                      <Badge color={getStatusColor(component.status)} variant="filled">
                        {component.status.replace('-', ' ')}
                      </Badge>
                    </Group>
                  </Group>

                  {component.performanceGain && (
                    <Group mt="sm" gap="xs">
                      <IconTrendingUp size={14} color="green" />
                      <Text size="xs" c="green" fw={500}>
                        Performance: {component.performanceGain}
                      </Text>
                    </Group>
                  )}
                </Card>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="active" pt="md">
            <Paper withBorder p="md">
              <Title order={3} mb="md">Active Component Testing</Title>
              <Text size="sm" c="dimmed" mb="lg">
                Toggle between MUI and Mantine versions for components in your current session.
                Changes are saved to localStorage and persist until reset.
              </Text>

              <Stack gap="sm">
                {MIGRATION_COMPONENTS
                  .filter(c => c.status === 'completed' || c.status === 'testing')
                  .map((component) => {
                    const currentVersion = migrationFlags[component.id] || 'mui';
                    const isActive = currentVersion === 'mantine';

                    return (
                      <Group key={component.id} justify="space-between" p="sm"
                             style={{ border: '1px solid var(--mantine-color-gray-3)', borderRadius: 'var(--mantine-radius-sm)' }}>
                        <div>
                          <Text fw={500}>{component.name}</Text>
                          <Text size="sm" c="dimmed">{component.description}</Text>
                        </div>
                        <Group>
                          <Badge color={isActive ? 'green' : 'blue'} variant="light">
                            {isActive ? 'Mantine' : 'MUI'}
                          </Badge>
                          <Tooltip label={`Switch to ${isActive ? 'MUI' : 'Mantine'}`}>
                            <ActionIcon
                              variant="light"
                              color={isActive ? 'blue' : 'green'}
                              onClick={() => handleToggleComponent(component.id)}
                            >
                              {isActive ? <IconBrandReact size={16} /> : <IconCheck size={16} />}
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Group>
                    );
                  })}
              </Stack>

              {MIGRATION_COMPONENTS.filter(c => c.status === 'completed' || c.status === 'testing').length === 0 && (
                <Text c="dimmed" ta="center" py="xl">
                  No components are currently available for testing.
                </Text>
              )}
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="detailed" pt="md">
            <Paper withBorder>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Component</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Priority</Table.Th>
                    <Table.Th>Complexity</Table.Th>
                    <Table.Th>Progress</Table.Th>
                    <Table.Th>Features</Table.Th>
                    <Table.Th>Dependencies</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {MIGRATION_COMPONENTS.map((component) => (
                    <Table.Tr key={component.id}>
                      <Table.Td>
                        <div>
                          <Text fw={500}>{component.name}</Text>
                          <Text size="xs" c="dimmed">{component.description}</Text>
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <Badge color={getStatusColor(component.status)}>
                          {component.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge color={getPriorityColor(component.priority)} variant="light">
                          {component.priority}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{component.complexity}</Text>
                      </Table.Td>
                      <Table.Td>
                        <div>
                          <Text size="sm">
                            {component.actualHours ? `${component.actualHours}h` : '0h'} / {component.estimatedHours}h
                          </Text>
                          {component.testCoverage > 0 && (
                            <Text size="xs" c="dimmed">
                              {component.testCoverage}% tested
                            </Text>
                          )}
                        </div>
                      </Table.Td>
                      <Table.Td>
                        <Stack gap={rem(2)}>
                          {component.mantineFeatures.slice(0, 2).map((feature) => (
                            <Code key={feature} size="xs">{feature}</Code>
                          ))}
                          {component.mantineFeatures.length > 2 && (
                            <Text size="xs" c="dimmed">
                              +{component.mantineFeatures.length - 2} more
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>
                      <Table.Td>
                        <Stack gap={rem(2)}>
                          {component.muiDependencies.slice(0, 2).map((dep) => (
                            <Code key={dep} size="xs" c="dimmed">{dep}</Code>
                          ))}
                          {component.muiDependencies.length > 2 && (
                            <Text size="xs" c="dimmed">
                              +{component.muiDependencies.length - 2} more
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Paper>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}

export default MigrationRegistry;