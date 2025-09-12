import * as React from "react";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Stack,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Tab,
  Tabs,
  Alert,
  AlertTitle,
  Grid,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  Paper,
  InputAdornment,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import StarIcon from "@mui/icons-material/Star";
import DiamondIcon from "@mui/icons-material/Diamond";
import CardGiftcardIcon from "@mui/icons-material/CardGiftcard";
import LocalOfferIcon from "@mui/icons-material/LocalOffer";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import LockIcon from "@mui/icons-material/Lock";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import SearchIcon from "@mui/icons-material/Search";
import AddIcon from "@mui/icons-material/Add";
import { useAppSelector, useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";

interface Reward {
  id: string;
  name: string;
  description: string;
  category: "avatar" | "theme" | "powerup" | "certificate" | "physical" | "privilege";
  cost: number;
  imageUrl?: string;
  icon: React.ReactNode;
  rarity: "common" | "rare" | "epic" | "legendary";
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
  status: "pending" | "delivered" | "used";
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`rewards-tabpanel-${index}`}
      aria-labelledby={`rewards-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Rewards() {
  const dispatch = useAppDispatch();
  const { xp, level, badges } = useAppSelector((s) => s.gamification);
  const role = useAppSelector((s) => s.user.role);
  
  const [activeTab, setActiveTab] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedReward, setSelectedReward] = useState<Reward | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [, setEditDialogOpen] = useState(false);
  const [cart, setCart] = useState<Reward[]>([]);
  
  // Mock rewards data
  const availableRewards: Reward[] = [
    {
      id: "1",
      name: "Golden Avatar Frame",
      description: "Show off your achievements with this exclusive golden frame",
      category: "avatar",
      cost: 500,
      icon: <EmojiEventsIcon sx={{ color: "#FFD700" }} />,
      rarity: "epic",
      requirements: { level: 10 },
    },
    {
      id: "2",
      name: "Dark Mode Theme",
      description: "Unlock the sleek dark mode theme for your dashboard",
      category: "theme",
      cost: 300,
      icon: <StarIcon sx={{ color: "#9C27B0" }} />,
      rarity: "rare",
    },
    {
      id: "3",
      name: "Double XP Booster (1 Hour)",
      description: "Earn double XP for the next hour of learning",
      category: "powerup",
      cost: 200,
      icon: <TrendingUpIcon sx={{ color: "#4CAF50" }} />,
      rarity: "common",
      stock: 10,
      maxRedeems: 3,
    },
    {
      id: "4",
      name: "Diamond Badge",
      description: "The ultimate badge for top performers",
      category: "avatar",
      cost: 1000,
      icon: <DiamondIcon sx={{ color: "#00BCD4" }} />,
      rarity: "legendary",
      requirements: { level: 20, badges: ["gold_star", "perfect_score"] },
    },
    {
      id: "5",
      name: "Certificate of Excellence",
      description: "Official certificate recognizing your outstanding performance",
      category: "certificate",
      cost: 750,
      icon: <CardGiftcardIcon sx={{ color: "#FF9800" }} />,
      rarity: "epic",
      requirements: { level: 15 },
    },
    {
      id: "6",
      name: "Extra Homework Pass",
      description: "Skip one homework assignment without penalty",
      category: "privilege",
      cost: 400,
      icon: <LocalOfferIcon sx={{ color: "#E91E63" }} />,
      rarity: "rare",
      stock: 5,
      maxRedeems: 1,
    },
    {
      id: "7",
      name: "Custom Username Color",
      description: "Choose a custom color for your username in leaderboards",
      category: "theme",
      cost: 250,
      icon: <StarIcon sx={{ color: "#673AB7" }} />,
      rarity: "common",
    },
    {
      id: "8",
      name: "School Merchandise",
      description: "Exclusive school-branded merchandise",
      category: "physical",
      cost: 1500,
      icon: <CardGiftcardIcon sx={{ color: "#795548" }} />,
      rarity: "legendary",
      stock: 3,
      requirements: { level: 25 },
    },
  ];

  const rewardHistory: RewardHistory[] = [
    {
      id: "h1",
      rewardId: "3",
      rewardName: "Double XP Booster",
      redeemedAt: "2024-01-28 14:30:00",
      cost: 200,
      status: "used",
    },
    {
      id: "h2",
      rewardId: "2",
      rewardName: "Dark Mode Theme",
      redeemedAt: "2024-01-25 10:15:00",
      cost: 300,
      status: "delivered",
    },
    {
      id: "h3",
      rewardId: "5",
      rewardName: "Certificate of Excellence",
      redeemedAt: "2024-01-20 16:45:00",
      cost: 750,
      status: "pending",
    },
  ];

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case "common":
        return "#757575";
      case "rare":
        return "#2196F3";
      case "epic":
        return "#9C27B0";
      case "legendary":
        return "#FF9800";
      default:
        return "#757575";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "avatar":
        return <EmojiEventsIcon />;
      case "theme":
        return <StarIcon />;
      case "powerup":
        return <TrendingUpIcon />;
      case "certificate":
        return <CardGiftcardIcon />;
      case "physical":
        return <CardGiftcardIcon />;
      case "privilege":
        return <LocalOfferIcon />;
      default:
        return <StarIcon />;
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
        type: "success",
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
        type: "warning",
        message: "This reward is already in your cart",
        autoHide: true,
      }));
      return;
    }
    setCart([...cart, reward]);
    dispatch(addNotification({
      type: "success",
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
      type: "success",
      message: "Reward removed successfully",
      autoHide: true,
    }));
  };

  const filteredRewards = availableRewards.filter(reward => {
    if (selectedCategory !== "all" && reward.category !== selectedCategory) return false;
    if (searchTerm && !reward.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <Grid2 container spacing={3}>
      {/* Header */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                  Rewards Store
                </Typography>
                <Stack direction="row" spacing={2} alignItems="center">
                  <Chip
                    icon={<StarIcon />}
                    label={`${xp.toLocaleString()} XP Available`}
                    color="primary"
                    variant="filled"
                  />
                  <Chip
                    icon={<TrendingUpIcon />}
                    label={`Level ${level}`}
                    color="secondary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<EmojiEventsIcon />}
                    label={`${badges.length} Badges`}
                    variant="outlined"
                  />
                </Stack>
              </Box>
              
              <Stack direction="row" spacing={2}>
                {role === "teacher" && (
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                  >
                    Create Reward
                  </Button>
                )}
                <Badge badgeContent={cart.length} color="primary">
                  <Button
                    variant="contained"
                    startIcon={<ShoppingCartIcon />}
                    disabled={cart.length === 0}
                    onClick={() => {
                      if (cart.length > 0) {
                        setConfirmDialogOpen(true);
                      }
                    }}
                  >
                    Cart ({getTotalCartCost()} XP)
                  </Button>
                </Badge>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Main Content */}
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Available Rewards" />
                <Tab label="My Rewards" />
                <Tab label="History" />
                {role === "teacher" && <Tab label="Manage" />}
              </Tabs>
            </Box>

            {/* Available Rewards Tab */}
            <TabPanel value={activeTab} index={0}>
              {/* Filters */}
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 3 }}>
                <TextField
                  size="small"
                  placeholder="Search rewards..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{ minWidth: 200 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={selectedCategory}
                    label="Category"
                    onChange={(e) => setSelectedCategory(e.target.value)}
                  >
                    <MenuItem value="all">All Categories</MenuItem>
                    <MenuItem value="avatar">Avatars</MenuItem>
                    <MenuItem value="theme">Themes</MenuItem>
                    <MenuItem value="powerup">Power-ups</MenuItem>
                    <MenuItem value="certificate">Certificates</MenuItem>
                    <MenuItem value="physical">Physical</MenuItem>
                    <MenuItem value="privilege">Privileges</MenuItem>
                  </Select>
                </FormControl>
              </Stack>

              {/* Rewards Grid */}
              <Grid container spacing={3}>
                {filteredRewards.map((reward) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={reward.id}>
                    <Card
                      sx={{
                        height: "100%",
                        display: "flex",
                        flexDirection: "column",
                        position: "relative",
                        border: `2px solid ${getRarityColor(reward.rarity)}`,
                        opacity: canRedeem(reward) ? 1 : 0.6,
                      }}
                    >
                      {/* Rarity Badge */}
                      <Chip
                        label={reward.rarity.toUpperCase()}
                        size="small"
                        sx={{
                          position: "absolute",
                          top: 8,
                          right: 8,
                          backgroundColor: getRarityColor(reward.rarity),
                          color: "white",
                          zIndex: 1,
                        }}
                      />
                      
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Stack alignItems="center" spacing={2}>
                          <Box sx={{ fontSize: 48 }}>{reward.icon}</Box>
                          <Typography variant="h6" textAlign="center">
                            {reward.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" textAlign="center">
                            {reward.description}
                          </Typography>
                          
                          {/* Requirements */}
                          {reward.requirements && (
                            <Stack spacing={0.5} sx={{ width: "100%" }}>
                              {reward.requirements.level && (
                                <Chip
                                  label={`Level ${reward.requirements.level} Required`}
                                  size="small"
                                  color={level >= reward.requirements.level ? "success" : "default"}
                                  icon={level >= reward.requirements.level ? <CheckCircleIcon /> : <LockIcon />}
                                />
                              )}
                            </Stack>
                          )}
                          
                          {/* Stock */}
                          {reward.stock !== undefined && (
                            <Chip
                              label={`${reward.stock} left`}
                              size="small"
                              color={reward.stock > 0 ? "default" : "error"}
                            />
                          )}
                        </Stack>
                      </CardContent>
                      
                      <CardActions sx={{ justifyContent: "space-between", p: 2 }}>
                        <Chip
                          icon={<StarIcon />}
                          label={`${reward.cost} XP`}
                          color="primary"
                        />
                        <Stack direction="row" spacing={1}>
                          <IconButton
                            size="small"
                            onClick={() => addToCart(reward)}
                            disabled={!canRedeem(reward)}
                          >
                            <AddIcon />
                          </IconButton>
                          <Button
                            size="small"
                            variant="contained"
                            disabled={!canRedeem(reward)}
                            onClick={() => handleRedeem(reward)}
                          >
                            Redeem
                          </Button>
                        </Stack>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </TabPanel>

            {/* My Rewards Tab */}
            <TabPanel value={activeTab} index={1}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <AlertTitle>Your Redeemed Rewards</AlertTitle>
                These are the rewards you've already redeemed. Some may still be active!
              </Alert>
              
              <Grid container spacing={3}>
                {rewardHistory
                  .filter(h => h.status === "delivered")
                  .map((item) => {
                    const reward = availableRewards.find(r => r.id === item.rewardId);
                    if (!reward) return null;
                    
                    return (
                      <Grid item xs={12} sm={6} md={4} key={item.id}>
                        <Card>
                          <CardContent>
                            <Stack spacing={2}>
                              <Stack direction="row" justifyContent="space-between" alignItems="center">
                                <Box sx={{ fontSize: 32 }}>{reward.icon}</Box>
                                <Chip
                                  label={item.status}
                                  size="small"
                                  color={item.status === "delivered" ? "success" : "default"}
                                />
                              </Stack>
                              <Typography variant="h6">{reward.name}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                Redeemed: {new Date(item.redeemedAt).toLocaleDateString()}
                              </Typography>
                              {reward.category === "powerup" && (
                                <Button variant="contained" size="small">
                                  Activate
                                </Button>
                              )}
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    );
                  })}
              </Grid>
            </TabPanel>

            {/* History Tab */}
            <TabPanel value={activeTab} index={2}>
              <List>
                {rewardHistory.map((item) => (
                  <ListItem key={item.id}>
                    <ListItemAvatar>
                      <Avatar>
                        {getCategoryIcon(availableRewards.find(r => r.id === item.rewardId)?.category || "")}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={item.rewardName}
                      secondary={`Redeemed on ${new Date(item.redeemedAt).toLocaleString()} • ${item.cost} XP`}
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={item.status}
                        size="small"
                        color={
                          item.status === "delivered" ? "success" :
                          item.status === "used" ? "default" :
                          "warning"
                        }
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </TabPanel>

            {/* Manage Tab (Teachers Only) */}
            {role === "teacher" && (
              <TabPanel value={activeTab} index={3}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <AlertTitle>Manage Rewards</AlertTitle>
                  Create custom rewards for your students and manage existing ones.
                </Alert>
                
                <Stack spacing={2}>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                  >
                    Create New Reward
                  </Button>
                  
                  <Typography variant="h6" sx={{ mt: 2 }}>
                    Active Rewards
                  </Typography>
                  
                  <Grid container spacing={2}>
                    {availableRewards.map((reward) => (
                      <Grid item xs={12} key={reward.id}>
                        <Paper sx={{ p: 2 }}>
                          <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <Stack direction="row" spacing={2} alignItems="center">
                              {reward.icon}
                              <Box>
                                <Typography variant="subtitle1">{reward.name}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {reward.cost} XP • {reward.rarity} • {reward.stock ? `${reward.stock} in stock` : "Unlimited"}
                                </Typography>
                              </Box>
                            </Stack>
                            <Stack direction="row" spacing={1}>
                              <Button 
                                size="small"
                                onClick={() => {
                                  setSelectedReward(reward);
                                  setEditDialogOpen(true);
                                }}
                              >
                                Edit
                              </Button>
                          <Button 
                                size="small" 
                                color="error"
                                onClick={handleRemoveReward}
                              >
                                Remove
                              </Button>
                            </Stack>
                          </Stack>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </Stack>
              </TabPanel>
            )}
          </CardContent>
        </Card>
      </Grid2>

      {/* Redeem Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogTitle>Confirm Redemption</DialogTitle>
        <DialogContent>
          {selectedReward && (
            <Stack spacing={2}>
              <Typography>
                Are you sure you want to redeem <strong>{selectedReward.name}</strong>?
              </Typography>
              <Alert severity="info">
                This will cost {selectedReward.cost} XP. You currently have {xp} XP.
              </Alert>
              <Typography variant="body2" color="text.secondary">
                After redemption: {xp - selectedReward.cost} XP remaining
              </Typography>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={confirmRedeem}>
            Confirm Redemption
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Reward Dialog (Teachers) */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Reward</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <TextField fullWidth label="Reward Name" />
            <TextField fullWidth label="Description" multiline rows={3} />
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select label="Category">
                <MenuItem value="avatar">Avatar</MenuItem>
                <MenuItem value="theme">Theme</MenuItem>
                <MenuItem value="powerup">Power-up</MenuItem>
                <MenuItem value="certificate">Certificate</MenuItem>
                <MenuItem value="privilege">Privilege</MenuItem>
              </Select>
            </FormControl>
            <TextField fullWidth label="XP Cost" type="number" />
            <FormControl fullWidth>
              <InputLabel>Rarity</InputLabel>
              <Select label="Rarity">
                <MenuItem value="common">Common</MenuItem>
                <MenuItem value="rare">Rare</MenuItem>
                <MenuItem value="epic">Epic</MenuItem>
                <MenuItem value="legendary">Legendary</MenuItem>
              </Select>
            </FormControl>
            <TextField fullWidth label="Stock (optional)" type="number" helperText="Leave empty for unlimited" />
            <TextField fullWidth label="Required Level (optional)" type="number" />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => {
            dispatch(addNotification({
              type: "success",
              message: "Reward created successfully!",
              autoHide: true,
            }));
            setCreateDialogOpen(false);
          }}>
            Create Reward
          </Button>
        </DialogActions>
      </Dialog>
    </Grid2>
  );
}