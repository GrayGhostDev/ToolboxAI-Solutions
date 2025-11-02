import { Stack, Text, Button, ThemeIcon } from '@mantine/core';
import { ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
  variant?: 'default' | 'compact';
}

/**
 * EmptyState - Displays when no content is available
 * 
 * @example
 * <EmptyState
 *   icon={<IconSchool size={40} />}
 *   title="No lessons yet"
 *   description="Create your first lesson to start teaching"
 *   action={{
 *     label: "Create Lesson",
 *     onClick: () => setCreateLessonOpen(true),
 *     icon: <IconPlus size={16} />
 *   }}
 * />
 */
export function EmptyState({ 
  icon, 
  title, 
  description, 
  action,
  variant = 'default' 
}: EmptyStateProps) {
  const minHeight = variant === 'compact' ? 200 : 300;
  const iconSize = variant === 'compact' ? 60 : 80;
  
  return (
    <Stack
      align="center"
      justify="center"
      gap="md"
      style={{
        padding: variant === 'compact' ? '2rem 1rem' : '4rem 2rem',
        textAlign: 'center',
        minHeight,
      }}
    >
      <ThemeIcon 
        size={iconSize} 
        radius="xl" 
        variant="light" 
        color="gray"
        styles={{
          root: {
            background: 'linear-gradient(135deg, rgba(108, 117, 125, 0.1), rgba(108, 117, 125, 0.05))',
          }
        }}
      >
        {icon}
      </ThemeIcon>
      
      <Stack gap="xs" align="center">
        <Text size={variant === 'compact' ? 'md' : 'lg'} fw={600}>
          {title}
        </Text>
        <Text size="sm" c="dimmed" maw={400}>
          {description}
        </Text>
      </Stack>
      
      {action && (
        <Button 
          size={variant === 'compact' ? 'sm' : 'md'} 
          onClick={action.onClick}
          leftSection={action.icon}
        >
          {action.label}
        </Button>
      )}
    </Stack>
  );
}
