import * as React from "react";
import { useEffect } from "react";
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
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import SearchIcon from "@mui/icons-material/Search";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import RemoveIcon from "@mui/icons-material/Remove";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import StarIcon from "@mui/icons-material/Star";
import { useAppSelector, useAppDispatch } from "../../store";
import { fetchLeaderboard, setLeaderboard } from "../../store/slices/gamificationSlice";
// import { wsService } from "../../services/ws";
import { sendWebSocketMessage, subscribeToChannel, unsubscribeFromChannel } from "../../services/websocket";
import { WebSocketMessageType } from "../../types/websocket";

export default function Leaderboard() {
  const dispatch = useAppDispatch();
  const currentUserId = useAppSelector((s) => s.user.userId);
  const currentClassId = useAppSelector((s) => s.user.classIds?.[0]);
  const { leaderboard, loading } = useAppSelector((s) => s.gamification);
  
  const [timeframe, setTimeframe] = React.useState<"daily" | "weekly" | "monthly" | "all">("weekly");
  const [searchTerm, setSearchTerm] = React.useState("");

  // Fetch leaderboard on mount and when timeframe changes
  useEffect(() => {
    dispatch(fetchLeaderboard({ classId: currentClassId, timeframe }));
  }, [dispatch, currentClassId, timeframe]);

  // Setup WebSocket listeners for real-time updates
  useEffect(() => {
    // Request initial leaderboard from realtime channel via server-triggered event
    void sendWebSocketMessage(WebSocketMessageType.REQUEST_LEADERBOARD, { classId: currentClassId }, { channel: 'public' });

    // Listen for leaderboard updates
    const handleLeaderboardUpdate = (message: any) => {
      const data = message.payload || message;
      dispatch(setLeaderboard(data.leaderboard || []));
    };

    const subLeaderboard = subscribeToChannel('public', handleLeaderboardUpdate, (msg) => msg.type === WebSocketMessageType.LEADERBOARD_UPDATE);

    const refresh = () => {
      dispatch(fetchLeaderboard({ classId: currentClassId, timeframe }));
    };

    const subXP = subscribeToChannel('public', refresh, (msg) => msg.type === WebSocketMessageType.XP_GAINED);
    const subBadge = subscribeToChannel('public', refresh, (msg) => msg.type === WebSocketMessageType.BADGE_EARNED);

    // Cleanup
    return () => {
      unsubscribeFromChannel(subLeaderboard);
      unsubscribeFromChannel(subXP);
      unsubscribeFromChannel(subBadge);
    };
  }, [dispatch, currentClassId, timeframe]);

  const handleTimeframeChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimeframe: "daily" | "weekly" | "monthly" | "all" | null
  ) => {
    void event;
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

  // Ensure leaderboard is always an array
  const leaderboardArray = Array.isArray(leaderboard) ? leaderboard : [];
  const filteredLeaderboard = leaderboardArray.filter((entry: any) =>
    entry.displayName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entry.className?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
      <Grid2 xs={12}>
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
              {leaderboard?.[1] && (
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
                      {leaderboard[1].xp?.toLocaleString() || 0} XP
                    </Typography>
                  </Stack>
                </Box>
              )}

              {/* 1st Place */}
              {leaderboard?.[0] && (
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
                      {leaderboard[0].xp?.toLocaleString() || 0} XP
                    </Typography>
                  </Stack>
                </Box>
              )}

              {/* 3rd Place */}
              {leaderboard?.[2] && (
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
                      {leaderboard[2].xp?.toLocaleString() || 0} XP
                    </Typography>
                  </Stack>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Full Leaderboard Table */}
      <Grid2 xs={12}>
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
                    filteredLeaderboard.map((entry: any) => (
                      <TableRow
                        key={entry.userId || entry.studentId || entry.id}
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
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {entry.displayName}
                              </Typography>
                              {(entry.userId === currentUserId || entry.studentId === currentUserId) && (
                                <Chip
                                  label="You"
                                  size="small"
                                  color="primary"
                                  sx={{ ml: 1, height: 20 }}
                                />
                              )}
                            </Box>
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
                            <Typography variant="body2">{entry.badgesCount || entry.badgeCount || 0}</Typography>
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