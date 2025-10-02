import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@mantine/core';
import { IconPlus, IconTrash, IconEdit } from '@tabler/icons-react';

/**
 * Button component from Mantine v8
 *
 * Official docs: https://mantine.dev/core/button/
 */
const meta = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Button component with multiple variants, sizes, and states. Uses Mantine v8 design system.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['filled', 'light', 'outline', 'subtle', 'default', 'white'],
      description: 'Button variant',
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Button size',
    },
    color: {
      control: 'select',
      options: ['blue', 'red', 'green', 'yellow', 'gray', 'dark'],
      description: 'Button color from theme',
    },
    radius: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Border radius',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state with spinner',
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default button with primary styling
 */
export const Primary: Story = {
  args: {
    children: 'Primary Button',
    variant: 'filled',
    color: 'blue',
  },
};

/**
 * Secondary button with outlined styling
 */
export const Secondary: Story = {
  args: {
    children: 'Secondary Button',
    variant: 'outline',
    color: 'blue',
  },
};

/**
 * Subtle button with minimal styling
 */
export const Subtle: Story = {
  args: {
    children: 'Subtle Button',
    variant: 'subtle',
    color: 'gray',
  },
};

/**
 * Button with icon on the left
 */
export const WithLeftIcon: Story = {
  args: {
    children: 'Add Item',
    leftSection: <IconPlus size={16} />,
    variant: 'filled',
    color: 'blue',
  },
};

/**
 * Button with icon on the right
 */
export const WithRightIcon: Story = {
  args: {
    children: 'Delete',
    rightSection: <IconTrash size={16} />,
    variant: 'filled',
    color: 'red',
  },
};

/**
 * Disabled button state
 */
export const Disabled: Story = {
  args: {
    children: 'Disabled Button',
    disabled: true,
  },
};

/**
 * Loading button with spinner
 */
export const Loading: Story = {
  args: {
    children: 'Loading Button',
    loading: true,
  },
};

/**
 * Small button size
 */
export const Small: Story = {
  args: {
    children: 'Small Button',
    size: 'sm',
  },
};

/**
 * Large button size
 */
export const Large: Story = {
  args: {
    children: 'Large Button',
    size: 'lg',
  },
};

/**
 * Full width button
 */
export const FullWidth: Story = {
  args: {
    children: 'Full Width Button',
    fullWidth: true,
  },
  parameters: {
    layout: 'padded',
  },
};

/**
 * Danger button for destructive actions
 */
export const Danger: Story = {
  args: {
    children: 'Delete Account',
    leftSection: <IconTrash size={16} />,
    variant: 'filled',
    color: 'red',
  },
};

/**
 * Success button for positive actions
 */
export const Success: Story = {
  args: {
    children: 'Save Changes',
    variant: 'filled',
    color: 'green',
  },
};

/**
 * Button group example
 */
export const ButtonGroup: Story = {
  render: () => (
    <Button.Group>
      <Button variant="default">Left</Button>
      <Button variant="default">Center</Button>
      <Button variant="default">Right</Button>
    </Button.Group>
  ),
};
