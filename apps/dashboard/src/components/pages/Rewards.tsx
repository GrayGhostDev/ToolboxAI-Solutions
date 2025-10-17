import {
  Box,
  Button,
  Text,
  Paper,
  Stack,
  Grid,
  Card,
  List,
  Chip,
  Badge,
  Alert,
  Modal,
  Tabs,
  TextInput,
  Select,
  ActionIcon,
  Avatar,
  Container,
  Flex,
  Group,
  SimpleGrid,
  Title
} from '@mantine/core';
import {
  IconStar,
  IconPlus,
  IconSearch,
  IconCircleCheck,
  IconLock,
  IconTrendingUp,
  IconShoppingCart,
  IconAward,
  IconDiamond,
  IconGift,
  IconTags
} from '@tabler/icons-react';
import * as React from 'react';

import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { useApiCallOnMount } from '../../hooks/useApiCall';

interface Reward {
  id: string;
  name: string;
  description: string;
  category: 'avatar' | 'theme' | 'powerup' | 'certificate' | 'physical' | 'privilege';
  cost: number;
  imageUrl?: string;
  icon: React.ReactNode;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  stock?: number;
  requirements?: {
    level?: number;
    badges?: string[];
    achievements?: string[];
  };
  expiresAt?: string;
  redeemCount?: number;
  maxRedeems?: number;
}

interface RewardHistory {
  id: string;
  rewardId: string;
  rewardName: string;
  redeemedAt: string;
  cost: number;
  status: 'pending' | 'delivered' | 'used';
}

// Remove TabPanel component - Mantine Tabs handles this internally

