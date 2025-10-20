import { Alert, Card, Stack, Text } from '@mantine/core';

export interface SystemSettingsPanelProps {
  readonly?: boolean;
}

export function SystemSettingsPanel({ readonly = false }: SystemSettingsPanelProps) {
  return (
    <Card withBorder radius="md" shadow="sm">
      <Stack gap="sm">
        <Text size="lg" fw={600}>
          System Settings
        </Text>
        <Alert color="blue" variant="light">
          {readonly
            ? 'System settings are currently in read-only mode. Administrative updates will be restored soon.'
            : 'The advanced system settings console is being refreshed. Please check back shortly for the updated experience.'}
        </Alert>
      </Stack>
    </Card>
  );
}

export default SystemSettingsPanel;
