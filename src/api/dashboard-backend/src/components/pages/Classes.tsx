import * as React from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Avatar,
  AvatarGroup,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Box,
  LinearProgress,
  TextField,
  InputAdornment,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import PeopleIcon from "@mui/icons-material/People";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ScheduleIcon from "@mui/icons-material/Schedule";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import VisibilityIcon from "@mui/icons-material/Visibility";
import { useAppDispatch, useAppSelector } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import { listClasses } from "../../services/api";

interface ClassCardData {
  id: string;
  name: string;
  grade: number;
  studentCount: number;
  schedule: string;
  averageXP: number;
  completionRate: number;
  nextLesson: string;
  isOnline: boolean;
  studentAvatars: string[];
}

export default function Classes() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
  const [classes, setClasses] = React.useState<ClassCardData[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedClass, setSelectedClass] = React.useState<ClassCardData | null>(null);

  React.useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    setLoading(true);
    try {
      // Use mock data for demonstration
      setClasses([
        {
          id: "class1",
          name: "Math Grade 5A",
          grade: 5,
          studentCount: 24,
          schedule: "Mon, Wed, Fri - 10:00 AM",
          averageXP: 1850,
          completionRate: 78,
          nextLesson: "Fractions & Decimals",
          isOnline: true,
          studentAvatars: ["/avatar1.png", "/avatar2.png", "/avatar3.png"],
        },
        {
          id: "class2",
          name: "Science Grade 6B",
          grade: 6,
          studentCount: 22,
          schedule: "Tue, Thu - 2:00 PM",
          averageXP: 2100,
          completionRate: 85,
          nextLesson: "Solar System",
          isOnline: false,
          studentAvatars: ["/avatar4.png", "/avatar5.png", "/avatar6.png"],
        },
        {
          id: "class3",
          name: "Language Arts 4C",
          grade: 4,
          studentCount: 26,
          schedule: "Daily - 11:00 AM",
          averageXP: 1650,
          completionRate: 72,
          nextLesson: "Creative Writing",
          isOnline: true,
          studentAvatars: ["/avatar7.png", "/avatar8.png", "/avatar9.png"],
        },
        {
          id: "class4",
          name: "Technology 7A",
          grade: 7,
          studentCount: 20,
          schedule: "Mon, Fri - 1:00 PM",
          averageXP: 2450,
          completionRate: 92,
          nextLesson: "Coding Basics",
          isOnline: false,
          studentAvatars: ["/avatar10.png", "/avatar11.png", "/avatar12.png"],
        },
      ]);
    } catch (error) {
      console.error("Failed to fetch classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => {
    setAnchorEl(event.currentTarget);
    setSelectedClass(classData);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedClass(null);
  };

  const handlePushToRoblox = (classData: ClassCardData) => {
    dispatch(
      addNotification({
        type: "success",
        message: `Class "${classData.name}" pushed to Roblox successfully`,
      })
    );
    handleMenuClose();
  };

  const handleDeleteClass = (classData: ClassCardData) => {
    if (window.confirm(`Are you sure you want to delete "${classData.name}"?`)) {
      dispatch(
        addNotification({
          type: "success",
          message: `Class "${classData.name}" deleted successfully`,
        })
      );
      setClasses(classes.filter((c) => c.id !== classData.id));
    }
    handleMenuClose();
  };

  const filteredClasses = classes.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
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
                My Classes
              </Typography>
              <Stack direction="row" gap={2} sx={{ width: { xs: "100%", md: "auto" } }}>
                <TextField
                  size="small"
                  placeholder="Search classes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{ minWidth: 250 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                {role === "Teacher" && (
                  <Button variant="contained" startIcon={<AddIcon />}>
                    Create Class
                  </Button>
                )}
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Stats Overview */}
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Total Students
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {classes.reduce((sum, c) => sum + c.studentCount, 0)}
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Active Classes
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {classes.length}
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Average XP
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {Math.round(
                  classes.reduce((sum, c) => sum + c.averageXP, 0) / classes.length || 0
                )}
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Avg Completion
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {Math.round(
                  classes.reduce((sum, c) => sum + c.completionRate, 0) / classes.length || 0
                )}
                %
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Class Cards */}
      {loading ? (
        <Grid2 size={12}>
          <Typography>Loading classes...</Typography>
        </Grid2>
      ) : filteredClasses.length === 0 ? (
        <Grid2 size={12}>
          <Card>
            <CardContent>
              <Typography align="center" color="text.secondary">
                No classes found. Create your first class to get started!
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
      ) : (
        filteredClasses.map((classData) => (
          <Grid2 key={classData.id} size={{ xs: 12, md: 6, lg: 4 }}>
            <Card
              sx={{
                height: "100%",
                transition: "all 0.3s",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Stack spacing={2}>
                  {/* Header */}
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                    <Stack>
                      <Stack direction="row" alignItems="center" gap={1}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {classData.name}
                        </Typography>
                        {classData.isOnline && (
                          <Chip
                            label="Online"
                            size="small"
                            color="success"
                            sx={{ height: 20 }}
                          />
                        )}
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        Grade {classData.grade} • {classData.schedule}
                      </Typography>
                    </Stack>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, classData)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </Stack>

                  {/* Students */}
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <AvatarGroup max={4} sx={{ "& .MuiAvatar-root": { width: 32, height: 32 } }}>
                      {classData.studentAvatars.map((avatar, index) => (
                        <Avatar key={index} src={avatar} />
                      ))}
                    </AvatarGroup>
                    <Stack>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {classData.studentCount} Students
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Avg. {classData.averageXP} XP
                      </Typography>
                    </Stack>
                  </Stack>

                  {/* Progress */}
                  <Box>
                    <Stack direction="row" justifyContent="space-between" mb={0.5}>
                      <Typography variant="caption" color="text.secondary">
                        Completion Rate
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {classData.completionRate}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={classData.completionRate}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  {/* Next Lesson */}
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: "background.default",
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      Next Lesson
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {classData.nextLesson}
                    </Typography>
                  </Box>

                  {/* Actions */}
                  <Stack direction="row" gap={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<VisibilityIcon />}
                      sx={{ flex: 1 }}
                    >
                      View
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<RocketLaunchIcon />}
                      sx={{ flex: 1 }}
                      onClick={() => handlePushToRoblox(classData)}
                    >
                      Roblox
                    </Button>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
        ))
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <VisibilityIcon fontSize="small" sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit Class
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <PeopleIcon fontSize="small" sx={{ mr: 1 }} />
          Manage Students
        </MenuItem>
        {selectedClass && !selectedClass.isOnline && (
          <MenuItem onClick={() => selectedClass && handlePushToRoblox(selectedClass)}>
            <RocketLaunchIcon fontSize="small" sx={{ mr: 1 }} />
            Push to Roblox
          </MenuItem>
        )}
        <MenuItem
          onClick={() => selectedClass && handleDeleteClass(selectedClass)}
          sx={{ color: "error.main" }}
        >
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete Class
        </MenuItem>
      </Menu>
    </Grid2>
  );
}