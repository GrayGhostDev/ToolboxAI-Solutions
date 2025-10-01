import * as React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  IconButton,
  LinearProgress,
  Chip,
  Alert,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Tab,
  Tabs,
  Avatar,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import {
  PlayArrow,
  Pause,
  SkipNext,
  SkipPrevious,
  Replay,
  VolumeUp,
  Fullscreen,
  Speed,
  EmojiEvents,
  Stars,
  TrendingUp,
  School,
  Timer,
  CheckCircle,
  Warning,
  SportsEsports,
  Timeline,
  Insights,
  Download,
  Share,
  CalendarToday,
} from "@mui/icons-material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { useAppSelector } from "../../store";

interface GameplaySession {
  id: string;
  studentName: string;
  studentAvatar: string;
  worldName: string;
  worldThumbnail: string;
  date: Date;
  duration: number; // in seconds
  highlights: Highlight[];
  achievements: Achievement[];
  interactions: Interaction[];
  progress: ProgressPoint[];
  overallScore: number;
  xpEarned: number;
  masteryConcepts: string[];
}

interface Highlight {
  id: string;
  timestamp: number; // seconds from start
  type: "achievement" | "milestone" | "struggle" | "breakthrough" | "collaboration";
  title: string;
  description: string;
  thumbnailUrl?: string;
  importance: "low" | "medium" | "high";
}

interface Achievement {
  id: string;
  name: string;
  icon: string;
  timestamp: number;
  xpReward: number;
}

interface Interaction {
  id: string;
  type: "npc_dialogue" | "puzzle_solve" | "quiz_complete" | "peer_help";
  timestamp: number;
  details: string;
  outcome: "success" | "partial" | "retry";
}

interface ProgressPoint {
  timestamp: number;
  concept: string;
  mastery: number; // 0-100
}

