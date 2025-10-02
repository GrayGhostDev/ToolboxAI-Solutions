/**
 * Roblox3DButton Storybook Stories
 *
 * Interactive documentation and testing for the Roblox3DButton component.
 *
 * @module Roblox3DButton.stories
 * @since 2025-10-01
 */

import type { Meta, StoryObj } from '@storybook/react';
import { Roblox3DButton } from './Roblox3DButton';
import { Box, Stack, Group, Title, Text } from '@mantine/core';

const meta = {
  title: 'Roblox/Core/Roblox3DButton',
  component: Roblox3DButton,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A vibrant, animated button with 3D icon support and multiple variants. Perfect for Roblox-themed interfaces.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'success', 'warning', 'error', 'info'],
      description: 'Button color variant',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'Button size',
    },
    iconName: {
      control: 'select',
      options: [
        'TROPHY', 'BADGE', 'GRADUATION_CAP', 'LIGHT_BULB', 'BOOKS',
        'BOARD', 'BACKPACK', 'ABC_CUBE', 'BASKETBALL', 'BRUSH_PAINT'
      ],
      description: '3D icon to display',
    },
    animated: {
      control: 'boolean',
      description: 'Enable/disable animations',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable the button',
    },
    loading: {
      control: 'boolean',
      description: 'Show loading state',
    },
    fullWidth: {
      control: 'boolean',
      description: 'Make button full width',
    },
  },
} satisfies Meta<typeof Roblox3DButton>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default button with primary variant
 */
export const Default: Story = {
  args: {
    iconName: 'TROPHY',
    label: 'Achievement',
    variant: 'primary',
    size: 'medium',
    animated: true,
  },
};

/**
 * All button variants showcase
 */
export const AllVariants: Story = {
  render: () => (
    <Stack gap="lg">
      <Box>
        <Title order={4} mb="md">Button Variants</Title>
        <Group>
          <Roblox3DButton
            iconName="TROPHY"
            label="Primary"
            variant="primary"
            onClick={() => console.log('Primary clicked')}
          />
          <Roblox3DButton
            iconName="BADGE"
            label="Secondary"
            variant="secondary"
            onClick={() => console.log('Secondary clicked')}
          />
          <Roblox3DButton
            iconName="LIGHT_BULB"
            label="Success"
            variant="success"
            onClick={() => console.log('Success clicked')}
          />
          <Roblox3DButton
            iconName="BOARD"
            label="Warning"
            variant="warning"
            onClick={() => console.log('Warning clicked')}
          />
          <Roblox3DButton
            iconName="BOOKS"
            label="Error"
            variant="error"
            onClick={() => console.log('Error clicked')}
          />
          <Roblox3DButton
            iconName="GRADUATION_CAP"
            label="Info"
            variant="info"
            onClick={() => console.log('Info clicked')}
          />
        </Group>
      </Box>
    </Stack>
  ),
};

/**
 * Different button sizes
 */
export const Sizes: Story = {
  render: () => (
    <Stack gap="lg">
      <Box>
        <Title order={4} mb="md">Button Sizes</Title>
        <Group align="center">
          <Roblox3DButton
            iconName="TROPHY"
            label="Small"
            size="small"
            variant="primary"
          />
          <Roblox3DButton
            iconName="TROPHY"
            label="Medium"
            size="medium"
            variant="primary"
          />
          <Roblox3DButton
            iconName="TROPHY"
            label="Large"
            size="large"
            variant="primary"
          />
        </Group>
      </Box>
    </Stack>
  ),
};

/**
 * Icon-only buttons (no label)
 */
export const IconOnly: Story = {
  render: () => (
    <Stack gap="lg">
      <Box>
        <Title order={4} mb="md">Icon Only Buttons</Title>
        <Group>
          <Roblox3DButton
            iconName="TROPHY"
            variant="primary"
            tooltip="Achievement"
          />
          <Roblox3DButton
            iconName="BADGE"
            variant="secondary"
            tooltip="Badge"
          />
          <Roblox3DButton
            iconName="LIGHT_BULB"
            variant="success"
            tooltip="Idea"
          />
          <Roblox3DButton
            iconName="GRADUATION_CAP"
            variant="info"
            tooltip="Education"
          />
        </Group>
      </Box>
    </Stack>
  ),
};

