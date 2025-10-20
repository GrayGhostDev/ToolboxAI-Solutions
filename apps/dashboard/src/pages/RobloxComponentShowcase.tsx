/**
 * Roblox Component Showcase Page
 *
 * Comprehensive demo of all Roblox-themed components
 * Perfect for testing, development, and client presentations
 */

import React, { useState } from 'react';
import {
  Container,
  Title,
  Text,
  Box,
  Paper,
  Grid,
  Stack,
  Group,
  Tabs,
  Badge,
  Divider,
  useMantineTheme,
  rem,
} from '@mantine/core';
import {
  IconPalette,
  IconPackage,
  Icon3dCubeSphere,
  IconDashboard,
  IconSparkles,
} from '@tabler/icons-react';

// Import Roblox components directly (avoiding barrel export issues on Vercel)
import { Roblox3DButton } from '@/components/roblox/Roblox3DButton';
import { Roblox3DNavigation } from '@/components/roblox/Roblox3DNavigation';
import { Roblox3DTabs } from '@/components/roblox/Roblox3DTabs';
import { Roblox3DMetricCard } from '@/components/roblox/Roblox3DMetricCard';
import { RobloxProgressBar } from '@/components/roblox/RobloxProgressBar';
import { RobloxAchievementBadge } from '@/components/roblox/RobloxAchievementBadge';
import { RobloxCharacterAvatar } from '@/components/roblox/RobloxCharacterAvatar';
import { ParticleEffects } from '@/components/roblox/ParticleEffects';
import { Roblox3DLoader } from '@/components/roblox/Roblox3DLoader';

// Import theme colors
import { robloxColors } from '@/theme/robloxTheme';

