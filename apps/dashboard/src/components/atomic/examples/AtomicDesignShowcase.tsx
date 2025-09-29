/**
 * Atomic Design Showcase
 *
 * A comprehensive example demonstrating how atomic design components
 * work together to create a cohesive, reusable interface.
 */

import React from 'react';
import { Box } from '@mantine/core';

// Atomic imports (migrated components)
import {
  AtomicInput,
  AtomicText,
  AtomicSpinner
} from '../atoms';

// Molecular imports (migrated components)
import { FormField, Card } from '../molecules';

// Compound imports (migrated components)
import { Table } from '../compound';

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

// Atoms showcase
const AtomsShowcase: React.FunctionComponent = () => {
  return (
    <Box mb={48}>
      <AtomicText variant="h2" weight="bold" gradient robloxTheme>
        🔬 Atoms - Basic Building Blocks
      </AtomicText>

      <Box style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 16,
        marginTop: 16
      }}>
        {/* Text variants */}
        <Card variant="roblox" title="Typography">
          <Box style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
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
          </Box>
        </Card>

        {/* Inputs */}
        <Card variant="roblox" title="Input Components">
          <Box style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <AtomicInput
              placeholder="Enter text..."
              variant="roblox"
              clearable
            />
            <AtomicInput
              type="password"
              placeholder="Password..."
              variant="default"
            />
            <AtomicSpinner variant="pulse" size="md" />
          </Box>
        </Card>
      </Box>
    </Box>
  );
};

// Molecules showcase
const MoleculesShowcase: React.FunctionComponent = () => {
  const [searchValue, setSearchValue] = React.useState('');
  const [email, setEmail] = React.useState('');

  return (
    <Box mb={48}>
      <AtomicText variant="h2" weight="bold" gradient robloxTheme>
        🧩 Molecules - Simple Combinations
      </AtomicText>

      <Box style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 16,
        marginTop: 16
      }}>
        {/* Form fields */}
        <Card variant="roblox" title="Form Fields">
          <Box style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
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
          </Box>
        </Card>

        {/* Player card */}
        <Card
          variant="game"
          title={gameData.player.name}
          subtitle={`Level ${gameData.player.level} Player`}
        >
          <Box style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Box>
              <AtomicText variant="sm" color="secondary">
                Experience Points
              </AtomicText>
              <AtomicText variant="lg" weight="bold" color="primary">
                {gameData.player.xp.toLocaleString()} / {gameData.player.maxXp.toLocaleString()}
              </AtomicText>
            </Box>

            <Box style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {gameData.player.achievements.map((achievement) => (
                <Box
                  key={achievement}
                  style={{
                    padding: '4px 8px',
                    backgroundColor: 'var(--mantine-color-blue-1)',
                    borderRadius: '4px',
                    border: '1px solid var(--mantine-color-blue-4)'
                  }}
                >
                  <AtomicText variant="xs">{achievement}</AtomicText>
                </Box>
              ))}
            </Box>
          </Box>
        </Card>
      </Box>
    </Box>
  );
};

// Organisms showcase (using compound components)
const OrganismsShowcase: React.FunctionComponent = () => {
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
    <Box mb={48}>
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
                  <Box
                    style={{
                      padding: '4px 8px',
                      backgroundColor: player.rank === 1 ? '#F59E0B' : player.rank === 2 ? '#6B7280' : '#8B4513',
                      color: 'white',
                      borderRadius: '4px',
                      textAlign: 'center',
                      minWidth: '24px'
                    }}
                  >
                    <AtomicText variant="xs" weight="bold">
                      {player.rank}
                    </AtomicText>
                  </Box>
                </Table.Cell>
                <Table.Cell>
                  <Box style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Box
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--mantine-color-blue-6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                      }}
                    >
                      <AtomicText variant="xs" weight="bold">
                        {player.name.slice(0, 2).toUpperCase()}
                      </AtomicText>
                    </Box>
                    <AtomicText weight="medium">{player.name}</AtomicText>
                  </Box>
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
    </Box>
  );
};

// Main showcase component
const AtomicDesignShowcase: React.FunctionComponent = () => {
  return (
    <Box
      style={{
        padding: '32px',
        maxWidth: '1200px',
        margin: '0 auto'
      }}
    >
      <Box style={{ textAlign: 'center', marginBottom: 48 }}>
        <AtomicText variant="h1" weight="extrabold" gradient robloxTheme>
          ⚛️ Atomic Design System
        </AtomicText>
        <AtomicText variant="lg" color="secondary" style={{ marginTop: 16 }}>
          Building scalable, reusable UI components with atomic design methodology
        </AtomicText>
      </Box>

      {/* Atoms */}
      <AtomsShowcase />

      {/* Molecules */}
      <MoleculesShowcase />

      {/* Organisms */}
      <OrganismsShowcase />

      {/* Component composition example */}
      <Box>
        <AtomicText variant="h2" weight="bold" gradient robloxTheme>
          🎯 Complete Example - Game Dashboard Card
        </AtomicText>

        <Card
          variant="game"
          title="Game Session Stats"
          subtitle="Real-time gaming metrics"
          interactive
        >
          <Box style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: 24
          }}>
            <Box style={{ textAlign: 'center' }}>
              <AtomicText variant="2xl" weight="bold" color="primary">
                2,847
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Active Players
              </AtomicText>
            </Box>

            <Box style={{ textAlign: 'center' }}>
              <AtomicText variant="2xl" weight="bold" color="success">
                94.2%
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Uptime
              </AtomicText>
            </Box>

            <Box style={{ textAlign: 'center' }}>
              <AtomicText variant="2xl" weight="bold" color="warning">
                156ms
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Avg Latency
              </AtomicText>
            </Box>
          </Box>
        </Card>
      </Box>
    </Box>
  );
};

export default AtomicDesignShowcase;