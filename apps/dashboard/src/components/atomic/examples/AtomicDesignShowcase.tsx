/**
 * Atomic Design Showcase
 *
 * A comprehensive example demonstrating how atomic design components
 * work together to create a cohesive, reusable interface.
 */

import React from 'react';
import { styled } from '@mui/material/styles';

// Atomic imports
import {
  AtomicButton,
  AtomicInput,
  AtomicText,
  AtomicBox,
  AtomicAvatar,
  AtomicBadge,
  AtomicSpinner
} from '../atoms';

// Molecular imports
import { FormField, Card } from '../molecules';

// Compound imports
import { Table } from '../compound';

// HOC imports
import { withErrorBoundary, withLoading } from '../hoc';

// Hook imports
import { useToggle, useDisclosure } from '../../../hooks/atomic';

// Gaming-specific example data
const gameData = {
  player: {
    name: 'RobloxPlayer123',
    level: 42,
    xp: 15750,
    maxXp: 20000,
    avatar: '/avatars/player1.jpg',
    status: 'online' as const,
    achievements: ['First Steps', 'Explorer', 'Builder']
  },
  leaderboard: [
    { rank: 1, name: 'ProGamer2024', score: 95420, level: 87 },
    { rank: 2, name: 'BuildMaster', score: 89340, level: 82 },
    { rank: 3, name: 'RobloxPlayer123', score: 76890, level: 42 }
  ]
};

// Styled showcase container
const ShowcaseContainer = styled(AtomicBox)(({ theme }) => ({
  padding: '2rem',
  maxWidth: '1200px',
  margin: '0 auto',

  '& .section': {
    marginBottom: '3rem',

    '& h2': {
      marginBottom: '1rem',
      color: theme.palette.text.primary
    },

    '& .demo-grid': {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: '1rem',
      marginBottom: '2rem'
    }
  }
}));

// Atoms showcase
const AtomsShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const buttonStates = useToggle(false);

  return (
    <div className="section">
      <AtomicText variant="h2" weight="bold" gradient robloxTheme>
        🔬 Atoms - Basic Building Blocks
      </AtomicText>

      <div className="demo-grid">
        {/* Buttons */}
        <Card variant="roblox" title="Buttons">
          <AtomicBox display="flex" flexDirection="column" gap={2}>
            <AtomicButton
              variant="primary"
              size="md"
              loading={buttonStates.value}
              loadingText="Processing..."
              onClick={(e: React.MouseEvent) => buttonStates.toggle}
            >
              Toggle Loading
            </AtomicButton>

            <AtomicButton variant="outlined" size="sm">
              Outlined Button
            </AtomicButton>

            <AtomicButton variant="danger" size="lg">
              Danger Button
            </AtomicButton>
          </AtomicBox>
        </Card>

        {/* Text variants */}
        <Card variant="roblox" title="Typography">
          <AtomicBox display="flex" flexDirection="column" gap={1}>
            <AtomicText variant="h1" weight="bold" truncate>
              Heading 1
            </AtomicText>
            <AtomicText variant="h3" color="primary">
              Heading 3 Primary
            </AtomicText>
            <AtomicText variant="body1">
              Body text with normal weight
            </AtomicText>
            <AtomicText variant="sm" color="secondary">
              Small secondary text
            </AtomicText>
            <AtomicText variant="lg" gradient weight="bold">
              Gradient text effect
            </AtomicText>
          </AtomicBox>
        </Card>

        {/* Avatars and badges */}
        <Card variant="roblox" title="Gaming Elements">
          <AtomicBox display="flex" flexDirection="column" gap={3}>
            <AtomicBox display="flex" alignItems="center" gap={2}>
              <AtomicAvatar
                size="lg"
                level={gameData.player.level}
                status={gameData.player.status}
                src={gameData.player.avatar}
                robloxTheme
              >
                RP
              </AtomicAvatar>
              <AtomicBox>
                <AtomicText variant="base" weight="semibold">
                  {gameData.player.name}
                </AtomicText>
                <AtomicText variant="sm" color="secondary">
                  Level {gameData.player.level}
                </AtomicText>
              </AtomicBox>
            </AtomicBox>

            <AtomicBox display="flex" gap={1} flexWrap="wrap">
              <AtomicBadge
                variant="achievement"
                rarity="legendary"
                pulse
                badgeContent="87"
              >
                <AtomicText variant="xs">LVL</AtomicText>
              </AtomicBadge>

              <AtomicBadge
                variant="notification"
                color="error"
                badgeContent="3"
              >
                <AtomicText variant="xs">NEW</AtomicText>
              </AtomicBadge>
            </AtomicBox>

            <AtomicSpinner variant="pulse" size="md" />
          </AtomicBox>
        </Card>
      </div>
    </div>
  );
};