/**
 * Button states: disabled and loading
 */
export const States: Story = {
  render: () => (
    <Stack gap="lg">
      <Box>
        <Title order={4} mb="md">Button States</Title>
        <Stack gap="md">
          <Group>
            <Text size="sm" w={100}>Normal:</Text>
            <Roblox3DButton
              iconName="TROPHY"
              label="Click Me"
              variant="primary"
            />
          </Group>
          <Group>
            <Text size="sm" w={100}>Disabled:</Text>
            <Roblox3DButton
              iconName="TROPHY"
              label="Disabled"
              variant="primary"
              disabled
            />
          </Group>
          <Group>
            <Text size="sm" w={100}>Loading:</Text>
            <Roblox3DButton
              iconName="TROPHY"
              label="Loading..."
              variant="primary"
              loading
            />
          </Group>
        </Stack>
      </Box>
    </Stack>
  ),
};

/**
 * Full width buttons
 */
export const FullWidth: Story = {
  render: () => (
    <Box style={{ width: '400px' }}>
      <Stack gap="md">
        <Roblox3DButton
          iconName="TROPHY"
          label="Full Width Primary"
          variant="primary"
          fullWidth
        />
        <Roblox3DButton
          iconName="BADGE"
          label="Full Width Secondary"
          variant="secondary"
          fullWidth
        />
        <Roblox3DButton
          iconName="LIGHT_BULB"
          label="Full Width Success"
          variant="success"
          fullWidth
        />
      </Stack>
    </Box>
  ),
};

/**
 * With and without animations
 */
export const Animations: Story = {
  render: () => (
    <Stack gap="lg">
      <Box>
        <Title order={4} mb="md">Animation Comparison</Title>
        <Group>
          <Stack gap="xs" align="center">
            <Text size="sm">Animated</Text>
            <Roblox3DButton
              iconName="TROPHY"
              label="Hover Me"
              variant="primary"
              animated={true}
            />
          </Stack>
          <Stack gap="xs" align="center">
            <Text size="sm">Static</Text>
            <Roblox3DButton
              iconName="TROPHY"
              label="Hover Me"
              variant="primary"
              animated={false}
            />
          </Stack>
        </Group>
      </Box>
    </Stack>
  ),
};

/**
 * Interactive example with click handler
 */
export const Interactive: Story = {
  render: () => {
    const [clickCount, setClickCount] = React.useState(0);

    return (
      <Stack gap="md" align="center">
        <Title order={4}>Click Counter</Title>
        <Text size="lg" fw={700}>Clicks: {clickCount}</Text>
        <Roblox3DButton
          iconName="TROPHY"
          label="Click Me!"
          variant="success"
          size="large"
          onClick={() => setClickCount(c => c + 1)}
        />
      </Stack>
    );
  },
};

/**
 * All available icons showcase
 */
export const AllIcons: Story = {
  render: () => {
    const icons = [
      'TROPHY', 'BADGE', 'GRADUATION_CAP', 'LIGHT_BULB', 'BOOKS',
      'BOARD', 'BACKPACK', 'ABC_CUBE', 'BASKETBALL', 'BRUSH_PAINT'
    ];

    return (
      <Stack gap="lg">
        <Title order={4}>Available Icons</Title>
        <Group>
          {icons.map((iconName) => (
            <Stack key={iconName} gap="xs" align="center">
              <Roblox3DButton
                iconName={iconName}
                variant="primary"
                tooltip={iconName}
              />
              <Text size="xs">{iconName}</Text>
            </Stack>
          ))}
        </Group>
      </Stack>
    );
  },
};