export default function Rewards() {
  const dispatch = useAppDispatch();
  const { xp, level, badges } = useAppSelector((s) => s.gamification);
  const role = useAppSelector((s) => s.user.role);

  const [activeTab, setActiveTab] = useState<string | null>('available');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReward, setSelectedReward] = useState<Reward | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [, setEditDialogOpen] = useState(false);
  const [cart, setCart] = useState<Reward[]>([]);

  // Fetch rewards from API
  const { data: rewardsData, loading, error, refetch } = useApiCallOnMount(
    null,
    {
      mockEndpoint: '/student/rewards',
      showNotification: false,
    }
  );

  // Defensive data transformation - handle multiple API response formats
  const availableRewards: Reward[] = React.useMemo(() => {
    if (!rewardsData) return [];
    if (Array.isArray(rewardsData)) return rewardsData;

    // Handle case where API returns data wrapped in an object
    if (typeof rewardsData === 'object' && 'data' in rewardsData && Array.isArray(rewardsData.data)) {
      return rewardsData.data;
    }

    // Handle case where API returns items array
    if (typeof rewardsData === 'object' && 'items' in rewardsData && Array.isArray(rewardsData.items)) {
      return rewardsData.items;
    }

    // Handle case where API returns rewards array
    if (typeof rewardsData === 'object' && 'rewards' in rewardsData && Array.isArray(rewardsData.rewards)) {
      return rewardsData.rewards;
    }

    return [];
  }, [rewardsData]);

  // TODO: Fetch reward history from API
  const rewardHistory: RewardHistory[] = [];

  // Mantine tabs don't need custom change handler

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common':
        return '#757575';
      case 'rare':
        return '#2196F3';
      case 'epic':
        return '#9C27B0';
      case 'legendary':
        return '#FF9800';
      default:
        return '#757575';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'avatar':
        return <IconAward />;
      case 'theme':
        return <IconStar />;
      case 'powerup':
        return <IconTrendingUp />;
      case 'certificate':
        return <IconGift />;
      case 'physical':
        return <IconGift />;
      case 'privilege':
        return <IconTags />;
      default:
        return <IconStar />;
    }
  };

  const canRedeem = (reward: Reward) => {
    if (xp < reward.cost) return false;
    if (reward.requirements?.level && level < reward.requirements.level) return false;
    if (reward.stock !== undefined && reward.stock <= 0) return false;
    return true;
  };

  const handleRedeem = (reward: Reward) => {
    setSelectedReward(reward);
    setConfirmDialogOpen(true);
  };

  const confirmRedeem = () => {
    if (selectedReward) {
      // Here you would call the API to redeem the reward
      dispatch(addNotification({
        type: 'success',
        message: `Successfully redeemed ${selectedReward.name}!`,
        autoHide: true,
      }));
      
      // Update XP (would be done by backend)
      // dispatch(setXP(xp - selectedReward.cost));
    }
    setConfirmDialogOpen(false);
    setSelectedReward(null);
  };

  const addToCart = (reward: Reward) => {
    if (cart.find(r => r.id === reward.id)) {
      dispatch(addNotification({
        type: 'warning',
        message: 'This reward is already in your cart',
        autoHide: true,
      }));
      return;
    }
    setCart([...cart, reward]);
    dispatch(addNotification({
      type: 'success',
      message: `Added ${reward.name} to cart`,
      autoHide: true,
    }));
  };

  // const removeFromCart = (rewardId: string) => {
  //   setCart(cart.filter(r => r.id !== rewardId));
  // };

  const getTotalCartCost = () => {
    return cart.reduce((total, reward) => total + reward.cost, 0);
  };

  const handleRemoveReward = () => {
    // TODO: API call to remove reward from the system
    dispatch(addNotification({
      type: 'success',
      message: 'Reward removed successfully',
      autoHide: true,
    }));
  };

  const filteredRewards = availableRewards.filter(reward => {
    if (selectedCategory !== 'all' && reward.category !== selectedCategory) return false;
    if (searchTerm && !reward.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <Container size="xl">
      {/* Header */}
      <Card withBorder mb="md">
        <Card.Section p="md">
          <Stack gap="md">
            <Box>
              <Title order={2} mb="sm">
                Rewards Store
              </Title>
              <Group gap="sm">
                <Badge color="blue" variant="filled" size="lg">
                  {xp.toLocaleString()} XP Available
                </Badge>
                <Badge color="gray" variant="outline" size="lg">
                  Level {level}
                </Badge>
                <Badge variant="outline" size="lg">
                  {badges.length} Badges
                </Badge>
              </Group>
            </Box>

            <Group gap="sm">
              {role === 'teacher' && (
                <Button
                  variant="outline"
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  Create Reward
                </Button>
              )}
              <Button
                variant="filled"
                leftSection={<IconShoppingCart size={16} />}
                disabled={cart.length === 0}
                onClick={() => {
                  if (cart.length > 0) {
                    setConfirmDialogOpen(true);
                  }
                }}
              >
                Cart ({getTotalCartCost()} XP)
              </Button>
            </Group>
          </Stack>
        </Card.Section>
      </Card>

      {/* Main Content */}
      <Card>
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="available">Available Rewards</Tabs.Tab>
            <Tabs.Tab value="my-rewards">My Rewards</Tabs.Tab>
            <Tabs.Tab value="history">History</Tabs.Tab>
            {role === 'teacher' && <Tabs.Tab value="manage">Manage</Tabs.Tab>}
          </Tabs.List>

          {/* Available Rewards Tab */}
          <Tabs.Panel value="available">
            {/* Filters */}
            <Stack gap="sm" mb="lg">
              <Group gap="md">
                <TextInput
                  placeholder="Search rewards..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  leftSection={<IconSearch size={16} />}
                  style={{ minWidth: 200 }}
                />
                <Select
                  value={selectedCategory}
                  onChange={(value) => setSelectedCategory(value || 'all')}
                  placeholder="Category"
                  data={[
                    { value: 'all', label: 'All Categories' },
                    { value: 'avatar', label: 'Avatars' },
                    { value: 'theme', label: 'Themes' },
                    { value: 'powerup', label: 'Power-ups' },
                    { value: 'certificate', label: 'Certificates' },
                    { value: 'physical', label: 'Physical' },
                    { value: 'privilege', label: 'Privileges' },
                  ]}
                  style={{ minWidth: 150 }}
                />
              </Group>
            </Stack>

            {/* Rewards Grid */}
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="md">
              {filteredRewards.map((reward) => (
                <Card
                  key={reward.id}
                  style={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    border: `2px solid ${getRarityColor(reward.rarity)}`,
                    opacity: canRedeem(reward) ? 1 : 0.6,
                  }}
                  withBorder
                >
                  {/* Rarity Badge */}
                  <Badge
                    color={getRarityColor(reward.rarity)}
                    style={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      zIndex: 1,
                    }}
                  >
                    {reward.rarity.toUpperCase()}
                  </Badge>

                  <Card.Section p="md" style={{ flexGrow: 1 }}>
                    <Stack align="center" gap="sm">
                      <Box style={{ fontSize: 48 }}>{reward.icon}</Box>
                      <Text fw={600} ta="center">
                        {reward.name}
                      </Text>
                      <Text size="sm" c="dimmed" ta="center">
                        {reward.description}
                      </Text>

                      {/* Requirements */}
                      {reward.requirements && (
                        <Stack gap="xs" w="100%">
                          {reward.requirements.level && (
                            <Badge
                              color={level >= reward.requirements.level ? 'green' : 'red'}
                              leftSection={level >= reward.requirements.level ? <IconCircleCheck size={12} /> : <IconLock size={12} />}
                              variant="light"
                            >
                              Level {reward.requirements.level} Required
                            </Badge>
                          )}
                        </Stack>
                      )}

                      {/* Stock */}
                      {reward.stock !== undefined && (
                        <Badge
                          color={reward.stock > 0 ? 'blue' : 'red'}
                          variant="light"
                        >
                          {reward.stock} left
                        </Badge>
                      )}
                    </Stack>
                  </Card.Section>

                  <Card.Section p="sm" style={{ borderTop: '1px solid var(--mantine-color-gray-3)' }}>
                    <Group justify="space-between">
                      <Badge leftSection={<IconStar size={12} />} color="blue">
                        {reward.cost} XP
                      </Badge>
                      <Group gap="xs">
                        <ActionIcon
                          size="sm"
                          onClick={() => addToCart(reward)}
                          disabled={!canRedeem(reward)}
                        >
                          <IconPlus size={16} />
                        </ActionIcon>
                        <Button
                          size="xs"
                          variant="filled"
                          disabled={!canRedeem(reward)}
                          onClick={() => handleRedeem(reward)}
                        >
                          Redeem
                        </Button>
                      </Group>
                    </Group>
                  </Card.Section>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>

          {/* My Rewards Tab */}
          <Tabs.Panel value="my-rewards">
            <Alert color="blue" mb="md">
              <Text fw={600}>Your Redeemed Rewards</Text>
              <Text size="sm">These are the rewards you've already redeemed. Some may still be active!</Text>
            </Alert>

            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
              {rewardHistory
                .filter(h => h.status === 'delivered')
                .map((item) => {
                  const reward = availableRewards.find(r => r.id === item.rewardId);
                  if (!reward) return null;

                  return (
                    <Card key={item.id} withBorder>
                      <Card.Section p="md">
                        <Stack gap="sm">
                          <Group justify="space-between" align="center">
                            <Box style={{ fontSize: 32 }}>{reward.icon}</Box>
                            <Badge
                              color={item.status === 'delivered' ? 'green' : 'gray'}
                              variant="light"
                            >
                              {item.status}
                            </Badge>
                          </Group>
                          <Text fw={600}>{reward.name}</Text>
                          <Text size="sm" c="dimmed">
                            Redeemed: {new Date(item.redeemedAt).toLocaleDateString()}
                          </Text>
                          {reward.category === 'powerup' && (
                            <Button variant="filled" size="sm">
                              Activate
                            </Button>
                          )}
                        </Stack>
                      </Card.Section>
                    </Card>
                  );
                })}
            </SimpleGrid>
          </Tabs.Panel>

          {/* History Tab */}
          <Tabs.Panel value="history">
            <Stack gap="sm">
              {rewardHistory.map((item) => (
                <Paper key={item.id} p="md" withBorder>
                  <Group justify="space-between" align="center">
                    <Group gap="md">
                      <Avatar color="blue" radius="sm">
                        {getCategoryIcon(availableRewards.find(r => r.id === item.rewardId)?.category || '')}
                      </Avatar>
                      <Stack gap="xs">
                        <Text fw={600}>{item.rewardName}</Text>
                        <Text size="sm" c="dimmed">
                          Redeemed on {new Date(item.redeemedAt).toLocaleString()} • {item.cost} XP
                        </Text>
                      </Stack>
                    </Group>
                    <Badge
                      color={
                        item.status === 'delivered' ? 'green' :
                        item.status === 'used' ? 'blue' :
                        'yellow'
                      }
                      variant="light"
                    >
                      {item.status}
                    </Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Tabs.Panel>

          {/* Manage Tab (Teachers Only) */}
          {role === 'teacher' && (
            <Tabs.Panel value="manage">
              <Alert color="blue" mb="md">
                <Text fw={600}>Manage Rewards</Text>
                <Text size="sm">Create custom rewards for your students and manage existing ones.</Text>
              </Alert>

              <Stack gap="md">
                <Button
                  variant="filled"
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  Create New Reward
                </Button>

                <Title order={3}>Active Rewards</Title>

                <Stack gap="sm">
                  {availableRewards.map((reward) => (
                    <Paper key={reward.id} p="md" withBorder>
                      <Group justify="space-between" align="center">
                        <Group gap="md">
                          {reward.icon}
                          <Stack gap="xs">
                            <Text fw={600}>{reward.name}</Text>
                            <Text size="sm" c="dimmed">
                              {reward.cost} XP • {reward.rarity} • {reward.stock ? `${reward.stock} in stock` : 'Unlimited'}
                            </Text>
                          </Stack>
                        </Group>
                        <Group gap="xs">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedReward(reward);
                              setEditDialogOpen(true);
                            }}
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            color="red"
                            variant="outline"
                            onClick={handleRemoveReward}
                          >
                            Remove
                          </Button>
                        </Group>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </Stack>
            </Tabs.Panel>
          )}
        </Tabs>
      </Card>

      {/* Redeem Confirmation Modal */}
      <Modal
        opened={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        title="Confirm Redemption"
        centered
      >
        {selectedReward && (
          <Stack gap="md">
            <Text>
              Are you sure you want to redeem <Text fw={600} component="span">{selectedReward.name}</Text>?
            </Text>
            <Alert color="blue">
              This will cost {selectedReward.cost} XP. You currently have {xp} XP.
            </Alert>
            <Text size="sm" c="dimmed">
              After redemption: {xp - selectedReward.cost} XP remaining
            </Text>
            <Group justify="flex-end" gap="sm">
              <Button variant="outline" onClick={() => setConfirmDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="filled" onClick={confirmRedeem}>
                Confirm Redemption
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>

      {/* Create Reward Modal (Teachers) */}
      <Modal
        opened={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        title="Create New Reward"
        size="lg"
        centered
      >
        <Stack gap="md">
          <TextInput label="Reward Name" placeholder="Enter reward name" />
          <TextInput
            label="Description"
            placeholder="Enter reward description"
            minRows={3}
            autosize
          />
          <Select
            label="Category"
            placeholder="Select category"
            data={[
              { value: 'avatar', label: 'Avatar' },
              { value: 'theme', label: 'Theme' },
              { value: 'powerup', label: 'Power-up' },
              { value: 'certificate', label: 'Certificate' },
              { value: 'privilege', label: 'Privilege' },
            ]}
          />
          <TextInput label="XP Cost" type="number" placeholder="Enter XP cost" />
          <Select
            label="Rarity"
            placeholder="Select rarity"
            data={[
              { value: 'common', label: 'Common' },
              { value: 'rare', label: 'Rare' },
              { value: 'epic', label: 'Epic' },
              { value: 'legendary', label: 'Legendary' },
            ]}
          />
          <TextInput
            label="Stock (optional)"
            type="number"
            placeholder="Leave empty for unlimited"
            description="Leave empty for unlimited stock"
          />
          <TextInput
            label="Required Level (optional)"
            type="number"
            placeholder="Enter required level"
          />
          <Group justify="flex-end" gap="sm" mt="md">
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="filled"
              onClick={() => {
                dispatch(addNotification({
                  type: 'success',
                  message: 'Reward created successfully!',
                  autoHide: true,
                }));
                setCreateDialogOpen(false);
              }}
            >
              Create Reward
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}