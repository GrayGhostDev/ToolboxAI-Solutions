import React from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Code,
  Divider,
  Stack,
  Table,
  Badge,
  Alert,
  Tabs,
  ScrollArea,
  Group
} from '@mantine/core';
import { IconInfoCircle, IconCode, IconArrowRight } from '@tabler/icons-react';

export function MantineMigrationGuide() {
  const componentMappings = [
    {
      mui: 'Box',
      mantine: 'Box',
      notes: 'Similar API, use style prop instead of sx',
      difficulty: 'Easy'
    },
    {
      mui: 'Card',
      mantine: 'Card',
      notes: 'Similar structure, use children instead of CardContent',
      difficulty: 'Easy'
    },
    {
      mui: 'TextField',
      mantine: 'TextInput',
      notes: 'Different prop names: value/onChange similar, helperText → description',
      difficulty: 'Medium'
    },
    {
      mui: 'Button',
      mantine: 'Button',
      notes: 'Very similar API, variant names slightly different',
      difficulty: 'Easy'
    },
    {
      mui: 'Typography',
      mantine: 'Text / Title',
      notes: 'Use Text for body text, Title for headings with order prop',
      difficulty: 'Medium'
    },
    {
      mui: 'Stack',
      mantine: 'Stack',
      notes: 'Similar API, use gap instead of spacing',
      difficulty: 'Easy'
    },
    {
      mui: 'Paper',
      mantine: 'Paper',
      notes: 'Similar API, elevation → shadow',
      difficulty: 'Easy'
    },
    {
      mui: 'Alert',
      mantine: 'Alert',
      notes: 'Similar API, severity → color',
      difficulty: 'Easy'
    },
    {
      mui: 'InputAdornment',
      mantine: 'leftSection/rightSection',
      notes: 'Built into input components as props',
      difficulty: 'Medium'
    },
    {
      mui: 'IconButton',
      mantine: 'ActionIcon',
      notes: 'Similar functionality, different component name',
      difficulty: 'Easy'
    }
  ];

  const styleComparisons = [
    {
      aspect: 'Styling Approach',
      mui: 'sx prop with CSS-in-JS',
      mantine: 'style prop with CSS or Emotion',
      example: 'sx={{ mt: 2 }} → style={{ marginTop: "var(--mantine-spacing-md)" }}'
    },
    {
      aspect: 'Theme Access',
      mui: 'theme.spacing(), theme.palette',
      mantine: 'CSS variables --mantine-*',
      example: 'theme.spacing(2) → var(--mantine-spacing-md)'
    },
    {
      aspect: 'Colors',
      mui: 'primary.main, secondary.main',
      mantine: 'blue.6, red.5 or custom colors',
      example: 'color="primary" → color="blue" or c="blue.6"'
    },
    {
      aspect: 'Responsive',
      mui: 'theme.breakpoints.up("md")',
      mantine: 'Built-in responsive props or CSS',
      example: 'display={{ xs: "none", md: "block" }}'
    }
  ];

  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1} mb="md">Mantine UI Migration Guide</Title>
          <Text size="lg" c="dimmed">
            A comprehensive guide for migrating from Material-UI to Mantine UI
          </Text>
        </div>

        <Alert icon={<IconInfoCircle />} color="blue">
          <Text fw={500}>Migration Strategy</Text>
          <Text size="sm" mt="xs">
            This guide shows side-by-side comparisons and migration patterns. Both UI libraries can coexist
            during migration, allowing for gradual component-by-component migration.
          </Text>
        </Alert>

        <Tabs defaultValue="components">
          <Tabs.List>
            <Tabs.Tab value="components" leftSection={<IconCode size={16} />}>
              Component Mapping
            </Tabs.Tab>
            <Tabs.Tab value="styling" leftSection={<IconArrowRight size={16} />}>
              Styling Migration
            </Tabs.Tab>
            <Tabs.Tab value="examples" leftSection={<IconCode size={16} />}>
              Code Examples
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="components" pt="md">
            <Paper withBorder p="md">
              <Title order={3} mb="md">Component Mappings</Title>
              <ScrollArea>
                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Material-UI</Table.Th>
                      <Table.Th>Mantine</Table.Th>
                      <Table.Th>Migration Notes</Table.Th>
                      <Table.Th>Difficulty</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {componentMappings.map((mapping) => (
                      <Table.Tr key={mapping.mui}>
                        <Table.Td>
                          <Code>{mapping.mui}</Code>
                        </Table.Td>
                        <Table.Td>
                          <Code>{mapping.mantine}</Code>
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm">{mapping.notes}</Text>
                        </Table.Td>
                        <Table.Td>
                          <Badge
                            color={
                              mapping.difficulty === 'Easy' ? 'green' :
                              mapping.difficulty === 'Medium' ? 'yellow' : 'red'
                            }
                            variant="light"
                          >
                            {mapping.difficulty}
                          </Badge>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="styling" pt="md">
            <Paper withBorder p="md">
              <Title order={3} mb="md">Styling Approach Comparison</Title>
              <ScrollArea>
                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Aspect</Table.Th>
                      <Table.Th>Material-UI</Table.Th>
                      <Table.Th>Mantine</Table.Th>
                      <Table.Th>Example</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {styleComparisons.map((comparison) => (
                      <Table.Tr key={comparison.aspect}>
                        <Table.Td>
                          <Text fw={500}>{comparison.aspect}</Text>
                        </Table.Td>
                        <Table.Td>
                          <Code>{comparison.mui}</Code>
                        </Table.Td>
                        <Table.Td>
                          <Code>{comparison.mantine}</Code>
                        </Table.Td>
                        <Table.Td>
                          <Code>{comparison.example}</Code>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="examples" pt="md">
            <Stack gap="md">
              <Paper withBorder p="md">
                <Title order={4} mb="md">Input Field Migration</Title>
                <Group grow align="flex-start">
                  <div>
                    <Text fw={500} mb="xs" c="blue">Material-UI</Text>
                    <Code block>
{`<TextField
  fullWidth
  name="email"
  label="Email"
  value={email}
  onChange={handleChange}
  helperText="Enter your email"
  InputProps={{
    startAdornment: (
      <InputAdornment position="start">
        <Email />
      </InputAdornment>
    ),
  }}
  sx={{ mb: 2 }}
/>`}
                    </Code>
                  </div>
                  <div>
                    <Text fw={500} mb="xs" c="green">Mantine</Text>
                    <Code block>
{`<TextInput
  label="Email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  description="Enter your email"
  leftSection={<IconMail size={16} />}
  style={{ marginBottom: 'var(--mantine-spacing-md)' }}
/>`}
                    </Code>
                  </div>
                </Group>
              </Paper>

              <Paper withBorder p="md">
                <Title order={4} mb="md">Button Migration</Title>
                <Group grow align="flex-start">
                  <div>
                    <Text fw={500} mb="xs" c="blue">Material-UI</Text>
                    <Code block>
{`<Button
  variant="contained"
  color="primary"
  fullWidth
  size="large"
  disabled={loading}
  sx={{
    borderRadius: 2,
    textTransform: 'none',
    fontWeight: 600
  }}
>
  Submit
</Button>`}
                    </Code>
                  </div>
                  <div>
                    <Text fw={500} mb="xs" c="green">Mantine</Text>
                    <Code block>
{`<Button
  variant="filled"
  color="blue"
  fullWidth
  size="md"
  loading={loading}
  radius="md"
  fw={600}
>
  Submit
</Button>`}
                    </Code>
                  </div>
                </Group>
              </Paper>

              <Paper withBorder p="md">
                <Title order={4} mb="md">Layout Migration</Title>
                <Group grow align="flex-start">
                  <div>
                    <Text fw={500} mb="xs" c="blue">Material-UI</Text>
                    <Code block>
{`<Box
  sx={{
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    p: 3,
    bgcolor: 'background.paper',
    borderRadius: 2,
    boxShadow: 1
  }}
>
  <Typography variant="h5">
    Title
  </Typography>
  <Typography variant="body1">
    Content
  </Typography>
</Box>`}
                    </Code>
                  </div>
                  <div>
                    <Text fw={500} mb="xs" c="green">Mantine</Text>
                    <Code block>
{`<Paper
  p="lg"
  radius="md"
  shadow="sm"
  withBorder
>
  <Stack gap="md">
    <Title order={3}>
      Title
    </Title>
    <Text>
      Content
    </Text>
  </Stack>
</Paper>`}
                    </Code>
                  </div>
                </Group>
              </Paper>
            </Stack>
          </Tabs.Panel>
        </Tabs>

        <Paper withBorder p="md">
          <Title order={3} mb="md">Migration Checklist</Title>
          <Stack gap="xs">
            <Text>✅ Install Mantine packages</Text>
            <Text>✅ Set up MantineProvider with theme</Text>
            <Text>✅ Configure notifications system</Text>
            <Text>⏳ Migrate components one by one</Text>
            <Text>⏳ Update styling approach</Text>
            <Text>⏳ Test responsive behavior</Text>
            <Text>⏳ Update tests for new components</Text>
            <Text>⏳ Remove Material-UI dependencies</Text>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}