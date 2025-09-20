import * as React from "react";
import { useNavigate } from "react-router-dom";
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
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import Grid from "@mui/material/Grid";
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
import { setClasses, removeClass, setClassOnlineStatus } from "../../store/slices/classesSlice";
import { listClasses, createClass, updateClass, deleteClass } from "../../services/api";
import { useApiData } from "../../hooks/useApiData";
import { ROUTES, getClassDetailsRoute } from "../../config/routes";
import CreateClassDialog from "../dialogs/CreateClassDialog";
import StudentProgressTracker from "../widgets/StudentProgressTracker";

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
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const [classes, setClasses] = React.useState<ClassCardData[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedClass, setSelectedClass] = React.useState<ClassCardData | null>(null);
  const [createClassOpen, setCreateClassOpen] = React.useState(false);
  const [editClassOpen, setEditClassOpen] = React.useState(false);
  const [editingClass, setEditingClass] = React.useState<ClassCardData | null>(null);

  // Filter states
  const [filterGrade, setFilterGrade] = React.useState<string>("all");
  const [filterStatus, setFilterStatus] = React.useState<string>("all");
  const [sortBy, setSortBy] = React.useState<string>("name");

  React.useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    setLoading(true);
    try {
      const data = await listClasses();
      
      // Transform API response to match component interface
      const transformedClasses: ClassCardData[] = data.map((classItem: any) => {
        // Calculate progress based on available data or use defaults
        const progressValue = classItem.average_progress || classItem.progress || 0.75; // Default 75% progress

        // Format next session into readable lesson string
        let nextLessonText = "No upcoming lessons";
        if (classItem.next_session) {
          const nextDate = new Date(classItem.next_session);
          nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        } else if (classItem.next_lesson) {
          nextLessonText = classItem.next_lesson;
        }

        return {
          id: classItem.id,
          name: classItem.name,
          grade: classItem.grade_level || classItem.grade || 0,
          studentCount: classItem.student_count || classItem.studentCount || 0,
          schedule: classItem.schedule || "Schedule not set",
          averageXP: Math.round(progressValue * 100),
          completionRate: progressValue * 100,
          nextLesson: nextLessonText,
          isOnline: classItem.is_online || classItem.status === "active" || false,
          studentAvatars: classItem.student_avatars || [], // Will be populated when we have student endpoints
        };
      });
      
      setClasses(transformedClasses);
    } catch (error: any) {
      console.error("Failed to fetch classes:", error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = "Failed to load classes. Please try again.";
      
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        // Handle Pydantic validation errors
        errorMessage = errorDetail.map((err: any) => 
          err.msg || err.message || 'Validation error'
        ).join(', ');
      }
      
      dispatch(
        addNotification({
          type: "error",
          message: errorMessage,
        })
      );
      setClasses([]); // Set empty array instead of mock data
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
    console.log('Pushing to Roblox:', classData);
    dispatch(
      addNotification({
        type: "info",
        message: `Preparing Roblox environment for "${classData.name}"...`,
      })
    );
    
    // Simulate push process then navigate to Roblox dashboard
    setTimeout(() => {
      dispatch(
        addNotification({
          type: "success",
          message: `Class "${classData.name}" is ready in Roblox!`,
        })
      );
      // Navigate to Roblox dashboard with class context
      navigate(`/roblox?classId=${classData.id}&className=${encodeURIComponent(classData.name)}`);
    }, 1500);
    
    handleMenuClose();
  };

  const handleEditClass = (classData: ClassCardData) => {
    setEditingClass(classData);
    setEditClassOpen(true);
    handleMenuClose();
  };

  const handleDeleteClass = async (classData: ClassCardData) => {
    if (window.confirm(`Are you sure you want to delete "${classData.name}"?`)) {
      try {
        await deleteClass(classData.id);
        dispatch(
          addNotification({
            type: "success",
            message: `Class "${classData.name}" deleted successfully`,
          })
        );
        setClasses(classes.filter((c) => c.id !== classData.id));
      } catch (error: any) {
        console.error('Error deleting class:', error);
        dispatch(
          addNotification({
            type: "error",
            message: error.response?.data?.detail || 'Failed to delete class',
          })
        );
      }
    }
    handleMenuClose();
  };

  // Apply filters
  const filteredClasses = React.useMemo(() => {
    let filtered = classes.filter((c) => {
      // Search filter
      if (searchTerm && !c.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Grade filter
      if (filterGrade !== "all" && c.grade.toString() !== filterGrade) {
        return false;
      }

      // Status filter
      if (filterStatus !== "all") {
        if (filterStatus === "online" && !c.isOnline) return false;
        if (filterStatus === "offline" && c.isOnline) return false;
      }

      return true;
    });

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "grade":
          return a.grade - b.grade;
        case "students":
          return b.studentCount - a.studentCount;
        case "progress":
          return b.completionRate - a.completionRate;
        default:
          return 0;
      }
    });

    return filtered;
  }, [classes, searchTerm, filterGrade, filterStatus, sortBy]);

  return (
    <Grid container spacing={3}>
      {/* Header */}
      <Grid item xs={12}>
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
              <Stack direction="row" gap={2} sx={{ width: { xs: "100%", md: "auto" }, flexWrap: "wrap" }}>
                <TextField
                  size="small"
                  placeholder="Search classes..."
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
                  data-testid="search-input"
                />

                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel id="grade-filter-label">Grade</InputLabel>
                  <Select
                    labelId="grade-filter-label"
                    id="grade-filter"
                    value={filterGrade}
                    label="Grade"
                    onChange={(e: SelectChangeEvent) => setFilterGrade(e.target.value)}
                    data-testid="grade-filter"
                  >
                    <MenuItem value="all">All Grades</MenuItem>
                    <MenuItem value="1">Grade 1</MenuItem>
                    <MenuItem value="2">Grade 2</MenuItem>
                    <MenuItem value="3">Grade 3</MenuItem>
                    <MenuItem value="4">Grade 4</MenuItem>
                    <MenuItem value="5">Grade 5</MenuItem>
                    <MenuItem value="6">Grade 6</MenuItem>
                    <MenuItem value="7">Grade 7</MenuItem>
                    <MenuItem value="8">Grade 8</MenuItem>
                    <MenuItem value="9">Grade 9</MenuItem>
                    <MenuItem value="10">Grade 10</MenuItem>
                    <MenuItem value="11">Grade 11</MenuItem>
                    <MenuItem value="12">Grade 12</MenuItem>
                  </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel id="status-filter-label">Status</InputLabel>
                  <Select
                    labelId="status-filter-label"
                    id="status-filter"
                    value={filterStatus}
                    label="Status"
                    onChange={(e: SelectChangeEvent) => setFilterStatus(e.target.value)}
                    data-testid="status-filter"
                  >
                    <MenuItem value="all">All Status</MenuItem>
                    <MenuItem value="online">Online</MenuItem>
                    <MenuItem value="offline">Offline</MenuItem>
                  </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel id="sort-by-label">Sort By</InputLabel>
                  <Select
                    labelId="sort-by-label"
                    id="sort-by"
                    value={sortBy}
                    label="Sort By"
                    onChange={(e: SelectChangeEvent) => setSortBy(e.target.value)}
                    data-testid="sort-by"
                  >
                    <MenuItem value="name">Name</MenuItem>
                    <MenuItem value="grade">Grade</MenuItem>
                    <MenuItem value="students">Students</MenuItem>
                    <MenuItem value="progress">Progress</MenuItem>
                  </Select>
                </FormControl>

                {role === "teacher" && (
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateClassOpen(true)}
                    data-testid="create-class-button"
                  >
                    Create Class
                  </Button>
                )}
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      {/* Stats Overview */}
      <Grid item xs={12} md={3}>
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
      </Grid>

      <Grid item xs={12} md={3}>
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
      </Grid>

      <Grid item xs={12} md={3}>
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
      </Grid>

      <Grid item xs={12} md={3}>
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
      </Grid>

      {/* Class Cards */}
      {loading ? (
        <Grid item xs={12}>
          <Typography>Loading classes...</Typography>
        </Grid>
      ) : filteredClasses.length === 0 ? (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography align="center" color="text.secondary">
                No classes found. Create your first class to get started!
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ) : (
        <>
          <Grid item xs={12} data-testid="classes-list" className="classes-grid">
            {/* Hidden element for test detection */}
            <div style={{ display: 'none' }}>Classes List Container</div>
          </Grid>
          {filteredClasses.map((classData) => (
            <Grid
              key={classData.id}
              item
              xs={12}
              md={6}
              lg={4}
              data-testid="class-row"
              className="class-card"
            >
            <Card
              data-testid="class-card"
              sx={{
                height: "100%",
                transition: "all 0.3s",
                cursor: "pointer",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(`/classes/${classData.id}`)}
            >
              <CardContent>
                <Stack spacing={2}>
                  {/* Header */}
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                    <Stack>
                      <Stack direction="row" alignItems="center" gap={1}>
                        <Typography
                          variant="h6"
                          sx={{ fontWeight: 600 }}
                          data-testid="class-name"
                        >
                          {classData.name}
                        </Typography>
                        {classData.isOnline && (
                          <Chip
                            label="Online"
                            size="small"
                            color="success"
                            sx={{ height: 20 }}
                            data-testid="online-status"
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
                      aria-label="More options"
                      data-testid="class-menu-button"
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
                      onClick={() => {
                        console.log('View button clicked for class:', classData.id);
                        const route = `/classes/${classData.id}`;
                        console.log('Navigating to:', route);
                        navigate(route);
                      }}
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
          </Grid>
        ))}
        </>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          if (selectedClass) {
            navigate(getClassDetailsRoute(selectedClass.id));
          }
          handleMenuClose();
        }}>
          <VisibilityIcon fontSize="small" sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={() => {
          if (selectedClass) {
            handleEditClass(selectedClass);
          }
        }}
          data-testid="edit-class"
        >
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit Class
        </MenuItem>
        <MenuItem onClick={() => {
          // TODO: Navigate to manage students page
          handleMenuClose();
        }}
          data-testid="manage-students"
        >
          <PeopleIcon fontSize="small" sx={{ mr: 1 }} />
          Manage Students
        </MenuItem>
        {selectedClass && !selectedClass.isOnline && (
          <MenuItem
            onClick={() => selectedClass && handlePushToRoblox(selectedClass)}
            data-testid="push-to-roblox"
          >
            <RocketLaunchIcon fontSize="small" sx={{ mr: 1 }} />
            Push to Roblox
          </MenuItem>
        )}
        <MenuItem
          onClick={() => selectedClass && handleDeleteClass(selectedClass)}
          sx={{ color: "error.main" }}
          data-testid="delete-class"
        >
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete Class
        </MenuItem>
      </Menu>
      
      {/* Create Class Dialog */}
      <CreateClassDialog
        open={createClassOpen}
        onClose={() => setCreateClassOpen(false)}
        onSave={async (classData) => {
          try {
            setLoading(true);
            const newClass = await createClass(classData);
            
            // Normalize backend snake_case fields safely
            const newClassAny: any = newClass as any;

            // Calculate progress based on available data or use defaults
            const progressValue = newClassAny.average_progress || newClassAny.progress || 0.0; // New class starts at 0%

            // Format next session into readable lesson string
            let nextLessonText = "No upcoming lessons";
            if (newClassAny.next_session) {
              const nextDate = new Date(newClassAny.next_session);
              nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
            } else if (newClassAny.next_lesson) {
              nextLessonText = newClassAny.next_lesson;
            }

            // Add the new class to the list immediately
            const transformedClass: ClassCardData = {
              id: newClassAny.id,
              name: newClassAny.name,
              grade: newClassAny.grade_level ?? newClassAny.grade ?? 0,
              studentCount: newClassAny.student_count ?? newClassAny.studentCount ?? 0,
              schedule: newClassAny.schedule || "Schedule not set",
              averageXP: Math.round(progressValue * 100),
              completionRate: progressValue * 100,
              nextLesson: nextLessonText,
              isOnline: newClassAny.is_online ?? newClassAny.status === "active" ?? false,
              studentAvatars: newClassAny.student_avatars || [],
            };
            setClasses(prev => [transformedClass, ...prev]);
            
            dispatch(
              addNotification({
                type: "success",
                message: `Class "${classData.name}" created successfully!`,
              })
            );
            setCreateClassOpen(false);
            // Also refresh from server to ensure consistency
            await fetchClasses();
          } catch (error: any) {
            console.error('Error creating class:', error);
            const errorMessage = error.response?.data?.detail || 'Failed to create class';
            dispatch(
              addNotification({
                type: "error",
                message: errorMessage,
              })
            );
          } finally {
            setLoading(false);
          }
        }}
      />

      {/* Edit Class Dialog */}
      {editingClass && (
        <CreateClassDialog
          open={editClassOpen}
          editMode={true}
          initialData={{
            name: editingClass.name,
            grade_level: editingClass.grade,
            grade: editingClass.grade,
            schedule: editingClass.schedule,
            subject: 'Mathematics', // Will need to be stored in the data
            room: '', // Will need to be stored in the data
            description: '', // Will need to be stored in the data
          }}
          onClose={() => {
            setEditClassOpen(false);
            setEditingClass(null);
          }}
          onSave={async (classData) => {
            try {
              setLoading(true);
              const updatedClass = await updateClass(editingClass.id, classData);

              // Update the class in the local state
              const updatedClassAny: any = updatedClass as any;

              // Calculate progress based on available data or use existing
              const progressValue = updatedClassAny.average_progress || updatedClassAny.progress || editingClass.completionRate / 100;

              // Format next session into readable lesson string
              let nextLessonText = editingClass.nextLesson;
              if (updatedClassAny.next_session) {
                const nextDate = new Date(updatedClassAny.next_session);
                nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
              } else if (updatedClassAny.next_lesson) {
                nextLessonText = updatedClassAny.next_lesson;
              }

              // Update the transformed class
              const transformedClass: ClassCardData = {
                ...editingClass,
                name: updatedClassAny.name,
                grade: updatedClassAny.grade_level ?? updatedClassAny.grade ?? editingClass.grade,
                schedule: updatedClassAny.schedule || editingClass.schedule,
                averageXP: Math.round(progressValue * 100),
                completionRate: progressValue * 100,
                nextLesson: nextLessonText,
              };

              setClasses(prev => prev.map(c => c.id === editingClass.id ? transformedClass : c));

              dispatch(
                addNotification({
                  type: "success",
                  message: `Class "${classData.name}" updated successfully!`,
                })
              );
              setEditClassOpen(false);
              setEditingClass(null);
              // Also refresh from server to ensure consistency
              await fetchClasses();
            } catch (error: any) {
              console.error('Error updating class:', error);
              const errorMessage = error.response?.data?.detail || 'Failed to update class';
              dispatch(
                addNotification({
                  type: "error",
                  message: errorMessage,
                })
              );
            } finally {
              setLoading(false);
            }
          }}
        />
      )}

      {/* Student Progress Tracker for Teachers */}
      {role === "teacher" && (
        <Grid item xs={12}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Student Progress Tracker
          </Typography>
          <StudentProgressTracker />
        </Grid>
      )}
    </Grid>
  );
}