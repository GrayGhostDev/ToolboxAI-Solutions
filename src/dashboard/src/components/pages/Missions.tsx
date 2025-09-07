import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Badge,
  Tooltip,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Skeleton,
  Avatar,
} from "@mui/material";
import {
  EmojiEvents,
  Timer,
  CalendarToday,
  Star,
  TrendingUp,
  Assignment,
  School,
  Palette,
  FitnessCenter,
  People,
  CheckCircle,
  RadioButtonUnchecked,
  Lock,
  LockOpen,
  Add,
  Edit,
  Delete,
  FilterList,
  Sort,
  Refresh,
  PlayArrow,
  MoreVert,
  Info,
  AttachMoney,
  CardGiftcard,
  LocalFireDepartment,
  AutoAwesome,
  Celebration,
  WorkspacePremium,
  Speed,
  Psychology,
  Groups,
  Schedule,
  Flag,
} from "@mui/icons-material";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../../store";
import { Mission, MissionProgress, Challenge, ChallengeLeaderboard } from "../../types/api";
import apiClient from "../../services/api";

const categoryIcons = {
  academic: <School />,
  social: <People />,
  creativity: <Palette />,
  physical: <FitnessCenter />,
  community: <Groups />,
};

const difficultyColors = {
  easy: "success",
  medium: "warning",
  hard: "error",
  expert: "secondary",
} as const;

const typeColors = {
  daily: "#4CAF50",
  weekly: "#2196F3",
  monthly: "#FF9800",
  special: "#9C27B0",
  custom: "#607D8B",
};

const challengeTypeIcons = {
  speed: <Speed />,
  accuracy: <Psychology />,
  creativity: <Palette />,
  collaboration: <Groups />,
  endurance: <Schedule />,
};