// Molecules showcase
const MoleculesShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const [searchValue, setSearchValue] = React.useState('');
  const [email, setEmail] = React.useState('');

  return (
    <div className="section">
      <AtomicText variant="h2" weight="bold" gradient robloxTheme>
        🧩 Molecules - Simple Combinations
      </AtomicText>

      <div className="demo-grid">
        {/* Form fields */}
        <Card variant="roblox" title="Form Fields">
          <AtomicBox display="flex" flexDirection="column" gap={3}>
            <FormField
              label="Search Query"
              placeholder="Enter search terms..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              helperText="Search across all game content"
              clearable
              onClear={() => setSearchValue('')}
              showCharacterCount
              maxLength={100}
            />

            <FormField
              label="Email Address"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              state={email && !email.includes('@') ? 'error' : 'default'}
              errorText={email && !email.includes('@') ? 'Please enter a valid email' : undefined}
            />
          </AtomicBox>
        </Card>

        {/* Player card */}
        <Card
          variant="game"
          title={gameData.player.name}
          subtitle={`Level ${gameData.player.level} Player`}
          avatar={
            <AtomicAvatar
              size="md"
              level={gameData.player.level}
              status={gameData.player.status}
              robloxTheme
            >
              RP
            </AtomicAvatar>
          }
          actions={
            <AtomicButton variant="outlined" size="sm">
              View Profile
            </AtomicButton>
          }
        >
          <AtomicBox display="flex" flexDirection="column" gap={2}>
            <AtomicBox>
              <AtomicText variant="sm" color="secondary">
                Experience Points
              </AtomicText>
              <AtomicText variant="lg" weight="bold" color="primary">
                {gameData.player.xp.toLocaleString()} / {gameData.player.maxXp.toLocaleString()}
              </AtomicText>
            </AtomicBox>

            <AtomicBox display="flex" gap={1} flexWrap="wrap">
              {gameData.player.achievements.map((achievement, index) => (
                <AtomicBadge
                  key={achievement}
                  variant="achievement"
                  rarity={index === 0 ? 'legendary' : index === 1 ? 'epic' : 'rare'}
                  badgeContent="✓"
                >
                  <AtomicText variant="xs">{achievement}</AtomicText>
                </AtomicBadge>
              ))}
            </AtomicBox>
          </AtomicBox>
        </Card>
      </div>
    </div>
  );
};

