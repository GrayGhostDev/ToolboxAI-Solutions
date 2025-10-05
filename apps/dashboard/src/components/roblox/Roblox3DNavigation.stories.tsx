/**
 * Roblox3DNavigation Storybook Stories
 *
 * Interactive documentation for the navigation component.
 *
 * @module Roblox3DNavigation.stories
 * @since 2025-10-01
 */

import type { Meta, StoryObj } from '@storybook/react';
import React, { useState } from 'react';
import { Roblox3DNavigation } from './Roblox3DNavigation';
import { Box, Stack, Title, Text } from '@mantine/core';

const meta = {
  title: 'Roblox/Core/Roblox3DNavigation',
  component: Roblox3DNavigation,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A comprehensive navigation component with buttons or tabs, supporting hierarchical menus and badges.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Roblox3DNavigation>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleNavItems = [
  { id: 'home', label: 'Home', iconName: 'BOARD', tooltip: 'Go to home' },
  { id: 'achievements', label: 'Achievements', iconName: 'TROPHY', badge: 3, tooltip: 'View achievements' },
  { id: 'learn', label: 'Learn', iconName: 'BOOKS', tooltip: 'Learning center' },
  { id: 'profile', label: 'Profile', iconName: 'GRADUATION_CAP', tooltip: 'Your profile' },
];

/**
 * Default horizontal navigation
 */
export const Default: Story = {
  render: () => {
    const [activeId, setActiveId] = useState('home');

    return (
      <Box>
        <Roblox3DNavigation
          items={sampleNavItems}
          onItemClick={(item) => {
            console.log('Clicked:', item);
            setActiveId(item.id);
          }}
          variant="buttons"
          orientation="horizontal"
          animated={true}
        />
        <Text mt="lg" ta="center">Active: {activeId}</Text>
      </Box>
    );
  },
};

/**
 * Vertical navigation
 */
export const Vertical: Story = {
  render: () => {
    const [activeId, setActiveId] = useState('home');

    return (
      <Box style={{ width: '250px' }}>
        <Roblox3DNavigation
          items={sampleNavItems}
          onItemClick={(item) => {
            setActiveId(item.id);
          }}
          variant="buttons"
          orientation="vertical"
          animated={true}
        />
        <Text mt="md">Selected: {activeId}</Text>
      </Box>
    );
  },
};

/**
 * Tab variant
 */
export const TabVariant: Story = {
  render: () => {
    const [activeId, setActiveId] = useState('home');

    return (
      <Box>
        <Roblox3DNavigation
          items={sampleNavItems}
          onItemClick={(item) => {
            setActiveId(item.id);
          }}
          variant="tabs"
          orientation="horizontal"
          animated={true}
        />
      </Box>
    );
  },
};

/**
 * With badges and notifications
 */
export const WithBadges: Story = {
  render: () => {
    const itemsWithBadges = [
      { id: 'inbox', label: 'Inbox', iconName: 'BOARD', badge: 5 },
      { id: 'achievements', label: 'Achievements', iconName: 'TROPHY', badge: 12 },
      { id: 'notifications', label: 'Alerts', iconName: 'LIGHT_BULB', badge: 99 },
      { id: 'messages', label: 'Messages', iconName: 'BOOKS' },
    ];

    return (
      <Box>
        <Roblox3DNavigation
          items={itemsWithBadges}
          onItemClick={(item) => console.log('Clicked:', item)}
          variant="buttons"
          orientation="horizontal"
        />
      </Box>
    );
  },
};

/**
 * Different sizes
 */
export const Sizes: Story = {
  render: () => {
    return (
      <Stack gap="xl">
        <Box>
          <Title order={5} mb="md">Small</Title>
          <Roblox3DNavigation
            items={sampleNavItems}
            onItemClick={(item) => console.log('Clicked:', item)}
            size="small"
          />
        </Box>
        <Box>
          <Title order={5} mb="md">Medium</Title>
          <Roblox3DNavigation
            items={sampleNavItems}
            onItemClick={(item) => console.log('Clicked:', item)}
            size="medium"
          />
        </Box>
        <Box>
          <Title order={5} mb="md">Large</Title>
          <Roblox3DNavigation
            items={sampleNavItems}
            onItemClick={(item) => console.log('Clicked:', item)}
            size="large"
          />
        </Box>
      </Stack>
    );
  },
};

/**
 * Compact mode
 */
export const Compact: Story = {
  render: () => {
    return (
      <Stack gap="lg">
        <Box>
          <Title order={5} mb="md">Full Labels</Title>
          <Roblox3DNavigation
            items={sampleNavItems}
            onItemClick={(item) => console.log('Clicked:', item)}
            compact={false}
          />
        </Box>
        <Box>
          <Title order={5} mb="md">Compact (Icons Only)</Title>
          <Roblox3DNavigation
            items={sampleNavItems}
            onItemClick={(item) => console.log('Clicked:', item)}
            compact={true}
          />
        </Box>
      </Stack>
    );
  },
};

/**
 * With glow effect
 */
export const WithGlow: Story = {
  render: () => {
    return (
      <Roblox3DNavigation
        items={sampleNavItems}
        onItemClick={(item) => console.log('Clicked:', item)}
        variant="buttons"
        glowEffect={true}
        animated={true}
      />
    );
  },
};
