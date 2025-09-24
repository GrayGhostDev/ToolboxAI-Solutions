import React from 'react';
import {
  Card as MuiCard,
  CardContent,
  CardActions,
  Typography,
  Button as MuiButton,
} from '@mui/material';
import {
  Card as MantineCard,
  Text,
  Button as MantineButton,
  Group,
  Stack,
} from '@mantine/core';
import { MigrationWrapper } from '../MigrationWrapper';

interface CardProps {
  title: string;
  content: string;
  actions?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  }[];
  elevation?: number;
  children?: React.ReactNode;
}

// MUI version of the card
const MuiCardVersion: React.FC<CardProps> = ({
  title,
  content,
  actions,
  elevation = 2,
  children,
}) => (
  <MuiCard elevation={elevation} sx={{ borderRadius: 2 }}>
    <CardContent>
      <Typography variant="h6" component="h2" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {content}
      </Typography>
      {children}
    </CardContent>
    {actions && actions.length > 0 && (
      <CardActions sx={{ padding: 2, paddingTop: 0 }}>
        {actions.map((action, index) => (
          <MuiButton
            key={index}
            size="small"
            variant={action.variant === 'primary' ? 'contained' : 'text'}
            onClick={action.onClick}
            sx={{ textTransform: 'none' }}
          >
            {action.label}
          </MuiButton>
        ))}
      </CardActions>
    )}
  </MuiCard>
);

// Mantine version of the card
const MantineCardVersion: React.FC<CardProps> = ({
  title,
  content,
  actions,
  elevation = 2,
  children,
}) => {
  const shadow = elevation <= 1 ? 'xs' : elevation <= 3 ? 'sm' : elevation <= 6 ? 'md' : 'lg';

  return (
    <MantineCard shadow={shadow} padding="lg" radius="md" withBorder>
      <Stack gap="md">
        <Text fw={600} size="lg">
          {title}
        </Text>
        <Text size="sm" c="dimmed">
          {content}
        </Text>
        {children}
        {actions && actions.length > 0 && (
          <Group justify="flex-end" mt="md">
            {actions.map((action, index) => (
              <MantineButton
                key={index}
                size="sm"
                variant={action.variant === 'primary' ? 'filled' : 'subtle'}
                onClick={action.onClick}
              >
                {action.label}
              </MantineButton>
            ))}
          </Group>
        )}
      </Stack>
    </MantineCard>
  );
};

// Migrated card component
export const MigratedCard: React.FC<CardProps> = (props) => {
  return (
    <MigrationWrapper
      componentId="card"
      muiComponent={<MuiCardVersion {...props} />}
      mantineComponent={<MantineCardVersion {...props} />}
    />
  );
};

// Example usage component
export const CardMigrationExample: React.FC = () => {
  const handleAction = (action: string) => {
    alert(`${action} clicked!`);
  };

  return (
    <div style={{ padding: '20px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
      <MigratedCard
        title="Simple Card"
        content="This is a basic card with just title and content. No actions or additional elements."
      />

      <MigratedCard
        title="Card with Actions"
        content="This card demonstrates how actions are handled in both MUI and Mantine versions."
        actions={[
          { label: 'Cancel', onClick: () => handleAction('Cancel'), variant: 'secondary' },
          { label: 'Confirm', onClick: () => handleAction('Confirm'), variant: 'primary' },
        ]}
      />

      <MigratedCard
        title="Elevated Card"
        content="This card has higher elevation to show shadow differences between the UI libraries."
        elevation={8}
        actions={[
          { label: 'Learn More', onClick: () => handleAction('Learn More') },
        ]}
      />

      <MigratedCard
        title="Card with Custom Content"
        content="This card contains additional custom content below the text."
        actions={[
          { label: 'Edit', onClick: () => handleAction('Edit'), variant: 'secondary' },
          { label: 'Delete', onClick: () => handleAction('Delete'), variant: 'primary' },
        ]}
      >
        <div style={{
          padding: '10px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '8px',
          color: 'white',
          textAlign: 'center',
          margin: '10px 0'
        }}>
          Custom Content Area
        </div>
      </MigratedCard>
    </div>
  );
};