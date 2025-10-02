import { Box, Button, Text, Paper, Stack, Grid, Container, ActionIcon, Avatar, Card, List, Divider, TextInput, Select, Chip, Badge, Alert, Loader, Progress, Modal, Drawer, AppShell, Tabs, Menu, Tooltip, Checkbox, Radio, Switch, Slider, Skeleton, Table } from '@mantine/core';
import { Link } from '@tabler/icons-react';
import * as React from "react";

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

  return (
    <Box
      style={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        display: open ? 'block' : 'none'
      }}
    >
      <Alert
        color="blue"
        variant="filled"
        action={
          <Stack direction="row" gap="xs">
            <Button color="inherit" size="sm" onClick={decline}>Decline</Button>
            <Button color="inherit" size="sm" onClick={accept}>Accept</Button>
          </Stack>
        }
      >
        <Text color="white">
          We use cookies to operate and improve the service. See our{' '}
          <Link href="/cookies.html" target="_blank" rel="noopener noreferrer" color="inherit" underline="always">
            Cookie Policy
          </Link>.
        </Text>
      </Alert>
    </Box>
  );
}