export const RobloxComponentShowcase: React.FC = () => {
  const theme = useMantineTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [showParticles, setShowParticles] = useState(false);
  const [selectedNavItem, setSelectedNavItem] = useState('dashboard');

  // Navigation items for demo
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      iconName: 'BOARD',
      tooltip: 'View your dashboard',
    },
    {
      id: 'achievements',
      label: 'Achievements',
      iconName: 'TROPHY',
      badge: 3,
      tooltip: 'View your achievements',
      children: [
        { id: 'badges', label: 'Badges', iconName: 'BADGE' },
        { id: 'levels', label: 'Levels', iconName: 'GRADUATION_CAP' },
      ],
    },
    {
      id: 'learn',
      label: 'Learn',
      iconName: 'BOOKS',
      tooltip: 'Learning resources',
    },
    {
      id: 'create',
      label: 'Create',
      iconName: 'BRUSH_PAINT',
      tooltip: 'Create new content',
    },
  ];

  const tabItems = [
    { id: '1', label: 'Overview', iconName: 'BOARD' },
    { id: '2', label: 'Progress', iconName: 'GRADUATION_CAP' },
    { id: '3', label: 'Rewards', iconName: 'TROPHY' },
  ];

  const handleNavClick = (item: any) => {
    setSelectedNavItem(item.id);
    console.log('Navigated to:', item.label);
  };

  const handleButtonClick = (label: string) => {
    console.log('Button clicked:', label);
    if (label === 'Celebrate') {
      setShowParticles(true);
      setTimeout(() => setShowParticles(false), 3000);
    }
  };

  return (
    <Container size="xl" py="xl">
      {/* Header */}
      <Box mb="xl">
        <Group position="apart" align="center">
          <Box>
            <Title
              order={1}
              style={{
                background: `linear-gradient(135deg, ${robloxColors.neon.electricBlue}, ${robloxColors.neon.hotPink})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: rem(48),
                fontWeight: 900,
              }}
            >
              🎮 Roblox Component Showcase
            </Title>
            <Text size="lg" c="dimmed" mt="sm">
              A comprehensive demo of all Roblox-themed UI components
            </Text>
          </Box>
          <Badge
            size="lg"
            variant="gradient"
            gradient={{ from: 'cyan', to: 'pink' }}
          >
            v1.0.0
          </Badge>
        </Group>
      </Box>

      <Divider mb="xl" />

      {/* Main Tabs */}
      <Tabs value={String(activeTab)} onTabChange={(value) => setActiveTab(Number(value))}>
        <Tabs.List>
          <Tabs.Tab value="0" leftSection={<IconPackage size={20} />}>
            Core Components
          </Tabs.Tab>
          <Tabs.Tab value="1" leftSection={<Icon3dCubeSphere size={20} />}>
            3D Components
          </Tabs.Tab>
          <Tabs.Tab value="2" leftSection={<IconDashboard size={20} />}>
            Dashboard Widgets
          </Tabs.Tab>
          <Tabs.Tab value="3" leftSection={<IconSparkles size={20} />}>
            Interactive Features
          </Tabs.Tab>
          <Tabs.Tab value="4" leftSection={<IconPalette size={20} />}>
            Theme & Colors
          </Tabs.Tab>
        </Tabs.List>

        {/* Tab 1: Core Components */}
        <Tabs.Panel value="0" pt="xl">
          <Stack spacing="xl">
            {/* Buttons Section */}
            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                3D Buttons
              </Title>
              <Text c="dimmed" mb="lg">
                Animated buttons with 20+ 3D icons and multiple variants
              </Text>

              <Stack spacing="md">
                {/* Button Variants */}
                <Box>
                  <Text fw={600} mb="sm">
                    Variants:
                  </Text>
                  <Group>
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Primary"
                      variant="primary"
                      onClick={() => handleButtonClick('Primary')}
                    />
                    <Roblox3DButton
                      iconName="BADGE"
                      label="Secondary"
                      variant="secondary"
                      onClick={() => handleButtonClick('Secondary')}
                    />
                    <Roblox3DButton
                      iconName="GRADUATION_CAP"
                      label="Success"
                      variant="success"
                      onClick={() => handleButtonClick('Success')}
                    />
                    <Roblox3DButton
                      iconName="LIGHT_BULB"
                      label="Warning"
                      variant="warning"
                      onClick={() => handleButtonClick('Warning')}
                    />
                    <Roblox3DButton
                      iconName="ERASER"
                      label="Error"
                      variant="error"
                      onClick={() => handleButtonClick('Error')}
                    />
                    <Roblox3DButton
                      iconName="BOOKS"
                      label="Info"
                      variant="info"
                      onClick={() => handleButtonClick('Info')}
                    />
                  </Group>
                </Box>

                {/* Button Sizes */}
                <Box>
                  <Text fw={600} mb="sm">
                    Sizes:
                  </Text>
                  <Group>
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Small"
                      size="small"
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Medium"
                      size="medium"
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Large"
                      size="large"
                    />
                  </Group>
                </Box>

                {/* Button States */}
                <Box>
                  <Text fw={600} mb="sm">
                    States:
                  </Text>
                  <Group>
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Normal"
                      variant="primary"
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Loading"
                      variant="primary"
                      loading={true}
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="Disabled"
                      variant="primary"
                      disabled={true}
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="With Tooltip"
                      variant="primary"
                      tooltip="This is a helpful tooltip!"
                    />
                  </Group>
                </Box>

                {/* Icon Showcase */}
                <Box>
                  <Text fw={600} mb="sm">
                    Available Icons:
                  </Text>
                  <Grid>
                    {[
                      'TROPHY',
                      'BADGE',
                      'GRADUATION_CAP',
                      'LIGHT_BULB',
                      'BOOKS',
                      'BACKPACK',
                      'BASKETBALL',
                      'SOCCER_BALL',
                      'BOARD',
                      'PENCIL',
                      'BRUSH_PAINT',
                      'CRAYON',
                    ].map((icon) => (
                      <Grid.Col key={icon} span={6} md={3}>
                        <Roblox3DButton
                          iconName={icon}
                          label={icon.replace('_', ' ')}
                          variant="secondary"
                          size="small"
                          fullWidth
                        />
                      </Grid.Col>
                    ))}
                  </Grid>
                </Box>
              </Stack>
            </Paper>

            {/* Navigation Section */}
            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                3D Navigation
              </Title>
              <Text c="dimmed" mb="lg">
                Responsive navigation with buttons or tabs, supporting hierarchical menus
              </Text>

              <Stack spacing="lg">
                <Box>
                  <Text fw={600} mb="sm">
                    Horizontal Button Navigation:
                  </Text>
                  <Roblox3DNavigation
                    items={navItems}
                    onItemClick={handleNavClick}
                    orientation="horizontal"
                    variant="buttons"
                    animated={true}
                  />
                  <Text size="sm" c="dimmed" mt="sm">
                    Selected: {selectedNavItem}
                  </Text>
                </Box>

                <Box>
                  <Text fw={600} mb="sm">
                    Tabs Navigation:
                  </Text>
                  <Roblox3DTabs
                    tabs={tabItems}
                    value={activeTab}
                    onChange={(e, value) => setActiveTab(value)}
                    variant="filled"
                    glowEffect={true}
                  />
                </Box>
              </Stack>
            </Paper>
          </Stack>
        </Tabs.Panel>

        {/* Tab 2: 3D Components */}
        <Tabs.Panel value="1" pt="xl">
          <Stack spacing="xl">
            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                3D Character Avatar
              </Title>
              <Text c="dimmed" mb="lg">
                Customizable 3D character with real-time rendering
              </Text>

              <Box style={{ textAlign: 'center' }}>
                <RobloxCharacterAvatar
                  characterData={{
                    skinTone: '#ffcc99',
                    shirtColor: '#0066ff',
                    pantsColor: '#333333',
                    accessories: [],
                  }}
                  size={300}
                  animate={true}
                  rotatable={true}
                />
                <Text c="dimmed" mt="md">
                  Click and drag to rotate
                </Text>
              </Box>
            </Paper>

            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                3D Loader
              </Title>
              <Text c="dimmed" mb="lg">
                Animated loading indicator
              </Text>

              <Box style={{ textAlign: 'center' }}>
                <Roblox3DLoader size={80} />
              </Box>
            </Paper>
          </Stack>
        </Tabs.Panel>

        {/* Tab 3: Dashboard Widgets */}
        <Tabs.Panel value="2" pt="xl">
          <Grid>
            <Grid.Col span={12} md={6} lg={4}>
              <Roblox3DMetricCard
                title="Total XP"
                value={15420}
                change={+12.5}
                iconName="LIGHT_BULB"
                variant="primary"
                animated={true}
              />
            </Grid.Col>
            <Grid.Col span={12} md={6} lg={4}>
              <Roblox3DMetricCard
                title="Achievements"
                value={42}
                change={+3}
                iconName="TROPHY"
                variant="success"
                animated={true}
              />
            </Grid.Col>
            <Grid.Col span={12} md={6} lg={4}>
              <Roblox3DMetricCard
                title="Current Level"
                value={7}
                change={+1}
                iconName="GRADUATION_CAP"
                variant="info"
                animated={true}
              />
            </Grid.Col>
          </Grid>

          <Paper p="xl" radius="lg" withBorder mt="xl">
            <Title order={3} mb="md">
              Progress Bar
            </Title>
            <RobloxProgressBar
              currentXP={750}
              requiredXP={1000}
              level={5}
              showLevel={true}
              animated={true}
              variant="gradient"
            />
          </Paper>
        </Tabs.Panel>

        {/* Tab 4: Interactive Features */}
        <Tabs.Panel value="3" pt="xl">
          <Stack spacing="xl">
            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                Achievement Badges
              </Title>
              <Text c="dimmed" mb="lg">
                Animated badges with rarity levels
              </Text>

              <Grid>
                <Grid.Col span={12} md={6}>
                  <RobloxAchievementBadge
                    title="First Steps"
                    description="Complete your first lesson"
                    iconName="BADGE"
                    rarity="common"
                    unlocked={true}
                  />
                </Grid.Col>
                <Grid.Col span={12} md={6}>
                  <RobloxAchievementBadge
                    title="Quick Learner"
                    description="Complete 10 lessons in a day"
                    iconName="LIGHT_BULB"
                    rarity="rare"
                    unlocked={true}
                  />
                </Grid.Col>
                <Grid.Col span={12} md={6}>
                  <RobloxAchievementBadge
                    title="Master Coder"
                    description="Complete 100 coding challenges"
                    iconName="TROPHY"
                    rarity="epic"
                    unlocked={false}
                    progress={75}
                  />
                </Grid.Col>
                <Grid.Col span={12} md={6}>
                  <RobloxAchievementBadge
                    title="Legendary"
                    description="Reach Level 50"
                    iconName="GRADUATION_CAP"
                    rarity="legendary"
                    unlocked={false}
                    progress={14}
                  />
                </Grid.Col>
              </Grid>
            </Paper>

            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                Particle Effects
              </Title>
              <Text c="dimmed" mb="lg">
                Celebration effects for achievements
              </Text>

              <Box style={{ textAlign: 'center' }}>
                <Roblox3DButton
                  iconName="TROPHY"
                  label="Celebrate 🎉"
                  variant="success"
                  size="large"
                  onClick={() => handleButtonClick('Celebrate')}
                />

                {showParticles && (
                  <ParticleEffects
                    type="confetti"
                    intensity="high"
                    colors={[
                      robloxColors.neon.electricBlue,
                      robloxColors.neon.hotPink,
                      robloxColors.neon.toxicGreen,
                      robloxColors.neon.plasmaYellow,
                    ]}
                    duration={3000}
                  />
                )}
              </Box>
            </Paper>
          </Stack>
        </Tabs.Panel>

        {/* Tab 5: Theme & Colors */}
        <Tabs.Panel value="4" pt="xl">
          <Stack spacing="xl">
            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                Neon Color Palette
              </Title>
              <Text c="dimmed" mb="lg">
                Vibrant colors for maximum visual impact
              </Text>

              <Grid>
                {Object.entries(robloxColors.neon).map(([name, color]) => (
                  <Grid.Col key={name} span={6} md={4} lg={3}>
                    <Box
                      style={{
                        background: color,
                        height: rem(100),
                        borderRadius: theme.radius.md,
                        boxShadow: `0 4px 12px ${color}40`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#000',
                        fontWeight: 700,
                        textTransform: 'capitalize',
                      }}
                    >
                      {name.replace(/([A-Z])/g, ' $1').trim()}
                    </Box>
                    <Text size="xs" c="dimmed" mt="xs" align="center">
                      {color}
                    </Text>
                  </Grid.Col>
                ))}
              </Grid>
            </Paper>

            <Paper p="xl" radius="lg" withBorder>
              <Title order={2} mb="md">
                Gamification Colors
              </Title>
              <Text c="dimmed" mb="lg">
                Colors designed for achievements and rewards
              </Text>

              <Grid>
                {Object.entries(robloxColors.gamification).map(([name, color]) => (
                  <Grid.Col key={name} span={6} md={4}>
                    <Box
                      style={{
                        background: color,
                        height: rem(80),
                        borderRadius: theme.radius.md,
                        boxShadow: `0 4px 12px ${color}40`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#000',
                        fontWeight: 700,
                        textTransform: 'capitalize',
                      }}
                    >
                      {name}
                    </Box>
                    <Text size="xs" c="dimmed" mt="xs" align="center">
                      {color}
                    </Text>
                  </Grid.Col>
                ))}
              </Grid>
            </Paper>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {/* Footer */}
      <Box mt="xl" py="xl">
        <Divider mb="md" />
        <Text size="sm" c="dimmed" align="center">
          Roblox Dashboard Component Library v1.0.0 • Built with React 19 + Mantine v8 • 2025
        </Text>
      </Box>
    </Container>
  );
};

export default RobloxComponentShowcase;