// Organisms showcase (using compound components)
const OrganismsShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const [sortColumn, setSortColumn] = React.useState<'rank' | 'name' | 'score'>('rank');
  const [sortDirection, setSortDirection] = React.useState<'asc' | 'desc'>('asc');

  const handleSort = (column: 'rank' | 'name' | 'score') => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  return (
    <div className="section">
      <AtomicText variant="h2" weight="bold" gradient robloxTheme>
        🏗️ Organisms - Complex Components
      </AtomicText>

      <Card variant="roblox" title="Leaderboard Table">
        <Table variant="roblox" sortable selectable robloxTheme>
          <Table.Header>
            <Table.Row>
              <Table.Cell
                as="th"
                sortable
                sorted={sortColumn === 'rank' ? sortDirection : false}
                onSort={() => handleSort('rank')}
              >
                Rank
              </Table.Cell>
              <Table.Cell
                as="th"
                sortable
                sorted={sortColumn === 'name' ? sortDirection : false}
                onSort={() => handleSort('name')}
              >
                Player
              </Table.Cell>
              <Table.Cell
                as="th"
                sortable
                sorted={sortColumn === 'score' ? sortDirection : false}
                onSort={() => handleSort('score')}
                align="right"
              >
                Score
              </Table.Cell>
              <Table.Cell as="th" align="center">
                Level
              </Table.Cell>
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {gameData.leaderboard.map((player) => (
              <Table.Row key={player.rank}>
                <Table.Cell>
                  <AtomicBadge
                    variant="achievement"
                    rarity={player.rank === 1 ? 'legendary' : player.rank === 2 ? 'epic' : 'rare'}
                    badgeContent={player.rank}
                  >
                    <span />
                  </AtomicBadge>
                </Table.Cell>
                <Table.Cell>
                  <AtomicBox display="flex" alignItems="center" gap={2}>
                    <AtomicAvatar size="sm" status="online">
                      {player.name.slice(0, 2).toUpperCase()}
                    </AtomicAvatar>
                    <AtomicText weight="medium">{player.name}</AtomicText>
                  </AtomicBox>
                </Table.Cell>
                <Table.Cell align="right">
                  <AtomicText variant="base" weight="bold" color="primary">
                    {player.score.toLocaleString()}
                  </AtomicText>
                </Table.Cell>
                <Table.Cell align="center">
                  <AtomicText variant="sm" color="secondary">
                    {player.level}
                  </AtomicText>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Card>
    </div>
  );
};

// HOC demonstration
const LoadingDemo = withLoading(
  withErrorBoundary(
    ({ title }: { title: string }) => (
      <Card variant="roblox" title={title}>
        <AtomicText>
          This component demonstrates HOC composition with error boundary and loading states.
        </AtomicText>
      </Card>
    ),
    {
      onError: (error) => console.error('Component error:', error)
    }
  ),
  {
    loadingText: 'Loading HOC demo...',
    spinnerSize: 'md'
  }
);

// Main showcase component
const AtomicDesignShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const loadingDemo = useToggle(false);

  React.useEffect(() => {
    if (loadingDemo.value) {
      const timer = setTimeout(() => {
        loadingDemo.setFalse();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [loadingDemo.value]);

  return (
    <ShowcaseContainer>
      <AtomicBox textAlign="center" mb={6}>
        <AtomicText variant="h1" weight="extrabold" gradient robloxTheme>
          ⚛️ Atomic Design System
        </AtomicText>
        <AtomicText variant="lg" color="secondary" mt={2}>
          Building scalable, reusable UI components with atomic design methodology
        </AtomicText>
      </AtomicBox>

      {/* Atoms */}
      <AtomsShowcase />

      {/* Molecules */}
      <MoleculesShowcase />

      {/* Organisms */}
      <OrganismsShowcase />

      {/* HOCs */}
      <div className="section">
        <AtomicText variant="h2" weight="bold" gradient robloxTheme>
          🔄 HOCs - Component Enhancement
        </AtomicText>

        <AtomicBox display="flex" gap={2} mb={3}>
          <AtomicButton
            variant="primary"
            onClick={(e: React.MouseEvent) => loadingDemo.toggle}
            disabled={loadingDemo.value}
          >
            {loadingDemo.value ? 'Loading...' : 'Demo HOC Loading'}
          </AtomicButton>
        </AtomicBox>

        <LoadingDemo
          title="HOC Enhanced Component"
          loading={loadingDemo.value}
        />
      </div>

      {/* Component composition example */}
      <div className="section">
        <AtomicText variant="h2" weight="bold" gradient robloxTheme>
          🎯 Complete Example - Game Dashboard Card
        </AtomicText>

        <Card
          variant="game"
          title="Game Session Stats"
          subtitle="Real-time gaming metrics"
          interactive
          actions={
            <AtomicBox display="flex" gap={1}>
              <AtomicButton variant="outlined" size="sm">
                Export
              </AtomicButton>
              <AtomicButton variant="primary" size="sm">
                Refresh
              </AtomicButton>
            </AtomicBox>
          }
        >
          <AtomicBox display="grid" gridTemplateColumns="repeat(auto-fit, minmax(120px, 1fr))" gap={3}>
            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="primary">
                2,847
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Active Players
              </AtomicText>
            </AtomicBox>

            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="success">
                94.2%
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Uptime
              </AtomicText>
            </AtomicBox>

            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="warning">
                156ms
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Avg Latency
              </AtomicText>
            </AtomicBox>
          </AtomicBox>
        </Card>
      </div>
    </ShowcaseContainer>
  );
};

export default AtomicDesignShowcase;