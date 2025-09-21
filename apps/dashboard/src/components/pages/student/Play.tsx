import { useState } from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';

import {
  SportsEsports,
  PlayArrow,
  Stars,
  Timer,
  People,
  EmojiEvents,
  Refresh,
} from "@mui/icons-material";
import { useAppSelector } from "../../../store";
interface RobloxWorld {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  playerCount: number;
  difficulty: "Easy" | "Medium" | "Hard";
  subject: string;
  estimatedTime: number;
  xpReward: number;
  badges: string[];
  isLocked: boolean;
  completionRate: number;
}
export default function Play() {
  const user = useAppSelector((s) => s.user);
  const userXP = useAppSelector((s) => s.gamification.xp);
  const [worlds, setWorlds] = useState<RobloxWorld[]>([
    {
      id: "1",
      name: "Math Adventure Island",
      description: "Explore mathematical concepts through exciting quests and puzzles",
      thumbnailUrl: "",
      playerCount: 156,
      difficulty: "Easy",
      subject: "Mathematics",
      estimatedTime: 25,
      xpReward: 100,
      badges: ["Math Explorer", "Problem Solver"],
      isLocked: false,
      completionRate: 85,
    },
    {
      id: "2",
      name: "Science Laboratory",
      description: "Conduct virtual experiments and discover scientific principles",
      thumbnailUrl: "",
      playerCount: 89,
      difficulty: "Medium",
      subject: "Science",
      estimatedTime: 35,
      xpReward: 150,
      badges: ["Scientist", "Experimenter"],
      isLocked: false,
      completionRate: 72,
    },
    {
      id: "3",
      name: "History Time Machine",
      description: "Travel through time and experience historical events firsthand",
      thumbnailUrl: "",
      playerCount: 67,
      difficulty: "Medium",
      subject: "History",
      estimatedTime: 40,
      xpReward: 175,
      badges: ["Time Traveler", "Historian"],
      isLocked: false,
      completionRate: 68,
    },
    {
      id: "4",
      name: "Advanced Physics Simulator",
      description: "Master complex physics concepts in an interactive environment",
      thumbnailUrl: "",
      playerCount: 23,
      difficulty: "Hard",
      subject: "Physics",
      estimatedTime: 60,
      xpReward: 250,
      badges: ["Physics Master", "Theory Expert"],
      isLocked: true,
      completionRate: 45,
    },
  ]);
  const [loading, setLoading] = useState(false);
  const handleJoinWorld = async (worldId: string) => {
    setLoading(true);
    try {
      // TODO: Implement API call to get Roblox join URL
      // const joinUrl = await getRobloxJoinUrl(worldId);
      // window.open(joinUrl, '_blank');
      console.log(`Joining world ${worldId}`);
    } catch (error) {
      console.error("Failed to join world:", error);
    } finally {
      setLoading(false);
    }
  };
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Easy": return "success";
      case "Medium": return "warning";
      case "Hard": return "error";
      default: return "default";
    }
  };
  const getSubjectColor = (subject: string) => {
    switch (subject) {
      case "Mathematics": return "#1976d2";
      case "Science": return "#2e7d32";
      case "History": return "#ed6c02";
      case "Physics": return "#9c27b0";
      default: return "#666";
    }
  };
  return (
    <Box>
      <Stack direction="row" justifyContent="between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Roblox Learning Worlds
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Learn through immersive gaming experiences
          </Typography>
        </Box>
        <IconButton onClick={(e: React.MouseEvent) => () => window.location.reload()}>
          <Refresh />
        </IconButton>
      </Stack>
      {/* Current Session Info */}
      {user && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Welcome back, <strong>{user.displayName}</strong>! 
            You currently have <strong>{userXP} XP</strong> and are Level <strong>{Math.floor(userXP / 100) + 1}</strong>.
          </Typography>
        </Alert>
      )}
      <Grid container spacing={3}>
        {worlds.map((world) => (
          <Grid item xs={12} md={6} lg={4} key={world.id}>
            <Card
              sx={{
                height: "100%",
                opacity: world.isLocked ? 0.6 : 1,
                transition: "transform 0.2s",
                "&:hover": {
                  transform: world.isLocked ? "none" : "translateY(-4px)",
                },
              }}
            >
              <Box
                sx={{
                  height: 120,
                  background: `linear-gradient(135deg, ${getSubjectColor(world.subject)}22 0%, ${getSubjectColor(world.subject)}44 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                }}
              >
                <SportsEsports sx={{ fontSize: 48, color: getSubjectColor(world.subject) }} />
                {world.isLocked && (
                  <Chip
                    label="Locked"
                    size="small"
                    sx={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                    }}
                  />
                )}
              </Box>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  {world.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {world.description}
                </Typography>
                <Stack spacing={2}>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Chip
                      label={world.difficulty}
                      size="small"
                      color={getDifficultyColor(world.difficulty) as any}
                    />
                    <Chip
                      label={world.subject}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                  <Stack spacing={1}>
                    <Stack direction="row" justifyContent="between" alignItems="center">
                      <Typography variant="caption" color="text.secondary">
                        Completion Rate
                      </Typography>
                      <Typography variant="caption" fontWeight={600}>
                        {world.completionRate}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={world.completionRate}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Stack>
                  <Divider />
                  <Stack spacing={1}>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Timer fontSize="small" />
                      <Typography variant="caption">
                        ~{world.estimatedTime} minutes
                      </Typography>
                    </Stack>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <People fontSize="small" />
                      <Typography variant="caption">
                        {world.playerCount} players online
                      </Typography>
                    </Stack>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Stars fontSize="small" />
                      <Typography variant="caption">
                        +{world.xpReward} XP reward
                      </Typography>
                    </Stack>
                  </Stack>
                  {world.badges.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Typography variant="caption" color="text.secondary" mb={1} display="block">
                          Available Badges:
                        </Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                          {world.badges.map((badge, index) => (
                            <Chip
                              key={index}
                              label={badge}
                              size="small"
                              variant="outlined"
                              color="secondary"
                            />
                          ))}
                        </Stack>
                      </Box>
                    </>
                  )}
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={<PlayArrow />}
                    onClick={(e: React.MouseEvent) => () => handleJoinWorld(world.id)}
                    disabled={world.isLocked || loading}
                    sx={{
                      borderRadius: 2,
                      textTransform: "none",
                      fontWeight: 600,
                      py: 1.5,
                    }}
                  >
                    {world.isLocked ? "Unlock Required" : "Join World"}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {/* Quick Tips */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Gaming Tips for Learning
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Stack direction="row" spacing={1}>
                <EmojiEvents color="primary" />
                <Box>
                  <Typography variant="subtitle2">Earn XP</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Complete lessons and challenges to gain experience points
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack direction="row" spacing={1}>
                <Stars color="secondary" />
                <Box>
                  <Typography variant="subtitle2">Collect Badges</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Achieve specific goals to unlock special badges
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack direction="row" spacing={1}>
                <People color="success" />
                <Box>
                  <Typography variant="subtitle2">Play Together</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Join friends in multiplayer learning experiences
                  </Typography>
                </Box>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}