/**
 * Component Composition Examples
 *
 * Demonstrates how to compose atomic design components to create
 * complex, reusable interfaces following best practices.
 */

import React from 'react';
import {
  AtomicButton,
  AtomicInput,
  AtomicText,
  AtomicBox,
  AtomicAvatar,
  AtomicBadge
} from '../atoms';
import { FormField, Card } from '../molecules';
import { Table } from '../compound';
import { withLoading, withErrorBoundary } from '../hoc';
import { useToggle, useDisclosure } from '../../../hooks/atomic';

// Example 1: Form Composition
export const RegistrationForm: React.FunctionComponent<Record<string, any>> = () => {
  const [formData, setFormData] = React.useState({
    username: '',
    email: '',
    password: ''
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const loadingState = useToggle(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    loadingState.setTrue();

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('Form submitted:', formData);
    } catch (error) {
      console.error('Submission failed:', error);
    } finally {
      loadingState.setFalse();
    }
  };

  const updateField = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Card
      variant="roblox"
      title="Join the Adventure!"
      subtitle="Create your Roblox account"
    >
      <AtomicBox as="form" onSubmit={handleSubmit} display="flex" flexDirection="column" gap={3}>
        <FormField
          label="Username"
          placeholder="Choose a unique username"
          value={formData.username}
          onChange={updateField('username')}
          required
          state={errors.username ? 'error' : 'default'}
          errorText={errors.username}
          showCharacterCount
          maxLength={20}
          helperText="This will be your display name in games"
        />

        <FormField
          label="Email Address"
          type="email"
          placeholder="your@email.com"
          value={formData.email}
          onChange={updateField('email')}
          required
          state={errors.email ? 'error' : 'default'}
          errorText={errors.email}
        />

        <FormField
          label="Password"
          type="password"
          placeholder="Create a strong password"
          value={formData.password}
          onChange={updateField('password')}
          required
          state={errors.password ? 'error' : 'default'}
          errorText={errors.password}
          helperText="Must be at least 8 characters long"
        />

        <AtomicButton
          type="submit"
          variant="primary"
          size="lg"
          loading={loadingState.value}
          loadingText="Creating account..."
          disabled={!formData.username || !formData.email || !formData.password}
          fullWidth
        >
          Start Playing!
        </AtomicButton>
      </AtomicBox>
    </Card>
  );
};

