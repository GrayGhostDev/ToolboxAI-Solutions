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
  Title,
  Group,
} from "@mantine/core";
import {
  IconUser,
  IconPalette,
  IconShirt,
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
    icon: <IconUser />,
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
    icon: <IconShirt />,
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
    icon: <IconStar />,
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
    icon: <IconPalette />,
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

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case "common": return "default";
      case "rare": return "primary";
      case "epic": return "secondary";
      case "legendary": return "warning";
      default: return "default";
    }
  };

  const getEquippedItems = () => {
    return avatarItems.filter((item) => item.equipped);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Avatar Customization
      </Typography>

      <Grid container spacing={3}>
        {/* Avatar Preview */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Avatar Preview
              </Typography>

              <Box sx={{ position: "relative", mb: 3 }}>
                <Paper
                  elevation={3}
                  sx={{
                    p: 4,
                    borderRadius: 2,
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    minHeight: 300,
                  }}
                >
                  <Box sx={{ textAlign: "center" }}>
                    <MuiAvatar
                      sx={{
                        width: 150,
                        height: 150,
                        fontSize: "4rem",
                        margin: "0 auto",
                        mb: 2,
                        bgcolor: "white",
                        color: "primary.main",
                      }}
                    >
                      {getEquippedItems().map((item) => item.preview)[0] || "👤"}
                    </MuiAvatar>

                    <Typography variant="h5" sx={{ color: "white", mb: 1 }}>
                      {avatarName}
                    </Typography>

                    {avatarSettings.showLevel && (
                      <Chip
                        label={`Level ${userLevel}`}
                        color="primary"
                        size="small"
                        sx={{ mr: 1 }}
                      />
                    )}

                    {avatarSettings.showBadges && (
                      <Chip
                        icon={<IconTrophy />}
                        label="5 Badges"
                        color="secondary"
                        size="small"
                      />
                    )}
                  </Box>
                </Paper>

                <IconButton
                  sx={{
                    position: "absolute",
                    top: 10,
                    right: 10,
                    bgcolor: "white",
                    "&:hover": { bgcolor: "grey.100" },
                  }}
                  size="small"
                >
                  <IconCamera />
                </IconButton>
              </Box>

              <TextField
                fullWidth
                label="Avatar Name"
                value={avatarName}
                onChange={(e) => setAvatarName(e.target.value)}
                variant="outlined"
                size="small"
                sx={{ mb: 2 }}
                InputProps={{
                  endAdornment: <Edit fontSize="small" />,
                }}
              />

              <Stack spacing={1}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={avatarSettings.showBadges}
                      onChange={(e) =>
                        setAvatarSettings({ ...avatarSettings, showBadges: e.target.checked })
                      }
                    />
                  }
                  label="Show Badges"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={avatarSettings.showLevel}
                      onChange={(e) =>
                        setAvatarSettings({ ...avatarSettings, showLevel: e.target.checked })
                      }
                    />
                  }
                  label="Show Level"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={avatarSettings.animatedEffects}
                      onChange={(e) =>
                        setAvatarSettings({ ...avatarSettings, animatedEffects: e.target.checked })
                      }
                    />
                  }
                  label="Animated Effects"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={avatarSettings.publicProfile}
                      onChange={(e) =>
                        setAvatarSettings({ ...avatarSettings, publicProfile: e.target.checked })
                      }
                    />
                  }
                  label="Public Profile"
                />
              </Stack>

              <Divider sx={{ my: 2 }} />

              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  fullWidth
                  leftSection={<IconDeviceFloppy />}
                  onClick={handleSaveAvatar}
                >
                  Save Avatar
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  leftSection={<IconRefresh />}
                  onClick={handleRandomize}
                >
                  Randomize
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Customization Options */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Customization Options</Typography>
                <Button
                  variant="outlined"
                  leftSection={<IconShoppingCart />}
                  onClick={() => setShowShop(!showShop)}
                >
                  {showShop ? "My Items" : "Shop"}
                </Button>
              </Stack>

              <Tabs
                value={selectedCategory}
                onChange={(_, value) => setSelectedCategory(value)}
                variant="scrollable"
                scrollButtons="auto"
                sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}
              >
                {AVATAR_CATEGORIES.map((category) => (
                  <Tab
                    key={category.id}
                    label={category.name}
                    value={category.id}
                    icon={category.icon as React.ReactElement}
                    iconPosition="start"
                  />
                ))}
              </Tabs>

              <Grid container spacing={2}>
                {currentCategory?.items
                  .filter((item) => showShop || item.owned)
                  .map((item) => (
                    <Grid item xs={6} sm={4} md={3} key={item.id}>
                      <Card
                        sx={{
                          position: "relative",
                          cursor: item.owned ? "pointer" : "default",
                          border: item.equipped ? 2 : 1,
                          borderColor: item.equipped ? "primary.main" : "divider",
                          transition: "all 0.2s",
                          "&:hover": item.owned ? {
                            transform: "translateY(-4px)",
                            boxShadow: 3,
                          } : {},
                        }}
                        onClick={() => item.owned && handleEquipItem(item.id)}
                      >
                        <CardContent sx={{ textAlign: "center", p: 1.5 }}>
                          <Typography fontSize="2.5rem">{item.preview}</Typography>
                          <Typography variant="body2" noWrap>
                            {item.name}
                          </Typography>

                          <Chip
                            label={item.rarity}
                            size="small"
                            color={getRarityColor(item.rarity) as any}
                            sx={{ mt: 0.5 }}
                          />

                          {!item.owned && (
                            <>
                              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                {item.xpCost} XP
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Level {item.levelRequired}
                              </Typography>
                            </>
                          )}

                          {item.equipped && (
                            <Chip
                              label="Equipped"
                              color="success"
                              size="small"
                              sx={{ mt: 1 }}
                            />
                          )}
                        </CardContent>

                        {!item.owned && (
                          <Box
                            sx={{
                              position: "absolute",
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              bgcolor: "rgba(0,0,0,0.6)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              flexDirection: "column",
                            }}
                          >
                            {userLevel >= item.levelRequired ? (
                              <IconButton
                                color="primary"
                                sx={{ bgcolor: "white", "&:hover": { bgcolor: "grey.100" } }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handlePurchaseItem(item);
                                }}
                              >
                                <IconShoppingCart />
                              </IconButton>
                            ) : (
                              <Lock sx={{ color: "white" }} />
                            )}
                          </Box>
                        )}
                      </Card>
                    </Grid>
                  ))}
              </Grid>

              {showShop && (
                <Box sx={{ mt: 3, p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    💡 <strong>Tip:</strong> Earn more XP by completing lessons and challenges to unlock rare items!
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Your XP: <strong>{userXP}</strong> | Level: <strong>{userLevel}</strong>
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
