import * as React from "react";
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  Stack,
  Chip,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  Box,
  IconButton,
  Tooltip,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import SearchIcon from "@mui/icons-material/Search";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import RemoveIcon from "@mui/icons-material/Remove";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import StarIcon from "@mui/icons-material/Star";
import { useAppSelector } from "../../store";
import { getLeaderboard } from "../../services/api";

interface LeaderboardEntry {
  rank: number;
  studentId: string;
  displayName: string;
  avatarUrl?: string;
  xp: number;
  level: number;
  badgeCount: number;
  streakDays: number;
  change: number; // Position change from last period
  classId?: string;
  className?: string;
}

export default function Leaderboard() {
  const currentUserId = useAppSelector((s) => s.user.userId);
  const [timeframe, setTimeframe] = React.useState<"daily" | "weekly" | "monthly" | "all">("weekly");
  const [searchTerm, setSearchTerm] = React.useState("");
  const [leaderboard, setLeaderboard] = React.useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    fetchLeaderboard();
  }, [timeframe]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      // Use mock data for demonstration
      setLeaderboard([
        {
          rank: 1,
          studentId: "student1",
          displayName: "Alex Johnson",
          avatarUrl: "/avatar1.png",
          xp: 3200,
          level: 32,
          badgeCount: 15,
          streakDays: 21,
          change: 0,
          className: "Math Grade 5A",
        },
        {
          rank: 2,
          studentId: "student2",
          displayName: "Sarah Williams",
          avatarUrl: "/avatar2.png",
          xp: 2850,
          level: 28,
          badgeCount: 13,
          streakDays: 14,
          change: 2,
          className: "Science Grade 6B",
        },
        {
          rank: 3,
          studentId: "student3",
          displayName: "Mike Chen",
          avatarUrl: "/avatar3.png",
          xp: 2450,
          level: 25,
          badgeCount: 12,
          streakDays: 7,
          change: -1,
          className: "Math Grade 5A",
        },
        {
          rank: 4,
          studentId: "student4",
          displayName: "Emma Davis",
          avatarUrl: "/avatar4.png",
          xp: 2380,
          level: 24,
          badgeCount: 11,
          streakDays: 18,
          change: 1,
          className: "Language Arts 4C",
        },
        {
          rank: 5,
          studentId: "student5",
          displayName: "James Wilson",
          avatarUrl: "/avatar5.png",
          xp: 2200,
          level: 22,
          badgeCount: 10,
          streakDays: 5,
          change: -2,
          className: "Technology 7A",
        },
        {
          rank: 6,
          studentId: "student6",
          displayName: "Olivia Brown",
          avatarUrl: "/avatar6.png",
          xp: 2150,
          level: 21,
          badgeCount: 9,
          streakDays: 12,
          change: 3,
          className: "Science Grade 6B",
        },
        {
          rank: 7,
          studentId: "student7",
          displayName: "William Garcia",
          avatarUrl: "/avatar7.png",
          xp: 2000,
          level: 20,
          badgeCount: 8,
          streakDays: 3,
          change: 0,
          className: "Math Grade 5A",
        },
        {
          rank: 8,
          studentId: "student8",
          displayName: "Sophia Martinez",
          avatarUrl: "/avatar8.png",
          xp: 1950,
          level: 19,
          badgeCount: 8,
          streakDays: 10,
          change: -1,
          className: "Language Arts 4C",
        },
      ]);
    } catch (error) {
      console.error("Failed to fetch leaderboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeframeChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimeframe: "daily" | "weekly" | "monthly" | "all" | null
  ) => {
    if (newTimeframe !== null) {
      setTimeframe(newTimeframe);
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <EmojiEventsIcon sx={{ color: "#FFD700", fontSize: 28 }} />;
      case 2:
        return <EmojiEventsIcon sx={{ color: "#C0C0C0", fontSize: 24 }} />;
      case 3:
        return <EmojiEventsIcon sx={{ color: "#CD7F32", fontSize: 20 }} />;
      default:
        return null;
    }
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) {
      return (
        <Chip
          icon={<TrendingUpIcon />}
          label={`+${change}`}
          size="small"
          color="success"
          sx={{ height: 20 }}
        />
      );
    } else if (change < 0) {
      return (
        <Chip
          icon={<TrendingDownIcon />}
          label={change}
          size="small"
          color="error"
          sx={{ height: 20 }}
        />
      );
    } else {
      return (
        <Chip
          icon={<RemoveIcon />}
          label="—"
          size="small"
          sx={{ height: 20 }}
        />
      );
    }
  };

  const filteredLeaderboard = leaderboard.filter((entry) =>
    entry.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.className?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Grid2 container spacing={3}>
      {/* Header */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Leaderboard
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  size="small"
                  placeholder="Search students..."
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
                <ToggleButtonGroup
                  value={timeframe}
                  exclusive
                  onChange={handleTimeframeChange}
                  aria-label="timeframe"
                  size="small"
                >
                  <ToggleButton value="daily" aria-label="daily">
                    Daily
                  </ToggleButton>
                  <ToggleButton value="weekly" aria-label="weekly">
                    Weekly
                  </ToggleButton>
                  <ToggleButton value="monthly" aria-label="monthly">
                    Monthly
                  </ToggleButton>
                  <ToggleButton value="all" aria-label="all time">
                    All Time
                  </ToggleButton>
                </ToggleButtonGroup>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Top 3 Podium */}
      <Grid2 size={12}>
        <Card sx={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" }}>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="center"
              alignItems="flex-end"
              gap={3}
              sx={{ py: 2 }}
            >
              {/* 2nd Place */}
              {leaderboard[1] && (
                <Box sx={{ textAlign: "center", order: { xs: 2, md: 1 } }}>
                  <Stack alignItems="center" spacing={1}>
                    <Typography variant="h4" sx={{ color: "white", opacity: 0.9 }}>
                      2nd
                    </Typography>
                    <Avatar
                      src={leaderboard[1].avatarUrl}
                      sx={{ width: 80, height: 80, border: "3px solid #C0C0C0" }}
                    />
                    <Typography variant="subtitle1" sx={{ color: "white", fontWeight: 600 }}>
                      {leaderboard[1].displayName}
                    </Typography>
                    <Typography variant="h6" sx={{ color: "white" }}>
                      {leaderboard[1].xp.toLocaleString()} XP
                    </Typography>
                  </Stack>
                </Box>
              )}

              {/* 1st Place */}
              {leaderboard[0] && (
                <Box sx={{ textAlign: "center", order: { xs: 1, md: 2 } }}>
                  <Stack alignItems="center" spacing={1}>
                    <EmojiEventsIcon sx={{ color: "#FFD700", fontSize: 48 }} />
                    <Avatar
                      src={leaderboard[0].avatarUrl}
                      sx={{ width: 100, height: 100, border: "3px solid #FFD700" }}
                    />
                    <Typography variant="h6" sx={{ color: "white", fontWeight: 700 }}>
                      {leaderboard[0].displayName}
                    </Typography>
                    <Typography variant="h5" sx={{ color: "white", fontWeight: 600 }}>
                      {leaderboard[0].xp.toLocaleString()} XP
                    </Typography>
                  </Stack>
                </Box>
              )}

              {/* 3rd Place */}
              {leaderboard[2] && (
                <Box sx={{ textAlign: "center", order: 3 }}>
                  <Stack alignItems="center" spacing={1}>
                    <Typography variant="h4" sx={{ color: "white", opacity: 0.9 }}>
                      3rd
                    </Typography>
                    <Avatar
                      src={leaderboard[2].avatarUrl}
                      sx={{ width: 80, height: 80, border: "3px solid #CD7F32" }}
                    />
                    <Typography variant="subtitle1" sx={{ color: "white", fontWeight: 600 }}>
                      {leaderboard[2].displayName}
                    </Typography>
                    <Typography variant="h6" sx={{ color: "white" }}>
                      {leaderboard[2].xp.toLocaleString()} XP
                    </Typography>
                  </Stack>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Full Leaderboard Table */}
      <Grid2 size={12}>
        <Card>
          <CardContent sx={{ p: 0 }}>
            <TableContainer>
              <Table aria-label="leaderboard table">
                <TableHead>
                  <TableRow>
                    <TableCell>Rank</TableCell>
                    <TableCell>Student</TableCell>
                    <TableCell>Class</TableCell>
                    <TableCell align="center">Level</TableCell>
                    <TableCell align="center">XP</TableCell>
                    <TableCell align="center">Badges</TableCell>
                    <TableCell align="center">Streak</TableCell>
                    <TableCell align="center">Trend</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center">
                        Loading leaderboard...
                      </TableCell>
                    </TableRow>
                  ) : filteredLeaderboard.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center">
                        No students found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredLeaderboard.map((entry) => (
                      <TableRow
                        key={entry.studentId}
                        hover
                        sx={{
                          bgcolor: entry.studentId === currentUserId ? "action.selected" : undefined,
                        }}
                      >
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            {getRankIcon(entry.rank)}
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              #{entry.rank}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={2}>
                            <Avatar src={entry.avatarUrl} />
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {entry.displayName}
                              {entry.studentId === currentUserId && (
                                <Chip
                                  label="You"
                                  size="small"
                                  color="primary"
                                  sx={{ ml: 1, height: 20 }}
                                />
                              )}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {entry.className}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={`Lvl ${entry.level}`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {entry.xp.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Stack direction="row" justifyContent="center" alignItems="center" spacing={0.5}>
                            <StarIcon sx={{ fontSize: 16, color: "warning.main" }} />
                            <Typography variant="body2">{entry.badgeCount}</Typography>
                          </Stack>
                        </TableCell>
                        <TableCell align="center">
                          <Stack direction="row" justifyContent="center" alignItems="center" spacing={0.5}>
                            <WhatshotIcon
                              sx={{
                                fontSize: 16,
                                color: entry.streakDays > 7 ? "error.main" : "text.secondary",
                              }}
                            />
                            <Typography variant="body2">{entry.streakDays}d</Typography>
                          </Stack>
                        </TableCell>
                        <TableCell align="center">{getTrendIcon(entry.change)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid2>
    </Grid2>
  );
}