// Example 2: Data Display with Interactive Elements
export const PlayerLeaderboard: React.FunctionComponent<Record<string, any>> = () => {
  const [sortField, setSortField] = React.useState<'rank' | 'name' | 'score' | 'level'>('rank');
  const [sortDirection, setSortDirection] = React.useState<'asc' | 'desc'>('asc');
  const [selectedPlayers, setSelectedPlayers] = React.useState<Set<string>>(new Set());

  const players = [
    { id: '1', rank: 1, name: 'EpicBuilder2024', score: 142500, level: 89, status: 'online' as const },
    { id: '2', rank: 2, name: 'RobloxMaster', score: 138900, level: 87, status: 'away' as const },
    { id: '3', rank: 3, name: 'GameDevPro', score: 135200, level: 85, status: 'online' as const },
    { id: '4', rank: 4, name: 'CreativeGamer', score: 128750, level: 82, status: 'offline' as const },
    { id: '5', rank: 5, name: 'BlockBuilder', score: 124300, level: 80, status: 'online' as const }
  ];

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const togglePlayerSelection = (playerId: string) => {
    setSelectedPlayers(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(playerId)) {
        newSelection.delete(playerId);
      } else {
        newSelection.add(playerId);
      }
      return newSelection;
    });
  };

  const getRarityBadge = (rank: number) => {
    if (rank === 1) return 'legendary';
    if (rank <= 3) return 'epic';
    if (rank <= 10) return 'rare';
    return 'common';
  };

  return (
    <Card
      variant="roblox"
      title="🏆 Player Leaderboard"
      subtitle="Top performers this week"
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
      {selectedPlayers.size > 0 && (
        <AtomicBox
          p={2}
          mb={3}
          bg="rgba(226, 35, 26, 0.1)"
          borderRadius="md"
          display="flex"
          justifyContent="space-between"
          alignItems="center"
        >
          <AtomicText variant="sm" weight="medium">
            {selectedPlayers.size} player{selectedPlayers.size > 1 ? 's' : ''} selected
          </AtomicText>
          <AtomicBox display="flex" gap={1}>
            <AtomicButton variant="outlined" size="sm">
              Compare
            </AtomicButton>
            <AtomicButton variant="outlined" size="sm">
              Message
            </AtomicButton>
          </AtomicBox>
        </AtomicBox>
      )}

      <Table variant="roblox" selectable>
        <Table.Header>
          <Table.Row>
            <Table.Cell as="th" width={60}>
              Select
            </Table.Cell>
            <Table.Cell
              as="th"
              sortable
              sorted={sortField === 'rank' ? sortDirection : false}
              onSort={() => handleSort('rank')}
              width={80}
            >
              Rank
            </Table.Cell>
            <Table.Cell
              as="th"
              sortable
              sorted={sortField === 'name' ? sortDirection : false}
              onSort={() => handleSort('name')}
            >
              Player
            </Table.Cell>
            <Table.Cell
              as="th"
              sortable
              sorted={sortField === 'score' ? sortDirection : false}
              onSort={() => handleSort('score')}
              align="right"
            >
              Score
            </Table.Cell>
            <Table.Cell
              as="th"
              sortable
              sorted={sortField === 'level' ? sortDirection : false}
              onSort={() => handleSort('level')}
              align="center"
            >
              Level
            </Table.Cell>
            <Table.Cell as="th" align="center">
              Status
            </Table.Cell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          {players.map((player) => (
            <Table.Row
              key={player.id}
              selected={selectedPlayers.has(player.id)}
              onClick={(e: React.MouseEvent) => () => togglePlayerSelection(player.id)}
            >
              <Table.Cell>
                <input
                  type="checkbox"
                  checked={selectedPlayers.has(player.id)}
                  onChange={() => togglePlayerSelection(player.id)}
                />
              </Table.Cell>

              <Table.Cell>
                <AtomicBadge
                  variant="achievement"
                  rarity={getRarityBadge(player.rank)}
                  badgeContent={player.rank}
                  glow={player.rank <= 3}
                >
                  <span />
                </AtomicBadge>
              </Table.Cell>

              <Table.Cell>
                <AtomicBox display="flex" alignItems="center" gap={2}>
                  <AtomicAvatar
                    size="sm"
                    status={player.status}
                    level={player.level}
                    robloxTheme
                  >
                    {player.name.slice(0, 2).toUpperCase()}
                  </AtomicAvatar>
                  <AtomicBox>
                    <AtomicText variant="sm" weight="medium">
                      {player.name}
                    </AtomicText>
                  </AtomicBox>
                </AtomicBox>
              </Table.Cell>

              <Table.Cell align="right">
                <AtomicText variant="base" weight="bold" color="primary">
                  {player.score.toLocaleString()}
                </AtomicText>
              </Table.Cell>

              <Table.Cell align="center">
                <AtomicBadge
                  variant="standard"
                  color="info"
                  badgeContent={player.level}
                >
                  <AtomicText variant="xs">LVL</AtomicText>
                </AtomicBadge>
              </Table.Cell>

              <Table.Cell align="center">
                <AtomicBox
                  w={8}
                  h={8}
                  borderRadius="50%"
                  bg={
                    player.status === 'online' ? '#22C55E' :
                    player.status === 'away' ? '#F59E0B' : '#6B7280'
                  }
                  title={player.status}
                />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </Card>
  );
};

// Example 3: HOC Enhanced Component
const EnhancedGameStats = withErrorBoundary(
  withLoading(
    ({ gameId }: { gameId: string }) => {
      const [stats, setStats] = React.useState(null);

      React.useEffect(() => {
        // Simulate data fetching
        setTimeout(() => {
          setStats({
            activePlayers: 2847,
            totalSessions: 15234,
            avgPlayTime: '12m 34s',
            satisfaction: 94.2
          });
        }, 1500);
      }, [gameId]);

      if (!stats) return null;

      return (
        <Card variant="game" title="Game Analytics" subtitle={`Game ID: ${gameId}`}>
          <AtomicBox display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={3}>
            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="primary">
                {stats.activePlayers.toLocaleString()}
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Active Players
              </AtomicText>
            </AtomicBox>

            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="success">
                {stats.totalSessions.toLocaleString()}
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Total Sessions
              </AtomicText>
            </AtomicBox>

            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="info">
                {stats.avgPlayTime}
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Avg Play Time
              </AtomicText>
            </AtomicBox>

            <AtomicBox textAlign="center">
              <AtomicText variant="2xl" weight="bold" color="warning">
                {stats.satisfaction}%
              </AtomicText>
              <AtomicText variant="sm" color="secondary">
                Satisfaction
              </AtomicText>
            </AtomicBox>
          </AtomicBox>
        </Card>
      );
    },
    { loadingText: 'Loading game stats...' }
  ),
  { onError: (error) => console.error('Game stats error:', error) }
);

// Main composition example
export const ComponentCompositionShowcase: React.FunctionComponent<Record<string, any>> = () => {
  const gameStatsModal = useDisclosure();

  return (
    <AtomicBox p={4} display="flex" flexDirection="column" gap={4}>
      <AtomicText variant="h1" weight="bold" gradient>
        🎮 Component Composition Examples
      </AtomicText>

      <AtomicText variant="lg" color="secondary">
        These examples demonstrate how atomic design components work together
        to create complex, interactive interfaces.
      </AtomicText>

      {/* Registration Form */}
      <AtomicBox>
        <AtomicText variant="h3" weight="semibold" mb={3}>
          Example 1: Registration Form
        </AtomicText>
        <RegistrationForm />
      </AtomicBox>

      {/* Player Leaderboard */}
      <AtomicBox>
        <AtomicText variant="h3" weight="semibold" mb={3}>
          Example 2: Interactive Data Table
        </AtomicText>
        <PlayerLeaderboard />
      </AtomicBox>

      {/* HOC Enhanced Component */}
      <AtomicBox>
        <AtomicText variant="h3" weight="semibold" mb={3}>
          Example 3: HOC Enhanced Component
        </AtomicText>
        <AtomicButton
          variant="primary"
          onClick={(e: React.MouseEvent) => gameStatsModal.open}
          mb={2}
        >
          Load Game Stats
        </AtomicButton>
        {gameStatsModal.isOpen && (
          <AtomicBox>
            <EnhancedGameStats gameId="game-123" loading={true} />
            <AtomicButton
              variant="outlined"
              onClick={(e: React.MouseEvent) => gameStatsModal.close}
              mt={2}
            >
              Close Stats
            </AtomicButton>
          </AtomicBox>
        )}
      </AtomicBox>
    </AtomicBox>
  );
};

export default ComponentCompositionShowcase;