const Missions: React.FC = () => {
  const dispatch = useDispatch();
  const { role, userId } = useSelector((state: RootState) => state.user);
  const { xp, level } = useSelector((state: RootState) => state.gamification);

  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [missionProgress, setMissionProgress] = useState<Map<string, MissionProgress>>(new Map());
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [challengeFilter, setChallengeFilter] = useState<"all" | "upcoming" | "active" | "completed">("active");
  const [missionFilter, setMissionFilter] = useState<"all" | "daily" | "weekly" | "monthly" | "special">("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null);
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [missionDetailsOpen, setMissionDetailsOpen] = useState(false);
  const [challengeDetailsOpen, setChallengeDetailsOpen] = useState(false);

  // Mock data for development
  const mockMissions: Mission[] = [
    {
      id: "1",
      title: "Daily Reading Quest",
      description: "Complete today's reading lesson and answer all comprehension questions",
      type: "daily",
      category: "academic",
      xpReward: 50,
      requirements: [
        {
          id: "r1",
          type: "lesson_complete",
          target: 1,
          current: 0,
          description: "Complete 1 reading lesson",
        },
        {
          id: "r2",
          type: "assessment_score",
          target: 80,
          current: 0,
          description: "Score at least 80% on comprehension quiz",
        },
      ],
      isActive: true,
      isRepeatable: true,
      difficulty: "easy",
      imageUrl: "/images/missions/reading.png",
      createdBy: "system",
      createdAt: new Date().toISOString(),
    },
    {
      id: "2",
      title: "Math Master Challenge",
      description: "Solve 20 math problems correctly this week",
      type: "weekly",
      category: "academic",
      xpReward: 200,
      badgeReward: "math-master",
      requirements: [
        {
          id: "r3",
          type: "custom",
          target: 20,
          current: 12,
          description: "Solve 20 math problems",
        },
      ],
      isActive: true,
      isRepeatable: true,
      difficulty: "medium",
      imageUrl: "/images/missions/math.png",
      createdBy: "system",
      createdAt: new Date().toISOString(),
    },
    {
      id: "3",
      title: "Creative Writer",
      description: "Write and submit an original story of at least 500 words",
      type: "monthly",
      category: "creativity",
      xpReward: 500,
      badgeReward: "creative-writer",
      requirements: [
        {
          id: "r4",
          type: "custom",
          target: 1,
          current: 0,
          description: "Submit an original story",
        },
      ],
      isActive: true,
      isRepeatable: false,
      difficulty: "hard",
      imageUrl: "/images/missions/writing.png",
      createdBy: "teacher1",
      createdAt: new Date().toISOString(),
    },
    {
      id: "4",
      title: "Team Player",
      description: "Participate in 3 group activities this week",
      type: "weekly",
      category: "social",
      xpReward: 150,
      requirements: [
        {
          id: "r5",
          type: "social_interaction",
          target: 3,
          current: 1,
          description: "Join 3 group activities",
        },
      ],
      isActive: true,
      isRepeatable: true,
      difficulty: "easy",
      imageUrl: "/images/missions/team.png",
      createdBy: "system",
      createdAt: new Date().toISOString(),
    },
    {
      id: "5",
      title: "Halloween Special: Spooky Scholar",
      description: "Complete all Halloween-themed lessons and earn the special badge!",
      type: "special",
      category: "academic",
      xpReward: 1000,
      badgeReward: "halloween-2024",
      requirements: [
        {
          id: "r6",
          type: "lesson_complete",
          target: 5,
          current: 3,
          description: "Complete 5 Halloween lessons",
        },
      ],
      startDate: "2024-10-25",
      endDate: "2024-11-01",
      isActive: true,
      isRepeatable: false,
      difficulty: "expert",
      imageUrl: "/images/missions/halloween.png",
      createdBy: "system",
      createdAt: new Date().toISOString(),
    },
  ];

  const mockProgress: MissionProgress[] = [
    {
      id: "p1",
      missionId: "2",
      studentId: userId || "",
      status: "in_progress",
      startedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      progress: 60,
      requirementsProgress: [
        {
          requirementId: "r3",
          current: 12,
          target: 20,
          completed: false,
        },
      ],
      completionCount: 0,
    },
    {
      id: "p2",
      missionId: "4",
      studentId: userId || "",
      status: "in_progress",
      startedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      progress: 33,
      requirementsProgress: [
        {
          requirementId: "r5",
          current: 1,
          target: 3,
          completed: false,
        },
      ],
      completionCount: 0,
    },
    {
      id: "p3",
      missionId: "5",
      studentId: userId || "",
      status: "in_progress",
      startedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      progress: 60,
      requirementsProgress: [
        {
          requirementId: "r6",
          current: 3,
          target: 5,
          completed: false,
        },
      ],
      completionCount: 0,
    },
  ];

  const mockChallenges: Challenge[] = [
    {
      id: "c1",
      title: "Speed Math Championship",
      description: "Solve as many math problems as possible in 5 minutes!",
      type: "speed",
      participants: ["user1", "user2", "user3"],
      startTime: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      rules: [
        "5 minutes time limit",
        "No calculators allowed",
        "Points based on speed and accuracy",
      ],
      prizes: [
        { position: 1, xpReward: 500, badgeId: "speed-champion" },
        { position: 2, xpReward: 300 },
        { position: 3, xpReward: 100 },
      ],
      status: "upcoming",
      createdBy: "teacher1",
      createdAt: new Date().toISOString(),
    },
    {
      id: "c2",
      title: "Creative Story Contest",
      description: "Write the most creative story based on the weekly theme",
      type: "creativity",
      participants: ["user1", "user4", "user5", "user6"],
      startTime: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString(),
      rules: [
        "Story must be 300-1000 words",
        "Must include this week's vocabulary words",
        "Original work only",
      ],
      prizes: [
        { position: 1, xpReward: 1000, badgeId: "creative-master", customReward: "Feature in school newsletter" },
        { position: 2, xpReward: 500, customReward: "Extra library time" },
        { position: 3, xpReward: 250 },
      ],
      leaderboard: [
        { rank: 1, studentId: "user4", displayName: "Alice", score: 95, submittedAt: new Date().toISOString() },
        { rank: 2, studentId: "user1", displayName: "You", score: 88, submittedAt: new Date().toISOString() },
        { rank: 3, studentId: "user5", displayName: "Bob", score: 82, submittedAt: new Date().toISOString() },
      ],
      status: "active",
      createdBy: "teacher2",
      createdAt: new Date().toISOString(),
    },
  ];

  useEffect(() => {
    loadMissionsAndChallenges();
  }, []);

  const loadMissionsAndChallenges = async () => {
    setLoading(true);
    try {
      // In production, these would be API calls
      setMissions(mockMissions);
      const progressMap = new Map<string, MissionProgress>();
      mockProgress.forEach(p => progressMap.set(p.missionId, p));
      setMissionProgress(progressMap);
      setChallenges(mockChallenges);
    } catch (error) {
      console.error("Failed to load missions and challenges:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartMission = async (mission: Mission) => {
    try {
      // API call to start mission
      const newProgress: MissionProgress = {
        id: `p${Date.now()}`,
        missionId: mission.id,
        studentId: userId || "",
        status: "in_progress",
        startedAt: new Date().toISOString(),
        progress: 0,
        requirementsProgress: mission.requirements.map(req => ({
          requirementId: req.id,
          current: 0,
          target: req.target,
          completed: false,
        })),
        completionCount: 0,
      };
      
      setMissionProgress(prev => new Map(prev).set(mission.id, newProgress));
    } catch (error) {
      console.error("Failed to start mission:", error);
    }
  };

  const handleClaimReward = async (mission: Mission) => {
    try {
      // API call to claim reward
      const progress = missionProgress.get(mission.id);
      if (progress) {
        const updatedProgress = { ...progress, status: "claimed" as const, claimedAt: new Date().toISOString() };
        setMissionProgress(prev => new Map(prev).set(mission.id, updatedProgress));
      }
    } catch (error) {
      console.error("Failed to claim reward:", error);
    }
  };

  const handleJoinChallenge = async (challenge: Challenge) => {
    try {
      // API call to join challenge
      const updatedChallenge = {
        ...challenge,
        participants: [...challenge.participants, userId || ""],
      };
      setChallenges(prev => prev.map(c => c.id === challenge.id ? updatedChallenge : c));
    } catch (error) {
      console.error("Failed to join challenge:", error);
    }
  };

  const renderMissionCard = (mission: Mission) => {
    const progress = missionProgress.get(mission.id);
    const isStarted = !!progress;
    const isCompleted = progress?.status === "completed";
    const isClaimed = progress?.status === "claimed";

    return (
      <Card
        key={mission.id}
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          borderTop: `4px solid ${typeColors[mission.type]}`,
          opacity: isClaimed ? 0.7 : 1,
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Box display="flex" gap={1} alignItems="center">
              {categoryIcons[mission.category]}
              <Chip
                label={mission.type}
                size="small"
                sx={{ bgcolor: typeColors[mission.type], color: "white" }}
              />
              <Chip
                label={mission.difficulty}
                size="small"
                color={difficultyColors[mission.difficulty]}
              />
            </Box>
            {mission.isRepeatable && (
              <Tooltip title="Repeatable Mission">
                <Refresh fontSize="small" />
              </Tooltip>
            )}
          </Box>

          <Typography variant="h6" gutterBottom>
            {mission.title}
          </Typography>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {mission.description}
          </Typography>

          <Box display="flex" alignItems="center" gap={1} my={2}>
            <AttachMoney />
            <Typography variant="h6" color="primary">
              {mission.xpReward} XP
            </Typography>
            {mission.badgeReward && (
              <>
                <WorkspacePremium />
                <Typography variant="body2">+ Badge</Typography>
              </>
            )}
          </Box>

          {isStarted && progress && (
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2">Progress</Typography>
                <Typography variant="body2">{Math.round(progress.progress)}%</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress.progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          )}

          <List dense>
            {mission.requirements.map((req) => {
              const reqProgress = progress?.requirementsProgress.find(
                rp => rp.requirementId === req.id
              );
              const current = reqProgress?.current || 0;
              const completed = reqProgress?.completed || false;

              return (
                <ListItem key={req.id} disableGutters>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {completed ? (
                      <CheckCircle color="success" fontSize="small" />
                    ) : (
                      <RadioButtonUnchecked fontSize="small" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={req.description}
                    secondary={`${current} / ${req.target}`}
                    primaryTypographyProps={{ variant: "body2" }}
                    secondaryTypographyProps={{ variant: "caption" }}
                  />
                </ListItem>
              );
            })}
          </List>

          {mission.endDate && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                Ends: {new Date(mission.endDate).toLocaleDateString()}
              </Typography>
            </Alert>
          )}
        </CardContent>

        <Box p={2} pt={0}>
          {!isStarted && (
            <Button
              fullWidth
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => handleStartMission(mission)}
            >
              Start Mission
            </Button>
          )}
          {isStarted && !isCompleted && !isClaimed && (
            <Button
              fullWidth
              variant="outlined"
              onClick={() => {
                setSelectedMission(mission);
                setMissionDetailsOpen(true);
              }}
            >
              View Details
            </Button>
          )}
          {isCompleted && !isClaimed && (
            <Button
              fullWidth
              variant="contained"
              color="success"
              startIcon={<Celebration />}
              onClick={() => handleClaimReward(mission)}
            >
              Claim Reward
            </Button>
          )}
          {isClaimed && (
            <Button fullWidth disabled startIcon={<CheckCircle />}>
              Claimed
            </Button>
          )}
        </Box>
      </Card>
    );
  };

  const renderChallengeCard = (challenge: Challenge) => {
    const isParticipant = challenge.participants.includes(userId || "");
    const timeUntilStart = new Date(challenge.startTime).getTime() - Date.now();
    const timeUntilEnd = new Date(challenge.endTime).getTime() - Date.now();

    return (
      <Card key={challenge.id} sx={{ height: "100%" }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" gap={1} alignItems="center">
              {challengeTypeIcons[challenge.type]}
              <Typography variant="h6">{challenge.title}</Typography>
            </Box>
            <Chip
              label={challenge.status}
              size="small"
              color={
                challenge.status === "active" ? "success" :
                challenge.status === "upcoming" ? "warning" : "default"
              }
            />
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {challenge.description}
          </Typography>

          <Box my={2}>
            <Typography variant="caption" color="text.secondary">
              {challenge.status === "upcoming" && `Starts in ${Math.ceil(timeUntilStart / (1000 * 60 * 60 * 24))} days`}
              {challenge.status === "active" && `Ends in ${Math.ceil(timeUntilEnd / (1000 * 60 * 60 * 24))} days`}
              {challenge.status === "completed" && "Challenge ended"}
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <People fontSize="small" />
            <Typography variant="body2">
              {challenge.participants.length} participants
            </Typography>
          </Box>

          {challenge.leaderboard && challenge.leaderboard.length > 0 && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Current Leaders
              </Typography>
              <List dense>
                {challenge.leaderboard.slice(0, 3).map((entry) => (
                  <ListItem key={entry.studentId} disableGutters>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
                        {entry.rank}
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={entry.displayName}
                      secondary={`Score: ${entry.score}`}
                      primaryTypographyProps={{ variant: "body2" }}
                      secondaryTypographyProps={{ variant: "caption" }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          <Typography variant="subtitle2" gutterBottom>
            Prizes
          </Typography>
          <Box display="flex" gap={1} mb={2}>
            {challenge.prizes.slice(0, 3).map((prize) => (
              <Chip
                key={prize.position}
                label={`#${prize.position}: ${prize.xpReward} XP`}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </CardContent>

        <Box p={2} pt={0}>
          {challenge.status === "upcoming" && !isParticipant && (
            <Button
              fullWidth
              variant="contained"
              startIcon={<Flag />}
              onClick={() => handleJoinChallenge(challenge)}
            >
              Join Challenge
            </Button>
          )}
          {challenge.status === "upcoming" && isParticipant && (
            <Button fullWidth disabled startIcon={<CheckCircle />}>
              Registered
            </Button>
          )}
          {challenge.status === "active" && (
            <Button
              fullWidth
              variant="contained"
              color="primary"
              onClick={() => {
                setSelectedChallenge(challenge);
                setChallengeDetailsOpen(true);
              }}
            >
              {isParticipant ? "Submit Entry" : "View Details"}
            </Button>
          )}
          {challenge.status === "completed" && (
            <Button
              fullWidth
              variant="outlined"
              onClick={() => {
                setSelectedChallenge(challenge);
                setChallengeDetailsOpen(true);
              }}
            >
              View Results
            </Button>
          )}
        </Box>
      </Card>
    );
  };

  const filteredMissions = missions.filter(mission => {
    if (missionFilter !== "all" && mission.type !== missionFilter) return false;
    if (categoryFilter !== "all" && mission.category !== categoryFilter) return false;
    return true;
  });

  const filteredChallenges = challenges.filter(challenge => {
    if (challengeFilter === "all") return true;
    return challenge.status === challengeFilter;
  });

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Missions & Challenges</Typography>
        {(role === "Teacher" || role === "Admin") && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Mission
          </Button>
        )}
      </Box>

      <Paper sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <LocalFireDepartment color="error" />
              <Box>
                <Typography variant="h4">{xp}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Total XP
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Star color="warning" />
              <Box>
                <Typography variant="h4">{level}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Current Level
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Assignment color="primary" />
              <Box>
                <Typography variant="h4">
                  {Array.from(missionProgress.values()).filter(p => p.status === "in_progress").length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Active Missions
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <EmojiEvents color="success" />
              <Box>
                <Typography variant="h4">
                  {Array.from(missionProgress.values()).filter(p => p.status === "completed" || p.status === "claimed").length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Completed
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="Missions" icon={<Assignment />} iconPosition="start" />
        <Tab label="Challenges" icon={<EmojiEvents />} iconPosition="start" />
        <Tab label="History" icon={<Timer />} iconPosition="start" />
      </Tabs>

      {activeTab === 0 && (
        <>
          <Box display="flex" gap={2} mb={3} flexWrap="wrap">
            <ToggleButtonGroup
              value={missionFilter}
              exclusive
              onChange={(_, v) => v && setMissionFilter(v)}
              size="small"
            >
              <ToggleButton value="all">All</ToggleButton>
              <ToggleButton value="daily">Daily</ToggleButton>
              <ToggleButton value="weekly">Weekly</ToggleButton>
              <ToggleButton value="monthly">Monthly</ToggleButton>
              <ToggleButton value="special">Special</ToggleButton>
            </ToggleButtonGroup>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="academic">Academic</MenuItem>
                <MenuItem value="social">Social</MenuItem>
                <MenuItem value="creativity">Creativity</MenuItem>
                <MenuItem value="physical">Physical</MenuItem>
                <MenuItem value="community">Community</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Grid container spacing={3}>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <Grid item xs={12} md={6} lg={4} key={i}>
                  <Skeleton variant="rectangular" height={300} />
                </Grid>
              ))
            ) : (
              filteredMissions.map((mission) => (
                <Grid item xs={12} md={6} lg={4} key={mission.id}>
                  {renderMissionCard(mission)}
                </Grid>
              ))
            )}
          </Grid>
        </>
      )}

      {activeTab === 1 && (
        <>
          <Box display="flex" gap={2} mb={3}>
            <ToggleButtonGroup
              value={challengeFilter}
              exclusive
              onChange={(_, v) => v && setChallengeFilter(v)}
              size="small"
            >
              <ToggleButton value="all">All</ToggleButton>
              <ToggleButton value="upcoming">Upcoming</ToggleButton>
              <ToggleButton value="active">Active</ToggleButton>
              <ToggleButton value="completed">Completed</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Grid container spacing={3}>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <Grid item xs={12} md={6} key={i}>
                  <Skeleton variant="rectangular" height={250} />
                </Grid>
              ))
            ) : (
              filteredChallenges.map((challenge) => (
                <Grid item xs={12} md={6} key={challenge.id}>
                  {renderChallengeCard(challenge)}
                </Grid>
              ))
            )}
          </Grid>
        </>
      )}

      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Mission History
          </Typography>
          <List>
            {Array.from(missionProgress.values())
              .filter(p => p.status === "claimed")
              .map((progress) => {
                const mission = missions.find(m => m.id === progress.missionId);
                if (!mission) return null;

                return (
                  <React.Fragment key={progress.id}>
                    <ListItem>
                      <ListItemIcon>{categoryIcons[mission.category]}</ListItemIcon>
                      <ListItemText
                        primary={mission.title}
                        secondary={`Completed on ${new Date(progress.claimedAt!).toLocaleDateString()}`}
                      />
                      <ListItemSecondaryAction>
                        <Chip label={`+${mission.xpReward} XP`} color="success" />
                      </ListItemSecondaryAction>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                );
              })}
          </List>
        </Paper>
      )}

      {/* Mission Details Dialog */}
      <Dialog
        open={missionDetailsOpen}
        onClose={() => setMissionDetailsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        {selectedMission && (
          <>
            <DialogTitle>{selectedMission.title}</DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedMission.description}
              </Typography>
              {/* Add more mission details here */}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setMissionDetailsOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Challenge Details Dialog */}
      <Dialog
        open={challengeDetailsOpen}
        onClose={() => setChallengeDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedChallenge && (
          <>
            <DialogTitle>{selectedChallenge.title}</DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedChallenge.description}
              </Typography>
              {/* Add challenge submission form or results here */}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setChallengeDetailsOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default Missions;