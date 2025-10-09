import { Modal, Button, Text, Stack, Group, Checkbox, Alert } from '@mantine/core';
import * as React from 'react';
import { recordConsent } from '../../services/api';
import { useAppSelector } from '../../store';

interface Props {
  opened: boolean;
  onClose: (accepted: boolean) => void;
}

export function ConsentModal({ opened, onClose }: Props) {
  const [coppaChecked, setCoppaChecked] = React.useState(false);
  const [ferpaChecked, setFerpaChecked] = React.useState(false);
  const [gdprChecked, setGdprChecked] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const userId = useAppSelector((s) => s.user.userId);

  const allChecked = coppaChecked && ferpaChecked && gdprChecked;

  const handleAccept = async () => {
    if (!allChecked || !userId) return;

    setLoading(true);
    try {
      await Promise.all([
        recordConsent('coppa', userId),
        recordConsent('ferpa', userId),
        recordConsent('gdpr', userId),
      ]);
      onClose(true);
    } catch (error) {
      console.error('Failed to record consent:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={() => onClose(false)}
      title="Parental Consent & Privacy Agreement"
      size="md"
    >
      <Stack gap="md">
        <Alert color="blue">
          To ensure the safety and privacy of students, we require parental consent in compliance
          with educational privacy laws.
        </Alert>

        <Text size="sm" fw={600}>
          Please review and accept the following:
        </Text>

        <Stack gap="sm">
          <Checkbox
            checked={coppaChecked}
            onChange={(event) => setCoppaChecked(event.currentTarget.checked)}
            label={
              <Stack gap="xs">
                <Text size="sm" fw={500}>
                  COPPA Compliance (Children's Online Privacy Protection Act)
                </Text>
                <Text size="xs" c="dimmed">
                  I am a parent/guardian and consent to my child's participation in accordance with
                  COPPA regulations for children under 13.
                </Text>
              </Stack>
            }
          />

          <Checkbox
            checked={ferpaChecked}
            onChange={(event) => setFerpaChecked(event.currentTarget.checked)}
            label={
              <Stack gap="xs">
                <Text size="sm" fw={500}>
                  FERPA Compliance (Family Educational Rights and Privacy Act)
                </Text>
                <Text size="xs" c="dimmed">
                  I understand and consent to the educational record keeping and sharing practices
                  as outlined in our FERPA policy.
                </Text>
              </Stack>
            }
          />

          <Checkbox
            checked={gdprChecked}
            onChange={(event) => setGdprChecked(event.currentTarget.checked)}
            label={
              <Stack gap="xs">
                <Text size="sm" fw={500}>
                  GDPR Compliance (General Data Protection Regulation)
                </Text>
                <Text size="xs" c="dimmed">
                  I consent to the processing of personal data in accordance with GDPR requirements
                  and understand my rights regarding data protection.
                </Text>
              </Stack>
            }
          />
        </Stack>

        <Text size="xs" c="dimmed">
          By accepting, you confirm that you have read and understood our
          <a href="/privacy.html" target="_blank" rel="noopener noreferrer"> Privacy Policy</a>
          &nbsp;and
          <a href="/terms.html" target="_blank" rel="noopener noreferrer"> Terms of Service</a>.
          You can withdraw consent at any time through your account settings.
        </Text>

        <Group justify="flex-end" gap="sm">
          <Button variant="outline" onClick={() => onClose(false)}>
            Cancel
          </Button>
          <Button
            disabled={!allChecked || loading}
            loading={loading}
            onClick={handleAccept}
          >
            {loading ? 'Processing...' : 'Accept & Continue'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}