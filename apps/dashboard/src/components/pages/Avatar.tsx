import * as React from "react";
import { useState } from "react";
import {
  Box,
  Card,
  Text,
  Grid,
  Button,
  Stack,
  Badge,
  ActionIcon,
  Tabs,
  Avatar as MantineAvatar,
  Paper,
  Slider,
  Switch,
  Divider,
  TextInput,
  Modal,
  Group,
} from "@mantine/core";
import {
  IconUser,
  IconPalette,
  IconHanger,
  IconTrophy,
  IconLock,
  IconLockOpen,
  IconDeviceFloppy,
  IconRefresh,
  IconCamera,
  IconEdit,
  IconShoppingCart,
  IconStar,
} from "@tabler/icons-react";
import { useAppSelector, useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";

interface AvatarCategory {
  id: string;
  name: string;
  icon: React.ReactNode;
  items: AvatarItem[];
}

interface AvatarItem {
  id: string;
  name: string;
  preview: string;
  category: string;
  rarity: "common" | "rare" | "epic" | "legendary";
  xpCost: number;
  levelRequired: number;
  owned: boolean;
  equipped: boolean;
}

const AVATAR_CATEGORIES: AvatarCategory[] = [
  {
    id: "hairstyles",
    name: "Hairstyles",
    icon: <IconUser size={20} />,
    items: [
      { id: "hair_1", name: "Short & Neat", preview: "👱", category: "hairstyles", rarity: "common", xpCost: 0, levelRequired: 1, owned: true, equipped: true },
      { id: "hair_2", name: "Long & Wavy", preview: "👩", category: "hairstyles", rarity: "common", xpCost: 50, levelRequired: 2, owned: true, equipped: false },
      { id: "hair_3", name: "Mohawk", preview: "🎸", category: "hairstyles", rarity: "rare", xpCost: 150, levelRequired: 5, owned: false, equipped: false },
      { id: "hair_4", name: "Rainbow Spikes", preview: "🌈", category: "hairstyles", rarity: "epic", xpCost: 300, levelRequired: 10, owned: false, equipped: false },
      { id: "hair_5", name: "Galaxy Hair", preview: "🌌", category: "hairstyles", rarity: "legendary", xpCost: 500, levelRequired: 15, owned: false, equipped: false },
    ],
  },
  {
    id: "outfits",
    name: "Outfits",
    icon: <IconHanger size={20} />,
    items: [
      { id: "outfit_1", name: "School Uniform", preview: "👔", category: "outfits", rarity: "common", xpCost: 0, levelRequired: 1, owned: true, equipped: true },
      { id: "outfit_2", name: "Casual Wear", preview: "👕", category: "outfits", rarity: "common", xpCost: 75, levelRequired: 2, owned: true, equipped: false },
      { id: "outfit_3", name: "Sports Jersey", preview: "🏈", category: "outfits", rarity: "rare", xpCost: 200, levelRequired: 6, owned: false, equipped: false },
      { id: "outfit_4", name: "Space Suit", preview: "🚀", category: "outfits", rarity: "epic", xpCost: 400, levelRequired: 12, owned: false, equipped: false },
      { id: "outfit_5", name: "Dragon Armor", preview: "🐉", category: "outfits", rarity: "legendary", xpCost: 750, levelRequired: 20, owned: false, equipped: false },
    ],
  },
  {
    id: "accessories",
    name: "Accessories",
    icon: <IconStar size={20} />,
    items: [
      { id: "acc_1", name: "Reading Glasses", preview: "👓", category: "accessories", rarity: "common", xpCost: 25, levelRequired: 1, owned: true, equipped: false },
      { id: "acc_2", name: "Cool Sunglasses", preview: "🕶️", category: "accessories", rarity: "common", xpCost: 50, levelRequired: 3, owned: false, equipped: false },
      { id: "acc_3", name: "Magic Hat", preview: "🎩", category: "accessories", rarity: "rare", xpCost: 175, levelRequired: 7, owned: false, equipped: false },
      { id: "acc_4", name: "Crown of Wisdom", preview: "👑", category: "accessories", rarity: "epic", xpCost: 350, levelRequired: 14, owned: false, equipped: false },
      { id: "acc_5", name: "Phoenix Wings", preview: "🔥", category: "accessories", rarity: "legendary", xpCost: 600, levelRequired: 18, owned: false, equipped: false },
    ],
  },
  {
    id: "backgrounds",
    name: "Backgrounds",
    icon: <IconPalette size={20} />,
    items: [
      { id: "bg_1", name: "Classroom", preview: "🏫", category: "backgrounds", rarity: "common", xpCost: 0, levelRequired: 1, owned: true, equipped: true },
      { id: "bg_2", name: "Library", preview: "📚", category: "backgrounds", rarity: "common", xpCost: 40, levelRequired: 2, owned: true, equipped: false },
      { id: "bg_3", name: "Laboratory", preview: "🔬", category: "backgrounds", rarity: "rare", xpCost: 125, levelRequired: 5, owned: false, equipped: false },
      { id: "bg_4", name: "Space Station", preview: "🛸", category: "backgrounds", rarity: "epic", xpCost: 275, levelRequired: 11, owned: false, equipped: false },
      { id: "bg_5", name: "Mystic Portal", preview: "🌀", category: "backgrounds", rarity: "legendary", xpCost: 450, levelRequired: 16, owned: false, equipped: false },
    ],
  },
];

export default function Avatar() {
  const dispatch = useAppDispatch();
  const userXP = useAppSelector((s) => s.gamification?.xp ?? 0);
  const userLevel = useAppSelector((s) => s.gamification?.level ?? 1);

  const [selectedCategory, setSelectedCategory] = useState("hairstyles");
  const [avatarItems, setAvatarItems] = useState<AvatarItem[]>(
    AVATAR_CATEGORIES.flatMap((cat) => cat.items)
  );
  const [avatarName, setAvatarName] = useState("Cool Student");
  const [showShop, setShowShop] = useState(false);
  const [avatarSettings, setAvatarSettings] = useState({
    showBadges: true,
    showLevel: true,
    animatedEffects: true,
    publicProfile: true,
  });

  const currentCategory = AVATAR_CATEGORIES.find((cat) => cat.id === selectedCategory);

  const handleEquipItem = (itemId: string) => {
    setAvatarItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId && item.owned) {
          // Unequip all items in the same category, then equip this one
          const newEquipped = item.category === currentCategory?.id ? !item.equipped : item.equipped;
          return { ...item, equipped: newEquipped };
        } else if (item.category === currentCategory?.id) {
          return { ...item, equipped: false };
        }
        return item;
      })
    );

    dispatch(addNotification({
      message: "Avatar item equipped!",
      type: "success",
    }));
  };

  const handlePurchaseItem = (item: AvatarItem) => {
    if (userXP >= item.xpCost && userLevel >= item.levelRequired) {
      setAvatarItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, owned: true } : i))
      );

      dispatch(addNotification({
        message: `Purchased ${item.name} for ${item.xpCost} XP!`,
        type: "success",
      }));
    } else {
      dispatch(addNotification({
        message: "Insufficient XP or level requirement not met",
        type: "error",
      }));
    }
  };

  const handleSaveAvatar = () => {
    // In production, this would save to the backend
    dispatch(addNotification({
      message: "Avatar saved successfully!",
      type: "success",
    }));
  };

  const handleRandomize = () => {
    // Randomize equipped items from owned items
    const categories = ["hairstyles", "outfits", "accessories", "backgrounds"];

    setAvatarItems((prev) => {
      const newItems = [...prev];
      categories.forEach((category) => {
        const ownedInCategory = newItems.filter((item) => item.category === category && item.owned);
        if (ownedInCategory.length > 0) {
          // Unequip all in category
          newItems.forEach((item) => {
            if (item.category === category) {
              item.equipped = false;
            }
          });
          // Equip random one
          const randomItem = ownedInCategory[Math.floor(Math.random() * ownedInCategory.length)];
          const itemIndex = newItems.findIndex((item) => item.id === randomItem.id);
          if (itemIndex !== -1) {
            newItems[itemIndex].equipped = true;
          }
        }
      });
      return newItems;
    });

    dispatch(addNotification({
      message: "Avatar randomized!",
      type: "info",
    }));
  };

  const getRarityColor = (rarity: string): "blue" | "green" | "grape" | "yellow" => {
    switch (rarity) {
      case "common": return "blue";
      case "rare": return "green";
      case "epic": return "grape";
      case "legendary": return "yellow";
      default: return "blue";
    }
  };

  const getEquippedItems = () => {
    return avatarItems.filter((item) => item.equipped);
  };

  return (
    <Box>
      <Text size="xl" fw={600} mb="md">
        Avatar Customization
      </Text>

      <Grid gutter="lg">
        {/* Avatar Preview */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card>
            <Text size="lg" fw={600} mb="md">
              Avatar Preview
            </Text>

            <Box style={{ position: "relative", marginBottom: "1.5rem" }}>
              <Paper
                shadow="md"
                p="xl"
                radius="md"
                style={{
                  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  minHeight: 300,
                }}
              >
                <Box style={{ textAlign: "center" }}>
                  <MantineAvatar
                    size={150}
                    style={{
                      fontSize: "4rem",
                      margin: "0 auto",
                      marginBottom: "1rem",
                      backgroundColor: "white",
                      color: "#00bfff",
                    }}
                  >
                    {getEquippedItems().map((item) => item.preview)[0] || "👤"}
                  </MantineAvatar>

                  <Text size="xl" fw={600} c="white" mb="xs">
                    {avatarName}
                  </Text>

                  <Group justify="center" gap="xs">
                    {avatarSettings.showLevel && (
                      <Badge color="blue" size="sm">
                        Level {userLevel}
                      </Badge>
                    )}

                    {avatarSettings.showBadges && (
                      <Badge
                        color="grape"
                        size="sm"
                        leftSection={<IconTrophy size={12} />}
                      >
                        5 Badges
                      </Badge>
                    )}
                  </Group>
                </Box>
              </Paper>

              <ActionIcon
                style={{
                  position: "absolute",
                  top: 10,
                  right: 10,
                  backgroundColor: "white",
                }}
                size="sm"
              >
                <IconCamera size={16} />
              </ActionIcon>
            </Box>

            <TextInput
              label="Avatar Name"
              value={avatarName}
              onChange={(e) => setAvatarName(e.target.value)}
              size="sm"
              mb="md"
              rightSection={<IconEdit size={16} />}
            />

            <Stack gap="xs">
              <Switch
                label="Show Badges"
                checked={avatarSettings.showBadges}
                onChange={(e) =>
                  setAvatarSettings({ ...avatarSettings, showBadges: e.currentTarget.checked })
                }
              />
              <Switch
                label="Show Level"
                checked={avatarSettings.showLevel}
                onChange={(e) =>
                  setAvatarSettings({ ...avatarSettings, showLevel: e.currentTarget.checked })
                }
              />
              <Switch
                label="Animated Effects"
                checked={avatarSettings.animatedEffects}
                onChange={(e) =>
                  setAvatarSettings({ ...avatarSettings, animatedEffects: e.currentTarget.checked })
                }
              />
              <Switch
                label="Public Profile"
                checked={avatarSettings.publicProfile}
                onChange={(e) =>
                  setAvatarSettings({ ...avatarSettings, publicProfile: e.currentTarget.checked })
                }
              />
            </Stack>

            <Divider my="md" />

            <Group grow>
              <Button
                variant="filled"
                leftSection={<IconDeviceFloppy size={16} />}
                onClick={handleSaveAvatar}
              >
                Save Avatar
              </Button>
              <Button
                variant="outline"
                leftSection={<IconRefresh size={16} />}
                onClick={handleRandomize}
              >
                Randomize
              </Button>
            </Group>
          </Card>
        </Grid.Col>

        {/* Customization Options */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card>
            <Group justify="space-between" mb="md">
              <Text size="lg" fw={600}>Customization Options</Text>
              <Button
                variant="outline"
                leftSection={<IconShoppingCart size={16} />}
                onClick={() => setShowShop(!showShop)}
              >
                {showShop ? "My Items" : "Shop"}
              </Button>
            </Group>

            <Tabs value={selectedCategory} onChange={(value) => setSelectedCategory(value || "hairstyles")}>
              <Tabs.List mb="md">
                {AVATAR_CATEGORIES.map((category) => (
                  <Tabs.Tab
                    key={category.id}
                    value={category.id}
                    leftSection={category.icon}
                  >
                    {category.name}
                  </Tabs.Tab>
                ))}
              </Tabs.List>

              <Grid gutter="md">
                {currentCategory?.items
                  .filter((item) => showShop || item.owned)
                  .map((item) => (
                    <Grid.Col span={{ base: 6, sm: 4, md: 3 }} key={item.id}>
                      <Card
                        style={{
                          position: "relative",
                          cursor: item.owned ? "pointer" : "default",
                          borderWidth: item.equipped ? 2 : 1,
                          borderColor: item.equipped ? "#00bfff" : undefined,
                          transition: "all 0.2s",
                        }}
                        onClick={() => item.owned && handleEquipItem(item.id)}
                        withBorder
                        padding="sm"
                      >
                        <Box style={{ textAlign: "center" }}>
                          <Text size="2.5rem">{item.preview}</Text>
                          <Text size="sm" lineClamp={1}>
                            {item.name}
                          </Text>

                          <Badge
                            size="sm"
                            color={getRarityColor(item.rarity)}
                            mt="xs"
                          >
                            {item.rarity}
                          </Badge>

                          {!item.owned && (
                            <>
                              <Text size="xs" mt="xs">
                                {item.xpCost} XP
                              </Text>
                              <Text size="xs" c="dimmed">
                                Level {item.levelRequired}
                              </Text>
                            </>
                          )}

                          {item.equipped && (
                            <Badge
                              color="green"
                              size="sm"
                              mt="xs"
                            >
                              Equipped
                            </Badge>
                          )}
                        </Box>

                        {!item.owned && (
                          <Box
                            style={{
                              position: "absolute",
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              backgroundColor: "rgba(0,0,0,0.6)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              flexDirection: "column",
                            }}
                          >
                            {userLevel >= item.levelRequired ? (
                              <ActionIcon
                                color="blue"
                                size="lg"
                                style={{ backgroundColor: "white" }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handlePurchaseItem(item);
                                }}
                              >
                                <IconShoppingCart size={20} />
                              </ActionIcon>
                            ) : (
                              <IconLock size={24} color="white" />
                            )}
                          </Box>
                        )}
                      </Card>
                    </Grid.Col>
                  ))}
              </Grid>

              {showShop && (
                <Box mt="lg" p="md" style={{ backgroundColor: "var(--mantine-color-gray-0)", borderRadius: "4px" }}>
                  <Text size="sm" c="dimmed">
                    💡 <strong>Tip:</strong> Earn more XP by completing lessons and challenges to unlock rare items!
                  </Text>
                  <Text size="sm" mt="xs">
                    Your XP: <strong>{userXP}</strong> | Level: <strong>{userLevel}</strong>
                  </Text>
                </Box>
              )}
            </Tabs>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
}