export default function GameplayReplay() {
  const user = useAppSelector((s) => s.user);
  const [selectedChild, setSelectedChild] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [sessions, setSessions] = useState<GameplaySession[]>([]);
  const [currentSession, setCurrentSession] = useState<GameplaySession | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedHighlight, setSelectedHighlight] = useState<string | null>(null);

  // Mock data for children (in real app, fetch from API)
  const children = [
    { id: "1", name: "Emma Johnson", avatar: "", grade: 5 },
    { id: "2", name: "Alex Johnson", avatar: "", grade: 3 },
  ];

  // Load mock sessions
  useEffect(() => {
    // Mock gameplay sessions
    const mockSessions: GameplaySession[] = [
      {
        id: "1",
        studentName: "Emma Johnson",
        studentAvatar: "",
        worldName: "Math Adventure Island",
        worldThumbnail: "",
        date: new Date(),
        duration: 1800, // 30 minutes
        highlights: [
          {
            id: "h1",
            timestamp: 120,
            type: "achievement",
            title: "First Puzzle Solved!",
            description: "Emma solved the fraction puzzle on her first try",
            importance: "high",
          },
          {
            id: "h2",
            timestamp: 450,
            type: "breakthrough",
            title: "Mastered Multiplication",
            description: "Completed all multiplication challenges with 100% accuracy",
            importance: "high",
          },
          {
            id: "h3",
            timestamp: 780,
            type: "collaboration",
            title: "Helped a Classmate",
            description: "Emma assisted another student with a difficult problem",
            importance: "medium",
          },
          {
            id: "h4",
            timestamp: 1200,
            type: "struggle",
            title: "Division Challenge",
            description: "Took 3 attempts but persevered through the division section",
            importance: "medium",
          },
          {
            id: "h5",
            timestamp: 1650,
            type: "milestone",
            title: "Level Complete!",
            description: "Finished Level 3 with a score of 95%",
            importance: "high",
          },
        ],
        achievements: [
          { id: "a1", name: "Problem Solver", icon: "🧩", timestamp: 120, xpReward: 50 },
          { id: "a2", name: "Math Master", icon: "🎓", timestamp: 450, xpReward: 100 },
          { id: "a3", name: "Team Player", icon: "🤝", timestamp: 780, xpReward: 75 },
        ],
        interactions: [
          {
            id: "i1",
            type: "npc_dialogue",
            timestamp: 60,
            details: "Spoke with Professor Math about fractions",
            outcome: "success",
          },
          {
            id: "i2",
            type: "puzzle_solve",
            timestamp: 120,
            details: "Fraction puzzle completed",
            outcome: "success",
          },
          {
            id: "i3",
            type: "quiz_complete",
            timestamp: 900,
            details: "Mid-level quiz: 9/10 correct",
            outcome: "success",
          },
          {
            id: "i4",
            type: "peer_help",
            timestamp: 780,
            details: "Helped Alex with multiplication",
            outcome: "success",
          },
        ],
        progress: [
          { timestamp: 0, concept: "Fractions", mastery: 60 },
          { timestamp: 300, concept: "Fractions", mastery: 75 },
          { timestamp: 600, concept: "Multiplication", mastery: 80 },
          { timestamp: 900, concept: "Multiplication", mastery: 95 },
          { timestamp: 1200, concept: "Division", mastery: 70 },
          { timestamp: 1500, concept: "Division", mastery: 85 },
        ],
        overallScore: 95,
        xpEarned: 225,
        masteryConcepts: ["Fractions", "Multiplication", "Problem Solving"],
      },
      {
        id: "2",
        studentName: "Emma Johnson",
        studentAvatar: "",
        worldName: "Science Laboratory",
        worldThumbnail: "",
        date: new Date(Date.now() - 86400000), // Yesterday
        duration: 2400, // 40 minutes
        highlights: [
          {
            id: "h6",
            timestamp: 180,
            type: "achievement",
            title: "Experiment Success!",
            description: "Completed the chemical reaction experiment perfectly",
            importance: "high",
          },
        ],
        achievements: [
          { id: "a4", name: "Scientist", icon: "🔬", timestamp: 180, xpReward: 75 },
        ],
        interactions: [
          {
            id: "i5",
            type: "npc_dialogue",
            timestamp: 100,
            details: "Learned about chemical reactions from Dr. Science",
            outcome: "success",
          },
        ],
        progress: [
          { timestamp: 0, concept: "Chemistry", mastery: 50 },
          { timestamp: 1200, concept: "Chemistry", mastery: 85 },
        ],
        overallScore: 88,
        xpEarned: 175,
        masteryConcepts: ["Chemistry", "Scientific Method"],
      },
    ];

    setSessions(mockSessions);
    if (mockSessions.length > 0) {
      setCurrentSession(mockSessions[0]);
    }
  }, [selectedChild, selectedDate]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (newTime: number) => {
    setCurrentTime(newTime);
  };

  const jumpToHighlight = (timestamp: number) => {
    setCurrentTime(timestamp);
    setIsPlaying(true);
  };

  const getHighlightIcon = (type: Highlight["type"]) => {
    switch (type) {
      case "achievement":
        return <EmojiEvents color="warning" />;
      case "milestone":
        return <Stars color="primary" />;
      case "breakthrough":
        return <TrendingUp color="success" />;
      case "struggle":
        return <Warning color="error" />;
      case "collaboration":
        return <School color="secondary" />;
      default:
        return <CheckCircle />;
    }
  };

  // Simulate playback
  useEffect(() => {
    if (isPlaying && currentSession && currentTime < currentSession.duration) {
      const timer = setTimeout(() => {
        setCurrentTime((prev) => Math.min(prev + playbackSpeed, currentSession.duration));
      }, 1000 / playbackSpeed);
      return () => clearTimeout(timer);
    } else if (currentTime >= (currentSession?.duration || 0)) {
      setIsPlaying(false);
    }
  }, [isPlaying, currentTime, playbackSpeed, currentSession]);

  if (!currentSession) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Gameplay Replay
        </Typography>
        <Alert severity="info">
          Select a child and date to view their gameplay sessions
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Gameplay Replay
        </Typography>
        <Stack direction="row" spacing={2}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Select Child</InputLabel>
            <Select
              value={selectedChild}
              onChange={(e) => setSelectedChild(e.target.value)}
              label="Select Child"
            >
              {children.map((child) => (
                <MenuItem key={child.id} value={child.id}>
                  {child.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Select Date"
              value={selectedDate}
              onChange={(newDate) => newDate && setSelectedDate(newDate)}
              slotProps={{ textField: { size: "small" } }}
            />
          </LocalizationProvider>
        </Stack>
      </Stack>

      <Grid2 container spacing={3}>
        {/* Video Player Area */}
        <Grid2 xs={12} lg={8}>
          <Card>
            <Box
              sx={{
                position: "relative",
                paddingTop: "56.25%", // 16:9 aspect ratio
                bgcolor: "black",
                borderRadius: 1,
                overflow: "hidden",
              }}
            >
              {/* Replay Visualization */}
              <Box
                sx={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`,
                }}
              >
                <Stack alignItems="center" spacing={2}>
                  <SportsEsports sx={{ fontSize: 80, color: "white", opacity: 0.8 }} />
                  <Typography variant="h5" color="white">
                    {currentSession.worldName}
                  </Typography>
                  <Typography variant="body1" color="white" sx={{ opacity: 0.9 }}>
                    {formatTime(currentTime)} / {formatTime(currentSession.duration)}
                  </Typography>
                </Stack>
              </Box>

              {/* Highlight Markers on Timeline */}
              <Box
                sx={{
                  position: "absolute",
                  bottom: 80,
                  left: 0,
                  right: 0,
                  height: 4,
                  bgcolor: "rgba(255,255,255,0.3)",
                }}
              >
                {currentSession.highlights.map((highlight) => (
                  <Box
                    key={highlight.id}
                    sx={{
                      position: "absolute",
                      left: `${(highlight.timestamp / currentSession.duration) * 100}%`,
                      top: -6,
                      width: 16,
                      height: 16,
                      borderRadius: "50%",
                      bgcolor:
                        highlight.importance === "high"
                          ? "warning.main"
                          : highlight.importance === "medium"
                          ? "info.main"
                          : "grey.500",
                      cursor: "pointer",
                      "&:hover": {
                        transform: "scale(1.3)",
                      },
                    }}
                    onClick={() => jumpToHighlight(highlight.timestamp)}
                  />
                ))}
              </Box>
            </Box>

            {/* Player Controls */}
            <CardContent>
              <Stack spacing={2}>
                <Slider
                  value={currentTime}
                  max={currentSession.duration}
                  onChange={(_, value) => handleSeek(value as number)}
                  sx={{ width: "100%" }}
                />
                <Stack direction="row" alignItems="center" justifyContent="center" spacing={2}>
                  <IconButton onClick={() => handleSeek(Math.max(0, currentTime - 30))}>
                    <SkipPrevious />
                  </IconButton>
                  <IconButton
                    onClick={handlePlayPause}
                    sx={{
                      bgcolor: "primary.main",
                      color: "white",
                      "&:hover": { bgcolor: "primary.dark" },
                    }}
                  >
                    {isPlaying ? <Pause /> : <PlayArrow />}
                  </IconButton>
                  <IconButton
                    onClick={() => handleSeek(Math.min(currentSession.duration, currentTime + 30))}
                  >
                    <SkipNext />
                  </IconButton>
                  <IconButton onClick={() => handleSeek(0)}>
                    <Replay />
                  </IconButton>
                  <FormControl size="small" sx={{ ml: 2, minWidth: 80 }}>
                    <Select
                      value={playbackSpeed}
                      onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                      size="small"
                    >
                      <MenuItem value={0.5}>0.5x</MenuItem>
                      <MenuItem value={1}>1x</MenuItem>
                      <MenuItem value={1.5}>1.5x</MenuItem>
                      <MenuItem value={2}>2x</MenuItem>
                    </Select>
                  </FormControl>
                  <IconButton sx={{ ml: "auto" }}>
                    <Download />
                  </IconButton>
                  <IconButton>
                    <Share />
                  </IconButton>
                  <IconButton>
                    <Fullscreen />
                  </IconButton>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {/* Session Tabs */}
          <Card sx={{ mt: 3 }}>
            <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
              <Tab label="Highlights" />
              <Tab label="Progress" />
              <Tab label="Interactions" />
              <Tab label="Achievements" />
            </Tabs>
            <CardContent>
              {activeTab === 0 && (
                <List>
                  {currentSession.highlights.map((highlight) => (
                    <React.Fragment key={highlight.id}>
                      <ListItemButton
                        selected={selectedHighlight === highlight.id}
                        onClick={() => {
                          setSelectedHighlight(highlight.id);
                          jumpToHighlight(highlight.timestamp);
                        }}
                      >
                        <ListItemIcon>{getHighlightIcon(highlight.type)}</ListItemIcon>
                        <ListItemText
                          primary={highlight.title}
                          secondary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="caption">
                                {formatTime(highlight.timestamp)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                • {highlight.description}
                              </Typography>
                            </Stack>
                          }
                        />
                        <Chip
                          label={highlight.importance}
                          size="small"
                          color={
                            highlight.importance === "high"
                              ? "error"
                              : highlight.importance === "medium"
                              ? "warning"
                              : "default"
                          }
                        />
                      </ListItemButton>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              )}

              {activeTab === 1 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Concept Mastery Progress
                  </Typography>
                  {Array.from(new Set(currentSession.progress.map((p) => p.concept))).map(
                    (concept) => {
                      const conceptProgress = currentSession.progress.filter(
                        (p) => p.concept === concept
                      );
                      const initial = conceptProgress[0]?.mastery || 0;
                      const final = conceptProgress[conceptProgress.length - 1]?.mastery || 0;
                      const improvement = final - initial;

                      return (
                        <Box key={concept} sx={{ mb: 2 }}>
                          <Stack direction="row" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">{concept}</Typography>
                            <Stack direction="row" spacing={1}>
                              <Chip
                                label={`${final}%`}
                                size="small"
                                color={final >= 80 ? "success" : "default"}
                              />
                              {improvement > 0 && (
                                <Chip
                                  label={`+${improvement}%`}
                                  size="small"
                                  color="success"
                                  variant="outlined"
                                />
                              )}
                            </Stack>
                          </Stack>
                          <LinearProgress variant="determinate" value={final} />
                        </Box>
                      );
                    }
                  )}
                </Box>
              )}

              {activeTab === 2 && (
                <List>
                  {currentSession.interactions.map((interaction) => (
                    <React.Fragment key={interaction.id}>
                      <ListItem>
                        <ListItemText
                          primary={interaction.details}
                          secondary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="caption">
                                {formatTime(interaction.timestamp)}
                              </Typography>
                              <Chip
                                label={interaction.outcome}
                                size="small"
                                color={interaction.outcome === "success" ? "success" : "warning"}
                              />
                            </Stack>
                          }
                        />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              )}

              {activeTab === 3 && (
                <List>
                  {currentSession.achievements.map((achievement) => (
                    <React.Fragment key={achievement.id}>
                      <ListItem>
                        <ListItemIcon>
                          <Typography variant="h5">{achievement.icon}</Typography>
                        </ListItemIcon>
                        <ListItemText
                          primary={achievement.name}
                          secondary={formatTime(achievement.timestamp)}
                        />
                        <Chip label={`+${achievement.xpReward} XP`} color="primary" />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid2>

        {/* Session Info Sidebar */}
        <Grid2 xs={12} lg={4}>
          {/* Session Overview */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Session Overview
              </Typography>
              <Stack spacing={2}>
                <Paper sx={{ p: 2, bgcolor: "primary.50" }}>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar src={currentSession.studentAvatar}>
                      {currentSession.studentName[0]}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">
                        {currentSession.studentName}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {currentSession.date.toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>

                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Duration
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {formatTime(currentSession.duration)}
                    </Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Overall Score
                    </Typography>
                    <Chip
                      label={`${currentSession.overallScore}%`}
                      size="small"
                      color={currentSession.overallScore >= 90 ? "success" : "primary"}
                    />
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      XP Earned
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="primary.main">
                      +{currentSession.xpEarned} XP
                    </Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Achievements
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {currentSession.achievements.length}
                    </Typography>
                  </Stack>
                </Stack>

                <Divider />

                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Mastered Concepts
                  </Typography>
                  <Stack direction="row" spacing={0.5} flexWrap="wrap">
                    {currentSession.masteryConcepts.map((concept) => (
                      <Chip key={concept} label={concept} size="small" variant="outlined" />
                    ))}
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          {/* Other Sessions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Other Sessions Today
              </Typography>
              <List>
                {sessions.slice(0, 3).map((session) => (
                  <ListItemButton
                    key={session.id}
                    selected={session.id === currentSession.id}
                    onClick={() => setCurrentSession(session)}
                  >
                    <ListItemIcon>
                      <SportsEsports />
                    </ListItemIcon>
                    <ListItemText
                      primary={session.worldName}
                      secondary={`${formatTime(session.duration)} • ${session.xpEarned} XP`}
                    />
                  </ListItemButton>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Insights */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                <Insights />
                <Typography variant="h6">AI Insights</Typography>
              </Stack>
              <Stack spacing={2}>
                <Alert severity="success">
                  Emma showed excellent problem-solving skills, particularly in the multiplication
                  section.
                </Alert>
                <Alert severity="info">
                  Consider more division practice. Emma needed multiple attempts but showed good
                  perseverance.
                </Alert>
                <Alert severity="warning">
                  Emma spent 5 minutes on one problem. This might indicate the need for additional
                  support in this area.
                </Alert>
              </Stack>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>
    </Box>
  );
}