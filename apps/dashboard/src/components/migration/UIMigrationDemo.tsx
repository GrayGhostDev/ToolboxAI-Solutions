import React, { useState } from 'react';

// Material-UI imports
import {
  Box as MuiBox,
  Card as MuiCard,
  CardContent as MuiCardContent,
  TextField as MuiTextField,
  Button as MuiButton,
  Typography as MuiTypography,
  Stack as MuiStack,
  Alert as MuiAlert,
  Chip as MuiChip,
  Switch as MuiSwitch,
  FormControlLabel as MuiFormControlLabel,
} from '@mui/material';
import { Email as MuiEmailIcon, Save as MuiSaveIcon } from '@mui/icons-material';

// Mantine imports
import {
  Box,
  Card,
  TextInput,
  Button,
  Text,
  Title,
  Stack,
  Alert,
  Badge,
  Switch,
  Group,
  Container,
  SimpleGrid,
  Paper,
  Divider,
} from '@mantine/core';
import { IconMail, IconDeviceFloppy, IconInfoCircle } from '@tabler/icons-react';

interface DemoFormData {
  name: string;
  email: string;
  notifications: boolean;
}

export function UIMigrationDemo() {
  const [muiData, setMuiData] = useState<DemoFormData>({
    name: '',
    email: '',
    notifications: false,
  });

  const [mantineData, setMantineData] = useState<DemoFormData>({
    name: '',
    email: '',
    notifications: false,
  });

  const [showAlert, setShowAlert] = useState(false);

  const handleMuiChange = (field: keyof DemoFormData) => (event: any) => {
    const value = field === 'notifications' ? event.target.checked : event.target.value;
    setMuiData(prev => ({ ...prev, [field]: value }));
  };

  const handleMantineChange = (field: keyof DemoFormData) => (value: any) => {
    setMantineData(prev => ({ ...prev, [field]: value }));
  };

  const handleMuiSubmit = () => {
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  const handleMantineSubmit = () => {
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <div style={{ textAlign: 'center' }}>
          <Title order={1} mb="md">UI Framework Migration Demo</Title>
          <Text size="lg" c="dimmed">
            Side-by-side comparison of Material-UI vs Mantine implementations
          </Text>
        </div>

        {showAlert && (
          <Alert icon={<IconInfoCircle />} color="blue" onClose={() => setShowAlert(false)}>
            Form submitted successfully! This demo shows identical functionality with different UI frameworks.
          </Alert>
        )}

        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl">
          {/* Material-UI Implementation */}
          <div>
            <MuiCard elevation={3} sx={{ height: '100%' }}>
              <MuiCardContent>
                <MuiBox mb={3} textAlign="center" bgcolor="primary.main" color="white" p={2} borderRadius={1}>
                  <MuiTypography variant="h5" fontWeight={600}>
                    Material-UI
                  </MuiTypography>
                  <MuiChip
                    label="Current Implementation"
                    size="small"
                    sx={{ mt: 1, bgcolor: 'white', color: 'primary.main' }}
                  />
                </MuiBox>

                <MuiStack spacing={3}>
                  <MuiTextField
                    fullWidth
                    label="Full Name"
                    value={muiData.name}
                    onChange={handleMuiChange('name')}
                    variant="outlined"
                    helperText="Enter your full name"
                  />

                  <MuiTextField
                    fullWidth
                    label="Email Address"
                    type="email"
                    value={muiData.email}
                    onChange={handleMuiChange('email')}
                    variant="outlined"
                    helperText="We'll never share your email"
                    InputProps={{
                      startAdornment: <MuiEmailIcon sx={{ mr: 1, color: 'action.active' }} />,
                    }}
                  />

                  <MuiFormControlLabel
                    control={
                      <MuiSwitch
                        checked={muiData.notifications}
                        onChange={handleMuiChange('notifications')}
                        color="primary"
                      />
                    }
                    label="Enable email notifications"
                  />

                  <MuiAlert severity="info" sx={{ mt: 2 }}>
                    Material-UI uses the <code>sx</code> prop for styling and theme integration.
                  </MuiAlert>

                  <MuiButton
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={<MuiSaveIcon />}
                    onClick={handleMuiSubmit}
                    sx={{ mt: 2, textTransform: 'none', fontWeight: 600 }}
                  >
                    Save Settings (MUI)
                  </MuiButton>

                  <MuiBox mt={2}>
                    <MuiTypography variant="body2" color="text.secondary">
                      Form Data: {JSON.stringify(muiData, null, 2)}
                    </MuiTypography>
                  </MuiBox>
                </MuiStack>
              </MuiCardContent>
            </MuiCard>
          </div>

          {/* Mantine Implementation */}
          <div>
            <Card shadow="md" radius="md" withBorder style={{ height: '100%' }}>
              <Box mb="lg" style={{ textAlign: 'center', background: 'var(--mantine-color-blue-6)', color: 'white', padding: 'var(--mantine-spacing-md)', borderRadius: 'var(--mantine-radius-sm)' }}>
                <Title order={3} fw={600}>
                  Mantine
                </Title>
                <Badge variant="filled" color="white" c="blue" mt="xs">
                  New Implementation
                </Badge>
              </Box>

              <Stack gap="lg">
                <TextInput
                  label="Full Name"
                  value={mantineData.name}
                  onChange={(event) => handleMantineChange('name')(event.currentTarget.value)}
                  description="Enter your full name"
                />

                <TextInput
                  label="Email Address"
                  type="email"
                  value={mantineData.email}
                  onChange={(event) => handleMantineChange('email')(event.currentTarget.value)}
                  description="We'll never share your email"
                  leftSection={<IconMail size={16} />}
                />

                <Group justify="space-between">
                  <Text size="sm">Enable email notifications</Text>
                  <Switch
                    checked={mantineData.notifications}
                    onChange={(event) => handleMantineChange('notifications')(event.currentTarget.checked)}
                    color="blue"
                  />
                </Group>

                <Alert variant="light" color="blue" icon={<IconInfoCircle />}>
                  Mantine uses CSS variables and <code>style</code> prop for custom styling.
                </Alert>

                <Button
                  fullWidth
                  size="md"
                  leftSection={<IconDeviceFloppy size={16} />}
                  onClick={handleMantineSubmit}
                  gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                  variant="gradient"
                >
                  Save Settings (Mantine)
                </Button>

                <Paper p="xs" withBorder>
                  <Text size="xs" c="dimmed">
                    Form Data: {JSON.stringify(mantineData, null, 2)}
                  </Text>
                </Paper>
              </Stack>
            </Card>
          </div>
        </SimpleGrid>

        {/* Comparison Table */}
        <Paper withBorder p="lg" mt="xl">
          <Title order={3} mb="md">Key Differences Summary</Title>
          <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
            <div>
              <Title order={5} c="blue">Styling</Title>
              <Text size="sm" mt="xs">
                <strong>MUI:</strong> sx prop, theme functions<br />
                <strong>Mantine:</strong> CSS variables, style prop
              </Text>
            </div>
            <div>
              <Title order={5} c="green">Bundle Size</Title>
              <Text size="sm" mt="xs">
                <strong>MUI:</strong> ~90kb gzipped<br />
                <strong>Mantine:</strong> ~45kb gzipped
              </Text>
            </div>
            <div>
              <Title order={5} c="orange">API Design</Title>
              <Text size="sm" mt="xs">
                <strong>MUI:</strong> More verbose, explicit<br />
                <strong>Mantine:</strong> Simpler, opinionated
              </Text>
            </div>
          </SimpleGrid>
        </Paper>

        <Alert icon={<IconInfoCircle />} color="teal">
          <Text fw={500}>Migration Strategy</Text>
          <Text size="sm" mt="xs">
            Both frameworks can coexist in the same application. Start by migrating new components to Mantine,
            then gradually convert existing components. The functionality is nearly identical, but the API
            and styling approaches differ.
          </Text>
        </Alert>
      </Stack>
    </Container>
  );
}