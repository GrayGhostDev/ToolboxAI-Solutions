import { Notification, Button, Group, Anchor } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import * as React from 'react';

export default function CookieBanner() {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const consent = localStorage.getItem('cookie_consent');
      if (!consent) setOpen(true);
    }
  }, []);

  const accept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    setOpen(false);
  };

  const decline = () => {
    localStorage.setItem('cookie_consent', 'declined');
    setOpen(false);
  };

  React.useEffect(() => {
    if (open) {
      notifications.show({
        id: 'cookie-consent',
        title: 'Cookie Consent',
        message: (
          <>
            We use cookies to operate and improve the service. See our{' '}
            <Anchor href="/cookies.html" target="_blank" rel="noopener noreferrer" c="inherit">
              Cookie Policy
            </Anchor>
            .
            <Group gap="sm" mt="sm">
              <Button variant="outline" size="xs" onClick={decline}>
                Decline
              </Button>
              <Button size="xs" onClick={accept}>
                Accept
              </Button>
            </Group>
          </>
        ),
        color: 'blue',
        autoClose: false,
        position: 'bottom-center',
        withCloseButton: false,
      });
    }
  }, [open]);

  // This component now uses Mantine's notification system
  return null;
}
