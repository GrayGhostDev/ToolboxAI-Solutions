import type { Meta, StoryObj } from '@storybook/react';
import { Card, Text, Badge, Button, Group, Image } from '@mantine/core';
import { IconHeart, IconShare, IconBookmark } from '@tabler/icons-react';

/**
 * Card component from Mantine v8
 *
 * Official docs: https://mantine.dev/core/card/
 */
const meta = {
  title: 'Components/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Card component for displaying content in a container with optional sections, padding, and borders.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    shadow: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Card shadow size',
    },
    padding: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Card padding',
    },
    radius: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Border radius',
    },
    withBorder: {
      control: 'boolean',
      description: 'Add border',
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Basic card with text content
 */
export const Basic: Story = {
  render: (args) => (
    <Card {...args} style={{ width: 340 }}>
      <Text fw={500} size="lg" mb="xs">
        Norway Fjords
      </Text>
      <Text size="sm" c="dimmed">
        With Fjord Tours you can explore more of the magical fjord landscapes with tours and
        activities on and around the fjords of Norway
      </Text>
    </Card>
  ),
  args: {
    shadow: 'sm',
    padding: 'lg',
    radius: 'md',
    withBorder: false,
  },
};

/**
 * Card with image header
 */
export const WithImage: Story = {
  render: (args) => (
    <Card {...args} style={{ width: 340 }}>
      <Card.Section>
        <Image
          src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/images/bg-8.png"
          height={160}
          alt="Norway"
        />
      </Card.Section>

      <Group justify="space-between" mt="md" mb="xs">
        <Text fw={500}>Norway Fjords</Text>
        <Badge color="pink" variant="light">
          On Sale
        </Badge>
      </Group>

      <Text size="sm" c="dimmed">
        With Fjord Tours you can explore more of the magical fjord landscapes
      </Text>

      <Button color="blue" fullWidth mt="md" radius="md">
        Book classic tour now
      </Button>
    </Card>
  ),
  args: {
    shadow: 'sm',
    padding: 'lg',
    radius: 'md',
    withBorder: true,
  },
};

/**
 * Card with multiple sections
 */
export const WithSections: Story = {
  render: (args) => (
    <Card {...args} style={{ width: 340 }}>
      <Card.Section withBorder inheritPadding py="xs">
        <Text fw={500}>System update</Text>
      </Card.Section>

      <Card.Section inheritPadding mt="sm" pb="md">
        <Text size="sm">
          The system will be updated on March 24th, 2024. Please save your work before the scheduled maintenance.
        </Text>
      </Card.Section>

      <Card.Section withBorder inheritPadding py="xs">
        <Group justify="space-between">
          <Button variant="subtle" color="gray">
            Dismiss
          </Button>
          <Button>Learn more</Button>
        </Group>
      </Card.Section>
    </Card>
  ),
  args: {
    shadow: 'sm',
    padding: 'lg',
    radius: 'md',
    withBorder: true,
  },
};

/**
 * Interactive card with hover effect
 */
export const Interactive: Story = {
  render: (args) => (
    <Card
      {...args}
      style={{ width: 340, cursor: 'pointer' }}
      onClick={() => alert('Card clicked!')}
    >
      <Card.Section>
        <Image
          src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/images/bg-7.png"
          height={160}
          alt="Mountains"
        />
      </Card.Section>

      <Text fw={500} size="lg" mt="md">
        Mountain Adventure
      </Text>

      <Text mt="xs" c="dimmed" size="sm">
        Explore breathtaking mountain views and hiking trails
      </Text>

      <Group mt="md">
        <Button variant="light" size="xs" leftSection={<IconHeart size={14} />}>
          Like
        </Button>
        <Button variant="light" size="xs" leftSection={<IconShare size={14} />}>
          Share
        </Button>
        <Button variant="light" size="xs" leftSection={<IconBookmark size={14} />}>
          Save
        </Button>
      </Group>
    </Card>
  ),
  args: {
    shadow: 'md',
    padding: 'lg',
    radius: 'md',
    withBorder: false,
  },
};

/**
 * Compact card with minimal padding
 */
export const Compact: Story = {
  render: (args) => (
    <Card {...args} style={{ width: 300 }}>
      <Group justify="space-between" mb="xs">
        <Text fw={500} size="sm">
          Quick Update
        </Text>
        <Badge size="sm">New</Badge>
      </Group>
      <Text size="xs" c="dimmed">
        Check out our latest features
      </Text>
    </Card>
  ),
  args: {
    shadow: 'xs',
    padding: 'sm',
    radius: 'sm',
    withBorder: true,
  },
};

/**
 * Card with custom background
 */
export const CustomBackground: Story = {
  render: (args) => (
    <Card {...args} style={{ width: 340, backgroundColor: '#f8f9fa' }}>
      <Text fw={500} size="lg" c="blue">
        Premium Feature
      </Text>
      <Text mt="xs" size="sm">
        Unlock advanced features with our premium plan
      </Text>
      <Button mt="md" color="blue" variant="light" fullWidth>
        Upgrade Now
      </Button>
    </Card>
  ),
  args: {
    shadow: 'lg',
    padding: 'xl',
    radius: 'md',
    withBorder: false,
  },
};

/**
 * Card grid layout example
 */
export const CardGrid: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
      {[1, 2, 3].map((item) => (
        <Card key={item} shadow="sm" padding="lg" radius="md" withBorder>
          <Text fw={500}>Card {item}</Text>
          <Text size="sm" c="dimmed" mt="xs">
            Example card content
          </Text>
          <Button variant="light" color="blue" fullWidth mt="md">
            Action
          </Button>
        </Card>
      ))}
    </div>
  ),
  parameters: {
    layout: 'padded',
  },
};
