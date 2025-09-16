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
import { listClasses, createClass } from "../../services/api";
import { useApiData } from "../../hooks/useApiData";
import { ROUTES, getClassDetailsRoute } from "../../config/routes";
import CreateClassDialog from "../dialogs/CreateClassDialog";
import StudentProgressTracker from "../widgets/StudentProgressTracker";
import VirtualizedList from "../common/VirtualizedList";
import { performanceUtils } from "../common/PerformanceMonitor";

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

// Memoized class card component for better performance
const ClassCard = React.memo<{
  classData: ClassCardData;
  onMenuClick: (event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => void;
  onCardClick: (classData: ClassCardData) => void;
}>(({ classData, onMenuClick, onCardClick }) => {
  const handleMenuClick = React.useCallback((event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    onMenuClick(event, classData);
  }, [onMenuClick, classData]);

  const handleCardClick = React.useCallback(() => {
    onCardClick(classData);
  }, [onCardClick, classData]);

  const performanceMark = React.useMemo(() => performanceUtils.measureComponent('ClassCard'), []);

  React.useEffect(() => {
    performanceMark.start();
    return () => {
      performanceMark.end();
    };
  }, [performanceMark]);

  return (
    <Card
      onClick={handleCardClick}
      sx={{
        cursor: "pointer",
        transition: "all 0.2s ease-in-out",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: 3,
        },
        margin: 1,
        height: "280px", // Fixed height for virtual scrolling
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h2" noWrap>
            {classData.name}
          </Typography>
          <IconButton size="small" onClick={handleMenuClick}>
            <MoreVertIcon />
          </IconButton>
        </Box>

        <Stack spacing={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <PeopleIcon color="primary" />
            <Typography variant="body2" color="text.secondary">
              Grade {classData.grade} • {classData.studentCount} students
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <ScheduleIcon color="action" />
            <Typography variant="body2" color="text.secondary" noWrap>
              {classData.schedule}
            </Typography>
          </Box>

          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                Progress
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {Math.round(classData.completionRate * 100)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={classData.completionRate * 100}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <TrendingUpIcon color="success" />
            <Typography variant="body2" color="text.secondary">
              Avg XP: {classData.averageXP}
            </Typography>
            <Chip
              size="small"
              label={classData.isOnline ? "Online" : "Offline"}
              color={classData.isOnline ? "success" : "default"}
              variant="outlined"
            />
          </Box>

          {classData.studentAvatars.length > 0 && (
            <AvatarGroup max={4} sx={{ justifyContent: "flex-start" }}>
              {classData.studentAvatars.map((avatar, index) => (
                <Avatar key={index} src={avatar} sx={{ width: 24, height: 24 }} />
              ))}
            </AvatarGroup>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
});

ClassCard.displayName = 'ClassCard';

// Memoized search and filters component
const ClassFilters = React.memo<{
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onCreateClass: () => void;
}>(({ searchTerm, onSearchChange, onCreateClass }) => {
  const handleSearchChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    onSearchChange(event.target.value);
  }, [onSearchChange]);

  return (
    <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
      <TextField
        placeholder="Search classes..."
        value={searchTerm}
        onChange={handleSearchChange}
        size="small"
        sx={{ minWidth: 300 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />
      <Button
        variant="contained"
        startIcon={<AddIcon />}
        onClick={onCreateClass}
        sx={{ minWidth: 140 }}
      >
        New Class
      </Button>
    </Box>
  );
});

ClassFilters.displayName = 'ClassFilters';

export default function ClassesOptimized() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);

  // State management with useState
  const [classes, setClassesState] = React.useState<ClassCardData[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedClass, setSelectedClass] = React.useState<ClassCardData | null>(null);
  const [createClassOpen, setCreateClassOpen] = React.useState(false);

  // Performance tracking
  const performanceMark = React.useMemo(() => performanceUtils.measureComponent('ClassesPage'), []);

  React.useEffect(() => {
    performanceMark.start();
    fetchClasses();
    return () => {
      performanceMark.end();
    };
  }, [performanceMark]);

  // Memoized filtered classes for performance
  const filteredClasses = React.useMemo(() => {
    if (!searchTerm) return classes;

    const lowercaseSearch = searchTerm.toLowerCase();
    return classes.filter(classItem =>
      classItem.name.toLowerCase().includes(lowercaseSearch) ||
      classItem.grade.toString().includes(lowercaseSearch) ||
      classItem.schedule.toLowerCase().includes(lowercaseSearch)
    );
  }, [classes, searchTerm]);

  // Optimized fetch function with useCallback
  const fetchClasses = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await listClasses();

      // Transform API response to match component interface
      const transformedClasses: ClassCardData[] = data.map((classItem: any) => ({
        id: classItem.id,
        name: classItem.name,
        grade: classItem.grade_level || classItem.grade,
        studentCount: classItem.student_count || classItem.studentCount || 0,
        schedule: classItem.schedule || "Schedule not set",
        averageXP: Math.round((classItem.average_progress || 0) * 100),
        completionRate: classItem.average_progress || 0,
        nextLesson: classItem.next_lesson || "No upcoming lessons",
        isOnline: classItem.is_online || false,
        studentAvatars: [], // Will be populated when we have student endpoints
      }));

      setClassesState(transformedClasses);
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

      dispatch(addNotification({
        type: "error",
        message: errorMessage,
      }));
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  // Memoized event handlers
  const handleMenuClick = React.useCallback((event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => {
    setAnchorEl(event.currentTarget);
    setSelectedClass(classData);
  }, []);

  const handleMenuClose = React.useCallback(() => {
    setAnchorEl(null);
    setSelectedClass(null);
  }, []);

  const handleCardClick = React.useCallback((classData: ClassCardData) => {
    navigate(getClassDetailsRoute(classData.id));
  }, [navigate]);

  const handleCreateClass = React.useCallback(() => {
    setCreateClassOpen(true);
  }, []);

  const handleCreateClassClose = React.useCallback(() => {
    setCreateClassOpen(false);
  }, []);

  const handleCreateClassSuccess = React.useCallback(() => {
    setCreateClassOpen(false);
    fetchClasses();
  }, [fetchClasses]);

  const handleDeleteClass = React.useCallback(async () => {
    if (selectedClass) {
      try {
        // TODO: Implement delete API call
        setClassesState(prev => prev.filter(c => c.id !== selectedClass.id));
        dispatch(addNotification({
          type: "success",
          message: "Class deleted successfully",
        }));
      } catch (error) {
        dispatch(addNotification({
          type: "error",
          message: "Failed to delete class",
        }));
      }
    }
    handleMenuClose();
  }, [selectedClass, dispatch, handleMenuClose]);

  // Render item function for virtualized list
  const renderClassItem = React.useCallback((item: ClassCardData, index: number) => (
    <ClassCard
      key={item.id}
      classData={item}
      onMenuClick={handleMenuClick}
      onCardClick={handleCardClick}
    />
  ), [handleMenuClick, handleCardClick]);

  if (loading && classes.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <Typography>Loading classes...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Classes
        </Typography>
        <Button
          variant="outlined"
          onClick={fetchClasses}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <ClassFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onCreateClass={handleCreateClass}
      />

      {/* Use VirtualizedList for large datasets */}
      {filteredClasses.length > 20 ? (
        <VirtualizedList
          items={filteredClasses}
          itemHeight={300} // Include margins
          height={600}
          renderItem={renderClassItem}
          overscanCount={5}
        />
      ) : (
        /* Use regular grid for smaller datasets */
        <Grid container spacing={2}>
          {filteredClasses.map((classData) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={classData.id}>
              <ClassCard
                classData={classData}
                onMenuClick={handleMenuClick}
                onCardClick={handleCardClick}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {filteredClasses.length === 0 && !loading && (
        <Box display="flex" justifyContent="center" alignItems="center" height="200px">
          <Typography color="text.secondary">
            {searchTerm ? 'No classes match your search.' : 'No classes available.'}
          </Typography>
        </Box>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedClass && handleCardClick(selectedClass)}>
          <VisibilityIcon sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <EditIcon sx={{ mr: 1 }} />
          Edit Class
        </MenuItem>
        <MenuItem onClick={handleDeleteClass}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Class
        </MenuItem>
      </Menu>

      {/* Create Class Dialog */}
      <CreateClassDialog
        open={createClassOpen}
        onClose={handleCreateClassClose}
        onSuccess={handleCreateClassSuccess}
      />
    </Box>
  );
}